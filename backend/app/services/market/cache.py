"""
In-memory price cache with optional Redis backend.
Falls back to a simple dict if Redis is not available.
"""
from __future__ import annotations

import asyncio
import json
import time
from typing import Dict, Optional

from app.config import get_settings

settings = get_settings()

# ── In-memory fallback cache ─────────────────────────────────────────────────
_mem_cache: Dict[str, dict] = {}  # {key: {"data": ..., "expires": float}}


def _mem_set(key: str, value: dict, ttl: int) -> None:
    _mem_cache[key] = {"data": value, "expires": time.monotonic() + ttl}


def _mem_get(key: str) -> Optional[dict]:
    entry = _mem_cache.get(key)
    if entry and time.monotonic() < entry["expires"]:
        return entry["data"]
    _mem_cache.pop(key, None)
    return None


# ── Redis client (lazy init) ──────────────────────────────────────────────────
_redis = None


async def _get_redis():
    global _redis
    if _redis is not None:
        return _redis
    if not settings.REDIS_ENABLED:
        return None
    try:
        import redis.asyncio as aioredis
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await _redis.ping()
        return _redis
    except Exception:
        return None


# ── Public interface ─────────────────────────────────────────────────────────
async def cache_set(key: str, value: dict, ttl: int = 60) -> None:
    r = await _get_redis()
    if r:
        await r.setex(key, ttl, json.dumps(value))
    else:
        _mem_set(key, value, ttl)


async def cache_get(key: str) -> Optional[dict]:
    r = await _get_redis()
    if r:
        raw = await r.get(key)
        return json.loads(raw) if raw else None
    return _mem_get(key)
