import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.ml.inference import get_feature_importance, get_model_info
from app.schemas.trust_score import (
    FeatureBreakdownItem,
    MLComponentDetail,
    PenaltyDetail,
    TrustScoreBreakdownResponse,
    TrustScoreCalculationResponse,
    TrustScoreRequest,
)
from app.services.trust_score_engine import FEATURE_WEIGHTS
from app.services.trust_score_service import TrustScoreService

router = APIRouter(prefix="/trust-score", tags=["trust-score"])


@router.post("/calculate", response_model=TrustScoreCalculationResponse)
async def calculate_trust_score(
    body: TrustScoreRequest,
    session: AsyncSession = Depends(get_session),
):
    try:
        result = await TrustScoreService(session).calculate_for_user(body.user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )

    return TrustScoreCalculationResponse(
        score=result.score,
        risk_tier=result.risk_tier,
        loan_limit=result.loan_limit,
        features=result.features,
        penalties=PenaltyDetail(
            circular_tx=result.penalties.circular_tx,
            sybil=result.penalties.sybil,
            velocity=result.penalties.velocity,
            decay=result.penalties.decay,
            gaming=result.penalties.gaming,
            total=result.penalties.total,
        ),
        raw_weighted=result.raw_weighted,
        model_version=result.model_version,
        ml_component=MLComponentDetail(
            default_probability=result.ml_component.default_probability,
            confidence=result.ml_component.confidence,
            feature_contributions=result.ml_component.feature_contributions,
            model_type=result.ml_component.model_type,
        ),
        heuristic_raw=result.heuristic_raw,
        ml_raw=result.ml_raw,
    )


@router.get("/breakdown", response_model=TrustScoreBreakdownResponse)
async def get_trust_score_breakdown(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Full explainable breakdown of a user's trust score showing both
    the heuristic and ML contributions per feature.
    """
    try:
        result = await TrustScoreService(session).calculate_for_user(user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )

    ml_contributions = result.ml_component.feature_contributions
    breakdown = []
    for feature_name, value in result.features.items():
        weight = FEATURE_WEIGHTS.get(feature_name, 0.0)
        heuristic_contrib = round(value * weight, 4)
        ml_contrib = ml_contributions.get(feature_name, 0.0)

        if ml_contrib < -0.01:
            direction = "increases_risk"
        elif ml_contrib > 0.01:
            direction = "reduces_risk"
        else:
            direction = "neutral"

        breakdown.append(FeatureBreakdownItem(
            feature=feature_name,
            value=round(value, 4),
            heuristic_weight=weight,
            heuristic_contribution=heuristic_contrib,
            ml_contribution=round(ml_contrib, 4),
            direction=direction,
        ))

    breakdown.sort(key=lambda x: abs(x.ml_contribution), reverse=True)

    importance = get_feature_importance()

    return TrustScoreBreakdownResponse(
        score=result.score,
        risk_tier=result.risk_tier,
        loan_limit=result.loan_limit,
        model_version=result.model_version,
        heuristic_raw=result.heuristic_raw,
        ml_raw=result.ml_raw,
        hybrid_formula="final = 0.6 × heuristic_penalised + 0.4 × (1 - default_probability)",
        ml_default_probability=result.ml_component.default_probability,
        ml_confidence=result.ml_component.confidence,
        ml_model_type=result.ml_component.model_type,
        feature_breakdown=breakdown,
        penalties=PenaltyDetail(
            circular_tx=result.penalties.circular_tx,
            sybil=result.penalties.sybil,
            velocity=result.penalties.velocity,
            decay=result.penalties.decay,
            gaming=result.penalties.gaming,
            total=result.penalties.total,
        ),
        global_feature_importance=importance,
    )


@router.get("/model-info")
async def model_info():
    """Return metadata about the currently loaded ML model."""
    return get_model_info()
