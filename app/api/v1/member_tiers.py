from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.membership import MemberTierOut
from app.services.membership_service import MembershipService

router = APIRouter()


@router.get("", response_model=list[MemberTierOut])
async def list_member_tiers(db: AsyncSession = Depends(get_db)) -> list[MemberTierOut]:
    tiers = await MembershipService.list_member_tiers(db)
    return [MemberTierOut.model_validate(t) for t in tiers]
