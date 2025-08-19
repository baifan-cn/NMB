from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.member_tier import MemberTier
from app.models.user_membership import UserMembership
from app.models.download import Download
from app.models.payment import Payment
from app.models.magazine import Magazine
from app.services.payment_service import PaymentService


class MembershipService:
    @staticmethod
    async def list_member_tiers(db: AsyncSession) -> list[MemberTier]:
        stmt = select(MemberTier).where(MemberTier.is_active == True).order_by(MemberTier.level.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_current_membership(db: AsyncSession, user_id: int) -> Optional[UserMembership]:
        today = date.today()
        stmt = (
            select(UserMembership)
            .options(joinedload(UserMembership.tier))
            .where(
                UserMembership.user_id == user_id,
                UserMembership.status == "active",
                UserMembership.end_date >= today,
            )
            .order_by(UserMembership.end_date.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def get_membership_history(db: AsyncSession, user_id: int) -> list[UserMembership]:
        stmt = (
            select(UserMembership)
            .options(joinedload(UserMembership.tier))
            .where(UserMembership.user_id == user_id)
            .order_by(UserMembership.start_date.desc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_current_month_downloads(db: AsyncSession, user_id: int) -> int:
        now = datetime.now(timezone.utc)
        first_day = datetime(year=now.year, month=now.month, day=1, tzinfo=timezone.utc)
        if now.month == 12:
            next_month_first = datetime(year=now.year + 1, month=1, day=1, tzinfo=timezone.utc)
        else:
            next_month_first = datetime(year=now.year, month=now.month + 1, day=1, tzinfo=timezone.utc)
        stmt = select(Download).where(
            Download.user_id == user_id,
            Download.status == "success",
            Download.download_time >= first_day,
            Download.download_time < next_month_first,
        )
        result = await db.execute(stmt)
        return len(result.scalars().all())

    @staticmethod
    async def create_membership_upgrade(
        db: AsyncSession,
        user_id: int,
        tier_id: int,
        billing_cycle: str,
        payment_method: str,
    ) -> Payment:
        tier = await db.get(MemberTier, tier_id)
        if tier is None or not tier.is_active:
            raise ValueError("Invalid or inactive member tier")
        if billing_cycle not in ("monthly", "yearly"):
            raise ValueError("Invalid billing cycle")
        amount: Optional[float]
        if billing_cycle == "monthly":
            amount = float(tier.price_monthly) if tier.price_monthly is not None else None
        else:
            amount = float(tier.price_yearly) if tier.price_yearly is not None else None
        if amount is None:
            raise ValueError("Tier does not support selected billing cycle")
        payment = Payment(
            user_id=user_id,
            tier_id=tier.id,
            amount=amount,
            payment_method=payment_method,
            status="pending",
            currency="CNY",
        )
        db.add(payment)
        await db.flush()
        return payment

    @staticmethod
    async def activate_membership(
        db: AsyncSession,
        user_id: int,
        tier_id: int,
        payment_id: Optional[int],
        billing_cycle: str,
        start: Optional[date] = None,
    ) -> UserMembership:
        if start is None:
            start = date.today()
        if billing_cycle == "monthly":
            end = start + timedelta(days=30)
        elif billing_cycle == "yearly":
            end = start + timedelta(days=365)
        else:
            raise ValueError("Invalid billing cycle")
        membership = UserMembership(
            user_id=user_id,
            tier_id=tier_id,
            start_date=start,
            end_date=end,
            status="active",
            payment_id=payment_id,
            auto_renew=False,
        )
        db.add(membership)
        await db.flush()
        return membership

    @staticmethod
    async def compute_remaining_downloads(db: AsyncSession, user_id: int, tier: MemberTier) -> Optional[int]:
        if tier.max_downloads_per_month is None:
            return None
        used = await MembershipService.get_current_month_downloads(db, user_id)
        remaining = max(0, int(tier.max_downloads_per_month) - used)
        return remaining

    @staticmethod
    def is_current_week(d: date) -> bool:
        today = date.today()
        # ISO week
        return (d.isocalendar().week == today.isocalendar().week) and (d.isocalendar().year == today.isocalendar().year)

    @staticmethod
    async def check_access_permission(
        db: AsyncSession, user_id: int, magazine: Magazine
    ) -> dict[str, bool]:
        # Free user default
        current = await MembershipService.get_current_membership(db, user_id)
        if current is None:
            if MembershipService.is_current_week(magazine.publish_date):
                return {"can_view": True, "can_download": False}
            return {"can_view": False, "can_download": False}

        tier = current.tier
        # Access history window
        if tier.access_history_days is not None:
            days_diff = (date.today() - magazine.publish_date).days
            if days_diff > int(tier.access_history_days):
                return {"can_view": False, "can_download": False}

        # Download quota
        if tier.max_downloads_per_month is None:
            can_download = True
        else:
            remaining = await MembershipService.compute_remaining_downloads(db, user_id, tier)
            can_download = bool(remaining and remaining > 0)

        return {"can_view": True, "can_download": can_download}
