"""AI Risk Analyzer — builds portfolio risk profile and generates Ollama-powered feedback."""
from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.simulator import VirtualHolding, VirtualOrder
from app.services.ai.ollama_client import generate_analysis
from app.services.market.fetcher import fetch_price


@dataclass
class RiskReport:
    risk_score: int  # 0 = low risk, 100 = very high risk
    level: str       # "Low" | "Moderate" | "High" | "Very High"
    warnings: List[str] = field(default_factory=list)
    tips: List[str] = field(default_factory=list)
    ai_summary: str = ""
    concentration: dict = field(default_factory=dict)


async def build_risk_report(user_id: int, db: AsyncSession) -> RiskReport:
    """Analyze virtual portfolio and generate risk report using DeepSeek."""

    # Fetch holdings
    result = await db.execute(select(VirtualHolding).where(VirtualHolding.user_id == user_id))
    holdings = result.scalars().all()

    # Fetch recent orders
    result = await db.execute(
        select(VirtualOrder)
        .where(VirtualOrder.user_id == user_id)
        .order_by(VirtualOrder.executed_at.desc())
        .limit(20)
    )
    orders = result.scalars().all()

    if not holdings and not orders:
        return RiskReport(
            risk_score=0,
            level="Low",
            warnings=[],
            tips=["Start trading in the simulator to get a personalized risk assessment."],
            ai_summary="No trading activity detected yet. Place some virtual trades to receive AI-powered risk analysis.",
        )

    # Compute allocation by asset type
    type_values: dict = defaultdict(float)
    total_value = 0.0
    holdings_data = []

    for h in holdings:
        price_data = await fetch_price(h.symbol, h.asset_type)
        price = float(price_data["price"]) if price_data else h.avg_cost_inr
        val = h.quantity * price
        type_values[h.asset_type] += val
        total_value += val
        holdings_data.append({"symbol": h.symbol, "type": h.asset_type, "value_inr": round(val, 2)})

    concentration = {
        k: round(v / total_value * 100, 1) if total_value else 0
        for k, v in type_values.items()
    }

    # Rule-based pattern detection
    warnings = []
    tips = []
    base_score = 20

    crypto_pct = concentration.get("crypto", 0)
    stock_pct = concentration.get("stock", 0)

    if crypto_pct > 60:
        warnings.append(f"⚠️ Your virtual portfolio is {crypto_pct:.0f}% crypto — highly volatile. Consider diversifying.")
        base_score += 35
    elif crypto_pct > 40:
        warnings.append(f"⚠️ Crypto is {crypto_pct:.0f}% of your portfolio. High risk exposure.")
        base_score += 20

    if len(holdings) <= 2 and total_value > 10000:
        warnings.append("⚠️ Very few assets held — concentration risk is high.")
        base_score += 15

    if len(holdings) == 0 and total_value == 0:
        tips.append("💡 Your portfolio is all cash. Consider deploying capital to grow your virtual wealth.")

    if stock_pct > 80:
        tips.append("💡 Consider adding some bonds, gold, or mutual funds for balance.")
        base_score += 10

    if total_value < 50000 and len(orders) > 15:
        warnings.append("⚠️ High trade frequency with a shrinking portfolio may indicate over-trading.")
        base_score += 15

    if len(holdings) >= 8:
        tips.append("✅ Good diversification! You hold multiple assets across your portfolio.")
        base_score = max(base_score - 10, 0)

    if not tips:
        tips.append("💡 Review your asset allocation monthly to stay aligned with your risk tolerance.")

    risk_score = min(base_score, 100)
    level = "Low" if risk_score < 30 else "Moderate" if risk_score < 55 else "High" if risk_score < 80 else "Very High"

    # Build AI prompt
    prompt = f"""You are InvestiGator, a friendly AI investment risk coach. Analyze this simulated portfolio:

Holdings: {json.dumps(holdings_data, indent=2)}
Asset Allocation: {json.dumps(concentration)}
Number of holdings: {len(holdings)}
Total portfolio value: ₹{total_value:,.2f}
Recent trade count: {len(orders)}
Risk Score (rule-based): {risk_score}/100 ({level})
Detected Issues: {json.dumps(warnings)}

Write a concise (3-4 sentences) personalized risk assessment for this trader. Be encouraging but honest.
Point out the biggest risk and give one actionable suggestion. Do not use markdown headers."""

    try:
        ai_summary = await generate_analysis(prompt)
    except Exception:
        ai_summary = f"Your simulated portfolio carries a {level.lower()} risk level (score: {risk_score}/100). {warnings[0] if warnings else 'Keep diversifying your portfolio for better risk management.'}"

    return RiskReport(
        risk_score=risk_score,
        level=level,
        warnings=warnings,
        tips=tips,
        ai_summary=ai_summary,
        concentration=concentration,
    )
