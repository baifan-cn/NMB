from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
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
from app.core.config import settings
from app.services.membership_service import MembershipService
from app.models.download import Download
from jose import jwt, JWTError

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


@router.get("/current-week")
async def get_current_week(db: AsyncSession = Depends(get_db)) -> Page:
    items = await get_current_week_magazines(db)
    return Page(items=[MagazineOut.model_validate(x) for x in items], total=len(items), page=1, size=len(items))


@router.get("/categories")
async def list_categories(db: AsyncSession = Depends(get_db)) -> list[CategoryOut]:
    tree = await get_active_categories_tree(db)
    return tree


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


def _optional_user_id(authorization: str | None) -> int | None:
    if not authorization:
        return None
    if not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split()[1]
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
        )
    except JWTError:
        return None
    sub = payload.get("sub")
    try:
        return int(sub) if sub is not None else None
    except (TypeError, ValueError):
        return None


def _require_user_id(authorization: str) -> int:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split()[1]
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid access token")
    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(status_code=401, detail="Invalid access token")
    return int(sub)


@router.get("/{magazine_id}/view")
async def view_magazine(magazine_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    authorization = request.headers.get("authorization") or request.headers.get("Authorization")
    user_id = _optional_user_id(authorization) or 0
    magazine = await get_magazine_by_id(db, magazine_id)
    if not magazine:
        raise HTTPException(status_code=404, detail="Magazine not found")
    perm = await MembershipService.check_access_permission(db, user_id, magazine)
    if not perm["can_view"]:
        raise HTTPException(status_code=403, detail="No permission to view this magazine")
    # TODO: replace with real temporary preview URL from OSS
    return {"can_view": True, "temporary_url": f"https://example.com/preview/{magazine.id}"}


@router.post("/{magazine_id}/download")
async def download_magazine(magazine_id: int, request: Request, authorization: str, db: AsyncSession = Depends(get_db)):
    user_id = _require_user_id(authorization)
    magazine = await get_magazine_by_id(db, magazine_id)
    if not magazine:
        raise HTTPException(status_code=404, detail="Magazine not found")
    perm = await MembershipService.check_access_permission(db, user_id, magazine)
    if not perm["can_download"]:
        raise HTTPException(status_code=403, detail="No permission to download this magazine")
    # Record download
    ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    record = Download(
        user_id=user_id,
        magazine_id=magazine.id,
        ip_address=ip,
        user_agent=user_agent,
        status="success",
    )
    db.add(record)
    # Increase download_count for magazine
    magazine.download_count = (magazine.download_count or 0) + 1
    await db.commit()
    # TODO: replace with real signed download URL from OSS
    return {"message": "ok", "download_url": f"https://example.com/download/{magazine.id}"}
