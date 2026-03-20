"""
Risk Mitigation API
====================
Endpoints for default processing, identity, social guarantees,
and repayment behavior tracking.
C3/C4: All endpoints now require authentication. User-scoped data
is accessed via the authenticated user's own ID to prevent IDOR.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_log import log_admin_action
from app.core.deps import get_current_user, require_admin
from app.core.logging import get_logger
from app.db.session import get_session
from app.models.user import User
from app.schemas.risk import (
    DefaultEventResponse,
    IdentityProfileResponse,
    LinkIdentityRequest,
    ProcessDefaultRequest,
    RepaymentBehaviorResponse,
    ReputationPenaltyResponse,
    SocialGuaranteeResponse,
    VouchRequest,
)
from app.services.risk_mitigation import (
    DefaultProcessor,
    IdentityService,
    RepaymentTracker,
    ReputationSlashingService,
    SocialGuaranteeService,
)

router = APIRouter(prefix="/risk", tags=["risk-mitigation"])
logger = get_logger(__name__)


# ── Default Processing ────────────────────────────────────────────

@router.post("/process-default", response_model=DefaultEventResponse)
async def process_default(
    body: ProcessDefaultRequest,
    user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    """
    Process a loan default. H5: Requires admin role.
    This triggers:
    - DefaultEvent creation
    - Borrower reputation slashing
    - Guarantor cascading slashing
    - Repayment behavior update
    - Loan status update to DEFAULTED
    """
    processor = DefaultProcessor(session)
    try:
        event = await processor.process_default(
            contract_id=body.contract_id,
            on_chain_tx_hash=body.on_chain_tx_hash,
            on_chain_block=body.on_chain_block,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    log_admin_action("process_default", admin_id=str(user.id), target=str(body.contract_id))
    return DefaultEventResponse.model_validate(event)


@router.get("/defaults/me", response_model=list[DefaultEventResponse])
async def get_my_defaults(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """C3/C4: Get default events for the authenticated user."""
    from sqlalchemy import select
    from app.models.risk import DefaultEvent

    events = list((await session.scalars(
        select(DefaultEvent)
        .where(DefaultEvent.borrower_id == user.id)
        .order_by(DefaultEvent.created_at.desc())
    )).all())
    return [DefaultEventResponse.model_validate(e) for e in events]


# ── Reputation Penalties ──────────────────────────────────────────

@router.get("/penalties/me", response_model=list[ReputationPenaltyResponse])
async def get_my_penalty_history(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """C3/C4: Get reputation penalty history for the authenticated user."""
    svc = ReputationSlashingService(session)
    penalties = await svc.get_penalty_history(user.id)
    return [ReputationPenaltyResponse.model_validate(p) for p in penalties]


@router.get("/penalties/me/active", response_model=list[ReputationPenaltyResponse])
async def get_my_active_penalties(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """C3/C4: Get currently active (non-expired) penalties for the authenticated user."""
    svc = ReputationSlashingService(session)
    penalties = await svc.get_active_penalties(user.id)
    return [ReputationPenaltyResponse.model_validate(p) for p in penalties]


# ── Identity Linking ──────────────────────────────────────────────

@router.post("/identity/link")
async def link_identity(
    body: LinkIdentityRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Link an identity source (email, GitHub, wallet, etc.) to the authenticated user."""
    svc = IdentityService(session)
    link = await svc.link_identity(
        user_id=user.id,
        provider=body.provider,
        identifier=body.identifier,
        is_verified=body.is_verified,
        verification_method=body.verification_method,
    )
    return {
        "id": str(link.id),
        "provider": link.provider,
        "identifier": link.identifier,
        "is_verified": link.is_verified,
        "confidence_weight": link.confidence_weight,
    }


@router.get("/identity/me", response_model=IdentityProfileResponse)
async def get_my_identity_profile(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """C3/C4: Get identity profile for the authenticated user."""
    svc = IdentityService(session)
    return await svc.get_identity_profile(user.id)


@router.get("/identity/me/confidence")
async def get_my_identity_confidence(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """C3/C4: Get identity confidence score for the authenticated user."""
    svc = IdentityService(session)
    score = await svc.compute_identity_confidence(user.id)
    return {"user_id": str(user.id), "confidence": round(score, 4)}


# ── Social Guarantees ─────────────────────────────────────────────

@router.post("/guarantee/vouch", response_model=SocialGuaranteeResponse)
async def vouch_for_borrower(
    body: VouchRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Vouch for a borrower. Guarantor's reputation is at stake."""
    svc = SocialGuaranteeService(session)
    try:
        guarantee = await svc.vouch(
            guarantor_id=user.id,
            borrower_id=body.borrower_id,
            contract_id=body.contract_id,
            stake_amount=body.stake_amount,
            message=body.message,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return SocialGuaranteeResponse.model_validate(guarantee)


@router.get("/guarantee/me/given", response_model=list[SocialGuaranteeResponse])
async def get_my_guarantees_given(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """C3/C4: List all guarantees made by the authenticated user."""
    svc = SocialGuaranteeService(session)
    guarantees = await svc.get_guarantees_by_guarantor(user.id)
    return [SocialGuaranteeResponse.model_validate(g) for g in guarantees]


@router.get("/guarantee/me/received", response_model=list[SocialGuaranteeResponse])
async def get_my_guarantees_received(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """C3/C4: List all guarantees for the authenticated user as borrower."""
    svc = SocialGuaranteeService(session)
    guarantees = await svc.get_guarantees_for_borrower(user.id)
    return [SocialGuaranteeResponse.model_validate(g) for g in guarantees]


# ── Repayment Behavior ───────────────────────────────────────────

@router.get("/behavior/me", response_model=RepaymentBehaviorResponse)
async def get_my_repayment_behavior(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """C3/C4: Get aggregate repayment behavior for the authenticated user."""
    tracker = RepaymentTracker(session)
    behavior = await tracker.refresh_behavior(user.id)
    return RepaymentBehaviorResponse.model_validate(behavior)
