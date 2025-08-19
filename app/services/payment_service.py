from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment
from app.models.member_tier import MemberTier
from app.services.membership_service import MembershipService


class PaymentService:
    @staticmethod
    def verify_alipay_signature(form: dict) -> bool:
        # TODO: Implement RSA2 verification with Alipay public key from settings
        # For now, accept all callbacks as valid in dev
        return True

    @staticmethod
    def _determine_billing_cycle(tier: MemberTier, amount: float) -> Optional[str]:
        pm = float(tier.price_monthly) if tier.price_monthly is not None else None
        py = float(tier.price_yearly) if tier.price_yearly is not None else None
        if pm is not None and abs(pm - amount) < 0.01:
            return "monthly"
        if py is not None and abs(py - amount) < 0.01:
            return "yearly"
        return None

    @staticmethod
    async def process_alipay_callback(db: AsyncSession, form: dict) -> dict:
        # Alipay common fields
        trade_status = form.get("trade_status")
        out_trade_no = form.get("out_trade_no")  # our order id
        trade_no = form.get("trade_no")  # alipay transaction id
        total_amount_str = form.get("total_amount")
        gmt_payment = form.get("gmt_payment")

        if not out_trade_no:
            return {"ok": False, "reason": "missing out_trade_no"}
        try:
            payment_id = int(out_trade_no)
        except ValueError:
            return {"ok": False, "reason": "invalid out_trade_no"}

        result = await db.execute(select(Payment).where(Payment.id == payment_id))
        payment = result.scalars().first()
        if payment is None:
            return {"ok": False, "reason": "payment not found"}

        # If already processed
        if payment.status == "success":
            return {"ok": True, "already_processed": True}

        if trade_status not in ("TRADE_SUCCESS", "TRADE_FINISHED"):
            return {"ok": True, "pending": True}

        # Update payment
        payment.status = "success"
        payment.external_transaction_id = trade_no
        payment.transaction_id = out_trade_no
        try:
            amount = float(total_amount_str) if total_amount_str is not None else float(payment.amount)
        except Exception:
            amount = float(payment.amount)
        # parse paid time
        try:
            paid_at = datetime.strptime(gmt_payment, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc) if gmt_payment else datetime.now(timezone.utc)
        except Exception:
            paid_at = datetime.now(timezone.utc)
        payment.paid_at = paid_at

        # Determine billing cycle from amount and tier
        tier = await db.get(MemberTier, payment.tier_id) if payment.tier_id is not None else None
        if tier is None:
            return {"ok": False, "reason": "tier not found on payment"}
        cycle = PaymentService._determine_billing_cycle(tier, amount)
        if cycle is None:
            return {"ok": False, "reason": "cannot determine billing cycle"}

        # Activate membership
        membership = await MembershipService.activate_membership(
            db=db,
            user_id=payment.user_id,
            tier_id=tier.id,
            payment_id=payment.id,
            billing_cycle=cycle,
            start=None,
        )
        await db.commit()
        return {"ok": True, "activated": True, "membership_id": membership.id}
