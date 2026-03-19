"""
Data Sync Orchestrator
=======================
Coordinates syncing data from all external sources for a user:
  1. GitHub metrics
  2. Stripe / income data
  3. Wallet on-chain data
  4. Feature extraction
  5. Trust score recalculation

Used by the /sync-user-data endpoint and the background periodic job.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.enums import SyncStatus
from app.models.integrations import DataSyncLog
from app.services.feature_extraction import FeatureExtractionPipeline
from app.services.github_service import GitHubService
from app.services.stripe_service import StripeService
from app.services.trust_score_service import TrustScoreService
from app.services.wallet_data_service import WalletDataService

logger = get_logger(__name__)


class DataSyncResult:
    def __init__(self) -> None:
        self.synced_providers: list[str] = []
        self.failed_providers: list[dict] = []
        self.features: dict[str, float] = {}
        self.trust_score: float | None = None
        self.risk_tier: str | None = None
        self.loan_limit: float | None = None


class DataSyncService:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def sync_all(self, user_id: uuid.UUID) -> DataSyncResult:
        """
        Full data sync pipeline:
        1. Sync GitHub → GitHubMetrics
        2. Sync Stripe → IncomeSource
        3. Sync Wallet → WalletMetrics
        4. Extract unified features
        5. Recalculate trust score
        """
        result = DataSyncResult()

        await self._sync_github(user_id, result)
        await self._sync_stripe(user_id, result)
        await self._sync_wallet(user_id, result)

        pipeline = FeatureExtractionPipeline(self._s)
        features = await pipeline.extract_features(user_id)
        result.features = features.to_dict()

        try:
            svc = TrustScoreService(self._s)
            score_result = await svc.calculate_for_user(user_id)
            result.trust_score = score_result.score
            result.risk_tier = score_result.risk_tier
            result.loan_limit = score_result.loan_limit
        except Exception as e:
            logger.error("Trust score recalculation failed for user=%s: %s", user_id, e)
            result.failed_providers.append({
                "provider": "trust_score",
                "error": str(e),
            })

        logger.info(
            "Data sync complete for user=%s: synced=%s failed=%d score=%s",
            user_id,
            result.synced_providers,
            len(result.failed_providers),
            result.trust_score,
        )
        return result

    async def _sync_github(self, user_id: uuid.UUID, result: DataSyncResult) -> None:
        log = self._create_log(user_id, "github")
        try:
            svc = GitHubService(self._s)
            metrics = await svc.sync_metrics(user_id)
            log.status = SyncStatus.COMPLETED
            log.completed_at = datetime.now(timezone.utc)
            log.records_synced = 1
            result.synced_providers.append("github")
        except Exception as e:
            log.status = SyncStatus.FAILED
            log.error_message = str(e)[:500]
            log.completed_at = datetime.now(timezone.utc)
            result.failed_providers.append({"provider": "github", "error": str(e)[:200]})
            logger.warning("GitHub sync failed for user=%s: %s", user_id, e)

    async def _sync_stripe(self, user_id: uuid.UUID, result: DataSyncResult) -> None:
        log = self._create_log(user_id, "stripe")
        try:
            svc = StripeService(self._s)
            sources = await svc.sync_income(user_id)
            log.status = SyncStatus.COMPLETED
            log.completed_at = datetime.now(timezone.utc)
            log.records_synced = len(sources)
            result.synced_providers.append("stripe")
        except Exception as e:
            log.status = SyncStatus.FAILED
            log.error_message = str(e)[:500]
            log.completed_at = datetime.now(timezone.utc)
            result.failed_providers.append({"provider": "stripe", "error": str(e)[:200]})
            logger.warning("Stripe sync failed for user=%s: %s", user_id, e)

    async def _sync_wallet(self, user_id: uuid.UUID, result: DataSyncResult) -> None:
        log = self._create_log(user_id, "wallet")
        try:
            svc = WalletDataService(self._s)
            metrics = await svc.sync_wallet(user_id)
            log.status = SyncStatus.COMPLETED
            log.completed_at = datetime.now(timezone.utc)
            log.records_synced = 1 if metrics else 0
            result.synced_providers.append("wallet")
        except Exception as e:
            log.status = SyncStatus.FAILED
            log.error_message = str(e)[:500]
            log.completed_at = datetime.now(timezone.utc)
            result.failed_providers.append({"provider": "wallet", "error": str(e)[:200]})
            logger.warning("Wallet sync failed for user=%s: %s", user_id, e)

    def _create_log(self, user_id: uuid.UUID, provider: str) -> DataSyncLog:
        log = DataSyncLog(
            user_id=user_id,
            provider=provider,
            status=SyncStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
        )
        self._s.add(log)
        return log
