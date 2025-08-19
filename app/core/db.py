from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


async_engine: AsyncEngine | None = None
async_session_maker: sessionmaker | None = None


async def init_db() -> None:
    global async_engine, async_session_maker

    # Use async engine for MySQL via aiomysql or async driver
    # If using PyMySQL sync, consider SQLAlchemy sync engine instead
    database_url = settings.DATABASE_URL
    if database_url.startswith("mysql+") and not database_url.startswith("mysql+aiomysql"):
        # Fallback to async with aiomysql if user provides plain mysql+pymysql
        database_url = database_url.replace("mysql+pymysql", "mysql+aiomysql")

    async_engine = create_async_engine(database_url, echo=False, future=True, pool_pre_ping=True)
    async_session_maker = sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    if async_session_maker is None:
        await init_db()
    assert async_session_maker is not None
    async with async_session_maker() as session:
        yield session
