import datetime as dt
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MonthlyReportRequest(BaseModel):
    year: int | None = Field(default=None, ge=2000, le=2100)
    month: int | None = Field(default=None, ge=1, le=12)

    @model_validator(mode="after")
    def validate_year_month_pair(self):
        if (self.year is None) != (self.month is None):
            raise ValueError("Debes proporcionar tanto 'year' como 'month', o ninguno para usar el mes actual")
        return self


class CategoryReportItem(BaseModel):
    category: str
    total_spent: Decimal
    transactions_count: int
    limit_amount: Decimal | None = None
    remaining_amount: Decimal | None = None
    exceeded_amount: Decimal = Decimal("0.00")
    over_budget: bool = False
    status: str = "SIN_PRESUPUESTO"


class ReportFilesOut(BaseModel):
    json_url: str
    csv_url: str


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    month: str
    date_from: dt.date
    date_to: dt.date
    total_spent: Decimal
    total_budget: Decimal
    transactions_count: int
    has_over_budget: bool = False
    over_budget_alerts: list[str] = Field(default_factory=list)
    categories: list[CategoryReportItem]
    files: ReportFilesOut
    created_at: dt.datetime
