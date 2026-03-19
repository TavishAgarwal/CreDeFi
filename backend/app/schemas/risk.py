import uuid
from datetime import datetime

from pydantic import BaseModel


class ProcessDefaultRequest(BaseModel):
    contract_id: uuid.UUID
    on_chain_tx_hash: str | None = None
    on_chain_block: int | None = None


class DefaultEventResponse(BaseModel):
    id: uuid.UUID
    borrower_id: uuid.UUID
    contract_id: uuid.UUID
    principal_owed: float
    interest_owed: float
    missed_installments: int
    days_overdue: int
    severity: str
    resolved: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ReputationPenaltyResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    reason: str
    score_before: float
    score_after: float
    penalty_points: float
    source_type: str
    is_active: bool
    expires_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class LinkIdentityRequest(BaseModel):
    provider: str
    identifier: str
    is_verified: bool = False
    verification_method: str | None = None


class IdentityProfileResponse(BaseModel):
    user_id: str
    confidence_score: float
    total_links: int
    verified_count: int
    links: list[dict]


class VouchRequest(BaseModel):
    borrower_id: uuid.UUID
    contract_id: uuid.UUID | None = None
    stake_amount: float = 0.0
    message: str | None = None


class SocialGuaranteeResponse(BaseModel):
    id: uuid.UUID
    guarantor_id: uuid.UUID
    borrower_id: uuid.UUID
    contract_id: uuid.UUID | None
    stake_amount: float
    is_active: bool
    slashed: bool
    vouch_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RepaymentBehaviorResponse(BaseModel):
    user_id: uuid.UUID
    total_loans: int
    loans_repaid: int
    loans_defaulted: int
    loans_active: int
    on_time_payments: int
    late_payments: int
    missed_payments: int
    total_borrowed: float
    total_repaid: float
    avg_days_to_repay: float
    current_streak_on_time: int
    default_count: int
    reliability_score: float

    model_config = {"from_attributes": True}
