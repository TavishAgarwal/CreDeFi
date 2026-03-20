"""
Authentication dependencies for FastAPI endpoints.

H1: Reads JWT from httpOnly cookie first, falls back to Authorization header.
This allows both cookie-based (browser) and token-based (API) auth.
"""

from fastapi import Cookie, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cookies import COOKIE_NAME
from app.core.security import decode_access_token
from app.db.session import get_session
from app.models.user import User

# Optional bearer — does not raise 403 if header is missing (cookie may be present)
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    """
    Extract the JWT from:
    1. httpOnly cookie (preferred for browsers)
    2. Authorization: Bearer header (fallback for API clients)

    Then decode and validate the token.
    """
    token: str | None = None

    # H1: Try cookie first
    cookie_token = request.cookies.get(COOKIE_NAME)
    if cookie_token:
        token = cookie_token
    # Fall back to Bearer header
    elif credentials:
        token = credentials.credentials

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = decode_access_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user = await session.scalar(select(User).where(User.id == user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


async def require_admin(
    user: User = Depends(get_current_user),
) -> User:
    """Dependency that requires the current user to have the 'admin' role."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
