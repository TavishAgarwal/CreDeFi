"""
Cookie-based authentication helpers.
Sets httpOnly, Secure, SameSite cookies for JWT storage.
"""

from fastapi import Response

from app.core.config import settings

COOKIE_NAME = "credefi_session"
COOKIE_MAX_AGE = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # seconds


def set_auth_cookie(response: Response, token: str) -> None:
    """Set the JWT as an httpOnly cookie on the response."""
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=not settings.DEBUG,      # Secure=true in production (HTTPS only)
        samesite="lax",                 # "lax" allows top-level navigations
        max_age=COOKIE_MAX_AGE,
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    """Remove the auth cookie."""
    response.delete_cookie(
        key=COOKIE_NAME,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        path="/",
    )
