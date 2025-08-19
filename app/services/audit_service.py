from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditService:
    @staticmethod
    async def log(db: AsyncSession, *, user_id: int | None, action: str, ip: str | None = None, user_agent: str | None = None, meta: dict[str, Any] | None = None) -> None:
        entry = AuditLog(user_id=user_id, action=action, ip=ip, user_agent=user_agent, meta=meta)
        db.add(entry)
        await db.flush()
