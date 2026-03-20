from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_log import log_auth_event
from app.core.cookies import clear_auth_cookie, set_auth_cookie
from app.core.deps import get_current_user
from app.core.login_tracker import login_tracker
from app.core.nonce_store import wallet_nonce_store
from app.db.session import get_session
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    NonceResponse,
    RegisterRequest,
    TokenResponse,
    WalletLoginRequest,
)
from app.schemas.user import UserResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

# H2: Strict rate limits for auth endpoints
limiter = Limiter(key_func=get_remote_address)


def _get_client_ip(request: Request) -> str:
    """Extract client IP from request (supports X-Forwarded-For)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
async def register(
    body: RegisterRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    ip = _get_client_ip(request)
    try:
        user = await AuthService(session).register(body)
        log_auth_event("register", identifier=body.email, user_id=str(user.id), ip=ip)
        return user
    except ValueError as exc:
        log_auth_event("register", identifier=body.email, ip=ip, success=False, detail=str(exc))
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
    ip = _get_client_ip(request)

    # L6: Check account lockout
    if login_tracker.is_locked(body.email):
        remaining = login_tracker.remaining_lockout_seconds(body.email)
        log_auth_event("login", identifier=body.email, ip=ip, success=False, detail=f"locked_out ({remaining}s)")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account temporarily locked. Try again in {remaining} seconds.",
        )

    try:
        result = await AuthService(session).login(body)
        login_tracker.record_success(body.email)
        log_auth_event("login", identifier=body.email, ip=ip)

        # H1: Set httpOnly cookie
        set_auth_cookie(response, result.access_token)

        return result
    except ValueError:
        login_tracker.record_failure(body.email)
        log_auth_event("login", identifier=body.email, ip=ip, success=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )


@router.post("/wallet-login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def wallet_login(
    body: WalletLoginRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
    ip = _get_client_ip(request)

    # L6: Check account lockout
    if login_tracker.is_locked(body.wallet_address):
        remaining = login_tracker.remaining_lockout_seconds(body.wallet_address)
        log_auth_event("wallet_login", identifier=body.wallet_address, ip=ip, success=False, detail="locked_out")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account temporarily locked. Try again in {remaining} seconds.",
        )

    try:
        result = await AuthService(session).wallet_login(
            body.wallet_address, body.signature, body.message, body.nonce
        )
        login_tracker.record_success(body.wallet_address)
        log_auth_event("wallet_login", identifier=body.wallet_address, ip=ip)

        # H1: Set httpOnly cookie
        set_auth_cookie(response, result.access_token)

        return result
    except ValueError:
        login_tracker.record_failure(body.wallet_address)
        log_auth_event("wallet_login", identifier=body.wallet_address, ip=ip, success=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid wallet credentials",
        )


@router.get("/wallet-nonce", response_model=NonceResponse)
@limiter.limit("10/minute")
async def get_wallet_nonce(request: Request, wallet_address: str):
    """Issue a one-time nonce for wallet login. Must be used within 5 minutes."""
    import uuid

    nonce = str(uuid.uuid4())
    wallet_nonce_store.issue(nonce)
    return NonceResponse(nonce=nonce, wallet_address=wallet_address)


@router.post("/logout")
async def logout(response: Response, user: User = Depends(get_current_user)):
    """Clear the auth cookie and end the session."""
    clear_auth_cookie(response)
    log_auth_event("logout", user_id=str(user.id))
    return {"status": "logged out"}


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return user
