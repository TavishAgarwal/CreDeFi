"""
GitHub OAuth API endpoints.

M5: redirect_uri validated against allowlist
M6: OAuth state validated in callback
L3: metadata_json filtered from profile response
H4: Internal errors not leaked to client
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.logging import get_logger
from app.db.session import get_session
from app.models.core import ConnectedAccount
from app.models.enums import AccountProvider
from app.models.user import User
from app.services.github_service import GitHubService, GitHubServiceError

router = APIRouter(prefix="/github", tags=["github"])
logger = get_logger(__name__)

# M5: Allowlist of valid redirect URIs for GitHub OAuth
_ALLOWED_REDIRECT_URIS = {
    "http://localhost:3000/platforms",
    "https://credefi.app/platforms",
}

# M6: In-memory state store (for production, use Redis or session store)
_pending_oauth_states: dict[str, str] = {}  # state -> user_id


@router.get("/connect")
async def github_connect(
    redirect_uri: str = Query(default="http://localhost:3000/platforms"),
    user: User = Depends(get_current_user),
):
    """Return the GitHub OAuth authorization URL."""
    # M5: Validate redirect_uri against allowlist
    if redirect_uri not in _ALLOWED_REDIRECT_URIS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid redirect URI",
        )

    state = str(uuid.uuid4())

    # M6: Store state for validation in callback
    _pending_oauth_states[state] = str(user.id)

    try:
        url = GitHubService.get_oauth_url(redirect_uri, state)
        return {"oauth_url": url, "state": state}
    except GitHubServiceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


@router.post("/callback")
async def github_callback(
    code: str,
    state: str = "",
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Exchange OAuth code for a token, fetch profile, and store as ConnectedAccount."""
    # M6: Validate the state parameter
    if not state or state not in _pending_oauth_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or missing OAuth state parameter",
        )

    expected_user_id = _pending_oauth_states.pop(state, None)
    if expected_user_id != str(user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="OAuth state mismatch — possible CSRF attack",
        )

    svc = GitHubService(session)
    try:
        account = await svc.connect_account(user.id, code)
        await session.commit()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except Exception:
        # H4: Don't leak internal error details
        logger.exception("GitHub OAuth callback failed for user=%s", user.id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="GitHub connection failed. Please try again.",
        )

    try:
        metrics = await svc.sync_metrics(user.id)
        await session.commit()
        return {
            "status": "connected",
            "login": account.account_identifier,
            "public_repos": metrics.public_repos,
            "account_age_days": metrics.account_age_days,
            "original_repos": metrics.public_repos,
            "total_stars": metrics.total_stars,
        }
    except Exception:
        return {
            "status": "connected",
            "login": account.account_identifier,
            "public_repos": 0,
            "account_age_days": 0,
            "original_repos": 0,
            "total_stars": 0,
        }


@router.get("/profile")
async def github_profile(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Return stored GitHub profile for the current user."""
    account = await session.scalar(
        select(ConnectedAccount).where(
            ConnectedAccount.user_id == user.id,
            ConnectedAccount.provider == AccountProvider.GITHUB,
        )
    )
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GitHub not connected",
        )

    # L3: Filter metadata_json to exclude sensitive fields (encrypted tokens)
    safe_metadata = {}
    if account.metadata_json:
        safe_metadata = {
            k: v for k, v in account.metadata_json.items()
            if k not in ("access_token_enc", "access_token", "refresh_token")
        }

    return {
        "login": account.account_identifier,
        "is_verified": account.is_verified,
        **safe_metadata,
    }


# ═══════════════════════════════════════════════════════════════════
# GET /github/public-profile/{username}  — NO AUTH REQUIRED
# ═══════════════════════════════════════════════════════════════════

@router.get("/public-profile/{username}")
async def github_public_profile(username: str):
    """
    Fetch public GitHub data for any user — no auth required.
    Uses GitHub's unauthenticated API (60 requests/hour).
    Perfect for demo mode to show REAL data.
    """
    import httpx

    headers = {"Accept": "application/vnd.github.v3+json"}
    # Use personal access token if available for higher rate limits
    if settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET:
        headers["Authorization"] = f"Basic {settings.GITHUB_CLIENT_ID}:{settings.GITHUB_CLIENT_SECRET}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Fetch user profile
            user_resp = await client.get(
                f"https://api.github.com/users/{username}", headers=headers
            )
            if user_resp.status_code == 404:
                raise HTTPException(status_code=404, detail=f"GitHub user '{username}' not found")
            if user_resp.status_code == 403:
                raise HTTPException(status_code=429, detail="GitHub API rate limit exceeded (60/hr). Try again later.")
            user_resp.raise_for_status()
            user_data = user_resp.json()

            # Fetch repos (first 30)
            repos_resp = await client.get(
                f"https://api.github.com/users/{username}/repos?sort=updated&per_page=30",
                headers=headers,
            )
            repos = repos_resp.json() if repos_resp.status_code == 200 else []

            # Calculate metrics
            total_stars = sum(r.get("stargazers_count", 0) for r in repos if isinstance(r, dict))
            original_repos = sum(1 for r in repos if isinstance(r, dict) and not r.get("fork", False))
            languages = set(r.get("language") for r in repos if isinstance(r, dict) and r.get("language"))

            created_at = user_data.get("created_at", "")
            account_age_days = 0
            if created_at:
                try:
                    created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    account_age_days = (datetime.now(timezone.utc) - created).days
                except (ValueError, TypeError):
                    pass

            return {
                "login": user_data.get("login", username),
                "name": user_data.get("name"),
                "avatar_url": user_data.get("avatar_url"),
                "bio": user_data.get("bio"),
                "public_repos": user_data.get("public_repos", 0),
                "followers": user_data.get("followers", 0),
                "following": user_data.get("following", 0),
                "account_age_days": account_age_days,
                "total_stars": total_stars,
                "original_repos": original_repos,
                "top_languages": sorted(languages)[:5],
                "hireable": user_data.get("hireable"),
                "created_at": created_at,
                "trust_signals": {
                    "has_bio": bool(user_data.get("bio")),
                    "has_name": bool(user_data.get("name")),
                    "account_mature": account_age_days > 365,
                    "has_followers": user_data.get("followers", 0) > 5,
                    "has_original_repos": original_repos > 3,
                    "has_stars": total_stars > 0,
                },
            }
    except httpx.HTTPStatusError as exc:
        logger.error("GitHub API error: %s", exc)
        raise HTTPException(status_code=502, detail="GitHub API request failed")
    except httpx.RequestError as exc:
        logger.error("GitHub request error: %s", exc)
        raise HTTPException(status_code=503, detail="Cannot reach GitHub API")
