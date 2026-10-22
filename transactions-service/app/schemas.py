import datetime as dt
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TransactionCreate(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    category: str = Field(min_length=1, max_length=64)
    date: dt.date

    @field_validator("category")
    @classmethod
    def normalize_category(cls, v: str) -> str:
        v = v.strip().lower()
        if not v:
            raise ValueError("La categoría no puede estar vacía")
        return v


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    amount: Decimal
    category: str
    date: dt.date