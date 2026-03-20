"""
Token encryption for storing OAuth tokens securely at rest.
Uses Fernet symmetric encryption from the cryptography library.
Raises RuntimeError if no encryption key is configured — no silent fallback.
"""

from __future__ import annotations

from app.core.config import settings

_fernet = None


def _get_fernet():
    global _fernet
    if _fernet is not None:
        return _fernet

    key = settings.TOKEN_ENCRYPTION_KEY
    if not key or len(key) < 32:
        return None

    from cryptography.fernet import Fernet

    # Require a proper base64-encoded Fernet key (44 chars).
    # If the provided key is not a valid Fernet key, wrap it.
    if len(key) == 44:
        _fernet = Fernet(key.encode() if isinstance(key, str) else key)
    else:
        import base64
        derived = base64.urlsafe_b64encode(key[:32].encode())
        _fernet = Fernet(derived)
    return _fernet


def encrypt_token(plaintext: str) -> str:
    """Encrypt a token string. Raises if no encryption key is configured."""
    f = _get_fernet()
    if f is None:
        raise RuntimeError(
            "TOKEN_ENCRYPTION_KEY is required for token encryption. "
            "Generate one with: python -c "
            "\"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return f.encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str) -> str:
    """Decrypt a token string. Raises if no encryption key is configured."""
    f = _get_fernet()
    if f is None:
        raise RuntimeError(
            "TOKEN_ENCRYPTION_KEY is required for token decryption."
        )
    return f.decrypt(ciphertext.encode()).decode()
