from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.config import settings
from app.services.membership_service import MembershipService
from app.schemas.membership import (
    MembershipCurrentOut,
    MembershipHistoryItem,
    UpgradeRequest,
    UpgradeResponse,
)
from jose import jwt, JWTError
from app.services.payment_service import PaymentService
from app.models.member_tier import MemberTier

router = APIRouter()


def _require_user_id(authorization: str) -> int:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split()[1]
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid access token")
    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(status_code=401, detail="Invalid access token")
    return int(sub)


@router.get("/current", response_model=MembershipCurrentOut)
async def get_current_membership(authorization: str, db: AsyncSession = Depends(get_db)) -> MembershipCurrentOut:
    user_id = _require_user_id(authorization)
    current = await MembershipService.get_current_membership(db, user_id)
    if current is None:
        # Free user
        return MembershipCurrentOut(tier=None, is_active=False, expires_at=None, remaining_downloads=0)
    remaining = await MembershipService.compute_remaining_downloads(db, user_id, current.tier)
    return MembershipCurrentOut(
        tier=MemberTierOut.model_validate(current.tier),
        is_active=True,
        expires_at=current.end_date,
        remaining_downloads=remaining,
    )


@router.get("/history", response_model=list[MembershipHistoryItem])
async def get_membership_history(authorization: str, db: AsyncSession = Depends(get_db)) -> list[MembershipHistoryItem]:
    user_id = _require_user_id(authorization)
    items = await MembershipService.get_membership_history(db, user_id)
    return [MembershipHistoryItem.model_validate(it) for it in items]


@router.post("/upgrade", response_model=UpgradeResponse)
async def upgrade_membership(payload: UpgradeRequest, authorization: str, db: AsyncSession = Depends(get_db)) -> UpgradeResponse:
    user_id = _require_user_id(authorization)
    try:
        payment = await MembershipService.create_membership_upgrade(
            db,
            user_id=user_id,
            tier_id=payload.tier_id,
            billing_cycle=payload.billing_cycle,
            payment_method=payload.payment_method,
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    # Build Alipay page pay URL
    tier = await db.get(MemberTier, payload.tier_id)
    subject = f"NMB会员-{tier.name}-{payload.billing_cycle}"
    pay_url = PaymentService.build_alipay_pc_pay_url(payment.id, subject, float(payment.amount))
    return UpgradeResponse(payment_id=payment.id, pay_url=pay_url)
