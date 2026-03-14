"""Portfolio (real-world tracker) ORM models."""
from __future__ import annotations

import enum
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AssetType(str, enum.Enum):
    STOCK = "stock"
    CRYPTO = "crypto"
    GOLD = "gold"
    MUTUAL_FUND = "mutual_fund"
    FIXED_DEPOSIT = "fixed_deposit"
    OTHER = "other"


class RealAsset(Base):
    """A real-world asset owned by the user (encrypted at rest)."""
    __tablename__ = "real_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    asset_type: Mapped[AssetType] = mapped_column(Enum(AssetType), nullable=False)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)          # ticker or identifier
    name: Mapped[str] = mapped_column(String(200), default="")               # human-friendly name
    quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    purchase_price: Mapped[float] = mapped_column(Float, default=0.0)        # avg cost per unit in INR
    notes_encrypted: Mapped[str] = mapped_column(Text, default="")           # AES-256 encrypted notes
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class PortfolioSnapshot(Base):
    """Daily net-worth snapshot for historical chart."""
    __tablename__ = "portfolio_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_value_inr: Mapped[float] = mapped_column(Float, nullable=False)
