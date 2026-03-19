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


class MLComponentDetail(BaseModel):
    default_probability: float
    confidence: float
    feature_contributions: dict[str, float]
    model_type: str


class TrustScoreCalculationResponse(BaseModel):
    score: float
    risk_tier: str
    loan_limit: float
    features: dict[str, float]
    penalties: PenaltyDetail
    raw_weighted: float
    model_version: str
    ml_component: MLComponentDetail
    heuristic_raw: float
    ml_raw: float


class FeatureBreakdownItem(BaseModel):
    feature: str
    value: float
    heuristic_weight: float
    heuristic_contribution: float
    ml_contribution: float
    direction: str


class TrustScoreBreakdownResponse(BaseModel):
    score: float
    risk_tier: str
    loan_limit: float
    model_version: str
    heuristic_raw: float
    ml_raw: float
    hybrid_formula: str
    ml_default_probability: float
    ml_confidence: float
    ml_model_type: str | None
    feature_breakdown: list[FeatureBreakdownItem]
    penalties: PenaltyDetail
    global_feature_importance: dict[str, float]


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
    ml_default_probability: float
    ml_confidence: float
    ml_model_type: str | None
    heuristic_raw: float
    ml_raw: float
    created_at: datetime

    model_config = {"from_attributes": True}
