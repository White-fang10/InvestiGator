"""Pydantic schemas for Virtual Simulator."""
from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel

from app.models.simulator import OrderStatus, OrderType


class OrderCreate(BaseModel):
    symbol: str
    asset_type: str = "stock"
    order_type: OrderType
    quantity: float


class OrderOut(BaseModel):
    id: int
    symbol: str
    asset_type: str
    order_type: OrderType
    quantity: float
    price_at_execution: float
    total_value: float
    status: OrderStatus
    executed_at: datetime

    model_config = {"from_attributes": True}


class WalletOut(BaseModel):
    balance_inr: float
    total_invested: float

    model_config = {"from_attributes": True}


class HoldingOut(BaseModel):
    id: int
    symbol: str
    asset_type: str
    quantity: float
    avg_cost_inr: float
    current_price: float = 0.0
    current_value: float = 0.0
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0

    model_config = {"from_attributes": True}


class PnLSummary(BaseModel):
    total_invested: float
    current_portfolio_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    wallet_balance: float
    total_account_value: float
