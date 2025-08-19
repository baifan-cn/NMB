from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.magazine_category import MagazineCategory
from app.schemas.category import CategoryOut


async def get_active_categories_tree(db: AsyncSession) -> list[CategoryOut]:
    result = await db.execute(
        select(MagazineCategory).where(MagazineCategory.is_active == True).order_by(MagazineCategory.sort_order)
    )
    rows: list[MagazineCategory] = result.scalars().all()
    nodes: Dict[int, CategoryOut] = {}
    children_map: Dict[int | None, list[CategoryOut]] = defaultdict(list)
    for row in rows:
        node = CategoryOut.model_validate(row)
        node.children = []
        nodes[row.id] = node
        children_map[row.parent_id].append(node)
    for node in nodes.values():
        node.children = children_map.get(node.id, [])
    return children_map.get(None, [])
