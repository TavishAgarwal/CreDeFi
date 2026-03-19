"""
GitHub OAuth Service
=====================
Connects to GitHub via OAuth, fetches profile & repo data,
and stores it as a ConnectedAccount + IncomeSource.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.models.core import ConnectedAccount, IncomeSource
from app.models.enums import AccountProvider, IncomeFrequency

logger = get_logger(__name__)

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_BASE = "https://api.github.com"


class GitHubServiceError(Exception):
    pass


class GitHubService:
    """Handles the OAuth flow and data fetching from GitHub."""

    @staticmethod
    def get_oauth_url(redirect_uri: str, state: str) -> str:
        """Build the GitHub OAuth authorization URL."""
        if not settings.GITHUB_CLIENT_ID:
            raise GitHubServiceError("GITHUB_CLIENT_ID not configured")
        return (
            f"{GITHUB_AUTH_URL}"
            f"?client_id={settings.GITHUB_CLIENT_ID}"
            f"&redirect_uri={redirect_uri}"
            f"&scope=read:user%20repo"
            f"&state={state}"
        )

    @staticmethod
    async def exchange_code(code: str) -> str:
        """Exchange an OAuth authorization code for an access token."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                GITHUB_TOKEN_URL,
                json={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                },
                headers={"Accept": "application/json"},
            )
            data = resp.json()
            if "access_token" not in data:
                error = data.get("error_description", data.get("error", "Unknown error"))
                raise GitHubServiceError(f"GitHub OAuth failed: {error}")
            return data["access_token"]

    @staticmethod
    async def fetch_profile(access_token: str) -> dict:
        """Fetch the user's GitHub profile and repo statistics."""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
        }

        async with httpx.AsyncClient() as client:
            # User profile
            user_resp = await client.get(f"{GITHUB_API_BASE}/user", headers=headers)
            if user_resp.status_code != 200:
                raise GitHubServiceError(f"GitHub /user failed: {user_resp.status_code}")
            user = user_resp.json()

            # Repos (first 100)
            repos_resp = await client.get(
                f"{GITHUB_API_BASE}/user/repos",
                headers=headers,
                params={"per_page": 100, "sort": "updated"},
            )
            repos = repos_resp.json() if repos_resp.status_code == 200 else []

            # Calculate metrics
            account_age_days = 0
            if user.get("created_at"):
                created = datetime.fromisoformat(user["created_at"].replace("Z", "+00:00"))
                account_age_days = (datetime.now(timezone.utc) - created).days

            original_repos = [r for r in repos if not r.get("fork", False)]
            total_stars = sum(r.get("stargazers_count", 0) for r in repos)

            return {
                "login": user.get("login", ""),
                "name": user.get("name", ""),
                "avatar_url": user.get("avatar_url", ""),
                "public_repos": user.get("public_repos", 0),
                "followers": user.get("followers", 0),
                "account_age_days": account_age_days,
                "total_repos_fetched": len(repos),
                "original_repos_count": len(original_repos),
                "total_stars": total_stars,
                "has_original_repos": len(original_repos) > 0,
                "bio": user.get("bio", ""),
                "company": user.get("company", ""),
                "hireable": user.get("hireable", False),
            }

    @staticmethod
    def build_connected_account(
        user_id: uuid.UUID,
        profile: dict,
    ) -> ConnectedAccount:
        """Create a ConnectedAccount record from GitHub profile data."""
        return ConnectedAccount(
            user_id=user_id,
            provider=AccountProvider.GITHUB,
            account_identifier=profile["login"],
            is_verified=True,
            metadata_json={
                "name": profile.get("name"),
                "avatar_url": profile.get("avatar_url"),
                "public_repos": profile.get("public_repos"),
                "followers": profile.get("followers"),
                "account_age_days": profile.get("account_age_days"),
                "original_repos_count": profile.get("original_repos_count"),
                "total_stars": profile.get("total_stars"),
                "bio": profile.get("bio"),
                "hireable": profile.get("hireable"),
            },
        )
