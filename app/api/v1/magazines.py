from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.common import Page
from app.schemas.magazine import MagazineOut
from app.services.magazine_service import (
    get_current_week_magazines,
    get_magazine_by_id,
    query_magazines,
)
from app.schemas.category import CategoryOut
from app.services.category_service import get_active_categories_tree

router = APIRouter()


@router.get("")
async def list_magazines(
    q: str | None = Query(default=None),
    is_published: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="publish_date"),
    order: str = Query(default="desc"),
    db: AsyncSession = Depends(get_db),
) -> Page:
    total, items = await query_magazines(
        db=db,
        q=q,
        is_published=is_published,
        page=page,
        size=size,
        sort_by=sort_by,
        order=order,
    )
    return Page(items=[MagazineOut.model_validate(x) for x in items], total=total, page=page, size=size)


@router.get("/{magazine_id}")
async def get_magazine_detail(magazine_id: int, db: AsyncSession = Depends(get_db)) -> MagazineOut:
    magazine = await get_magazine_by_id(db, magazine_id)
    if not magazine:
        raise HTTPException(status_code=404, detail="Magazine not found")
    return MagazineOut.model_validate(magazine)


@router.get("/current-week")
async def get_current_week(db: AsyncSession = Depends(get_db)) -> Page:
    items = await get_current_week_magazines(db)
    return Page(items=[MagazineOut.model_validate(x) for x in items], total=len(items), page=1, size=len(items))


@router.get("/categories")
async def list_categories(db: AsyncSession = Depends(get_db)) -> list[CategoryOut]:
    tree = await get_active_categories_tree(db)
    return tree
