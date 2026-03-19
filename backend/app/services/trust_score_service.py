"""
Trust Score Service
====================
Orchestrates: DB reads  →  engine computation  →  DB persistence.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.core import ConnectedAccount, IncomeSource, TrustScore
from app.models.enums import LoanStatus, RepaymentStatus, SybilVerdict
from app.models.graph import GraphFeatureVector
from app.models.loan import LoanContract, LoanRequest, Repayment, Transaction
from app.models.sybil import SybilAnalysis
from app.models.user import User
from app.services.trust_score_engine import (
    AccountInfo,
    GraphMetrics,
    IncomeRecord,
    LoanHistory,
    RawUserData,
    ScoreResult,
    SybilInfo,
    TransactionStats,
    calculate_trust_score,
)

logger = get_logger(__name__)


class TrustScoreService:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    # ─── public API ───────────────────────────────────────────────

    async def calculate_for_user(self, user_id: uuid.UUID) -> ScoreResult:
        raw = await self._gather_raw_data(user_id)
        result = calculate_trust_score(raw)
        await self._persist(user_id, result)
        logger.info(
            "Trust score calculated: user=%s score=%.1f tier=%s",
            user_id, result.score, result.risk_tier,
        )
        return result

    # ─── data gathering ───────────────────────────────────────────

    async def _gather_raw_data(self, user_id: uuid.UUID) -> RawUserData:
        user = await self._s.scalar(select(User).where(User.id == user_id))
        if not user:
            raise ValueError(f"User {user_id} not found")

        income_sources = await self._fetch_income(user_id)
        loan_history = await self._fetch_loan_history(user_id)
        tx_stats = await self._fetch_transaction_stats(user_id)
        graph = await self._fetch_graph_metrics(user_id)
        sybil = await self._fetch_sybil(user_id)
        accounts = await self._fetch_accounts(user_id)
        prev_scores = await self._fetch_previous_scores(user_id)
        last_activity = await self._fetch_last_activity(user_id)
        primary_currency = self._determine_primary_currency(income_sources)

        return RawUserData(
            user_created_at=user.created_at,
            wallet_address=user.wallet_address,
            income_sources=income_sources,
            loan_history=loan_history,
            transaction_stats=tx_stats,
            graph_metrics=graph,
            sybil_info=sybil,
            connected_accounts=accounts,
            primary_currency=primary_currency,
            previous_scores=prev_scores,
            last_activity_at=last_activity,
        )

    async def _fetch_income(self, uid: uuid.UUID) -> list[IncomeRecord]:
        rows = (await self._s.scalars(
            select(IncomeSource).where(IncomeSource.user_id == uid)
        )).all()
        return [
            IncomeRecord(
                monthly_amount=float(r.monthly_amount),
                currency=r.currency,
                frequency=r.frequency.value,
                is_verified=r.is_verified,
            )
            for r in rows
        ]

    async def _fetch_loan_history(self, uid: uuid.UUID) -> LoanHistory:
        requests = (await self._s.scalars(
            select(LoanRequest).where(LoanRequest.borrower_id == uid)
        )).all()

        contract_ids: list[uuid.UUID] = []
        repaid = defaulted = active = 0
        for req in requests:
            if req.contract:
                contract_ids.append(req.contract.id)
                if req.contract.status == LoanStatus.REPAID:
                    repaid += 1
                elif req.contract.status == LoanStatus.DEFAULTED:
                    defaulted += 1
                elif req.contract.status == LoanStatus.ACTIVE:
                    active += 1

        on_time = late = missed = total_repayments = 0
        if contract_ids:
            repayments = (await self._s.scalars(
                select(Repayment).where(Repayment.contract_id.in_(contract_ids))
            )).all()
            for r in repayments:
                total_repayments += 1
                if r.status == RepaymentStatus.PAID:
                    if r.paid_at and r.paid_at <= r.due_date:
                        on_time += 1
                    else:
                        late += 1
                elif r.status == RepaymentStatus.MISSED:
                    missed += 1

        return LoanHistory(
            total_contracts=len(contract_ids),
            repaid_count=repaid,
            defaulted_count=defaulted,
            active_count=active,
            on_time_repayments=on_time,
            late_repayments=late,
            missed_repayments=missed,
            total_repayments=total_repayments,
        )

    async def _fetch_transaction_stats(self, uid: uuid.UUID) -> TransactionStats:
        contract_ids_q = (
            select(LoanContract.id)
            .join(LoanRequest, LoanContract.loan_request_id == LoanRequest.id)
            .where(LoanRequest.borrower_id == uid)
        )
        txs = (await self._s.scalars(
            select(Transaction).where(Transaction.contract_id.in_(contract_ids_q))
        )).all()

        if not txs:
            return TransactionStats()

        types = set()
        chains = set()
        counterparties: set[str] = set()
        circular = 0
        for t in txs:
            types.add(t.tx_type.value)
            if t.chain:
                chains.add(t.chain)
            if t.from_address:
                counterparties.add(t.from_address)
            if t.to_address:
                counterparties.add(t.to_address)
            if t.from_address and t.to_address and t.from_address == t.to_address:
                circular += 1

        return TransactionStats(
            total_count=len(txs),
            unique_types=len(types),
            unique_chains=len(chains),
            unique_counterparties=len(counterparties),
            circular_count=circular,
        )

    async def _fetch_graph_metrics(self, uid: uuid.UUID) -> GraphMetrics:
        row = await self._s.scalar(
            select(GraphFeatureVector)
            .where(GraphFeatureVector.user_id == uid)
            .order_by(GraphFeatureVector.created_at.desc())
            .limit(1)
        )
        if not row:
            return GraphMetrics()
        return GraphMetrics(
            pagerank=row.pagerank,
            betweenness_centrality=row.betweenness_centrality,
            closeness_centrality=row.closeness_centrality,
            clustering_coeff=row.clustering_coeff,
            degree_in=row.degree_in,
            degree_out=row.degree_out,
        )

    async def _fetch_sybil(self, uid: uuid.UUID) -> SybilInfo:
        row = await self._s.scalar(
            select(SybilAnalysis)
            .where(SybilAnalysis.user_id == uid)
            .order_by(SybilAnalysis.created_at.desc())
            .limit(1)
        )
        if not row:
            return SybilInfo()
        return SybilInfo(
            verdict=row.verdict.value,
            confidence=row.confidence,
        )

    async def _fetch_accounts(self, uid: uuid.UUID) -> list[AccountInfo]:
        rows = (await self._s.scalars(
            select(ConnectedAccount).where(ConnectedAccount.user_id == uid)
        )).all()
        return [
            AccountInfo(provider=r.provider.value, is_verified=r.is_verified)
            for r in rows
        ]

    async def _fetch_previous_scores(self, uid: uuid.UUID) -> list[float]:
        rows = (await self._s.execute(
            select(TrustScore.score)
            .where(TrustScore.user_id == uid)
            .order_by(TrustScore.created_at.asc())
            .limit(10)
        )).scalars().all()
        return [float(s) for s in rows]

    async def _fetch_last_activity(self, uid: uuid.UUID) -> datetime | None:
        contract_ids_q = (
            select(LoanContract.id)
            .join(LoanRequest, LoanContract.loan_request_id == LoanRequest.id)
            .where(LoanRequest.borrower_id == uid)
        )
        result = await self._s.scalar(
            select(func.max(Transaction.created_at))
            .where(Transaction.contract_id.in_(contract_ids_q))
        )
        return result

    # ─── helpers ──────────────────────────────────────────────────

    @staticmethod
    def _determine_primary_currency(sources: list[IncomeRecord]) -> str:
        if not sources:
            return "USD"
        by_amount: dict[str, float] = {}
        for s in sources:
            by_amount[s.currency] = by_amount.get(s.currency, 0) + s.monthly_amount
        return max(by_amount, key=by_amount.get)  # type: ignore[arg-type]

    # ─── persistence ──────────────────────────────────────────────

    async def _persist(self, uid: uuid.UUID, result: ScoreResult) -> TrustScore:
        record = TrustScore(
            user_id=uid,
            score=result.score,
            risk_tier=result.risk_tier,
            repayment_component=result.features.get("loan_reliability", 0.0),
            identity_component=result.features.get("platform_quality", 0.0),
            social_component=result.features.get("graph_reputation", 0.0),
            income_component=result.features.get("income", 0.0),
            model_version=result.model_version,
            explanation=self._build_explanation(result),
        )
        self._s.add(record)
        await self._s.flush()
        return record

    @staticmethod
    def _build_explanation(r: ScoreResult) -> str:
        lines = [f"Score {r.score} ({r.risk_tier} risk) | model={r.model_version}"]
        lines.append(f"Raw weighted: {r.raw_weighted}")
        lines.append("Features: " + ", ".join(
            f"{k}={v:.3f}" for k, v in r.features.items()
        ))
        p = r.penalties
        if p.total > 0:
            parts = []
            if p.circular_tx:
                parts.append(f"circular_tx={p.circular_tx:.2f}")
            if p.sybil:
                parts.append(f"sybil={p.sybil:.2f}")
            if p.velocity:
                parts.append(f"velocity={p.velocity:.2f}")
            if p.decay:
                parts.append(f"decay={p.decay:.2f}")
            if p.gaming:
                parts.append(f"gaming={p.gaming:.2f}")
            lines.append(f"Penalties ({p.total:.2f}): " + ", ".join(parts))
        lines.append(f"Loan limit: ${r.loan_limit:,.2f}")
        return "\n".join(lines)
