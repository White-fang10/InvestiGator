"""Pydantic schemas for Portfolio (real-world tracker)."""
from __future__ import annotations

from datetime import date, datetime
from typing import Dict, List, Optional

from pydantic import BaseModel

from app.models.portfolio import AssetType


class RealAssetCreate(BaseModel):
    asset_type: AssetType
    symbol: str
    name: str = ""
    quantity: float
    purchase_price: float = 0.0
    notes: str = ""


class RealAssetUpdate(BaseModel):
    name: Optional[str] = None
    quantity: Optional[float] = None
    purchase_price: Optional[float] = None
    notes: Optional[str] = None


class RealAssetOut(BaseModel):
    id: int
    asset_type: AssetType
    symbol: str
    name: str
    quantity: float
    purchase_price: float
    live_price: float = 0.0
    current_value: float = 0.0
    gain_loss: float = 0.0
    gain_loss_pct: float = 0.0
    created_at: datetime

    model_config = {"from_attributes": True}


class AllocationBreakdown(BaseModel):
    asset_type: str
    value_inr: float
    percentage: float


class PortfolioSummary(BaseModel):
    total_invested: float
    total_current_value: float
    overall_gain_loss: float
    overall_gain_loss_pct: float
    allocation: List[AllocationBreakdown]
    assets: List[RealAssetOut]


class SnapshotOut(BaseModel):
    snapshot_date: date
    total_value_inr: float

    model_config = {"from_attributes": True}
