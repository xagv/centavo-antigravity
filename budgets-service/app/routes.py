from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db
from .models import Budget
from .schemas import BudgetCreate, BudgetOut
from .session import get_current_user_id

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.post("", response_model=BudgetOut, status_code=status.HTTP_201_CREATED)
def create_budget(
    data: BudgetCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    budget = Budget(
        user_id=user_id,
        category=data.category,
        limit_amount=data.limit_amount,
        period=data.period,
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


@router.get("", response_model=list[BudgetOut])
def list_budgets(
    category: str | None = None,
    period: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    stmt = select(Budget).where(Budget.user_id == user_id)
    if category:
        stmt = stmt.where(Budget.category == category.strip().lower())
    if period:
        stmt = stmt.where(Budget.period == period.strip().lower())
    stmt = stmt.order_by(Budget.created_at.desc()).limit(limit).offset(offset)
    return db.scalars(stmt).all()
