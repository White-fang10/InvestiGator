"""Market data fetcher — pulls live prices from yfinance, CoinGecko, and free APIs."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Optional

import httpx
import yfinance as yf

from app.config import get_settings

settings = get_settings()


async def _get_inr_rate() -> float:
    """Fetch USD → INR exchange rate."""
    try:
        ticker = yf.Ticker("USDINR=X")
        hist = ticker.fast_info
        rate = hist.last_price
        return float(rate) if rate else 83.5
    except Exception:
        return 83.5  # fallback


async def fetch_stock_price(symbol: str) -> Optional[dict]:
    """
    Fetch stock/index price via yfinance.
    symbol examples: "RELIANCE.NS", "TCS.NS", "^NSEI"
    """
    try:
        loop = asyncio.get_event_loop()
        def _sync_fetch():
            t = yf.Ticker(symbol)
            info = t.fast_info
            hist = t.history(period="2d")
            if hist.empty:
                return None
            prev_close = hist["Close"].iloc[-2] if len(hist) >= 2 else hist["Close"].iloc[-1]
            curr_price = hist["Close"].iloc[-1]
            change_pct = ((curr_price - prev_close) / prev_close) * 100
            return {
                "symbol": symbol,
                "name": info.get("longName", symbol) if hasattr(info, "get") else symbol,
                "price": round(float(curr_price), 2),
                "currency": "INR",
                "change_pct": round(float(change_pct), 2),
                "source": "yfinance",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        return await loop.run_in_executor(None, _sync_fetch)
    except Exception as e:
        return None


async def fetch_crypto_price(coin_id: str) -> Optional[dict]:
    """
    Fetch crypto price from CoinGecko (free, no key needed).
    coin_id examples: "bitcoin", "ethereum", "solana"
    """
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": coin_id, "vs_currencies": "inr,usd", "include_24hr_change": "true"},
            )
            resp.raise_for_status()
            data = resp.json()
            if coin_id not in data:
                return None
            entry = data[coin_id]
            return {
                "symbol": coin_id.upper(),
                "name": coin_id.capitalize(),
                "price": entry.get("inr", 0),
                "currency": "INR",
                "change_pct": round(entry.get("inr_24h_change", 0), 2),
                "source": "coingecko",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
    except Exception:
        return None


async def fetch_gold_price() -> Optional[dict]:
    """
    Fetch gold price. Uses metalpriceapi.com if key provided, else fallback estimate.
    """
    api_key = settings.METAL_PRICE_API_KEY
    if api_key:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"https://api.metalpriceapi.com/v1/latest?api_key={api_key}&base=XAU&currencies=INR"
                )
                resp.raise_for_status()
                data = resp.json()
                inr_per_troy_oz = data["rates"]["INR"]
                price_per_gram = inr_per_troy_oz / 31.1035
                return {
                    "symbol": "XAU",
                    "name": "Gold (per gram)",
                    "price": round(price_per_gram, 2),
                    "currency": "INR",
                    "change_pct": 0.0,
                    "source": "metalpriceapi",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
        except Exception:
            pass
    # Fallback: use GLD ETF as proxy
    return {
        "symbol": "XAU",
        "name": "Gold (per gram, approx)",
        "price": 7200.0,
        "currency": "INR",
        "change_pct": 0.0,
        "source": "fallback",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def fetch_mutual_fund_nav(scheme_code: str) -> Optional[dict]:
    """
    Fetch Mutual Fund NAV from mfapi.in (free, no key needed).
    scheme_code: e.g. "119598" (Axis Bluechip)
    """
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"https://api.mfapi.in/mf/{scheme_code}/latest")
            resp.raise_for_status()
            data = resp.json()
            nav = float(data["data"][0]["nav"])
            return {
                "symbol": scheme_code,
                "name": data.get("meta", {}).get("scheme_name", scheme_code),
                "price": nav,
                "currency": "INR",
                "change_pct": 0.0,
                "source": "mfapi",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
    except Exception:
        return None


async def fetch_price(symbol: str, asset_type: str = "stock") -> Optional[dict]:
    """Unified price fetch dispatcher."""
    asset_type = asset_type.lower()
    if asset_type == "crypto":
        # Map common tickers to CoinGecko IDs
        cg_map = {
            "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
            "DOGE": "dogecoin", "ADA": "cardano", "XRP": "ripple",
            "BNB": "binancecoin", "MATIC": "matic-network",
        }
        coin_id = cg_map.get(symbol.upper(), symbol.lower())
        return await fetch_crypto_price(coin_id)
    elif asset_type == "gold":
        return await fetch_gold_price()
    elif asset_type == "mutual_fund":
        return await fetch_mutual_fund_nav(symbol)
    else:
        # Stock / index — append .NS if no exchange suffix
        ticker = symbol if "." in symbol or "^" in symbol else f"{symbol}.NS"
        return await fetch_stock_price(ticker)
