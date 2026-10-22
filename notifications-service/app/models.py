import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    category: Mapped[str] = mapped_column(String(64), index=True)
    transaction_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    total_spent: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    limit_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    exceeded_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    message: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
