"""Portfolio router — CRUD for real assets + live valuation."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.security import encrypt_data
from app.models.portfolio import RealAsset, PortfolioSnapshot
from app.models.user import User
from app.schemas.portfolio import RealAssetCreate, RealAssetOut, RealAssetUpdate, SnapshotOut
from app.services.portfolio.valuation import compute_portfolio_summary, take_snapshot

router = APIRouter(prefix="/portfolio", tags=["Portfolio Tracker"])


@router.get("/", response_model=dict)
async def get_portfolio(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full portfolio with live valuations."""
    return await compute_portfolio_summary(current_user.id, db)


@router.post("/", response_model=RealAssetOut, status_code=status.HTTP_201_CREATED)
async def add_asset(
    payload: RealAssetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a new real-world asset to the portfolio."""
    notes_enc = encrypt_data(payload.notes) if payload.notes else ""
    asset = RealAsset(
        user_id=current_user.id,
        asset_type=payload.asset_type,
        symbol=payload.symbol.upper(),
        name=payload.name or payload.symbol.upper(),
        quantity=payload.quantity,
        purchase_price=payload.purchase_price,
        notes_encrypted=notes_enc,
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return {**asset.__dict__, "live_price": 0.0, "current_value": 0.0, "gain_loss": 0.0, "gain_loss_pct": 0.0}


@router.put("/{asset_id}", response_model=RealAssetOut)
async def update_asset(
    asset_id: int,
    payload: RealAssetUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing asset."""
    result = await db.execute(
        select(RealAsset).where(RealAsset.id == asset_id, RealAsset.user_id == current_user.id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    update_data = payload.model_dump(exclude_none=True)
    if "notes" in update_data:
        asset.notes_encrypted = encrypt_data(update_data.pop("notes"))
    for field, value in update_data.items():
        setattr(asset, field, value)

    await db.commit()
    await db.refresh(asset)
    return {**asset.__dict__, "live_price": 0.0, "current_value": 0.0, "gain_loss": 0.0, "gain_loss_pct": 0.0}


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an asset from the portfolio."""
    result = await db.execute(
        select(RealAsset).where(RealAsset.id == asset_id, RealAsset.user_id == current_user.id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    await db.delete(asset)
    await db.commit()


@router.get("/history", response_model=List[SnapshotOut])
async def get_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get historical daily portfolio value snapshots."""
    result = await db.execute(
        select(PortfolioSnapshot)
        .where(PortfolioSnapshot.user_id == current_user.id)
        .order_by(PortfolioSnapshot.snapshot_date)
    )
    return result.scalars().all()


@router.post("/snapshot", status_code=status.HTTP_201_CREATED)
async def create_snapshot(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger a portfolio snapshot."""
    await take_snapshot(current_user.id, db)
    return {"message": "Snapshot saved"}
