import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import RiskTier


class TrustScoreRequest(BaseModel):
    user_id: uuid.UUID


class PenaltyDetail(BaseModel):
    circular_tx: float
    sybil: float
    velocity: float
    decay: float
    gaming: float
    total: float


class TrustScoreCalculationResponse(BaseModel):
    score: float
    risk_tier: str
    loan_limit: float
    features: dict[str, float]
    penalties: PenaltyDetail
    raw_weighted: float
    model_version: str


class TrustScoreHistoryItem(BaseModel):
    id: uuid.UUID
    score: float
    risk_tier: RiskTier
    repayment_component: float
    identity_component: float
    social_component: float
    income_component: float
    model_version: str
    explanation: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
