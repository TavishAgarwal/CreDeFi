"""
Data Sync API
==============
POST /sync-user-data       — Full data sync + trust score recalculation
POST /connect/github       — GitHub OAuth account connection
GET  /features/{user_id}   — Retrieve extracted features for a user
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.data_sync import (
    GitHubConnectRequest,
    GitHubConnectResponse,
    SyncProviderResult,
    SyncRequest,
    SyncResponse,
)
from app.services.data_sync_service import DataSyncService
from app.services.feature_extraction import FeatureExtractionPipeline
from app.services.github_service import GitHubService

router = APIRouter(prefix="/data", tags=["data-sync"])


@router.post("/sync-user-data", response_model=SyncResponse)
async def sync_user_data(
    body: SyncRequest | None = None,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Trigger a full data sync for the authenticated user.
    Fetches data from all connected platforms (GitHub, Stripe, Wallet),
    extracts features, and recalculates the trust score.
    """
    svc = DataSyncService(session)
    result = await svc.sync_all(user.id)

    return SyncResponse(
        synced_providers=result.synced_providers,
        failed_providers=[
            SyncProviderResult(**fp) for fp in result.failed_providers
        ],
        features=result.features,
        trust_score=result.trust_score,
        risk_tier=result.risk_tier,
        loan_limit=result.loan_limit,
    )


@router.post("/connect/github", response_model=GitHubConnectResponse)
async def connect_github(
    body: GitHubConnectRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Exchange a GitHub OAuth authorization code for a token,
    verify the user, and store the connected account.
    """
    svc = GitHubService(session)
    try:
        account = await svc.connect_account(user.id, body.code)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GitHub OAuth failed: {e}",
        )

    return GitHubConnectResponse(
        username=account.account_identifier,
        is_verified=account.is_verified,
    )


@router.get("/features/{user_id}")
async def get_features(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Retrieve the extracted feature vector for a user (all 0→1 normalized)."""
    pipeline = FeatureExtractionPipeline(session)
    features = await pipeline.extract_features(user_id)
    return features.to_dict()
