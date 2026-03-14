"""Download historical OHLCV data via yfinance and save as Parquet files."""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import List

import yfinance as yf

DATA_DIR = Path("data/historical")


def download_historical(symbol: str, start: str, end: str) -> List[dict]:
    """
    Download daily OHLCV data for symbol between start and end dates.
    Returns list of dicts: [{date, open, high, low, close, volume}]
    Also caches to Parquet file for offline use.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    parquet_path = DATA_DIR / f"{symbol.replace('/', '_')}_{start}_{end}.parquet"

    # Try loading from cache first
    if parquet_path.exists():
        try:
            import polars as pl
            df = pl.read_parquet(parquet_path)
            return df.to_dicts()
        except Exception:
            pass

    # Fetch from yfinance
    ticker = yf.Ticker(symbol if "." in symbol or "^" in symbol else f"{symbol}.NS")
    hist = ticker.history(start=start, end=end)
    if hist.empty:
        return []

    records = []
    for idx, row in hist.iterrows():
        records.append({
            "date": str(idx.date()),
            "open": round(float(row["Open"]), 2),
            "high": round(float(row["High"]), 2),
            "low": round(float(row["Low"]), 2),
            "close": round(float(row["Close"]), 2),
            "volume": int(row["Volume"]),
        })

    # Cache to Parquet
    try:
        import polars as pl
        df = pl.DataFrame(records)
        df.write_parquet(parquet_path)
    except Exception:
        pass

    return records
