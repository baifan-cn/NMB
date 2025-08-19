from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UserMembership(Base):
    __tablename__ = "user_memberships"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    tier_id: Mapped[int] = mapped_column(Integer, ForeignKey("member_tiers.id"), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("active", "expired", "cancelled", name="membership_status"), default="active", nullable=False
    )
    payment_id: Mapped[int | None] = mapped_column(BigInteger)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="CURRENT_TIMESTAMP")

    user = relationship("User", back_populates="memberships")
    tier = relationship("MemberTier", back_populates="memberships")
