from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.trust_score import (
    PenaltyDetail,
    TrustScoreCalculationResponse,
    TrustScoreRequest,
)
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
    )
