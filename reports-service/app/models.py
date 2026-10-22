import datetime as dt
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Date, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    month: Mapped[str] = mapped_column(String(7), index=True)
    date_from: Mapped[dt.date] = mapped_column(Date)
    date_to: Mapped[dt.date] = mapped_column(Date)
    total_spent: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    total_budget: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    transactions_count: Mapped[int] = mapped_column(Integer)
    json_file_path: Mapped[str] = mapped_column(String(255))
    csv_file_path: Mapped[str] = mapped_column(String(255))
    categories_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
