"""Virtual Trading Simulator ORM models."""
from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OrderType(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, enum.Enum):
    FILLED = "filled"
    CANCELLED = "cancelled"
    FAILED = "failed"


class VirtualWallet(Base):
    """Each user gets one virtual wallet."""
    __tablename__ = "virtual_wallets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    balance_inr: Mapped[float] = mapped_column(Float, default=100000.0)  # ₹1,00,000 starting balance
    total_invested: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class VirtualOrder(Base):
    """Each simulated trade order."""
    __tablename__ = "virtual_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(30), default="stock")
    order_type: Mapped[OrderType] = mapped_column(Enum(OrderType), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    price_at_execution: Mapped[float] = mapped_column(Float, nullable=False)  # INR
    total_value: Mapped[float] = mapped_column(Float, nullable=False)          # qty × price
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.FILLED)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class VirtualHolding(Base):
    """Current virtual holdings (aggregated from orders)."""
    __tablename__ = "virtual_holdings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(30), default="stock")
    quantity: Mapped[float] = mapped_column(Float, default=0.0)
    avg_cost_inr: Mapped[float] = mapped_column(Float, default=0.0)  # weighted avg cost per unit
