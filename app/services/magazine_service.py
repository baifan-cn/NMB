from __future__ import annotations

from typing import Sequence, Tuple

from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.magazine import Magazine


async def query_magazines(
    db: AsyncSession,
    q: str | None,
    is_published: bool | None,
    page: int,
    size: int,
    sort_by: str,
    order: str,
) -> tuple[int, list[Magazine]]:
    stmt = select(Magazine)
    if q:
        like_expr = f"%{q}%"
        stmt = stmt.where(
            or_(
                Magazine.title.ilike(like_expr),
                Magazine.description.ilike(like_expr),
                Magazine.issue_number.ilike(like_expr),
            )
        )
    if is_published is not None:
        stmt = stmt.where(Magazine.is_published == is_published)

    order_by_col = Magazine.publish_date if sort_by == "publish_date" else Magazine.created_at
    stmt = stmt.order_by(desc(order_by_col) if order == "desc" else asc(order_by_col))

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(total_stmt)).scalar_one()

    stmt = stmt.offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    items = result.scalars().all()
    return total, items


async def get_magazine_by_id(db: AsyncSession, magazine_id: int) -> Magazine | None:
    result = await db.execute(select(Magazine).where(Magazine.id == magazine_id))
    return result.scalar_one_or_none()


async def get_current_week_magazines(db: AsyncSession) -> list[Magazine]:
    from datetime import date, timedelta

    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    stmt = (
        select(Magazine)
        .where(Magazine.publish_date >= start_of_week, Magazine.publish_date <= end_of_week)
        .where(Magazine.is_published == True)
        .order_by(desc(Magazine.publish_date))
    )
    result = await db.execute(stmt)
    return result.scalars().all()
