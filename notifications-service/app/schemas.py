import datetime as dt
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TransactionEvent(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    category: str = Field(min_length=1, max_length=64)
    period: str | None = Field(default=None, max_length=32)
    date: dt.date | None = None
    current_spent: Decimal = Field(default=Decimal("0.00"), ge=0, max_digits=12, decimal_places=2)
    limit_amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)

    @field_validator("category")
    @classmethod
    def normalize_category(cls, v: str) -> str:
        v = v.strip().lower()
        if not v:
            raise ValueError("La categoría no puede estar vacía")
        return v

    @field_validator("period")
    @classmethod
    def normalize_period(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip().lower()
        if not v:
            raise ValueError("El periodo no puede estar vacío")
        return v


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    category: str
    transaction_amount: Decimal
    total_spent: Decimal
    limit_amount: Decimal
    exceeded_amount: Decimal
    message: str
    created_at: dt.datetime


class TransactionEvaluationOut(BaseModel):
    alert_triggered: bool
    category: str
    total_spent: Decimal
    limit_amount: Decimal | None = None
    exceeded_amount: Decimal = Decimal("0.00")
    notification: NotificationOut | None = None
