from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    real_name: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(
        Enum("active", "inactive", "banned", name="user_status"), default="active", nullable=False
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="CURRENT_TIMESTAMP")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="CURRENT_TIMESTAMP", onupdate="CURRENT_TIMESTAMP"
    )

    memberships = relationship("UserMembership", back_populates="user")
