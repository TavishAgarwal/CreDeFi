from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.sybil import (
    ClusterDetail,
    DetectorDetail,
    SybilAnalyzeResponse,
)
from app.services.sybil_service import SybilService

router = APIRouter(prefix="/sybil", tags=["sybil"])


@router.post("/analyze", response_model=SybilAnalyzeResponse)
async def analyze_sybil(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """C3/C4: Now requires authentication. Analyzes the caller's own account."""
    try:
        result = await SybilService(session).analyze_user(user.id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )

    return SybilAnalyzeResponse(
        risk_score=result.risk_score,
        verdict=result.verdict,
        detectors=[
            DetectorDetail(name=d.name, score=d.score, detail=d.detail)
            for d in result.detectors
        ],
        clusters=[
            ClusterDetail(
                label=c.label,
                wallet_addresses=c.wallet_addresses,
                shared_funding_source=c.shared_funding_source,
                similarity_score=c.similarity_score,
            )
            for c in result.clusters
        ],
        features=result.features,
        model_version=result.model_version,
    )
