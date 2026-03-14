"""
Background scheduler that refreshes common market prices every 60 seconds.
Uses APScheduler with asyncio.
"""
from __future__ import annotations

import asyncio
import logging
from typing import List, Tuple

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.services.market.cache import cache_set
from app.services.market.fetcher import fetch_price

logger = logging.getLogger("market.scheduler")

# Default symbols to keep warm in cache
WATCHED_ASSETS: List[Tuple[str, str]] = [
    ("RELIANCE", "stock"),
    ("TCS", "stock"),
    ("INFY", "stock"),
    ("HDFCBANK", "stock"),
    ("^NSEI", "stock"),    # Nifty 50
    ("^BSESN", "stock"),   # Sensex
    ("BTC", "crypto"),
    ("ETH", "crypto"),
    ("SOL", "crypto"),
    ("GOLD", "gold"),
]

_scheduler: AsyncIOScheduler | None = None


async def _refresh_prices() -> None:
    tasks = [
        _refresh_one(symbol, asset_type)
        for symbol, asset_type in WATCHED_ASSETS
    ]
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.debug("Market prices refreshed")


async def _refresh_one(symbol: str, asset_type: str) -> None:
    try:
        data = await fetch_price(symbol, asset_type)
        if data:
            ttl = 30 if asset_type == "crypto" else 60
            await cache_set(f"price:{symbol}", data, ttl=ttl)
    except Exception as e:
        logger.warning(f"Failed to refresh {symbol}: {e}")


def start_scheduler() -> None:
    global _scheduler
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(_refresh_prices, "interval", seconds=60, id="market_refresh")
    _scheduler.start()
    logger.info("Market data scheduler started")


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
