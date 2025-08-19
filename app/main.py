from fastapi import FastAPI

from app.api.v1.routes import api_router
from app.core.config import settings
from app.core.db import init_db


def create_app() -> FastAPI:
    app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

    # Include API routes
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @app.on_event("startup")
    async def on_startup() -> None:
        await init_db()

    return app


app = create_app()
