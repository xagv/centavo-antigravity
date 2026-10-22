import datetime as dt

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db
from .models import Transaction
from .schemas import TransactionCreate, TransactionOut
from .session import get_current_user_id

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def create_transaction(
    data: TransactionCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    tx = Transaction(user_id=user_id, amount=data.amount, category=data.category, date=data.date)
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


@router.get("", response_model=list[TransactionOut])
def list_transactions(
    category: str | None = None,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    stmt = select(Transaction).where(Transaction.user_id == user_id)
    if category:
        stmt = stmt.where(Transaction.category == category.strip().lower())
    if date_from:
        stmt = stmt.where(Transaction.date >= date_from)
    if date_to:
        stmt = stmt.where(Transaction.date <= date_to)
    stmt = stmt.order_by(Transaction.date.desc(), Transaction.created_at.desc()).limit(limit).offset(offset)
    return db.scalars(stmt).all()