"""Pydantic schemas for User and Auth."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.user import RiskTolerance


# ── Auth Schemas ─────────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    display_name: str = Field(default="Investor", min_length=1, max_length=100)
    risk_tolerance: RiskTolerance = RiskTolerance.MODERATE


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# ── User / Profile Schemas ────────────────────────────────────────────────────
class ProfileOut(BaseModel):
    display_name: str
    risk_tolerance: RiskTolerance
    avatar_url: str
    bio: str

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    created_at: datetime
    profile: Optional[ProfileOut] = None

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    risk_tolerance: Optional[RiskTolerance] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)
