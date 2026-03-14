"""Virtual trading simulator router."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.simulator import OrderType, VirtualOrder, VirtualWallet
from app.models.user import User
from app.schemas.simulator import OrderCreate, OrderOut, WalletOut
from app.services.simulator.engine import (
    STARTING_BALANCE,
    calculate_pnl,
    execute_order,
    get_or_create_wallet,
)

router = APIRouter(prefix="/simulator", tags=["Virtual Trading Simulator"])


@router.get("/wallet", response_model=WalletOut)
async def get_wallet(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get virtual wallet balance."""
    return await get_or_create_wallet(current_user.id, db)


@router.post("/orders", status_code=status.HTTP_201_CREATED)
async def place_order(
    payload: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Place a virtual buy or sell order."""
    result = await execute_order(
        user_id=current_user.id,
        symbol=payload.symbol,
        asset_type=payload.asset_type,
        order_type=payload.order_type,
        quantity=payload.quantity,
        db=db,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    order = result["order"]
    return {
        "id": order.id,
        "symbol": order.symbol,
        "asset_type": order.asset_type,
        "order_type": order.order_type,
        "quantity": order.quantity,
        "price_at_execution": order.price_at_execution,
        "total_value": order.total_value,
        "status": order.status,
        "executed_at": order.executed_at,
        "price": result["price"],
    }


@router.get("/orders", response_model=List[OrderOut])
async def get_orders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all historical virtual orders."""
    result = await db.execute(
        select(VirtualOrder)
        .where(VirtualOrder.user_id == current_user.id)
        .order_by(VirtualOrder.executed_at.desc())
    )
    return result.scalars().all()


@router.get("/pnl")
async def get_pnl(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get P&L summary and current holdings with live prices."""
    return await calculate_pnl(current_user.id, db)


@router.post("/reset", status_code=status.HTTP_200_OK)
async def reset_wallet(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reset virtual wallet to ₹1,00,000 and clear all holdings/orders."""
    from app.models.simulator import VirtualHolding
    from sqlalchemy import delete

    # Delete orders and holdings
    await db.execute(delete(VirtualOrder).where(VirtualOrder.user_id == current_user.id))
    await db.execute(delete(VirtualHolding).where(VirtualHolding.user_id == current_user.id))

    # Reset wallet
    wallet = await get_or_create_wallet(current_user.id, db)
    wallet.balance_inr = STARTING_BALANCE
    wallet.total_invested = 0.0
    await db.commit()
    return {"message": "Wallet reset to ₹1,00,000", "balance": STARTING_BALANCE}
