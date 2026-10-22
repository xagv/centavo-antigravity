import calendar
import csv
import datetime as dt
import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Literal

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .models import Report
from .schemas import CategoryReportItem, MonthlyReportRequest, ReportFilesOut, ReportOut
from .session import get_current_user_id

router = APIRouter(prefix="/reports", tags=["reports"])
_bearer = HTTPBearer(auto_error=False)


def fetch_transactions_for_period(
    date_from: dt.date,
    date_to: dt.date,
    creds: HTTPAuthorizationCredentials | None,
) -> list[dict]:
    """Consulta las transacciones del rango de fechas en transactions-service."""
    headers = {"Authorization": f"Bearer {creds.credentials}"} if creds else {}
    all_transactions: list[dict] = []
    limit = 200
    offset = 0

    while True:
        params = {
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "limit": str(limit),
            "offset": str(offset),
        }
        try:
            resp = httpx.get(
                f"{settings.transactions_service_url}/transactions",
                params=params,
                headers=headers,
                timeout=5.0,
            )
        except httpx.HTTPError:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "transactions-service no disponible")
        if resp.status_code != 200:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Error al consultar transactions-service")

        batch = resp.json()
        all_transactions.extend(batch)
        if len(batch) < limit:
            break
        offset += limit

    return all_transactions


def fetch_budgets(creds: HTTPAuthorizationCredentials | None) -> list[dict]:
    """Consulta los presupuestos del usuario en budgets-service."""
    headers = {"Authorization": f"Bearer {creds.credentials}"} if creds else {}
    try:
        resp = httpx.get(
            f"{settings.budgets_service_url}/budgets",
            params={"limit": "200"},
            headers=headers,
            timeout=5.0,
        )
    except httpx.HTTPError:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "budgets-service no disponible")
    if resp.status_code != 200:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Error al consultar budgets-service")
    return resp.json()


def _resolve_budget_by_category(budgets: list[dict], month_key: str) -> dict[str, Decimal]:
    """Selecciona el límite de presupuesto aplicable por categoría para el mes."""
    limits: dict[str, Decimal] = {}
    monthly_periods = {month_key.lower(), "mensual", "monthly", "mes"}

    for b in budgets:
        cat = str(b["category"]).strip().lower()
        period = str(b.get("period", "")).strip().lower()
        limit_val = Decimal(str(b["limit_amount"])).quantize(Decimal("0.01"))
        if cat not in limits:
            limits[cat] = limit_val
        elif period in monthly_periods:
            limits[cat] = limit_val

    return limits


def _build_category_breakdown(
    transactions: list[dict],
    budgets_by_category: dict[str, Decimal],
) -> tuple[list[CategoryReportItem], Decimal, Decimal]:
    """Agrega gastos por categoría y los cruza con los presupuestos."""
    spent_by_cat: dict[str, Decimal] = {}
    count_by_cat: dict[str, int] = {}

    for tx in transactions:
        cat = str(tx["category"]).strip().lower()
        amount = Decimal(str(tx["amount"])).quantize(Decimal("0.01"))
        spent_by_cat[cat] = (spent_by_cat.get(cat, Decimal("0.00")) + amount).quantize(Decimal("0.01"))
        count_by_cat[cat] = count_by_cat.get(cat, 0) + 1

    all_categories = sorted(set(spent_by_cat.keys()) | set(budgets_by_category.keys()))
    items: list[CategoryReportItem] = []

    for cat in all_categories:
        spent = spent_by_cat.get(cat, Decimal("0.00"))
        tx_count = count_by_cat.get(cat, 0)
        limit_amount = budgets_by_category.get(cat)

        if limit_amount is not None:
            if spent > limit_amount:
                exceeded = (spent - limit_amount).quantize(Decimal("0.01"))
                remaining = Decimal("0.00")
                over_budget = True
                cat_status = f"SOBREGASTO (+{exceeded:.2f})"
            else:
                exceeded = Decimal("0.00")
                remaining = (limit_amount - spent).quantize(Decimal("0.01"))
                over_budget = False
                cat_status = "DENTRO_DE_PRESUPUESTO"
        else:
            exceeded = Decimal("0.00")
            remaining = None
            over_budget = False
            cat_status = "SIN_PRESUPUESTO"

        items.append(
            CategoryReportItem(
                category=cat,
                total_spent=spent,
                transactions_count=tx_count,
                limit_amount=limit_amount,
                remaining_amount=remaining,
                exceeded_amount=exceeded,
                over_budget=over_budget,
                status=cat_status,
            )
        )

    total_spent = sum((item.total_spent for item in items), Decimal("0.00")).quantize(Decimal("0.01"))
    total_budget = sum(
        (item.limit_amount for item in items if item.limit_amount is not None),
        Decimal("0.00"),
    ).quantize(Decimal("0.01"))
    return items, total_spent, total_budget


