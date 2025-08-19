from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class CategoryOut(ORMModel):
    id: int
    name: str
    description: str | None = None
    parent_id: int | None = None
    sort_order: int
    is_active: bool
    created_at: datetime
    children: list["CategoryOut"] = Field(default_factory=list)
