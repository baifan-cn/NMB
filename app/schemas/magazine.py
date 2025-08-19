from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class SortField(str, Enum):
    publish_date = "publish_date"
    created_at = "created_at"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


class MagazineQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
    q: str | None = None
    is_published: bool | None = None
    start_date: date | None = None
    end_date: date | None = None
    sort_by: SortField = SortField.publish_date
    order: SortOrder = SortOrder.desc


class MagazineBase(ORMModel):
    title: str
    issue_number: str
    publish_date: date
    description: str | None = None
    cover_image_url: str | None = None
    is_sensitive: bool
    is_published: bool


class MagazineOut(MagazineBase):
    id: int
    file_size: int | None = None
    page_count: int | None = None
    view_count: int
    download_count: int
    created_at: datetime
    updated_at: datetime | None = None


class MagazineCreate(BaseModel):
    title: str
    issue_number: str
    publish_date: date
    description: str | None = None
    cover_image_url: str | None = None
    is_sensitive: bool = False
    is_published: bool = False


class MagazineUpdate(BaseModel):
    title: str | None = None
    issue_number: str | None = None
    publish_date: date | None = None
    description: str | None = None
    cover_image_url: str | None = None
    is_sensitive: bool | None = None
    is_published: bool | None = None