def _write_report_files(
    user_id: str,
    report_id: str,
    month_key: str,
    date_from: dt.date,
    date_to: dt.date,
    total_spent: Decimal,
    total_budget: Decimal,
    transactions_count: int,
    categories: list[CategoryReportItem],
    created_at: datetime,
) -> tuple[Path, Path]:
    """Escribe el reporte en formato JSON y CSV dentro de settings.storage_dir."""
    user_dir = settings.storage_dir / user_id
    user_dir.mkdir(parents=True, exist_ok=True)

    base_name = f"report_{month_key}_{report_id}"
    json_path = user_dir / f"{base_name}.json"
    csv_path = user_dir / f"{base_name}.csv"

    over_budget_alerts = [
        f"SOBREGASTO en '{c.category}': gastado {c.total_spent:.2f} vs presupuesto {c.limit_amount:.2f} (exceso de {c.exceeded_amount:.2f})"
        for c in categories
        if c.over_budget and c.limit_amount is not None
    ]

    json_payload = {
        "id": report_id,
        "user_id": user_id,
        "month": month_key,
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "total_spent": f"{total_spent:.2f}",
        "total_budget": f"{total_budget:.2f}",
        "transactions_count": transactions_count,
        "has_over_budget": bool(over_budget_alerts),
        "over_budget_alerts": over_budget_alerts,
        "created_at": created_at.isoformat(),
        "categories": [
            {
                "category": c.category,
                "total_spent": f"{c.total_spent:.2f}",
                "transactions_count": c.transactions_count,
                "limit_amount": f"{c.limit_amount:.2f}" if c.limit_amount is not None else None,
                "remaining_amount": f"{c.remaining_amount:.2f}" if c.remaining_amount is not None else None,
                "exceeded_amount": f"{c.exceeded_amount:.2f}",
                "over_budget": c.over_budget,
                "status": c.status,
            }
            for c in categories
        ],
    }
    json_path.write_text(json.dumps(json_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "month",
                "category",
                "transactions_count",
                "total_spent",
                "limit_amount",
                "remaining_amount",
                "exceeded_amount",
                "over_budget",
                "status",
            ]
        )
        for c in categories:
            writer.writerow(
                [
                    month_key,
                    c.category,
                    c.transactions_count,
                    f"{c.total_spent:.2f}",
                    f"{c.limit_amount:.2f}" if c.limit_amount is not None else "",
                    f"{c.remaining_amount:.2f}" if c.remaining_amount is not None else "",
                    f"{c.exceeded_amount:.2f}",
                    str(c.over_budget).lower(),
                    c.status,
                ]
            )

    return json_path, csv_path


def _serialize_report(report: Report) -> ReportOut:
    raw_categories = json.loads(report.categories_json)
    categories = [CategoryReportItem(**item) for item in raw_categories]
    over_budget_alerts = [
        f"SOBREGASTO en '{c.category}': gastado {c.total_spent:.2f} vs presupuesto {c.limit_amount:.2f} (exceso de {c.exceeded_amount:.2f})"
        for c in categories
        if c.over_budget and c.limit_amount is not None
    ]
    return ReportOut(
        id=report.id,
        month=report.month,
        date_from=report.date_from,
        date_to=report.date_to,
        total_spent=report.total_spent,
        total_budget=report.total_budget,
        transactions_count=report.transactions_count,
        has_over_budget=bool(over_budget_alerts),
        over_budget_alerts=over_budget_alerts,
        categories=categories,
        files=ReportFilesOut(
            json_url=f"/reports/{report.id}/download?format=json",
            csv_url=f"/reports/{report.id}/download?format=csv",
        ),
        created_at=report.created_at,
    )


@router.post("/monthly", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
def generate_monthly_report(
    data: MonthlyReportRequest | None = Body(default=None),
    user_id: str = Depends(get_current_user_id),
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
):
    today = datetime.now(timezone.utc).date()
    year = data.year if (data and data.year is not None) else today.year
    month = data.month if (data and data.month is not None) else today.month

    last_day = calendar.monthrange(year, month)[1]
    date_from = dt.date(year, month, 1)
    date_to = dt.date(year, month, last_day)
    month_key = f"{year:04d}-{month:02d}"

    transactions = fetch_transactions_for_period(date_from, date_to, creds)
    budgets = fetch_budgets(creds)

    budgets_by_category = _resolve_budget_by_category(budgets, month_key)
    categories, total_spent, total_budget = _build_category_breakdown(transactions, budgets_by_category)

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
    return _serialize_report(report)


@router.get("", response_model=list[ReportOut])
def list_reports(
    month: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    stmt = select(Report).where(Report.user_id == user_id)
    if month:
        stmt = stmt.where(Report.month == month.strip())
    stmt = stmt.order_by(Report.created_at.desc()).limit(limit).offset(offset)
    reports = db.scalars(stmt).all()
    return [_serialize_report(r) for r in reports]


@router.get("/{report_id}", response_model=ReportOut)
def get_report(
    report_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    stmt = select(Report).where(Report.id == report_id, Report.user_id == user_id)
    report = db.scalar(stmt)
    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reporte no encontrado")
    return _serialize_report(report)


@router.get("/{report_id}/download")
def download_report_file(
    report_id: str,
    format: Literal["json", "csv"] = Query("json"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    stmt = select(Report).where(Report.id == report_id, Report.user_id == user_id)
    report = db.scalar(stmt)
    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reporte no encontrado")

    if format == "csv":
        file_path = Path(report.csv_file_path)
        media_type = "text/csv"
        filename = f"report_{report.month}_{report.id}.csv"
    else:
        file_path = Path(report.json_file_path)
        media_type = "application/json"
        filename = f"report_{report.month}_{report.id}.json"

    if not file_path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Archivo de reporte no disponible en disco")

    return FileResponse(path=file_path, media_type=media_type, filename=filename)
