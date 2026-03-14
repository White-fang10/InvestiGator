"""
Application configuration loaded from environment variables / .env file.
Uses pydantic-settings for type-safe, validated settings.
"""
from __future__ import annotations

import secrets
from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ─────────────────────────────────────────────────────────
    APP_NAME: str = "InvestiGator"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./investigator.db"

    # ── JWT ──────────────────────────────────────────────────────────────────
    SECRET_KEY: str = secrets.token_hex(64)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── AES-256 Encryption (32-byte key, base64-url-encoded) ─────────────────
    AES_MASTER_KEY: str = ""

    # ── CORS ─────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://localhost:5174"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    AUTH_RATE_LIMIT: str = "10/minute"
    AUTH_HOUR_LIMIT: str = "30/hour"

    # ── Redis (optional — falls back to in-memory cache) ─────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = False

    # ── Market Data API Keys ──────────────────────────────────────────────────
    METAL_PRICE_API_KEY: str = ""   # https://metalpriceapi.com (free tier)
    ALPHA_VANTAGE_API_KEY: str = "" # optional fallback for stocks

    # ── Ollama / AI ───────────────────────────────────────────────────────────
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "deepseek-r1:1.5b"

    # ── OAuth2 (optional) ─────────────────────────────────────────────────────
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings instance — call this everywhere instead of Settings()."""
    return Settings()
