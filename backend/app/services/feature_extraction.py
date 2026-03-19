"""
Feature Extraction Pipeline
=============================
Aggregates data from all integration sources (GitHub, Stripe, Alchemy)
and the existing DB tables into a unified feature vector with all values
normalized to 0→1 scale.

Entry point: extractFeatures(user_id) → dict[str, float]
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.core import ConnectedAccount, IncomeSource
from app.models.integrations import GitHubMetrics, WalletMetrics

logger = get_logger(__name__)

# ═══════════════════════════════════════════════════════════════
# Normalization constants (caps for 0→1 mapping)
# ═══════════════════════════════════════════════════════════════
GITHUB_REPO_CAP = 50
GITHUB_STARS_CAP = 200
GITHUB_COMMITS_CAP = 500
GITHUB_STREAK_CAP = 90
GITHUB_FOLLOWERS_CAP = 100
GITHUB_ACCOUNT_AGE_CAP = 2000  # ~5.5 years

WALLET_TX_CAP = 500
WALLET_AGE_CAP = 1095  # 3 years
WALLET_ETH_CAP = 10.0  # ETH
WALLET_TOKEN_VALUE_CAP = 50_000  # USD
WALLET_COUNTERPARTY_CAP = 50
WALLET_DEFI_CAP = 50

INCOME_MONTHLY_CAP = 50_000  # USD


@dataclass
class IntegrationFeatures:
    """All extracted features with values normalized to 0→1."""
    # GitHub features
    github_repo_activity: float = 0.0
    github_star_reputation: float = 0.0
    github_commit_consistency: float = 0.0
    github_streak_dedication: float = 0.0
    github_community_standing: float = 0.0
    github_account_maturity: float = 0.0

    # Wallet features
    wallet_transaction_volume: float = 0.0
    wallet_age_score: float = 0.0
    wallet_balance_health: float = 0.0
    wallet_token_diversity: float = 0.0
    wallet_counterparty_breadth: float = 0.0
    wallet_defi_engagement: float = 0.0

    # Income features
    income_level: float = 0.0
    income_verification: float = 0.0
    income_consistency: float = 0.0

    # Platform connectivity
    platform_count: float = 0.0
    platform_verification_ratio: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return {
            "github_repo_activity": self.github_repo_activity,
            "github_star_reputation": self.github_star_reputation,
            "github_commit_consistency": self.github_commit_consistency,
            "github_streak_dedication": self.github_streak_dedication,
            "github_community_standing": self.github_community_standing,
            "github_account_maturity": self.github_account_maturity,
            "wallet_transaction_volume": self.wallet_transaction_volume,
            "wallet_age_score": self.wallet_age_score,
            "wallet_balance_health": self.wallet_balance_health,
            "wallet_token_diversity": self.wallet_token_diversity,
            "wallet_counterparty_breadth": self.wallet_counterparty_breadth,
            "wallet_defi_engagement": self.wallet_defi_engagement,
            "income_level": self.income_level,
            "income_verification": self.income_verification,
            "income_consistency": self.income_consistency,
            "platform_count": self.platform_count,
            "platform_verification_ratio": self.platform_verification_ratio,
        }


def _clamp(value: float, cap: float) -> float:
    """Normalize value to 0-1 scale with a cap."""
    if cap <= 0:
        return 0.0
    return min(max(value / cap, 0.0), 1.0)


def _log_normalize(value: float, cap: float) -> float:
    """Log-scale normalization for values with long tails."""
    if value <= 0 or cap <= 0:
        return 0.0
    return min(math.log1p(value) / math.log1p(cap), 1.0)


FREQUENCY_SCORE = {
    "monthly": 1.0,
    "biweekly": 0.85,
    "weekly": 0.70,
    "daily": 0.55,
    "irregular": 0.30,
}


class FeatureExtractionPipeline:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def extract_features(self, user_id: uuid.UUID) -> IntegrationFeatures:
        """Main entry point: gather all data and produce normalized features."""
        features = IntegrationFeatures()

        github = await self._fetch_github(user_id)
        if github:
            features.github_repo_activity = _clamp(github.public_repos, GITHUB_REPO_CAP)
            features.github_star_reputation = _log_normalize(github.total_stars, GITHUB_STARS_CAP)
            features.github_commit_consistency = _clamp(github.total_commits_last_year, GITHUB_COMMITS_CAP)
            features.github_streak_dedication = _clamp(github.contribution_streak_days, GITHUB_STREAK_CAP)
            features.github_community_standing = _log_normalize(github.followers, GITHUB_FOLLOWERS_CAP)
            features.github_account_maturity = _clamp(github.account_age_days, GITHUB_ACCOUNT_AGE_CAP)

        wallet = await self._fetch_wallet(user_id)
        if wallet:
            features.wallet_transaction_volume = _log_normalize(wallet.total_transactions, WALLET_TX_CAP)
            features.wallet_age_score = _clamp(wallet.wallet_age_days, WALLET_AGE_CAP)
            features.wallet_balance_health = _log_normalize(wallet.eth_balance, WALLET_ETH_CAP)
            features.wallet_token_diversity = _log_normalize(
                wallet.total_token_value_usd, WALLET_TOKEN_VALUE_CAP
            )
            features.wallet_counterparty_breadth = _clamp(
                wallet.unique_counterparties, WALLET_COUNTERPARTY_CAP
            )
            features.wallet_defi_engagement = _clamp(wallet.defi_interactions, WALLET_DEFI_CAP)

        incomes = await self._fetch_income(user_id)
        if incomes:
            total_monthly = sum(float(i.monthly_amount) for i in incomes)
            features.income_level = _log_normalize(total_monthly, INCOME_MONTHLY_CAP)

            verified_count = sum(1 for i in incomes if i.is_verified)
            features.income_verification = verified_count / len(incomes)

            freq_scores = [FREQUENCY_SCORE.get(i.frequency.value, 0.3) for i in incomes]
            weights = [float(i.monthly_amount) for i in incomes]
            total_w = sum(weights)
            if total_w > 0:
                features.income_consistency = sum(
                    s * w for s, w in zip(freq_scores, weights)
                ) / total_w

        accounts = await self._fetch_accounts(user_id)
        features.platform_count = _clamp(len(accounts), 6)
        if accounts:
            verified = sum(1 for a in accounts if a.is_verified)
            features.platform_verification_ratio = verified / len(accounts)

        logger.info(
            "Features extracted for user=%s: github=%s wallet=%s income=%s platforms=%d",
            user_id,
            "yes" if github else "no",
            "yes" if wallet else "no",
            "yes" if incomes else "no",
            len(accounts),
        )

        return features

    async def _fetch_github(self, user_id: uuid.UUID) -> GitHubMetrics | None:
        return await self._s.scalar(
            select(GitHubMetrics)
            .where(GitHubMetrics.user_id == user_id)
            .order_by(GitHubMetrics.created_at.desc())
            .limit(1)
        )

    async def _fetch_wallet(self, user_id: uuid.UUID) -> WalletMetrics | None:
        return await self._s.scalar(
            select(WalletMetrics)
            .where(WalletMetrics.user_id == user_id)
            .order_by(WalletMetrics.created_at.desc())
            .limit(1)
        )

    async def _fetch_income(self, user_id: uuid.UUID) -> list[IncomeSource]:
        return list((await self._s.scalars(
            select(IncomeSource).where(IncomeSource.user_id == user_id)
        )).all())

    async def _fetch_accounts(self, user_id: uuid.UUID) -> list[ConnectedAccount]:
        return list((await self._s.scalars(
            select(ConnectedAccount).where(ConnectedAccount.user_id == user_id)
        )).all())
