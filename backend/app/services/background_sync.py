"""
Background Periodic Sync Job
==============================
Runs on a configurable interval to refresh data for all active users
who have connected accounts. Designed to be kicked off from the
FastAPI lifespan context.
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import async_session_factory
from app.models.core import ConnectedAccount
from app.models.user import User
from app.services.data_sync_service import DataSyncService

logger = get_logger(__name__)

_task: asyncio.Task | None = None


async def _sync_loop() -> None:
    """Infinite loop that syncs all users with connected accounts."""
    while True:
        try:
            await asyncio.sleep(settings.SYNC_INTERVAL_SECONDS)
            logger.info("Background sync: starting periodic refresh")

            async with async_session_factory() as session:
                user_ids = (await session.execute(
                    select(ConnectedAccount.user_id).distinct()
                )).scalars().all()

                for uid in user_ids:
                    try:
                        svc = DataSyncService(session)
                        await svc.sync_all(uid)
                        await session.commit()
                    except Exception as e:
                        await session.rollback()
                        logger.error("Background sync failed for user=%s: %s", uid, e)

            logger.info("Background sync: completed for %d users", len(user_ids))

        except asyncio.CancelledError:
            logger.info("Background sync: cancelled")
            return
        except Exception as e:
            logger.error("Background sync loop error: %s", e)
            await asyncio.sleep(60)


def start_background_sync() -> None:
    """Start the background sync task (call during app startup)."""
    global _task
    if _task is not None:
        return
    _task = asyncio.create_task(_sync_loop())
    logger.info(
        "Background sync started (interval=%ds)", settings.SYNC_INTERVAL_SECONDS
    )


def stop_background_sync() -> None:
    """Cancel the background sync task (call during app shutdown)."""
    global _task
    if _task is not None:
        _task.cancel()
        _task = None
        logger.info("Background sync stopped")
