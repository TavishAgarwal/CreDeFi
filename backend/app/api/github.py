"""
GitHub OAuth API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_session
from app.models.core import ConnectedAccount
from app.models.enums import AccountProvider
from app.models.user import User
from app.services.github_service import GitHubService, GitHubServiceError

router = APIRouter(prefix="/github", tags=["github"])


@router.get("/connect")
async def github_connect(
    redirect_uri: str = Query(default="http://localhost:3000/connections/callback"),
    user: User = Depends(get_current_user),
):
    """Return the GitHub OAuth authorization URL."""
    import uuid

    state = str(uuid.uuid4())
    try:
        url = GitHubService.get_oauth_url(redirect_uri, state)
        return {"oauth_url": url, "state": state}
    except GitHubServiceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


@router.post("/callback")
async def github_callback(
    code: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Exchange OAuth code for a token, fetch profile, and store as ConnectedAccount."""
    try:
        # Exchange code for access token
        access_token = await GitHubService.exchange_code(code)

        # Fetch GitHub profile
        profile = await GitHubService.fetch_profile(access_token)

        # Check if GitHub is already connected
        existing = await session.scalar(
            select(ConnectedAccount).where(
                ConnectedAccount.user_id == user.id,
                ConnectedAccount.provider == AccountProvider.GITHUB,
            )
        )

        if existing:
            # Update metadata
            existing.account_identifier = profile["login"]
            existing.is_verified = True
            existing.metadata_json = profile
        else:
            # Create new
            account = GitHubService.build_connected_account(user.id, profile)
            session.add(account)

        await session.flush()

        return {
            "status": "connected",
            "login": profile["login"],
            "public_repos": profile["public_repos"],
            "account_age_days": profile["account_age_days"],
            "original_repos": profile["original_repos_count"],
            "total_stars": profile["total_stars"],
        }
    except GitHubServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc),
        )


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
    return {
        "login": account.account_identifier,
        "is_verified": account.is_verified,
        **(account.metadata_json or {}),
    }
