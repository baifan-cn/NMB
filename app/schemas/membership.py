from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel

from app.schemas.common import ORMModel


class MemberTierOut(ORMModel):
    id: int
    name: str
    level: int
    price_monthly: float | None
    price_yearly: float | None
    max_downloads_per_month: int | None
    access_history_days: int | None
    can_view_current_week: bool
    description: str | None
    is_active: bool


class UserMembershipOut(ORMModel):
    id: int
    tier: MemberTierOut
    start_date: date
    end_date: date
    status: str
    payment_id: int | None
    auto_renew: bool
    created_at: datetime


class UpgradeRequest(BaseModel):
    tier_id: int
    billing_cycle: Literal["monthly", "yearly"]
    payment_method: Literal["alipay", "wechat", "bank_card"]
    channel: Literal["pc", "wap"] = "pc"


class UpgradeResponse(BaseModel):
    payment_id: int
    pay_url: str


class MembershipHistoryItem(ORMModel):
    id: int
    tier: MemberTierOut
    start_date: date
    end_date: date
    status: str
    payment_id: int | None
    auto_renew: bool
    created_at: datetime


class MembershipCurrentOut(BaseModel):
    tier: Optional[MemberTierOut]
    is_active: bool
    expires_at: Optional[date]
    remaining_downloads: Optional[int]
