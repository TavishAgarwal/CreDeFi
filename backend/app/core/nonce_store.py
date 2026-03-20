"""
Wallet Login Nonce Store
=========================
In-memory nonce store with TTL for wallet-based authentication.
Prevents replay attacks by ensuring each signed message can only be used once.

For production, replace with Redis or database-backed storage.
"""

from __future__ import annotations

import time
import threading

NONCE_TTL_SECONDS = 300  # 5 minutes


class NonceStore:
    """Thread-safe in-memory nonce store with expiry."""

    def __init__(self, ttl: int = NONCE_TTL_SECONDS) -> None:
        self._nonces: dict[str, float] = {}  # nonce -> expiry timestamp
        self._lock = threading.Lock()
        self._ttl = ttl

    def issue(self, nonce: str) -> None:
        """Record a newly issued nonce with TTL."""
        with self._lock:
            self._cleanup()
            self._nonces[nonce] = time.time() + self._ttl

    def consume(self, nonce: str) -> bool:
        """
        Consume a nonce. Returns True if it was valid (existed and not expired).
        The nonce is removed after consumption, preventing replay.
        """
        with self._lock:
            self._cleanup()
            expiry = self._nonces.pop(nonce, None)
            if expiry is None:
                return False
            return time.time() < expiry

    def _cleanup(self) -> None:
        """Remove expired nonces."""
        now = time.time()
        expired = [k for k, v in self._nonces.items() if v <= now]
        for k in expired:
            del self._nonces[k]


# Singleton instance
wallet_nonce_store = NonceStore()
