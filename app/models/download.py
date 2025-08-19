from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Download(Base):
    __tablename__ = "downloads"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    magazine_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("magazines.id"), nullable=False, index=True)
    download_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="CURRENT_TIMESTAMP")
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(length=65535))
    file_size: Mapped[int | None] = mapped_column(BigInteger)
    download_duration: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(
        Enum("success", "failed", "cancelled", name="download_status"), default="success", nullable=False
    )

    user = relationship("User")
    magazine = relationship("Magazine")
