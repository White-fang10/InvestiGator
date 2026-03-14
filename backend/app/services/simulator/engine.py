"""Virtual trading simulator engine."""
from __future__ import annotations

from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.simulator import OrderStatus, OrderType, VirtualHolding, VirtualOrder, VirtualWallet
from app.services.market.fetcher import fetch_price


STARTING_BALANCE = 100_000.0  # ₹1,00,000


async def get_or_create_wallet(user_id: int, db: AsyncSession) -> VirtualWallet:
    result = await db.execute(select(VirtualWallet).where(VirtualWallet.user_id == user_id))
    wallet = result.scalar_one_or_none()
    if not wallet:
        wallet = VirtualWallet(user_id=user_id, balance_inr=STARTING_BALANCE)
        db.add(wallet)
        await db.commit()
        await db.refresh(wallet)
    return wallet


async def execute_order(user_id: int, symbol: str, asset_type: str, order_type: OrderType, quantity: float, db: AsyncSession) -> dict:
    """Execute a simulated buy/sell order at live market price."""
    # Fetch live price
    price_data = await fetch_price(symbol, asset_type)
    if not price_data or price_data.get("price", 0) <= 0:
        return {"success": False, "error": "Could not fetch live price for this symbol"}

    price = float(price_data["price"])
    total_value = price * quantity

    wallet = await get_or_create_wallet(user_id, db)

    if order_type == OrderType.BUY:
        if wallet.balance_inr < total_value:
            return {"success": False, "error": f"Insufficient balance. Need ₹{total_value:.2f}, have ₹{wallet.balance_inr:.2f}"}
        wallet.balance_inr -= total_value
        wallet.total_invested += total_value

        # Update or create holding
        result = await db.execute(
            select(VirtualHolding).where(
                VirtualHolding.user_id == user_id,
                VirtualHolding.symbol == symbol.upper(),
            )
        )
        holding = result.scalar_one_or_none()
        if holding:
            # Weighted average cost
            total_qty = holding.quantity + quantity
            holding.avg_cost_inr = (holding.avg_cost_inr * holding.quantity + price * quantity) / total_qty
            holding.quantity = total_qty
        else:
            holding = VirtualHolding(
                user_id=user_id,
                symbol=symbol.upper(),
                asset_type=asset_type,
                quantity=quantity,
                avg_cost_inr=price,
            )
            db.add(holding)

    elif order_type == OrderType.SELL:
        result = await db.execute(
            select(VirtualHolding).where(
                VirtualHolding.user_id == user_id,
                VirtualHolding.symbol == symbol.upper(),
            )
        )
        holding = result.scalar_one_or_none()
        if not holding or holding.quantity < quantity:
            available = holding.quantity if holding else 0
            return {"success": False, "error": f"Insufficient holdings. Have {available:.4f} units, trying to sell {quantity}"}
        holding.quantity -= quantity
        wallet.balance_inr += total_value
        if holding.quantity <= 0:
            await db.delete(holding)

    # Record the order
    order = VirtualOrder(
        user_id=user_id,
        symbol=symbol.upper(),
        asset_type=asset_type,
        order_type=order_type,
        quantity=quantity,
        price_at_execution=price,
        total_value=round(total_value, 2),
        status=OrderStatus.FILLED,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return {"success": True, "order": order, "price": price}


async def calculate_pnl(user_id: int, db: AsyncSession) -> dict:
    """Compute unrealized P&L across all virtual holdings."""
    wallet = await get_or_create_wallet(user_id, db)
    result = await db.execute(select(VirtualHolding).where(VirtualHolding.user_id == user_id))
    holdings = result.scalars().all()

    total_invested = 0.0
    current_value = 0.0

    enriched = []
    for h in holdings:
        price_data = await fetch_price(h.symbol, h.asset_type)
        live_price = float(price_data["price"]) if price_data else h.avg_cost_inr
        invested = h.quantity * h.avg_cost_inr
        current = h.quantity * live_price
        pnl = current - invested
        pnl_pct = (pnl / invested * 100) if invested else 0

        total_invested += invested
        current_value += current

        enriched.append({
            "id": h.id,
            "symbol": h.symbol,
            "asset_type": h.asset_type,
            "quantity": h.quantity,
            "avg_cost_inr": h.avg_cost_inr,
            "current_price": live_price,
            "current_value": round(current, 2),
            "unrealized_pnl": round(pnl, 2),
            "unrealized_pnl_pct": round(pnl_pct, 2),
        })

    unrealized = current_value - total_invested
    return {
        "total_invested": round(total_invested, 2),
        "current_portfolio_value": round(current_value, 2),
        "unrealized_pnl": round(unrealized, 2),
        "unrealized_pnl_pct": round((unrealized / total_invested * 100) if total_invested else 0, 2),
        "wallet_balance": round(wallet.balance_inr, 2),
        "total_account_value": round(wallet.balance_inr + current_value, 2),
        "holdings": enriched,
    }
