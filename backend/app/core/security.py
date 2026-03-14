"""Security utilities: password hashing, AES-256 encryption, JWT tokens."""
from __future__ import annotations

import base64
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()

# ── Password Hashing ─────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── AES-256-GCM Encryption ───────────────────────────────────────────────────
def _get_aes_key() -> bytes:
    """Derive a 32-byte AES key from the master key setting."""
    key_str = settings.AES_MASTER_KEY
    if not key_str or key_str.startswith("CHANGE_ME"):
        # Generate a random key for dev (not persistent across restarts)
        return os.urandom(32)
    raw = base64.urlsafe_b64decode(key_str + "==")  # pad
    return raw[:32]


def encrypt_data(plaintext: str) -> str:
    """Encrypt a string → base64-encoded ciphertext (nonce + tag + ct)."""
    key = _get_aes_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return base64.urlsafe_b64encode(nonce + ct).decode()


def decrypt_data(token: str) -> str:
    """Decrypt a base64-encoded ciphertext back to the original string."""
    key = _get_aes_key()
    aesgcm = AESGCM(key)
    raw = base64.urlsafe_b64decode(token + "==")
    nonce, ct = raw[:12], raw[12:]
    return aesgcm.decrypt(nonce, ct, None).decode()


# ── JWT Tokens ───────────────────────────────────────────────────────────────
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: Dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """Returns payload dict or raises JWTError."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
