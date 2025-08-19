from fastapi import APIRouter

from app.api.v1 import auth, members, magazines, subscriptions, payments, search, health
from app.api.v1 import member_tiers
from app.api.v1 import members as memberships

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(memberships.router, prefix="/memberships", tags=["memberships"])
api_router.include_router(member_tiers.router, prefix="/member-tiers", tags=["member-tiers"])
api_router.include_router(magazines.router, prefix="/magazines", tags=["magazines"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
api_router.include_router(payments.router, prefix="/payment", tags=["payment"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(health.router, tags=["health"])
