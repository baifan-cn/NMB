from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment
from app.models.member_tier import MemberTier
from app.services.membership_service import MembershipService
from app.core.config import settings
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
import base64
import urllib.parse


class PaymentService:
    @staticmethod
    def verify_alipay_signature(form: dict) -> bool:
        # Implement RSA2 signature verification
        try:
            sign = form.get("sign")
            sign_type = form.get("sign_type", settings.ALIPAY_SIGN_TYPE)
            if not sign:
                return False
            # Exclude sign and sign_type, sort by key
            params = {k: v for k, v in form.items() if k not in ("sign", "sign_type") and v is not None}
            unsigned_items = [f"{k}={v}" for k, v in sorted(params.items())]
            unsigned_string = "&".join(unsigned_items)
            # URL decode once as Alipay posts encoded values
            unsigned_string = urllib.parse.unquote_plus(unsigned_string)
            public_key_pem = settings.ALIPAY_PUBLIC_KEY
            if not public_key_pem:
                # In dev, allow missing key
                return True
            key = RSA.import_key(public_key_pem)
            h = SHA256.new(unsigned_string.encode("utf-8"))
            verifier = PKCS1_v1_5.new(key)
            signature = base64.b64decode(sign)
            return verifier.verify(h, signature)
        except Exception:
            return False

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
        # Verify signature
        if not PaymentService.verify_alipay_signature(form):
            return {"ok": False, "reason": "invalid signature"}

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
