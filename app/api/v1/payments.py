from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.services.membership_service import MembershipService
from app.services.payment_service import PaymentService

router = APIRouter()


@router.post("/create-order")
async def create_order():
    return {"payment_id": 1, "pay_url": "https://example.com/pay"}


@router.post("/callback/alipay")
async def alipay_callback(
    db: AsyncSession = Depends(get_db),
    # Alipay sends form-encoded fields
    trade_status: str | None = Form(default=None),
    out_trade_no: str | None = Form(default=None),
    trade_no: str | None = Form(default=None),
    total_amount: str | None = Form(default=None),
    gmt_payment: str | None = Form(default=None),
):
    form = {
        "trade_status": trade_status,
        "out_trade_no": out_trade_no,
        "trade_no": trade_no,
        "total_amount": total_amount,
        "gmt_payment": gmt_payment,
    }
    # TODO: signature verification using PaymentService.verify_alipay_signature
    result = await PaymentService.process_alipay_callback(db, form)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("reason", "callback failed"))
    # Alipay expects a plain text 'success' to acknowledge
    return {"message": "success", **result}
