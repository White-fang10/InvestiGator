"""Backtesting router — submit and retrieve backtest jobs."""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.backtest import BacktestJob
from app.models.user import User
from app.services.backtest.downloader import download_historical
from app.services.backtest.engine import run_strategy

router = APIRouter(prefix="/backtest", tags=["Backtesting"])


class BacktestRequest(BaseModel):
    symbol: str
    strategy: str = "sma_crossover"  # or "rsi_mean_reversion"
    start_date: str = "2022-01-01"
    end_date: str = "2024-12-31"
    params: dict = {}


class BacktestOut(BaseModel):
    id: int
    symbol: str
    strategy: str
    status: str
    result_json: str
    created_at: datetime

    model_config = {"from_attributes": True}


@router.post("/run", status_code=status.HTTP_202_ACCEPTED)
async def run_backtest(
    payload: BacktestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a backtest job (runs synchronously for now — async queue in production)."""
    job = BacktestJob(
        user_id=current_user.id,
        symbol=payload.symbol,
        strategy=payload.strategy,
        params_json=json.dumps(payload.params),
        status="running",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Run in executor to avoid blocking
    loop = asyncio.get_event_loop()
    try:
        def _run():
            data = download_historical(payload.symbol, payload.start_date, payload.end_date)
            if not data:
                return {"error": "No historical data found for this symbol/date range"}
            return run_strategy(payload.strategy, data, payload.params)

        result = await loop.run_in_executor(None, _run)
        job.status = "done" if "error" not in result else "failed"
        job.result_json = json.dumps(result)
        job.completed_at = datetime.now(timezone.utc)
    except Exception as e:
        job.status = "failed"
        job.result_json = json.dumps({"error": str(e)})
        job.completed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(job)
    return {
        "id": job.id,
        "symbol": job.symbol,
        "strategy": job.strategy,
        "status": job.status,
        "result": json.loads(job.result_json),
        "created_at": job.created_at,
    }


@router.get("/history")
async def get_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get list of past backtest jobs for the current user."""
    result = await db.execute(
        select(BacktestJob)
        .where(BacktestJob.user_id == current_user.id)
        .order_by(BacktestJob.created_at.desc())
        .limit(20)
    )
    jobs = result.scalars().all()
    return [
        {
            "id": j.id,
            "symbol": j.symbol,
            "strategy": j.strategy,
            "status": j.status,
            "created_at": j.created_at,
            "completed_at": j.completed_at,
        }
        for j in jobs
    ]


@router.get("/{job_id}")
async def get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific backtest job result."""
    result = await db.execute(
        select(BacktestJob).where(
            BacktestJob.id == job_id, BacktestJob.user_id == current_user.id
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": job.id,
        "symbol": job.symbol,
        "strategy": job.strategy,
        "status": job.status,
        "result": json.loads(job.result_json),
        "created_at": job.created_at,
        "completed_at": job.completed_at,
    }
