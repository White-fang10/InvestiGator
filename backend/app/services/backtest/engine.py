"""
Backtesting engine — Polars-based MapReduce-equivalent strategy processor.
Supports SMA Crossover and RSI Mean Reversion strategies.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import polars as pl


def _calculate_sma(prices: List[float], window: int) -> List[Optional[float]]:
    """Simple moving average — returns None for first (window-1) values."""
    result = []
    for i in range(len(prices)):
        if i < window - 1:
            result.append(None)
        else:
            result.append(sum(prices[i - window + 1: i + 1]) / window)
    return result


def _calculate_rsi(prices: List[float], period: int = 14) -> List[Optional[float]]:
    """Relative Strength Index."""
    rsi = [None] * len(prices)
    if len(prices) < period + 1:
        return rsi
    gains, losses = [], []
    for i in range(1, period + 1):
        delta = prices[i] - prices[i - 1]
        gains.append(max(delta, 0))
        losses.append(max(-delta, 0))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    for i in range(period, len(prices)):
        if i > period:
            delta = prices[i] - prices[i - 1]
            gain = max(delta, 0)
            loss = max(-delta, 0)
            avg_gain = (avg_gain * (period - 1) + gain) / period
            avg_loss = (avg_loss * (period - 1) + loss) / period
        rs = avg_gain / avg_loss if avg_loss != 0 else float("inf")
        rsi[i] = 100 - (100 / (1 + rs))
    return rsi


def run_sma_crossover(data: List[dict], fast: int = 20, slow: int = 50) -> dict:
    """
    SMA Crossover strategy:
    Buy when fast SMA crosses above slow SMA; Sell when it crosses below.
    """
    prices = [d["close"] for d in data]
    dates = [d["date"] for d in data]
    fast_sma = _calculate_sma(prices, fast)
    slow_sma = _calculate_sma(prices, slow)

    capital = 100_000.0
    position = 0.0
    trades = 0
    wins = 0
    equity_curve = []

    for i in range(1, len(prices)):
        if fast_sma[i] is None or slow_sma[i] is None:
            equity_curve.append({"date": dates[i], "value": capital})
            continue
        if fast_sma[i - 1] is not None and slow_sma[i - 1] is not None:
            if fast_sma[i] > slow_sma[i] and fast_sma[i - 1] <= slow_sma[i - 1]:
                # Buy signal
                if position == 0:
                    position = capital / prices[i]
                    capital = 0
                    buy_price = prices[i]
            elif fast_sma[i] < slow_sma[i] and fast_sma[i - 1] >= slow_sma[i - 1]:
                # Sell signal
                if position > 0:
                    capital = position * prices[i]
                    if prices[i] > buy_price:
                        wins += 1
                    trades += 1
                    position = 0

        portfolio_value = capital + position * prices[i]
        equity_curve.append({"date": dates[i], "value": round(portfolio_value, 2)})

    final_value = capital + position * prices[-1] if prices else 100_000.0
    return _compute_metrics(equity_curve, final_value, trades, wins)


def run_rsi_mean_reversion(data: List[dict], period: int = 14, oversold: int = 30, overbought: int = 70) -> dict:
    """RSI Mean Reversion: buy when RSI < oversold, sell when RSI > overbought."""
    prices = [d["close"] for d in data]
    dates = [d["date"] for d in data]
    rsi = _calculate_rsi(prices, period)

    capital = 100_000.0
    position = 0.0
    trades = 0
    wins = 0
    buy_price = 0.0
    equity_curve = []

    for i in range(len(prices)):
        if rsi[i] is None:
            equity_curve.append({"date": dates[i], "value": capital})
            continue
        if rsi[i] < oversold and position == 0:
            position = capital / prices[i]
            buy_price = prices[i]
            capital = 0
        elif rsi[i] > overbought and position > 0:
            capital = position * prices[i]
            if prices[i] > buy_price:
                wins += 1
            trades += 1
            position = 0
        portfolio_value = capital + position * prices[i]
        equity_curve.append({"date": dates[i], "value": round(portfolio_value, 2)})

    final_value = capital + position * prices[-1] if prices else 100_000.0
    return _compute_metrics(equity_curve, final_value, trades, wins)


def _compute_metrics(equity_curve: List[dict], final_value: float, trades: int, wins: int) -> dict:
    """Compute CAGR, Sharpe ratio, max drawdown, win rate from equity curve."""
    if not equity_curve:
        return {}

    initial = 100_000.0
    values = [e["value"] for e in equity_curve]
    n_days = len(values)
    n_years = n_days / 252

    cagr = ((final_value / initial) ** (1 / n_years) - 1) * 100 if n_years > 0 else 0

    # Daily returns
    daily_returns = []
    for i in range(1, len(values)):
        if values[i - 1] > 0:
            daily_returns.append((values[i] - values[i - 1]) / values[i - 1])

    sharpe = 0.0
    if daily_returns:
        mean_r = sum(daily_returns) / len(daily_returns)
        std_r = math.sqrt(sum((r - mean_r) ** 2 for r in daily_returns) / len(daily_returns))
        sharpe = (mean_r / std_r) * math.sqrt(252) if std_r > 0 else 0

    # Max drawdown
    peak = values[0]
    max_drawdown = 0.0
    for v in values:
        peak = max(peak, v)
        dd = (peak - v) / peak
        max_drawdown = max(max_drawdown, dd)

    win_rate = (wins / trades * 100) if trades > 0 else 0

    return {
        "final_value": round(final_value, 2),
        "total_return_pct": round((final_value - initial) / initial * 100, 2),
        "cagr_pct": round(cagr, 2),
        "sharpe_ratio": round(sharpe, 3),
        "max_drawdown_pct": round(max_drawdown * 100, 2),
        "total_trades": trades,
        "win_rate_pct": round(win_rate, 2),
        "equity_curve": equity_curve[-365:],  # cap to last year for response size
    }


def run_strategy(strategy: str, data: List[dict], params: dict) -> dict:
    """Dispatch strategy by name."""
    if strategy == "sma_crossover":
        return run_sma_crossover(data, fast=params.get("fast", 20), slow=params.get("slow", 50))
    elif strategy == "rsi_mean_reversion":
        return run_rsi_mean_reversion(data, period=params.get("period", 14), oversold=params.get("oversold", 30), overbought=params.get("overbought", 70))
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
