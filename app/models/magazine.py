from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Magazine(Base):
    __tablename__ = "magazines"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    issue_number: Mapped[str] = mapped_column(String(50), nullable=False)
    publish_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str | None] = mapped_column(String(length=65535))
    cover_image_url: Mapped[str | None] = mapped_column(String(500))
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    encrypted_key: Mapped[str | None] = mapped_column(String(255))
    file_size: Mapped[int | None] = mapped_column(BigInteger)
    page_count: Mapped[int | None] = mapped_column(Integer)
    is_sensitive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    download_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="CURRENT_TIMESTAMP")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="CURRENT_TIMESTAMP", onupdate="CURRENT_TIMESTAMP"
    )

    # Relationships can be defined via association table in future if needed

    __table_args__ = (
        Index("idx_publish_date", "publish_date"),
        Index("idx_issue_number", "issue_number"),
    )
