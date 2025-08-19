from fastapi import APIRouter

router = APIRouter()


@router.post("/create-order")
async def create_order():
    return {"payment_id": 1, "pay_url": "https://example.com/pay"}
