from decimal import Decimal

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .models import Notification
from .schemas import NotificationOut, TransactionEvaluationOut, TransactionEvent
from .session import get_current_user_id

router = APIRouter(prefix="/notifications", tags=["notifications"])
_bearer = HTTPBearer(auto_error=False)


def fetch_budget_limit(
    category: str,
    period: str | None,
    creds: HTTPAuthorizationCredentials | None,
) -> Decimal | None:
    """Consulta el presupuesto correspondiente en budgets-service."""
    headers = {"Authorization": f"Bearer {creds.credentials}"} if creds else {}
    params: dict[str, str] = {"category": category}
    if period:
        params["period"] = period
    try:
        resp = httpx.get(
            f"{settings.budgets_service_url}/budgets",
            params=params,
            headers=headers,
            timeout=5.0,
        )
    except httpx.HTTPError:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "budgets-service no disponible")
    if resp.status_code != 200:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Error al consultar budgets-service")
    budgets = resp.json()
    if not budgets:
        return None
    return Decimal(str(budgets[0]["limit_amount"]))


@router.post("/transactions", response_model=TransactionEvaluationOut, status_code=status.HTTP_200_OK)
@router.post("/events/transaction", response_model=TransactionEvaluationOut, status_code=status.HTTP_200_OK)
def evaluate_transaction_event(
    data: TransactionEvent,
    user_id: str = Depends(get_current_user_id),
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
):
    limit_amount = data.limit_amount
    if limit_amount is None:
        limit_amount = fetch_budget_limit(data.category, data.period, creds)

    total_spent = (data.current_spent + data.amount).quantize(Decimal("0.01"))

    if limit_amount is None or total_spent <= limit_amount:
        return TransactionEvaluationOut(
            alert_triggered=False,
            category=data.category,
            total_spent=total_spent,
            limit_amount=limit_amount,
            exceeded_amount=Decimal("0.00"),
            notification=None,
        )

    exceeded_amount = (total_spent - limit_amount).quantize(Decimal("0.01"))
    message = (
        f"Alerta de sobregasto en '{data.category}': gastaste {total_spent:.2f} "
        f"sobre un límite de {limit_amount:.2f} (exceso de {exceeded_amount:.2f})."
    )
    notification = Notification(
        user_id=user_id,
        category=data.category,
        transaction_amount=data.amount,
        total_spent=total_spent,
        limit_amount=limit_amount,
        exceeded_amount=exceeded_amount,
        message=message,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)

    return TransactionEvaluationOut(
        alert_triggered=True,
        category=data.category,
        total_spent=total_spent,
        limit_amount=limit_amount,
        exceeded_amount=exceeded_amount,
        notification=notification,
    )


@router.get("", response_model=list[NotificationOut])
def list_notifications(
    category: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    stmt = select(Notification).where(Notification.user_id == user_id)
    if category:
        stmt = stmt.where(Notification.category == category.strip().lower())
    stmt = stmt.order_by(Notification.created_at.desc()).limit(limit).offset(offset)
    return db.scalars(stmt).all()
