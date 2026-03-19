"""
GitHub Integration Service
===========================
- OAuth code-for-token exchange
- REST API data fetching (user profile, repos, commit activity)
- Persists to GitHubMetrics + ConnectedAccount tables
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.models.core import ConnectedAccount
from app.models.enums import AccountProvider
from app.models.integrations import GitHubMetrics
from app.utils.crypto import encrypt_token

logger = get_logger(__name__)

GITHUB_API = "https://api.github.com"
GITHUB_OAUTH_URL = "https://github.com/login/oauth/access_token"
GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"


class GitHubServiceError(Exception):
    """User-visible GitHub OAuth or API failure."""


class GitHubService:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    @staticmethod
    def get_oauth_url(redirect_uri: str, state: str) -> str:
        """Build GitHub OAuth authorize URL (used by /github/connect)."""
        if not settings.GITHUB_CLIENT_ID:
            raise GitHubServiceError("GITHUB_CLIENT_ID not configured")
        return (
            f"{GITHUB_AUTH_URL}?client_id={settings.GITHUB_CLIENT_ID}"
            f"&redirect_uri={redirect_uri}"
            f"&scope=read:user%20repo"
            f"&state={state}"
        )

    async def exchange_oauth_code(self, code: str) -> str:
        """Exchange an OAuth authorization code for an access token."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                GITHUB_OAUTH_URL,
                json={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                },
                headers={"Accept": "application/json"},
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()

        token = data.get("access_token")
        if not token:
            raise ValueError(f"GitHub OAuth failed: {data.get('error_description', 'unknown')}")
        return token

    async def connect_account(
        self, user_id: uuid.UUID, code: str
    ) -> ConnectedAccount:
        """Full OAuth flow: exchange code, fetch profile, store account."""
        token = await self.exchange_oauth_code(code)
        profile = await self._fetch_user_profile(token)
        username = profile["login"]

        existing = await self._s.scalar(
            select(ConnectedAccount).where(
                ConnectedAccount.user_id == user_id,
                ConnectedAccount.provider == AccountProvider.GITHUB,
            )
        )
        if existing:
            existing.account_identifier = username
            existing.is_verified = True
            existing.metadata_json = {
                "access_token_enc": encrypt_token(token),
                "avatar_url": profile.get("avatar_url"),
            }
            await self._s.flush()
            return existing

        account = ConnectedAccount(
            user_id=user_id,
            provider=AccountProvider.GITHUB,
            account_identifier=username,
            is_verified=True,
            metadata_json={
                "access_token_enc": encrypt_token(token),
                "avatar_url": profile.get("avatar_url"),
            },
        )
        self._s.add(account)
        await self._s.flush()
        return account

    async def sync_metrics(
        self, user_id: uuid.UUID, token: str | None = None
    ) -> GitHubMetrics:
        """Fetch all GitHub data and upsert into GitHubMetrics."""
        if token is None:
            token = await self._get_stored_token(user_id)
        if not token:
            raise ValueError("No GitHub token available for this user")

        profile = await self._fetch_user_profile(token)
        repos = await self._fetch_repos(token, profile["login"])
        events = await self._fetch_contribution_events(token, profile["login"])

        total_stars = sum(r.get("stargazers_count", 0) for r in repos)
        languages: dict[str, int] = {}
        for r in repos:
            lang = r.get("language")
            if lang:
                languages[lang] = languages.get(lang, 0) + 1

        created = datetime.fromisoformat(profile["created_at"].replace("Z", "+00:00"))
        age_days = (datetime.now(timezone.utc) - created).days

        commit_count, streak = self._analyze_events(events)
        weekly_freq = commit_count / max(52, 1) if commit_count > 0 else 0.0

        existing = await self._s.scalar(
            select(GitHubMetrics).where(GitHubMetrics.user_id == user_id)
            .order_by(GitHubMetrics.created_at.desc()).limit(1)
        )

        if existing:
            existing.github_username = profile["login"]
            existing.public_repos = profile.get("public_repos", 0)
            existing.total_stars = total_stars
            existing.total_commits_last_year = commit_count
            existing.contribution_streak_days = streak
            existing.followers = profile.get("followers", 0)
            existing.following = profile.get("following", 0)
            existing.account_age_days = age_days
            existing.top_languages = languages
            existing.commit_frequency_weekly = round(weekly_freq, 2)
            existing.last_synced_at = datetime.now(timezone.utc)
            await self._s.flush()
            return existing

        metrics = GitHubMetrics(
            user_id=user_id,
            github_username=profile["login"],
            public_repos=profile.get("public_repos", 0),
            total_stars=total_stars,
            total_commits_last_year=commit_count,
            contribution_streak_days=streak,
            followers=profile.get("followers", 0),
            following=profile.get("following", 0),
            account_age_days=age_days,
            top_languages=languages,
            commit_frequency_weekly=round(weekly_freq, 2),
            last_synced_at=datetime.now(timezone.utc),
        )
        self._s.add(metrics)
        await self._s.flush()
        return metrics

    # ── GitHub REST API calls ──────────────────────────────────────

    async def _fetch_user_profile(self, token: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GITHUB_API}/user",
                headers=self._auth_headers(token),
                timeout=15.0,
            )
            resp.raise_for_status()
            return resp.json()

    async def _fetch_repos(self, token: str, username: str) -> list[dict]:
        repos = []
        page = 1
        async with httpx.AsyncClient() as client:
            while page <= 5:  # cap at 500 repos
                resp = await client.get(
                    f"{GITHUB_API}/users/{username}/repos",
                    params={"per_page": 100, "page": page, "sort": "updated"},
                    headers=self._auth_headers(token),
                    timeout=15.0,
                )
                resp.raise_for_status()
                batch = resp.json()
                if not batch:
                    break
                repos.extend(batch)
                page += 1
        return repos

    async def _fetch_contribution_events(self, token: str, username: str) -> list[dict]:
        events = []
        async with httpx.AsyncClient() as client:
            for page in range(1, 4):  # 3 pages of events (90 events max)
                resp = await client.get(
                    f"{GITHUB_API}/users/{username}/events",
                    params={"per_page": 30, "page": page},
                    headers=self._auth_headers(token),
                    timeout=15.0,
                )
                if resp.status_code != 200:
                    break
                batch = resp.json()
                if not batch:
                    break
                events.extend(batch)
        return events

    @staticmethod
    def _analyze_events(events: list[dict]) -> tuple[int, int]:
        """Returns (total_push_events, current_contribution_streak_days)."""
        push_dates: set[str] = set()
        for e in events:
            if e.get("type") == "PushEvent":
                date_str = e.get("created_at", "")[:10]
                if date_str:
                    push_dates.add(date_str)

        total = len(push_dates)
        if not push_dates:
            return 0, 0

        sorted_dates = sorted(push_dates, reverse=True)
        streak = 1
        for i in range(1, len(sorted_dates)):
            prev = datetime.strptime(sorted_dates[i - 1], "%Y-%m-%d")
            curr = datetime.strptime(sorted_dates[i], "%Y-%m-%d")
            if (prev - curr).days == 1:
                streak += 1
            else:
                break
        return total, streak

    async def _get_stored_token(self, user_id: uuid.UUID) -> str | None:
        account = await self._s.scalar(
            select(ConnectedAccount).where(
                ConnectedAccount.user_id == user_id,
                ConnectedAccount.provider == AccountProvider.GITHUB,
            )
        )
        if not account or not account.metadata_json:
            return None
        enc = account.metadata_json.get("access_token_enc")
        if not enc:
            return None
        from app.utils.crypto import decrypt_token
        return decrypt_token(enc)

    @staticmethod
    def _auth_headers(token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
