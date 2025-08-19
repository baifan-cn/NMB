from fastapi import FastAPI
from fastapi.responses import JSONResponse
import asyncio

from app.api.v1.routes import api_router
from app.core.config import settings
from app.core.db import init_db
from app.core.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from app.services.membership_service import MembershipService
from app.core.rate_limit import limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware


def create_app() -> FastAPI:
    app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

    # Rate limiting middleware
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request, exc):  # type: ignore[no-redef]
        return JSONResponse(status_code=429, content={"detail": "Too many requests"})

    # Include API routes
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @app.on_event("startup")
    async def on_startup() -> None:
        await init_db()
        # Fire-and-forget background task: daily membership expiration
        async def expire_loop() -> None:
            while True:
                try:
                    # wait until next 3:00 AM UTC-ish
                    await asyncio.sleep(60 * 60 * 6)
                    # run once per cycle
                    from app.core.db import async_session_maker
                    if async_session_maker is None:
                        continue
                    async with async_session_maker() as session:  # type: ignore
                        assert isinstance(session, AsyncSession)
                        await MembershipService.expire_due_memberships(session)
                except Exception:
                    # swallow errors to keep loop alive
                    pass

        asyncio.create_task(expire_loop())

    return app


app = create_app()
