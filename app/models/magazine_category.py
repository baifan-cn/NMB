from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class MagazineCategory(Base):
    __tablename__ = "magazine_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(length=65535))
    parent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("magazine_categories.id"))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="CURRENT_TIMESTAMP")

    parent = relationship("MagazineCategory", remote_side=[id], back_populates="children")
    children = relationship("MagazineCategory", back_populates="parent", cascade="all, delete-orphan")
