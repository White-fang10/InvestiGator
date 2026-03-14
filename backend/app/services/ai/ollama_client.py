"""Ollama client for local DeepSeek inference."""
from __future__ import annotations

import httpx

from app.config import get_settings

settings = get_settings()


async def is_ollama_available() -> bool:
    """Check if Ollama server is running."""
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            return resp.status_code == 200
    except Exception:
        return False


async def generate_analysis(prompt: str) -> str:
    """
    Send a prompt to the local Ollama DeepSeek model and return the response.
    Uses streaming=False for simplicity.
    """
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 800,
        },
    }
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{settings.OLLAMA_BASE_URL}/api/generate",
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "").strip()
