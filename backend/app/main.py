"""
InvestiGator — FastAPI Application Entry Point
Wires together all 6 modules with CORS, rate limiting, and startup tasks.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import get_settings
from app.db.base import init_db
from app.routers import ai, auth, backtest, market, portfolio, profile, simulator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("investigator")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    logger.info("🐊 InvestiGator starting up…")
    # Initialize database tables
    await init_db()
    # Start market data background scheduler
    from app.services.market.scheduler import start_scheduler, stop_scheduler
    start_scheduler()
    logger.info("✅ Market data scheduler started")
    yield
    # Shutdown
    from app.services.market.scheduler import stop_scheduler
    stop_scheduler()
    logger.info("🐊 InvestiGator shut down")


# ── Create app ───────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="InvestiGator API",
    description="Investment simulation & portfolio tracking platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────────
PREFIX = "/api"
app.include_router(auth.router, prefix=PREFIX)
app.include_router(profile.router, prefix=PREFIX)
app.include_router(market.router, prefix=PREFIX)
app.include_router(portfolio.router, prefix=PREFIX)
app.include_router(simulator.router, prefix=PREFIX)
app.include_router(backtest.router, prefix=PREFIX)
app.include_router(ai.router, prefix=PREFIX)


# ── Health check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}
