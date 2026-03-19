"""
Risk Mitigation Service
========================
Orchestrates:
  1. Reputation Slashing     - score reduction on default
  2. Identity Confidence     - multi-source identity scoring
  3. Social Guarantees       - vouch/slash cascading
  4. Repayment Behavior      - aggregate payment statistics
  5. Default Processing      - end-to-end default event handling

All penalty math is based on configurable severity tiers.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.core import TrustScore
from app.models.enums import LoanStatus, RepaymentStatus
from app.models.loan import LoanContract, LoanRequest, Repayment
from app.models.risk import (
    DefaultEvent,
    IdentityLink,
    RepaymentBehavior,
    ReputationPenalty,
    SocialGuarantee,
)
from app.models.user import User

logger = get_logger(__name__)

# ═══════════════════════════════════════════════════════════════════
# Severity + penalty configuration
# ═══════════════════════════════════════════════════════════════════

SEVERITY_TIERS = {
    "minor":    {"score_penalty": 50,  "recovery_days": 90,  "max_overdue_days": 14},
    "standard": {"score_penalty": 120, "recovery_days": 180, "max_overdue_days": 60},
    "severe":   {"score_penalty": 200, "recovery_days": 365, "max_overdue_days": 120},
    "critical": {"score_penalty": 350, "recovery_days": 730, "max_overdue_days": 999},
}

GUARANTOR_SLASH_RATIO = 0.30
SCORE_FLOOR = 300

# Identity confidence weights per provider
IDENTITY_WEIGHTS = {
    "email":    0.15,
    "wallet":   0.20,
    "github":   0.25,
    "linkedin": 0.15,
    "stripe":   0.15,
    "phone":    0.10,
}
VERIFIED_BONUS = 1.0
UNVERIFIED_PENALTY = 0.3


# ═══════════════════════════════════════════════════════════════════
# 1. Reputation Slashing
# ═══════════════════════════════════════════════════════════════════

class ReputationSlashingService:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def slash_for_default(
        self,
        user_id: uuid.UUID,
        default_event_id: uuid.UUID,
        severity: str = "standard",
    ) -> ReputationPenalty:
        """Apply a trust score penalty for a default event."""
        config = SEVERITY_TIERS.get(severity, SEVERITY_TIERS["standard"])
        penalty_points = config["score_penalty"]
        recovery_days = config["recovery_days"]

        current_score = await self._get_latest_score(user_id)
        new_score = max(SCORE_FLOOR, current_score - penalty_points)

        penalty = ReputationPenalty(
            user_id=user_id,
            reason=f"loan_default_{severity}",
            score_before=current_score,
            score_after=new_score,
            penalty_points=penalty_points,
            source_event_id=default_event_id,
            source_type="default",
            expires_at=datetime.now(timezone.utc) + timedelta(days=recovery_days),
            is_active=True,
        )
        self._s.add(penalty)

        new_trust = TrustScore(
            user_id=user_id,
            score=new_score,
            risk_tier=self._classify_risk(new_score),
            repayment_component=0.0,
            identity_component=0.0,
            social_component=0.0,
            income_component=0.0,
            model_version="v3-slash",
            explanation=f"Score slashed from {current_score} to {new_score} "
                        f"due to {severity} default (penalty: -{penalty_points}pts, "
                        f"recovery: {recovery_days}d)",
        )
        self._s.add(new_trust)
        await self._s.flush()

        logger.info(
            "Reputation slashed: user=%s %s -> %s (-%d pts, severity=%s)",
            user_id, current_score, new_score, penalty_points, severity,
        )
        return penalty

    async def get_penalty_history(self, user_id: uuid.UUID) -> list[ReputationPenalty]:
        result = await self._s.scalars(
            select(ReputationPenalty)
            .where(ReputationPenalty.user_id == user_id)
            .order_by(ReputationPenalty.created_at.desc())
        )
        return list(result.all())

    async def get_active_penalties(self, user_id: uuid.UUID) -> list[ReputationPenalty]:
        now = datetime.now(timezone.utc)
        result = await self._s.scalars(
            select(ReputationPenalty).where(
                ReputationPenalty.user_id == user_id,
                ReputationPenalty.is_active == True,
                (ReputationPenalty.expires_at > now) | (ReputationPenalty.expires_at == None),
            )
        )
        return list(result.all())

    async def expire_old_penalties(self) -> int:
        """Mark expired penalties as inactive. Returns count updated."""
        now = datetime.now(timezone.utc)
        result = await self._s.execute(
            update(ReputationPenalty)
            .where(
                ReputationPenalty.is_active == True,
                ReputationPenalty.expires_at != None,
                ReputationPenalty.expires_at <= now,
            )
            .values(is_active=False)
        )
        return result.rowcount

    async def _get_latest_score(self, user_id: uuid.UUID) -> float:
        row = await self._s.scalar(
            select(TrustScore.score)
            .where(TrustScore.user_id == user_id)
            .order_by(TrustScore.created_at.desc())
            .limit(1)
        )
        return float(row) if row else 500.0

    @staticmethod
    def _classify_risk(score: float) -> str:
        if score >= 750:
            return "low"
        if score >= 600:
            return "medium"
        if score >= 450:
            return "high"
        return "critical"


# ═══════════════════════════════════════════════════════════════════
# 2. Identity Confidence Scoring
# ═══════════════════════════════════════════════════════════════════

class IdentityService:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def link_identity(
        self,
        user_id: uuid.UUID,
        provider: str,
        identifier: str,
        is_verified: bool = False,
        verification_method: str | None = None,
    ) -> IdentityLink:
        """Link or update an identity source for a user."""
        weight = IDENTITY_WEIGHTS.get(provider, 0.10)
        effective_weight = weight * (VERIFIED_BONUS if is_verified else UNVERIFIED_PENALTY)

        existing = await self._s.scalar(
            select(IdentityLink).where(
                IdentityLink.user_id == user_id,
                IdentityLink.provider == provider,
            )
        )
        if existing:
            existing.identifier = identifier
            existing.is_verified = is_verified
            existing.verification_method = verification_method
            existing.confidence_weight = effective_weight
            if is_verified:
                existing.verified_at = datetime.now(timezone.utc)
            await self._s.flush()
            return existing

        link = IdentityLink(
            user_id=user_id,
            provider=provider,
            identifier=identifier,
            is_verified=is_verified,
            verification_method=verification_method,
            verified_at=datetime.now(timezone.utc) if is_verified else None,
            confidence_weight=effective_weight,
        )
        self._s.add(link)
        await self._s.flush()
        return link

    async def compute_identity_confidence(self, user_id: uuid.UUID) -> float:
        """
        Calculate an overall identity confidence score (0-1).
        Based on the sum of weighted identity links, capped at 1.0.
        """
        links = await self._get_links(user_id)
        if not links:
            return 0.0

        total = sum(l.confidence_weight for l in links)
        max_possible = sum(IDENTITY_WEIGHTS.values())
        return min(total / max_possible, 1.0) if max_possible > 0 else 0.0

    async def get_identity_profile(self, user_id: uuid.UUID) -> dict:
        """Full identity breakdown for a user."""
        links = await self._get_links(user_id)
        confidence = await self.compute_identity_confidence(user_id)

        return {
            "user_id": str(user_id),
            "confidence_score": round(confidence, 4),
            "total_links": len(links),
            "verified_count": sum(1 for l in links if l.is_verified),
            "links": [
                {
                    "provider": l.provider,
                    "identifier": l.identifier,
                    "is_verified": l.is_verified,
                    "confidence_weight": round(l.confidence_weight, 4),
                    "verified_at": l.verified_at.isoformat() if l.verified_at else None,
                }
                for l in links
            ],
        }

    async def _get_links(self, user_id: uuid.UUID) -> list[IdentityLink]:
        result = await self._s.scalars(
            select(IdentityLink).where(IdentityLink.user_id == user_id)
        )
        return list(result.all())


# ═══════════════════════════════════════════════════════════════════
# 3. Social Guarantee System
# ═══════════════════════════════════════════════════════════════════

class SocialGuaranteeService:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def vouch(
        self,
        guarantor_id: uuid.UUID,
        borrower_id: uuid.UUID,
        contract_id: uuid.UUID | None = None,
        stake_amount: float = 0.0,
        message: str | None = None,
    ) -> SocialGuarantee:
        """Guarantor vouches for a borrower on a specific loan."""
        if guarantor_id == borrower_id:
            raise ValueError("Cannot vouch for yourself")

        existing = await self._s.scalar(
            select(SocialGuarantee).where(
                SocialGuarantee.guarantor_id == guarantor_id,
                SocialGuarantee.borrower_id == borrower_id,
                SocialGuarantee.contract_id == contract_id,
            )
        )
        if existing:
            raise ValueError("Guarantee already exists for this loan")

        guarantee = SocialGuarantee(
            guarantor_id=guarantor_id,
            borrower_id=borrower_id,
            contract_id=contract_id,
            stake_amount=stake_amount,
            is_active=True,
            vouch_message=message,
        )
        self._s.add(guarantee)
        await self._s.flush()

        logger.info(
            "Social guarantee created: %s vouches for %s (contract=%s)",
            guarantor_id, borrower_id, contract_id,
        )
        return guarantee

    async def slash_guarantors(
        self,
        borrower_id: uuid.UUID,
        default_event_id: uuid.UUID,
        contract_id: uuid.UUID | None = None,
    ) -> list[ReputationPenalty]:
        """Slash all active guarantors when a borrower defaults."""
        q = select(SocialGuarantee).where(
            SocialGuarantee.borrower_id == borrower_id,
            SocialGuarantee.is_active == True,
            SocialGuarantee.slashed == False,
        )
        if contract_id:
            q = q.where(
                (SocialGuarantee.contract_id == contract_id)
                | (SocialGuarantee.contract_id == None)
            )

        guarantees = list((await self._s.scalars(q)).all())
        if not guarantees:
            return []

        slasher = ReputationSlashingService(self._s)
        penalties = []

        for g in guarantees:
            guarantor_score = await slasher._get_latest_score(g.guarantor_id)
            penalty_points = guarantor_score * GUARANTOR_SLASH_RATIO
            new_score = max(SCORE_FLOOR, guarantor_score - penalty_points)

            penalty = ReputationPenalty(
                user_id=g.guarantor_id,
                reason="guarantor_slash",
                score_before=guarantor_score,
                score_after=new_score,
                penalty_points=penalty_points,
                source_event_id=default_event_id,
                source_type="social_guarantee",
                expires_at=datetime.now(timezone.utc) + timedelta(days=180),
                is_active=True,
            )
            self._s.add(penalty)

            new_trust = TrustScore(
                user_id=g.guarantor_id,
                score=new_score,
                risk_tier=slasher._classify_risk(new_score),
                model_version="v3-guarantor-slash",
                explanation=f"Guarantor penalty: vouched for defaulting borrower "
                            f"{borrower_id}. Score {guarantor_score} -> {new_score} "
                            f"(-{penalty_points:.0f}pts, 30% slash)",
            )
            self._s.add(new_trust)

            g.slashed = True
            g.slashed_at = datetime.now(timezone.utc)
            g.is_active = False

            penalties.append(penalty)
            logger.info(
                "Guarantor slashed: %s lost %.0f pts for vouching for %s",
                g.guarantor_id, penalty_points, borrower_id,
            )

        await self._s.flush()
        return penalties

    async def get_guarantees_for_borrower(
        self, borrower_id: uuid.UUID
    ) -> list[SocialGuarantee]:
        result = await self._s.scalars(
            select(SocialGuarantee).where(
                SocialGuarantee.borrower_id == borrower_id,
                SocialGuarantee.is_active == True,
            )
        )
        return list(result.all())

    async def get_guarantees_by_guarantor(
        self, guarantor_id: uuid.UUID
    ) -> list[SocialGuarantee]:
        result = await self._s.scalars(
            select(SocialGuarantee).where(
                SocialGuarantee.guarantor_id == guarantor_id
            ).order_by(SocialGuarantee.created_at.desc())
        )
        return list(result.all())


# ═══════════════════════════════════════════════════════════════════
# 4. Repayment Behavior Tracker
# ═══════════════════════════════════════════════════════════════════

class RepaymentTracker:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def refresh_behavior(self, user_id: uuid.UUID) -> RepaymentBehavior:
        """Recompute aggregate repayment statistics from loan history."""
        requests = list((await self._s.scalars(
            select(LoanRequest).where(LoanRequest.borrower_id == user_id)
        )).all())

        total_loans = len(requests)
        repaid = defaulted = active = 0
        total_borrowed = 0.0
        total_repaid_amount = 0.0
        contract_ids = []

        for req in requests:
            total_borrowed += float(req.amount_requested)
            if req.contract:
                contract_ids.append(req.contract.id)
                if req.contract.status == LoanStatus.REPAID:
                    repaid += 1
                elif req.contract.status == LoanStatus.DEFAULTED:
                    defaulted += 1
                elif req.contract.status == LoanStatus.ACTIVE:
                    active += 1

        on_time = late = missed = total_installments = 0
        repay_durations = []

        if contract_ids:
            repayments = list((await self._s.scalars(
                select(Repayment).where(Repayment.contract_id.in_(contract_ids))
            )).all())

            for r in repayments:
                total_installments += 1
                if r.status == RepaymentStatus.PAID:
                    total_repaid_amount += float(r.amount_paid)
                    if r.paid_at and r.paid_at <= r.due_date:
                        on_time += 1
                    else:
                        late += 1
                    if r.paid_at:
                        days = (r.paid_at - r.due_date).days
                        repay_durations.append(days)
                elif r.status == RepaymentStatus.MISSED:
                    missed += 1

        avg_days = sum(repay_durations) / len(repay_durations) if repay_durations else 0.0
        streak = self._compute_on_time_streak(on_time, late, missed)
        reliability = self._compute_reliability(on_time, late, missed, defaulted, total_installments)

        defaults = list((await self._s.scalars(
            select(DefaultEvent).where(DefaultEvent.borrower_id == user_id)
        )).all())
        last_default = max(
            (d.created_at for d in defaults), default=None
        )

        existing = await self._s.scalar(
            select(RepaymentBehavior).where(RepaymentBehavior.user_id == user_id)
        )

        if existing:
            existing.total_loans = total_loans
            existing.loans_repaid = repaid
            existing.loans_defaulted = defaulted
            existing.loans_active = active
            existing.total_installments = total_installments
            existing.on_time_payments = on_time
            existing.late_payments = late
            existing.missed_payments = missed
            existing.total_borrowed = total_borrowed
            existing.total_repaid = total_repaid_amount
            existing.avg_days_to_repay = avg_days
            existing.longest_streak_on_time = streak
            existing.current_streak_on_time = streak
            existing.default_count = len(defaults)
            existing.last_default_at = last_default
            existing.reliability_score = reliability
            await self._s.flush()
            return existing

        behavior = RepaymentBehavior(
            user_id=user_id,
            total_loans=total_loans,
            loans_repaid=repaid,
            loans_defaulted=defaulted,
            loans_active=active,
            total_installments=total_installments,
            on_time_payments=on_time,
            late_payments=late,
            missed_payments=missed,
            total_borrowed=total_borrowed,
            total_repaid=total_repaid_amount,
            avg_days_to_repay=avg_days,
            longest_streak_on_time=streak,
            current_streak_on_time=streak,
            default_count=len(defaults),
            last_default_at=last_default,
            reliability_score=reliability,
        )
        self._s.add(behavior)
        await self._s.flush()
        return behavior

    @staticmethod
    def _compute_on_time_streak(on_time: int, late: int, missed: int) -> int:
        if on_time == 0:
            return 0
        total = on_time + late + missed
        if total == 0:
            return 0
        return on_time

    @staticmethod
    def _compute_reliability(
        on_time: int, late: int, missed: int, defaults: int, total: int
    ) -> float:
        if total == 0 and defaults == 0:
            return 0.5
        on_time_ratio = on_time / total if total > 0 else 0.5
        default_penalty = min(defaults * 0.15, 0.6)
        late_penalty = (late / total * 0.1) if total > 0 else 0.0
        score = on_time_ratio - default_penalty - late_penalty
        return max(0.0, min(1.0, score))


# ═══════════════════════════════════════════════════════════════════
# 5. Default Processing Orchestrator
# ═══════════════════════════════════════════════════════════════════

class DefaultProcessor:
    """
    End-to-end handler when a loan defaults. Coordinates:
      1. Create DefaultEvent record
      2. Slash borrower reputation
      3. Slash guarantor reputations
      4. Update repayment behavior
      5. Mark loan as defaulted
    """

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def process_default(
        self,
        contract_id: uuid.UUID,
        on_chain_tx_hash: str | None = None,
        on_chain_block: int | None = None,
    ) -> DefaultEvent:
        contract = await self._s.scalar(
            select(LoanContract).where(LoanContract.id == contract_id)
        )
        if not contract:
            raise ValueError(f"Contract {contract_id} not found")
        if contract.status not in (LoanStatus.ACTIVE, LoanStatus.LIQUIDATED):
            raise ValueError(f"Contract is {contract.status.value}, cannot default")

        request = await self._s.scalar(
            select(LoanRequest).where(LoanRequest.id == contract.loan_request_id)
        )
        borrower_id = request.borrower_id

        missed = await self._count_missed(contract_id)
        days_overdue = 0
        if contract.maturity_date:
            delta = datetime.now(timezone.utc) - contract.maturity_date
            days_overdue = max(0, delta.days)

        severity = self._determine_severity(days_overdue, missed, float(contract.principal))

        principal_owed = float(contract.principal) - sum(
            float(r.amount_paid) for r in contract.repayments
            if r.status == RepaymentStatus.PAID
        )
        interest_owed = 0.0

        event = DefaultEvent(
            borrower_id=borrower_id,
            contract_id=contract_id,
            principal_owed=max(0, principal_owed),
            interest_owed=interest_owed,
            missed_installments=missed,
            days_overdue=days_overdue,
            severity=severity,
            on_chain_tx_hash=on_chain_tx_hash,
            on_chain_block=on_chain_block,
        )
        self._s.add(event)
        await self._s.flush()

        contract.status = LoanStatus.DEFAULTED
        contract.closed_at = datetime.now(timezone.utc)
        request.status = LoanStatus.DEFAULTED

        slasher = ReputationSlashingService(self._s)
        await slasher.slash_for_default(borrower_id, event.id, severity)

        guarantor_svc = SocialGuaranteeService(self._s)
        await guarantor_svc.slash_guarantors(borrower_id, event.id, contract_id)

        tracker = RepaymentTracker(self._s)
        await tracker.refresh_behavior(borrower_id)

        await self._s.flush()

        logger.info(
            "Default processed: contract=%s borrower=%s severity=%s days_overdue=%d",
            contract_id, borrower_id, severity, days_overdue,
        )
        return event

    async def _count_missed(self, contract_id: uuid.UUID) -> int:
        result = await self._s.execute(
            select(func.count(Repayment.id)).where(
                Repayment.contract_id == contract_id,
                Repayment.status.in_([RepaymentStatus.MISSED, RepaymentStatus.OVERDUE]),
            )
        )
        return result.scalar_one()

    @staticmethod
    def _determine_severity(days_overdue: int, missed: int, principal: float) -> str:
        if days_overdue > 120 or missed >= 4 or principal > 5000:
            return "critical"
        if days_overdue > 60 or missed >= 3:
            return "severe"
        if days_overdue > 14 or missed >= 2:
            return "standard"
        return "minor"
