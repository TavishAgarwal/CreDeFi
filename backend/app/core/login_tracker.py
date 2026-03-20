"""
Login attempt tracking for account lockout (L6).
Tracks failed login attempts per identifier (email or wallet address)
and locks accounts after too many failures.

For production, replace with Redis for distributed lockout.
"""

from __future__ import annotations

import time
import threading

MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 900  # 15 minutes


class LoginAttemptTracker:
    """Thread-safe in-memory failed login attempt tracker."""

    def __init__(
        self,
        max_attempts: int = MAX_ATTEMPTS,
        lockout_seconds: int = LOCKOUT_SECONDS,
    ) -> None:
        self._attempts: dict[str, list[float]] = {}  # identifier -> list of timestamps
        self._lockouts: dict[str, float] = {}  # identifier -> lockout_until timestamp
        self._lock = threading.Lock()
        self._max_attempts = max_attempts
        self._lockout_seconds = lockout_seconds

    def is_locked(self, identifier: str) -> bool:
        """Check if the identifier is currently locked out."""
        with self._lock:
            lockout_until = self._lockouts.get(identifier)
            if lockout_until is None:
                return False
            if time.time() >= lockout_until:
                # Lockout expired — clear it
                del self._lockouts[identifier]
                self._attempts.pop(identifier, None)
                return False
            return True

    def remaining_lockout_seconds(self, identifier: str) -> int:
        """Return seconds remaining in lockout, or 0 if not locked."""
        with self._lock:
            lockout_until = self._lockouts.get(identifier)
            if lockout_until is None:
                return 0
            remaining = lockout_until - time.time()
            return max(0, int(remaining))

    def record_failure(self, identifier: str) -> bool:
        """
        Record a failed login attempt. Returns True if the account
        is now locked out (just crossed the threshold).
        """
        with self._lock:
            now = time.time()
            window_start = now - self._lockout_seconds

            # Get existing attempts, filter to the recent window
            attempts = self._attempts.get(identifier, [])
            attempts = [t for t in attempts if t > window_start]
            attempts.append(now)
            self._attempts[identifier] = attempts

            if len(attempts) >= self._max_attempts:
                self._lockouts[identifier] = now + self._lockout_seconds
                return True
            return False

    def record_success(self, identifier: str) -> None:
        """Clear failed attempts on successful login."""
        with self._lock:
            self._attempts.pop(identifier, None)
            self._lockouts.pop(identifier, None)


# Singleton instance
login_tracker = LoginAttemptTracker()
