"""Async Redis client factory."""

import json
from typing import Any

import redis.asyncio as aioredis

from shared.config import get_settings

settings = get_settings()

_redis_pool: aioredis.ConnectionPool | None = None


def get_redis_pool() -> aioredis.ConnectionPool:
    """Get or create Redis connection pool."""
    global _redis_pool  # noqa: PLW0603
    if _redis_pool is None:
        _redis_pool = aioredis.ConnectionPool.from_url(
            settings.redis_url,
            max_connections=settings.redis_max_connections,
            decode_responses=True,
        )
    return _redis_pool


def get_redis_client() -> aioredis.Redis:
    """Get Redis client from pool."""
    return aioredis.Redis(connection_pool=get_redis_pool())


async def close_redis_pool() -> None:
    """Close Redis connection pool."""
    global _redis_pool  # noqa: PLW0603
    if _redis_pool is not None:
        await _redis_pool.aclose()
        _redis_pool = None


class RedisCache:
    """Higher-level Redis cache interface."""

    def __init__(self, prefix: str = "", ttl: int = 300) -> None:
        self.prefix = prefix
        self.ttl = ttl
        self._client = get_redis_client()

    def _key(self, key: str) -> str:
        return f"{self.prefix}:{key}" if self.prefix else key

    async def get(self, key: str) -> Any | None:
        value = await self._client.get(self._key(key))
        if value is None:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        serialized = json.dumps(value) if not isinstance(value, str) else value
        await self._client.setex(self._key(key), ttl or self.ttl, serialized)

    async def delete(self, key: str) -> None:
        await self._client.delete(self._key(key))

    async def exists(self, key: str) -> bool:
        return bool(await self._client.exists(self._key(key)))

    async def expire(self, key: str, ttl: int) -> None:
        await self._client.expire(self._key(key), ttl)

    async def publish(self, channel: str, message: Any) -> None:
        payload = json.dumps(message) if not isinstance(message, str) else message
        await self._client.publish(channel, payload)

    async def lpush(self, key: str, *values: Any) -> int:
        serialized = [json.dumps(v) if not isinstance(v, str) else v for v in values]
        return await self._client.lpush(self._key(key), *serialized)

    async def lrange(self, key: str, start: int, end: int) -> list[Any]:
        items = await self._client.lrange(self._key(key), start, end)
        result = []
        for item in items:
            try:
                result.append(json.loads(item))
            except (json.JSONDecodeError, TypeError):
                result.append(item)
        return result
