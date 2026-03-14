"""AI Risk Assessor router."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.services.ai.analyzer import build_risk_report
from app.services.ai.ollama_client import is_ollama_available

router = APIRouter(prefix="/ai", tags=["AI Risk Assessor"])


@router.get("/health")
async def ai_health():
    """Check if the local Ollama AI is reachable."""
    available = await is_ollama_available()
    return {
        "ollama_available": available,
        "message": "Ollama is running ✅" if available else "Ollama not detected — AI features will use rule-based fallback",
    }


@router.get("/risk-report")
async def get_risk_report(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a personalized AI risk report for the user's virtual portfolio."""
    report = await build_risk_report(current_user.id, db)
    return {
        "risk_score": report.risk_score,
        "level": report.level,
        "warnings": report.warnings,
        "tips": report.tips,
        "ai_summary": report.ai_summary,
        "concentration": report.concentration,
    }
