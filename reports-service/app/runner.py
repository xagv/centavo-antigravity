"""Ejecutor de generación de reporte mensual (para ejecuciones programadas o CLI)."""
import calendar
import datetime as dt
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .db import Base, SessionLocal, engine
from .models import Report
from .routes import (
    _build_category_breakdown,
    _resolve_budget_by_category,
    _serialize_report,
    _write_report_files,
)

ROOT_DIR = Path(__file__).resolve().parents[2]
TX_DB_PATH = ROOT_DIR / "transactions-service" / "transactions.db"
BUDGETS_DB_PATH = ROOT_DIR / "budgets-service" / "budgets.db"
AUTH_DB_PATH = ROOT_DIR / "auth-service" / "auth.db"


def _load_users_and_data(date_from: dt.date, date_to: dt.date) -> dict[str, tuple[list[dict], list[dict]]]:
    user_ids: set[str] = set()
    tx_by_user: dict[str, list[dict]] = {}
    budgets_by_user: dict[str, list[dict]] = {}

    if AUTH_DB_PATH.exists():
        with sqlite3.connect(AUTH_DB_PATH) as con:
            con.row_factory = sqlite3.Row
            tables = {r["name"] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if "users" in tables:
                for row in con.execute("SELECT id FROM users"):
                    user_ids.add(str(row["id"]))

    if TX_DB_PATH.exists():
        with sqlite3.connect(TX_DB_PATH) as con:
            con.row_factory = sqlite3.Row
            tables = {r["name"] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if "transactions" in tables:
                rows = con.execute(
                    "SELECT id, user_id, amount, category, date FROM transactions WHERE date >= ? AND date <= ?",
                    (date_from.isoformat(), date_to.isoformat()),
                ).fetchall()
                for row in rows:
                    uid = str(row["user_id"])
                    user_ids.add(uid)
                    tx_by_user.setdefault(uid, []).append(dict(row))

    if BUDGETS_DB_PATH.exists():
        with sqlite3.connect(BUDGETS_DB_PATH) as con:
            con.row_factory = sqlite3.Row
            tables = {r["name"] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if "budgets" in tables:
                rows = con.execute(
                    "SELECT id, user_id, category, limit_amount, period FROM budgets ORDER BY created_at DESC"
                ).fetchall()
                for row in rows:
                    uid = str(row["user_id"])
                    user_ids.add(uid)
                    budgets_by_user.setdefault(uid, []).append(dict(row))

    if not user_ids:
        user_ids.add("system")

    return {uid: (tx_by_user.get(uid, []), budgets_by_user.get(uid, [])) for uid in sorted(user_ids)}


def run_hourly_report() -> list[dict]:
    Base.metadata.create_all(engine)
    today = datetime.now(timezone.utc).date()
    year, month = today.year, today.month
    last_day = calendar.monthrange(year, month)[1]
    date_from = dt.date(year, month, 1)
    date_to = dt.date(year, month, last_day)
    month_key = f"{year:04d}-{month:02d}"

    data_by_user = _load_users_and_data(date_from, date_to)
    generated: list[dict] = []

    with SessionLocal() as db:
        for user_id, (transactions, budgets) in data_by_user.items():
            budgets_by_cat = _resolve_budget_by_category(budgets, month_key)
            categories, total_spent, total_budget = _build_category_breakdown(transactions, budgets_by_cat)

            report_id = str(uuid.uuid4())
            created_at = datetime.now(timezone.utc)
            json_path, csv_path = _write_report_files(
                user_id=user_id,
                report_id=report_id,
                month_key=month_key,
                date_from=date_from,
                date_to=date_to,
                total_spent=total_spent,
                total_budget=total_budget,
                transactions_count=len(transactions),
                categories=categories,
                created_at=created_at,
            )

            report = Report(
                id=report_id,
                user_id=user_id,
                month=month_key,
                date_from=date_from,
                date_to=date_to,
                total_spent=total_spent,
                total_budget=total_budget,
                transactions_count=len(transactions),
                json_file_path=str(json_path),
                csv_file_path=str(csv_path),
                categories_json=json.dumps([c.model_dump(mode="json") for c in categories], ensure_ascii=False),
                created_at=created_at,
            )
            db.add(report)
            db.commit()
            db.refresh(report)

            out = _serialize_report(report).model_dump(mode="json")
            out["user_id"] = user_id
            out["saved_files"] = {"json": str(json_path), "csv": str(csv_path)}
            generated.append(out)

    return generated


if __name__ == "__main__":
    results = run_hourly_report()
    print(json.dumps(results, indent=2, ensure_ascii=False))
