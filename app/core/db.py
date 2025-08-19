from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.base import Base
from app.core.db_url import normalize_database_url
from app.models.member_tier import MemberTier


async_engine: AsyncEngine | None = None
async_session_maker: sessionmaker | None = None


async def init_db() -> None:
    global async_engine, async_session_maker

    # Use async engine for MySQL via aiomysql or async driver
    # If using PyMySQL sync, consider SQLAlchemy sync engine instead
    database_url = normalize_database_url(settings.DATABASE_URL)

    async_engine = create_async_engine(database_url, echo=False, future=True, pool_pre_ping=True)
    async_session_maker = sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)

    # Create tables in dev if configured
    if settings.AUTO_CREATE_TABLES:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Seed default member tiers if not present
        assert async_session_maker is not None
        async with async_session_maker() as session:
            await _seed_member_tiers(session)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    if async_session_maker is None:
        await init_db()
    assert async_session_maker is not None
    async with async_session_maker() as session:
        yield session


async def _seed_member_tiers(session: AsyncSession) -> None:
    from sqlalchemy import select

    result = await session.execute(select(MemberTier).limit(1))
    exists = result.scalars().first()
    if exists:
        return
    # Levels 0-4
    tiers: list[MemberTier] = [
        MemberTier(
            name="免费用户",
            level=0,
            price_monthly=None,
            price_yearly=None,
            max_downloads_per_month=0,
            access_history_days=0,
            can_view_current_week=True,
            description="仅在线查看本周",
            is_active=True,
        ),
        MemberTier(
            name="基础会员",
            level=1,
            price_monthly=39.00,
            price_yearly=399.00,
            max_downloads_per_month=50,
            access_history_days=30,
            can_view_current_week=True,
            description="下载1个月内，历史30天，月50次",
            is_active=True,
        ),
        MemberTier(
            name="高级会员",
            level=2,
            price_monthly=79.00,
            price_yearly=799.00,
            max_downloads_per_month=200,
            access_history_days=90,
            can_view_current_week=True,
            description="下载3个月内，历史90天，月200次",
            is_active=True,
        ),
        MemberTier(
            name="VIP会员",
            level=3,
            price_monthly=159.00,
            price_yearly=1599.00,
            max_downloads_per_month=None,
            access_history_days=365,
            can_view_current_week=True,
            description="下载1年内，历史365天，无限次",
            is_active=True,
        ),
        MemberTier(
            name="终身会员",
            level=4,
            price_monthly=None,
            price_yearly=2999.00,
            max_downloads_per_month=None,
            access_history_days=None,
            can_view_current_week=True,
            description="下载无限制，历史无限制",
            is_active=True,
        ),
    ]
    session.add_all(tiers)
    await session.commit()
