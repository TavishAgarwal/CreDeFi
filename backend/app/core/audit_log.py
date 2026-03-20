"""
Security Audit Logger
======================
Structured logging for security-relevant events.
Provides a dedicated logger for auth, admin, and security events
separate from the general application logger.
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone


def _get_audit_logger() -> logging.Logger:
    """Create a dedicated security audit logger."""
    logger = logging.getLogger("credefi.security.audit")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | AUDIT | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


audit_log = _get_audit_logger()


def log_auth_event(
    event: str,
    *,
    identifier: str = "",
    user_id: str = "",
    ip: str = "",
    success: bool = True,
    detail: str = "",
) -> None:
    """Log an authentication event."""
    status = "SUCCESS" if success else "FAILED"
    parts = [f"event={event}", f"status={status}"]
    if identifier:
        parts.append(f"identifier={identifier}")
    if user_id:
        parts.append(f"user_id={user_id}")
    if ip:
        parts.append(f"ip={ip}")
    if detail:
        parts.append(f"detail={detail}")

    message = " | ".join(parts)
    if success:
        audit_log.info(message)
    else:
        audit_log.warning(message)


def log_admin_action(
    action: str,
    *,
    admin_id: str = "",
    target: str = "",
    detail: str = "",
) -> None:
    """Log an admin/privileged action."""
    parts = [f"action={action}"]
    if admin_id:
        parts.append(f"admin_id={admin_id}")
    if target:
        parts.append(f"target={target}")
    if detail:
        parts.append(f"detail={detail}")

    audit_log.info(" | ".join(parts))
