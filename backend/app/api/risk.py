"""
Risk Mitigation API
====================
Endpoints for default processing, identity, social guarantees,
and repayment behavior tracking.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
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


# ── Default Processing ────────────────────────────────────────────

@router.post("/process-default", response_model=DefaultEventResponse)
async def process_default(
    body: ProcessDefaultRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Process a loan default. This triggers:
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

    return DefaultEventResponse.model_validate(event)


@router.get("/defaults/{user_id}", response_model=list[DefaultEventResponse])
async def get_user_defaults(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get all default events for a user."""
    from sqlalchemy import select
    from app.models.risk import DefaultEvent

    events = list((await session.scalars(
        select(DefaultEvent)
        .where(DefaultEvent.borrower_id == user_id)
        .order_by(DefaultEvent.created_at.desc())
    )).all())
    return [DefaultEventResponse.model_validate(e) for e in events]


# ── Reputation Penalties ──────────────────────────────────────────

@router.get("/penalties/{user_id}", response_model=list[ReputationPenaltyResponse])
async def get_penalty_history(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get full reputation penalty history for a user."""
    svc = ReputationSlashingService(session)
    penalties = await svc.get_penalty_history(user_id)
    return [ReputationPenaltyResponse.model_validate(p) for p in penalties]


@router.get("/penalties/{user_id}/active", response_model=list[ReputationPenaltyResponse])
async def get_active_penalties(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get currently active (non-expired) penalties."""
    svc = ReputationSlashingService(session)
    penalties = await svc.get_active_penalties(user_id)
    return [ReputationPenaltyResponse.model_validate(p) for p in penalties]


# ── Identity Linking ──────────────────────────────────────────────

@router.post("/identity/link")
async def link_identity(
    body: LinkIdentityRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Link an identity source (email, GitHub, wallet, etc.) to the user."""
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


@router.get("/identity/{user_id}", response_model=IdentityProfileResponse)
async def get_identity_profile(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get full identity profile with confidence score."""
    svc = IdentityService(session)
    return await svc.get_identity_profile(user_id)


@router.get("/identity/{user_id}/confidence")
async def get_identity_confidence(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get just the identity confidence score (0-1)."""
    svc = IdentityService(session)
    score = await svc.compute_identity_confidence(user_id)
    return {"user_id": str(user_id), "confidence": round(score, 4)}


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


@router.get("/guarantee/borrower/{borrower_id}", response_model=list[SocialGuaranteeResponse])
async def get_guarantees_for_borrower(
    borrower_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """List all active guarantees for a borrower."""
    svc = SocialGuaranteeService(session)
    guarantees = await svc.get_guarantees_for_borrower(borrower_id)
    return [SocialGuaranteeResponse.model_validate(g) for g in guarantees]


@router.get("/guarantee/guarantor/{guarantor_id}", response_model=list[SocialGuaranteeResponse])
async def get_guarantees_by_guarantor(
    guarantor_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """List all guarantees made by a user."""
    svc = SocialGuaranteeService(session)
    guarantees = await svc.get_guarantees_by_guarantor(guarantor_id)
    return [SocialGuaranteeResponse.model_validate(g) for g in guarantees]


# ── Repayment Behavior ───────────────────────────────────────────

@router.get("/behavior/{user_id}", response_model=RepaymentBehaviorResponse)
async def get_repayment_behavior(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get aggregate repayment behavior statistics for a user."""
    tracker = RepaymentTracker(session)
    behavior = await tracker.refresh_behavior(user_id)
    return RepaymentBehaviorResponse.model_validate(behavior)
