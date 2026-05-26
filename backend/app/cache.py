"""Redis 캐시 헬퍼."""
from __future__ import annotations

import logging

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

_redis_client: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    """Redis 클라이언트 싱글턴을 반환한다."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def cache_get(key: str) -> str | None:
    """Redis에서 키에 해당하는 값을 조회한다. 없으면 None을 반환한다."""
    try:
        client = get_redis()
        return await client.get(key)
    except Exception as e:
        logger.warning("Redis cache_get 실패 (key=%s): %s", key, e)
        return None


async def cache_set(key: str, value: str, ttl: int = 300) -> None:
    """Redis에 키-값을 저장한다. ttl(초) 후 자동 만료된다."""
    try:
        client = get_redis()
        await client.set(key, value, ex=ttl)
    except Exception as e:
        logger.warning("Redis cache_set 실패 (key=%s): %s", key, e)


async def cache_delete(key: str) -> None:
    """Redis에서 키를 삭제한다."""
    try:
        client = get_redis()
        await client.delete(key)
    except Exception as e:
        logger.warning("Redis cache_delete 실패 (key=%s): %s", key, e)
