from __future__ import annotations

import json
from typing import Any

import redis.asyncio as redis

from app.core.config import settings


class RedisKV:
    def __init__(self) -> None:
        self.client = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def set_json(self, key: str, value: Any, ex: int | None = None) -> None:
        await self.client.set(key, json.dumps(value), ex=ex)

    async def get_json(self, key: str) -> Any | None:
        raw = await self.client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def delete(self, key: str) -> None:
        await self.client.delete(key)
