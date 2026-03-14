"""Market data router: price lookup, search, and WebSocket stream."""
from __future__ import annotations

import asyncio
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect

from app.core.deps import get_current_user
from app.models.user import User
from app.services.market.cache import cache_get, cache_set
from app.services.market.fetcher import fetch_price

router = APIRouter(prefix="/market", tags=["Market Data"])


@router.get("/price/{symbol}")
async def get_price(
    symbol: str,
    asset_type: str = "stock",
    _: User = Depends(get_current_user),
):
    """Get live price for a symbol. Checks cache first, then fetches if stale."""
    cache_key = f"price:{symbol.upper()}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    data = await fetch_price(symbol, asset_type)
    if not data:
        raise HTTPException(status_code=404, detail=f"Price not found for symbol: {symbol}")

    ttl = 30 if asset_type == "crypto" else 60
    await cache_set(cache_key, data, ttl=ttl)
    return data


@router.get("/prices")
async def get_multiple_prices(
    symbols: str,  # comma-separated e.g. "RELIANCE,TCS,BTC"
    asset_type: str = "stock",
    _: User = Depends(get_current_user),
):
    """Batch price fetch for multiple symbols."""
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    results = []
    tasks = [fetch_price(s, asset_type) for s in symbol_list]
    prices = await asyncio.gather(*tasks, return_exceptions=True)
    for sym, price in zip(symbol_list, prices):
        if isinstance(price, dict) and price:
            results.append(price)
    return results


@router.get("/watchlist")
async def get_watchlist(_: User = Depends(get_current_user)):
    """Return default market watchlist prices (cached)."""
    from app.services.market.scheduler import WATCHED_ASSETS
    results = []
    for symbol, asset_type in WATCHED_ASSETS:
        cached = await cache_get(f"price:{symbol}")
        if cached:
            results.append(cached)
    return results


@router.websocket("/ws/prices")
async def ws_prices(websocket: WebSocket):
    """WebSocket that pushes live prices every 10 seconds."""
    await websocket.accept()
    from app.services.market.scheduler import WATCHED_ASSETS
    try:
        while True:
            prices = []
            for symbol, asset_type in WATCHED_ASSETS:
                cached = await cache_get(f"price:{symbol}")
                if cached:
                    prices.append(cached)
            await websocket.send_json({"type": "prices", "data": prices})
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        pass
