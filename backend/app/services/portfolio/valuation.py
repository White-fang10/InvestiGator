"""Portfolio valuation service — computes live values for real assets."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timezone
from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portfolio import AssetType, PortfolioSnapshot, RealAsset
from app.services.market.cache import cache_get, cache_set
from app.services.market.fetcher import fetch_price


async def get_live_price(symbol: str, asset_type: str) -> float:
    """Get price from cache or fetch fresh."""
    key = f"price:{symbol.upper()}"
    cached = await cache_get(key)
    if cached:
        return float(cached.get("price", 0))
    data = await fetch_price(symbol, asset_type)
    if data:
        await cache_set(key, data, ttl=60)
        return float(data.get("price", 0))
    return 0.0


async def compute_portfolio_summary(user_id: int, db: AsyncSession) -> dict:
    """Compute full portfolio summary with live prices for all assets."""
    result = await db.execute(select(RealAsset).where(RealAsset.user_id == user_id))
    assets = result.scalars().all()

    enriched = []
    by_type: Dict[str, float] = defaultdict(float)
    total_invested = 0.0
    total_current = 0.0

    for asset in assets:
        live_price = await get_live_price(asset.symbol, asset.asset_type.value)
        current_value = asset.quantity * live_price
        invested_value = asset.quantity * asset.purchase_price
        gain_loss = current_value - invested_value
        gain_loss_pct = (gain_loss / invested_value * 100) if invested_value > 0 else 0.0

        total_invested += invested_value
        total_current += current_value
        by_type[asset.asset_type.value] += current_value

        enriched.append({
            "id": asset.id,
            "asset_type": asset.asset_type.value,
            "symbol": asset.symbol,
            "name": asset.name,
            "quantity": asset.quantity,
            "purchase_price": asset.purchase_price,
            "live_price": live_price,
            "current_value": round(current_value, 2),
            "gain_loss": round(gain_loss, 2),
            "gain_loss_pct": round(gain_loss_pct, 2),
            "created_at": asset.created_at,
        })

    overall_gain = total_current - total_invested
    overall_pct = (overall_gain / total_invested * 100) if total_invested > 0 else 0.0

    allocation = [
        {
            "asset_type": k,
            "value_inr": round(v, 2),
            "percentage": round((v / total_current * 100) if total_current else 0, 2),
        }
        for k, v in by_type.items()
    ]

    return {
        "total_invested": round(total_invested, 2),
        "total_current_value": round(total_current, 2),
        "overall_gain_loss": round(overall_gain, 2),
        "overall_gain_loss_pct": round(overall_pct, 2),
        "allocation": allocation,
        "assets": enriched,
    }


async def take_snapshot(user_id: int, db: AsyncSession) -> None:
    """Store today's portfolio total as a snapshot."""
    summary = await compute_portfolio_summary(user_id, db)
    today = date.today()
    # Upsert snapshot for today
    result = await db.execute(
        select(PortfolioSnapshot).where(
            PortfolioSnapshot.user_id == user_id,
            PortfolioSnapshot.snapshot_date == today,
        )
    )
    snap = result.scalar_one_or_none()
    if snap:
        snap.total_value_inr = summary["total_current_value"]
    else:
        db.add(PortfolioSnapshot(
            user_id=user_id,
            snapshot_date=today,
            total_value_inr=summary["total_current_value"],
        ))
    await db.commit()
