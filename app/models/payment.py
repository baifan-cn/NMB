from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    tier_id: Mapped[int | None] = mapped_column(Integer)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="CNY", nullable=False)
    payment_method: Mapped[str] = mapped_column(
        Enum("alipay", "wechat", "bank_card", name="payment_method"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        Enum("pending", "success", "failed", "cancelled", "refunded", name="payment_status"),
        default="pending",
        nullable=False,
    )
    transaction_id: Mapped[str | None] = mapped_column(String(100))
    external_transaction_id: Mapped[str | None] = mapped_column(String(100))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="CURRENT_TIMESTAMP")

    user = relationship("User")
