"""
Token encryption for storing OAuth tokens securely at rest.
Uses Fernet symmetric encryption from the cryptography library.
Falls back to base64 encoding if no key is configured (dev only).
"""

from __future__ import annotations

import base64

from app.core.config import settings

_fernet = None


def _get_fernet():
    global _fernet
    if _fernet is not None:
        return _fernet

    key = settings.TOKEN_ENCRYPTION_KEY
    if not key:
        return None

    from cryptography.fernet import Fernet
    if len(key) < 32:
        key = base64.urlsafe_b64encode(key.ljust(32, "0")[:32].encode()).decode()
    _fernet = Fernet(key.encode() if isinstance(key, str) else key)
    return _fernet


def encrypt_token(plaintext: str) -> str:
    f = _get_fernet()
    if f is None:
        return base64.b64encode(plaintext.encode()).decode()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str) -> str:
    f = _get_fernet()
    if f is None:
        return base64.b64decode(ciphertext.encode()).decode()
    return f.decrypt(ciphertext.encode()).decode()
