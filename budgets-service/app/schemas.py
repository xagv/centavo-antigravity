from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BudgetCreate(BaseModel):
    category: str = Field(min_length=1, max_length=64)
    limit_amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    period: str = Field(min_length=1, max_length=32)

    @field_validator("category")
    @classmethod
    def normalize_category(cls, v: str) -> str:
        v = v.strip().lower()
        if not v:
            raise ValueError("La categoría no puede estar vacía")
        return v

    @field_validator("period")
    @classmethod
    def normalize_period(cls, v: str) -> str:
        v = v.strip().lower()
        if not v:
            raise ValueError("El periodo no puede estar vacío")
        return v


class BudgetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    category: str
    limit_amount: Decimal
    period: str
