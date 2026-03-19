import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import (
    LoanStatus,
    RepaymentStatus,
    RiskTier,
    TransactionStatus,
    TransactionType,
)


# ═══════════════════════════════════════════════════════════════════
# Requests
# ═══════════════════════════════════════════════════════════════════

class LoanRequestCreate(BaseModel):
    currency: str = Field(default="USD", max_length=10)
    amount_requested: float = Field(gt=0)
    term_days: int = Field(gt=0, le=365)
    purpose: str | None = None


class LoanFundRequest(BaseModel):
    loan_request_id: uuid.UUID
    collateral_currency: str = Field(default="ETH", max_length=10)


class LoanRepayRequest(BaseModel):
    contract_id: uuid.UUID
    amount: float = Field(gt=0)


class MarketplaceQuery(BaseModel):
    currency: str | None = None
    max_risk: RiskTier | None = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class HistoryQuery(BaseModel):
    role: str = Field(default="borrower", pattern="^(borrower|lender)$")
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


# ═══════════════════════════════════════════════════════════════════
# Responses
# ═══════════════════════════════════════════════════════════════════

class LoanRequestResponse(BaseModel):
    id: uuid.UUID
    borrower_id: uuid.UUID
    currency: str
    amount_requested: float
    term_days: int
    purpose: str | None
    status: LoanStatus
    risk_tier_at_request: RiskTier | None
    trust_score_at_request: float | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RepaymentResponse(BaseModel):
    id: uuid.UUID
    contract_id: uuid.UUID
    installment_number: int
    currency: str
    amount_due: float
    amount_paid: float
    due_date: datetime
    paid_at: datetime | None
    status: RepaymentStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionResponse(BaseModel):
    id: uuid.UUID
    contract_id: uuid.UUID
    tx_type: TransactionType
    status: TransactionStatus
    currency: str
    amount: float
    tx_hash: str | None
    chain: str | None
    from_address: str | None
    to_address: str | None
    block_number: int | None
    confirmed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class LoanContractResponse(BaseModel):
    id: uuid.UUID
    loan_request_id: uuid.UUID
    lender_id: uuid.UUID | None
    currency: str
    principal: float
    interest_rate_bps: int
    term_days: int
    status: LoanStatus
    collateral_currency: str | None
    collateral_amount: float | None
    collateral_tx_hash: str | None
    disbursed_at: datetime | None
    maturity_date: datetime | None
    closed_at: datetime | None
    on_chain_address: str | None
    created_at: datetime
    repayments: list[RepaymentResponse] = []

    model_config = {"from_attributes": True}


class LoanRequestDetail(LoanRequestResponse):
    """Loan request with its contract (if funded)."""
    contract: LoanContractResponse | None = None


class FundLoanResponse(BaseModel):
    contract: LoanContractResponse
    collateral_locked: bool
    disbursement_tx_hash: str


class RepayLoanResponse(BaseModel):
    repayment: RepaymentResponse
    loan_fully_repaid: bool
    remaining_installments: int


class LoanEligibilityResponse(BaseModel):
    trust_score: float
    collateral_ratio: float | None = None   # e.g. 0.80 for 80%
    max_borrow_amount: float
    interest_rate: float                     # annual, e.g. 0.12 for 12%
    eligible: bool
    message: str | None = None

