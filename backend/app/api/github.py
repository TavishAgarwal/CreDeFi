"""
GitHub OAuth API endpoints.
"""

import uuid

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
    redirect_uri: str = Query(default="http://localhost:3000/platforms"),
    user: User = Depends(get_current_user),
):
    """Return the GitHub OAuth authorization URL."""
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
    svc = GitHubService(session)
    try:
        account = await svc.connect_account(user.id, code)
        await session.commit()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GitHub OAuth failed: {exc}",
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
    return {
        "login": account.account_identifier,
        "is_verified": account.is_verified,
        **(account.metadata_json or {}),
    }
