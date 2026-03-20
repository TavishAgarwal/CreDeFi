from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_session
from app.models.enums import RiskTier
from app.models.user import User
from app.schemas.loan import (
    FundLoanResponse,
    LoanContractResponse,
    LoanEligibilityResponse,
    LoanFundRequest,
    LoanRepayRequest,
    LoanRequestCreate,
    LoanRequestDetail,
    LoanRequestResponse,
    RepayLoanResponse,
    RepaymentResponse,
)
from app.services.loan_service import (
    LoanService,
    LoanServiceError,
    get_collateral_ratio,
    get_interest_rate_bps,
    get_max_loan,
)

router = APIRouter(prefix="/loans", tags=["loans"])


# ─── POST /loans/request ──────────────────────────────────────────

@router.post(
    "/request",
    response_model=LoanRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_loan_request(
    body: LoanRequestCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        req = await LoanService(session).create_request(
            borrower_id=user.id,
            amount=body.amount_requested,
            term_days=body.term_days,
            currency=body.currency,
            purpose=body.purpose,
        )
        return req
    except LoanServiceError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


# ─── GET /loans/marketplace ───────────────────────────────────────

@router.get("/marketplace", response_model=list[LoanRequestResponse])
async def marketplace(
    currency: str | None = Query(default=None),
    max_risk: RiskTier | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    return await LoanService(session).marketplace(
        limit=limit, offset=offset, currency=currency, max_risk=max_risk,
    )


# ─── POST /loans/fund ─────────────────────────────────────────────

@router.post("/fund", response_model=FundLoanResponse)
async def fund_loan(
    body: LoanFundRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        contract = await LoanService(session).fund_loan(
            loan_request_id=body.loan_request_id,
            lender_id=user.id,
            collateral_currency=body.collateral_currency,
        )
    except LoanServiceError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    disburse_tx = next(
        (t for t in contract.transactions if t.tx_type.value == "disbursement"), None
    )

    return FundLoanResponse(
        contract=LoanContractResponse.model_validate(contract),
        collateral_locked=contract.collateral_amount is not None and contract.collateral_amount > 0,
        disbursement_tx_hash=disburse_tx.tx_hash if disburse_tx else "",
    )


# ─── POST /loans/repay ────────────────────────────────────────────

@router.post("/repay", response_model=RepayLoanResponse)
async def repay_loan(
    body: LoanRepayRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    svc = LoanService(session)
    try:
        repayment = await svc.repay(
            contract_id=body.contract_id,
            payer_id=user.id,
            amount=body.amount,
        )
    except LoanServiceError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    remaining = await svc.remaining_installments(body.contract_id)
    return RepayLoanResponse(
        repayment=RepaymentResponse.model_validate(repayment),
        loan_fully_repaid=(remaining == 0),
        remaining_installments=remaining,
    )


# ─── GET /loans/history ───────────────────────────────────────────

@router.get("/history", response_model=list[LoanRequestDetail])
async def loan_history(
    role: str = Query(default="borrower", pattern="^(borrower|lender)$"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    rows = await LoanService(session).history(
        user_id=user.id, role=role, limit=limit, offset=offset,
    )
    return [LoanRequestDetail.model_validate(r) for r in rows]


# ─── GET /loans/eligibility ─────────────────────────────────────────

@router.get("/eligibility", response_model=LoanEligibilityResponse)
async def loan_eligibility(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Return the caller’s dynamic collateral ratio, max borrow amount,
    and interest rate based on their latest trust score."""
    svc = LoanService(session)
    trust = await svc.latest_trust_score(user.id)

    if trust is None:
        return LoanEligibilityResponse(
            trust_score=0,
            collateral_ratio=None,
            max_borrow_amount=0,
            interest_rate=0,
            eligible=False,
            message="No trust score found. Please compute your trust score first.",
        )

    score = trust.score
    coll = get_collateral_ratio(score)
    rate_bps = get_interest_rate_bps(score)
    max_borrow = get_max_loan(score)
    eligible = coll is not None

    return LoanEligibilityResponse(
        trust_score=score,
        collateral_ratio=coll,
        max_borrow_amount=max_borrow,
        interest_rate=(rate_bps / 10_000) if rate_bps else 0,
        eligible=eligible,
        message=(
            f"Your trust score of {score:.0f} unlocks a {coll * 100:.0f}% collateral requirement."
            if eligible
            else "Trust score below 450 — not eligible for loans."
        ),
    )
