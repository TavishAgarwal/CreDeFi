"""
Loan Service
=============
Full loan lifecycle: request → fund → repay → close.

Business rules:
  • Trust-score validation before a loan request is accepted.
  • Interest rate derived from the borrower's risk tier.
  • Collateral ratio computed from risk tier (higher risk → more collateral).
  • Repayment schedule auto-generated at funding time.
  • Blockchain calls abstracted through BlockchainClient.
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.core import TrustScore
from app.models.enums import (
    LoanStatus,
    RepaymentStatus,
    RiskTier,
    TransactionStatus,
    TransactionType,
)
from app.models.loan import LoanContract, LoanRequest, Repayment, Transaction
from app.models.user import User
from app.services.blockchain import ChainTxReceipt, blockchain_client

logger = get_logger(__name__)

MOCK_ESCROW = "0xCREDEFI_ESCROW_CONTRACT"

# ─── Dynamic trust-score policy functions ─────────────────────────
#
# These mirror the on-chain getCollateralRatioBps() exactly so the
# backend and smart contract agree on eligibility.

MIN_TRUST_SCORE = 450          # absolute floor to request any loan
REPAYMENT_FREQUENCY_DAYS = 30  # monthly installments


def get_collateral_ratio(trust_score: float) -> float | None:
    """Return collateral ratio (e.g. 1.20 for 120%) based on trust score.
    Returns None if the user is not eligible (score < 450)."""
    if trust_score < 450:
        return None
    if trust_score < 600:
        return 1.20
    if trust_score < 750:
        return 0.80
    if trust_score < 850:
        return 0.60
    if trust_score < 950:
        return 0.40
    return 0.20   # 950 – 1000


def get_interest_rate_bps(trust_score: float) -> int | None:
    """Annual interest rate in basis points based on trust score.
    Returns None if the user is not eligible."""
    if trust_score < 450:
        return None
    if trust_score < 600:
        return 2400   # 24 %  (high risk)
    if trust_score < 750:
        return 1200   # 12 %
    if trust_score < 850:
        return 800    #  8 %
    if trust_score < 950:
        return 500    #  5 %
    return 300        #  3 %  (best tier)


def get_max_loan(trust_score: float) -> float:
    """Maximum borrow amount based on trust score."""
    if trust_score < 450:
        return 0.0
    if trust_score < 600:
        return 1_500.0
    if trust_score < 750:
        return 5_000.0
    if trust_score < 850:
        return 10_000.0
    if trust_score < 950:
        return 25_000.0
    return 50_000.0   # 950 – 1000


class LoanServiceError(Exception):
    """Raised for any domain-level rejection."""


class LoanService:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    # ═══════════════════════════════════════════════════════════════
    # 1. Create loan request
    # ═══════════════════════════════════════════════════════════════

    async def create_request(
        self,
        borrower_id: uuid.UUID,
        amount: float,
        term_days: int,
        currency: str = "USD",
        purpose: str | None = None,
    ) -> LoanRequest:
        borrower = await self._get_user(borrower_id)
        trust = await self._latest_trust_score(borrower_id)

        if trust is None or trust.score < MIN_TRUST_SCORE:
            raise LoanServiceError(
                f"Trust score too low ({trust.score if trust else 'none'}). "
                f"Minimum required: {MIN_TRUST_SCORE}."
            )

        tier = trust.risk_tier
        score = trust.score

        coll_ratio = get_collateral_ratio(score)
        if coll_ratio is None:
            raise LoanServiceError("Trust score not eligible for a loan.")

        cap = get_max_loan(score)
        if amount > cap:
            raise LoanServiceError(
                f"Amount ${amount:,.2f} exceeds the ${cap:,.2f} limit for your trust score ({score})."
            )

        active_count = await self._active_loan_count(borrower_id)
        if active_count >= 3:
            raise LoanServiceError("Maximum 3 concurrent active loans allowed.")

        req = LoanRequest(
            borrower_id=borrower_id,
            currency=currency,
            amount_requested=amount,
            term_days=term_days,
            purpose=purpose,
            status=LoanStatus.PENDING,
            risk_tier_at_request=tier,
            trust_score_at_request=trust.score,
        )
        self._s.add(req)
        await self._s.flush()
        logger.info("Loan request created: %s  amount=%s score=%s", req.id, amount, score)
        return req

    # ═══════════════════════════════════════════════════════════════
    # 2. Marketplace (all pending requests)
    # ═══════════════════════════════════════════════════════════════

    async def marketplace(
        self,
        limit: int = 50,
        offset: int = 0,
        currency: str | None = None,
        max_risk: RiskTier | None = None,
    ) -> list[LoanRequest]:
        q = (
            select(LoanRequest)
            .where(LoanRequest.status == LoanStatus.PENDING)
            .order_by(LoanRequest.created_at.desc())
        )
        if currency:
            q = q.where(LoanRequest.currency == currency)
        if max_risk:
            allowed = _tiers_up_to(max_risk)
            q = q.where(LoanRequest.risk_tier_at_request.in_(allowed))

        q = q.offset(offset).limit(limit)
        return list((await self._s.scalars(q)).all())

    # ═══════════════════════════════════════════════════════════════
    # 3. Fund a loan
    # ═══════════════════════════════════════════════════════════════

    async def fund_loan(
        self,
        loan_request_id: uuid.UUID,
        lender_id: uuid.UUID,
        collateral_currency: str = "ETH",
    ) -> LoanContract:
        req = await self._get_request(loan_request_id)

        if req.status != LoanStatus.PENDING:
            raise LoanServiceError(f"Loan request is {req.status.value}, not pending.")
        if req.borrower_id == lender_id:
            raise LoanServiceError("Cannot fund your own loan request.")

        lender = await self._get_user(lender_id)

        score = req.trust_score_at_request or 0
        rate_bps = get_interest_rate_bps(score) or 2400  # fallback to high rate
        coll_ratio = get_collateral_ratio(score) or 1.20  # fallback to high collateral
        coll_amount = round(float(req.amount_requested) * coll_ratio, 8) if coll_ratio > 0 else None

        # Lock collateral on-chain (mock)
        coll_receipt: ChainTxReceipt | None = None
        if coll_amount and coll_amount > 0:
            borrower = await self._get_user(req.borrower_id)
            coll_receipt = await blockchain_client.lock_collateral(
                borrower_address=borrower.wallet_address or "0xBORROWER",
                escrow_address=MOCK_ESCROW,
                amount=coll_amount,
                currency=collateral_currency,
            )

        # Disburse principal (mock)
        disburse_receipt = await blockchain_client.disburse(
            escrow_address=MOCK_ESCROW,
            borrower_address=(await self._get_user(req.borrower_id)).wallet_address or "0xBORROWER",
            amount=float(req.amount_requested),
            currency=req.currency,
        )

        now = datetime.now(timezone.utc)
        maturity = now + timedelta(days=req.term_days)

        contract = LoanContract(
            loan_request_id=req.id,
            lender_id=lender_id,
            currency=req.currency,
            principal=float(req.amount_requested),
            interest_rate_bps=rate_bps,
            term_days=req.term_days,
            status=LoanStatus.ACTIVE,
            collateral_currency=collateral_currency if coll_amount else None,
            collateral_amount=coll_amount,
            collateral_tx_hash=coll_receipt.tx_hash if coll_receipt else None,
            disbursed_at=now,
            maturity_date=maturity,
            on_chain_address=MOCK_ESCROW,
        )
        self._s.add(contract)

        req.status = LoanStatus.ACTIVE
        await self._s.flush()

        # Disbursement transaction record
        self._s.add(self._tx_from_receipt(contract.id, disburse_receipt, TransactionType.DISBURSEMENT))
        if coll_receipt:
            self._s.add(self._tx_from_receipt(contract.id, coll_receipt, TransactionType.COLLATERAL_LOCK))

        # Generate repayment schedule
        schedule = self._build_repayment_schedule(contract)
        for rep in schedule:
            self._s.add(rep)

        await self._s.flush()
        logger.info(
            "Loan funded: contract=%s lender=%s principal=%s rate=%dbps collateral=%s",
            contract.id, lender_id, contract.principal, rate_bps, coll_amount,
        )
        return contract

    # ═══════════════════════════════════════════════════════════════
    # 4. Repay a loan installment
    # ═══════════════════════════════════════════════════════════════

    async def repay(
        self,
        contract_id: uuid.UUID,
        payer_id: uuid.UUID,
        amount: float,
    ) -> Repayment:
        contract = await self._get_contract(contract_id)

        if contract.status != LoanStatus.ACTIVE:
            raise LoanServiceError(f"Contract is {contract.status.value}, not active.")
        if contract.loan_request.borrower_id != payer_id:
            raise LoanServiceError("Only the borrower can repay this loan.")

        next_due = await self._next_due_repayment(contract_id)
        if next_due is None:
            raise LoanServiceError("No outstanding installments found.")

        if amount < float(next_due.amount_due):
            raise LoanServiceError(
                f"Minimum payment is {next_due.amount_due}. Got {amount}."
            )

        borrower = await self._get_user(payer_id)
        receipt = await blockchain_client.record_repayment(
            borrower_address=borrower.wallet_address or "0xBORROWER",
            escrow_address=MOCK_ESCROW,
            amount=amount,
            currency=contract.currency,
        )

        now = datetime.now(timezone.utc)
        next_due.amount_paid = amount
        next_due.paid_at = now
        next_due.status = RepaymentStatus.PAID

        self._s.add(self._tx_from_receipt(contract.id, receipt, TransactionType.REPAYMENT))
        await self._s.flush()

        # Check if loan is fully repaid
        remaining = await self._remaining_installments(contract_id)
        if remaining == 0:
            contract.status = LoanStatus.REPAID
            contract.closed_at = now

            # Release collateral if any
            if contract.collateral_amount and contract.collateral_amount > 0:
                release = await blockchain_client.release_collateral(
                    escrow_address=MOCK_ESCROW,
                    borrower_address=borrower.wallet_address or "0xBORROWER",
                    amount=float(contract.collateral_amount),
                    currency=contract.collateral_currency or "ETH",
                )
                self._s.add(self._tx_from_receipt(
                    contract.id, release, TransactionType.COLLATERAL_RELEASE
                ))

            # Mark the loan request as repaid too
            contract.loan_request.status = LoanStatus.REPAID
            await self._s.flush()
            logger.info("Loan fully repaid: contract=%s", contract_id)

        return next_due

    # ═══════════════════════════════════════════════════════════════
    # 5. Loan history for a user
    # ═══════════════════════════════════════════════════════════════

    async def history(
        self,
        user_id: uuid.UUID,
        role: str = "borrower",
        limit: int = 50,
        offset: int = 0,
    ) -> list[LoanRequest]:
        q = select(LoanRequest).order_by(LoanRequest.created_at.desc())

        if role == "lender":
            q = (
                q.join(LoanContract, LoanContract.loan_request_id == LoanRequest.id)
                .where(LoanContract.lender_id == user_id)
            )
        else:
            q = q.where(LoanRequest.borrower_id == user_id)

        q = q.offset(offset).limit(limit)
        return list((await self._s.scalars(q)).all())

    # ═══════════════════════════════════════════════════════════════
    # Private helpers
    # ═══════════════════════════════════════════════════════════════

    async def _get_user(self, uid: uuid.UUID) -> User:
        user = await self._s.scalar(select(User).where(User.id == uid))
        if not user:
            raise LoanServiceError(f"User {uid} not found")
        return user

    async def _get_request(self, rid: uuid.UUID) -> LoanRequest:
        req = await self._s.scalar(select(LoanRequest).where(LoanRequest.id == rid))
        if not req:
            raise LoanServiceError(f"Loan request {rid} not found")
        return req

    async def _get_contract(self, cid: uuid.UUID) -> LoanContract:
        c = await self._s.scalar(select(LoanContract).where(LoanContract.id == cid))
        if not c:
            raise LoanServiceError(f"Loan contract {cid} not found")
        return c

    async def _latest_trust_score(self, uid: uuid.UUID) -> TrustScore | None:
        return await self._s.scalar(
            select(TrustScore)
            .where(TrustScore.user_id == uid)
            .order_by(TrustScore.created_at.desc())
            .limit(1)
        )

    async def _active_loan_count(self, uid: uuid.UUID) -> int:
        result = await self._s.execute(
            select(LoanRequest.id)
            .where(
                LoanRequest.borrower_id == uid,
                LoanRequest.status == LoanStatus.ACTIVE,
            )
        )
        return len(result.all())

    async def _next_due_repayment(self, contract_id: uuid.UUID) -> Repayment | None:
        return await self._s.scalar(
            select(Repayment)
            .where(
                Repayment.contract_id == contract_id,
                Repayment.status == RepaymentStatus.SCHEDULED,
            )
            .order_by(Repayment.installment_number.asc())
            .limit(1)
        )

    async def _remaining_installments(self, contract_id: uuid.UUID) -> int:
        result = await self._s.execute(
            select(Repayment.id).where(
                Repayment.contract_id == contract_id,
                Repayment.status == RepaymentStatus.SCHEDULED,
            )
        )
        return len(result.all())

    # ─── schedule generation ──────────────────────────────────────

    @staticmethod
    def _build_repayment_schedule(contract: LoanContract) -> list[Repayment]:
        """
        Equal-installment schedule.  Total repayment = principal × (1 + rate).
        Split evenly across monthly periods within the term.
        """
        principal = float(contract.principal)
        annual_rate = contract.interest_rate_bps / 10_000
        term_fraction = contract.term_days / 365
        total_interest = principal * annual_rate * term_fraction
        total_due = principal + total_interest

        n_installments = max(contract.term_days // REPAYMENT_FREQUENCY_DAYS, 1)
        per_installment = round(total_due / n_installments, 2)

        schedule: list[Repayment] = []
        for i in range(1, n_installments + 1):
            due_date = contract.disbursed_at + timedelta(days=REPAYMENT_FREQUENCY_DAYS * i)  # type: ignore[operator]
            amt = per_installment if i < n_installments else round(total_due - per_installment * (n_installments - 1), 2)
            schedule.append(Repayment(
                contract_id=contract.id,
                installment_number=i,
                currency=contract.currency,
                amount_due=amt,
                due_date=due_date,
                status=RepaymentStatus.SCHEDULED,
            ))
        return schedule

    @staticmethod
    def _tx_from_receipt(
        contract_id: uuid.UUID,
        receipt: ChainTxReceipt,
        tx_type: TransactionType,
    ) -> Transaction:
        return Transaction(
            contract_id=contract_id,
            tx_type=tx_type,
            status=TransactionStatus.CONFIRMED if receipt.success else TransactionStatus.FAILED,
            currency=receipt.currency,
            amount=receipt.amount,
            tx_hash=receipt.tx_hash,
            chain=receipt.chain,
            from_address=receipt.from_address,
            to_address=receipt.to_address,
            block_number=receipt.block_number,
            confirmed_at=receipt.confirmed_at,
        )


# ─── Helpers ──────────────────────────────────────────────────────

_TIER_ORDER = [RiskTier.LOW, RiskTier.MEDIUM, RiskTier.HIGH, RiskTier.CRITICAL]


def _tiers_up_to(max_tier: RiskTier) -> list[RiskTier]:
    """Return all tiers from LOW up to and including max_tier."""
    idx = _TIER_ORDER.index(max_tier)
    return _TIER_ORDER[: idx + 1]
