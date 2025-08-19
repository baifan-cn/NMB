from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("magazine_categories.id"), nullable=False)
    frequency: Mapped[str] = mapped_column(
        Enum("daily", "weekly", "monthly", name="subscription_frequency"), nullable=False
    )
    last_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_send_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        Enum("active", "paused", "cancelled", name="subscription_status"), default="active", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="CURRENT_TIMESTAMP")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="CURRENT_TIMESTAMP", onupdate="CURRENT_TIMESTAMP"
    )

    user = relationship("User")
    category = relationship("MagazineCategory")
