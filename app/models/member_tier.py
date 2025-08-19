from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, Numeric, String, Boolean, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class MemberTier(Base):
    __tablename__ = "member_tiers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    price_monthly: Mapped[float | None] = mapped_column(Numeric(10, 2))
    price_yearly: Mapped[float | None] = mapped_column(Numeric(10, 2))
    max_downloads_per_month: Mapped[int | None] = mapped_column(Integer)
    access_history_days: Mapped[int | None] = mapped_column(Integer)
    can_view_current_week: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(length=65535))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="CURRENT_TIMESTAMP")

    memberships = relationship("UserMembership", back_populates="tier")

    __table_args__ = (UniqueConstraint("level", name="uq_member_tiers_level"),)
