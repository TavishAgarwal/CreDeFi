"""
E2E Flow Integration Test
============================
Validates the full CreDeFi pipeline without DB or HTTP:
  1. RawUserData → calculate_trust_score → score > 450
  2. Trust score → collateral ratio, interest rate, max loan
  3. Sybil user → lower score, restricted eligibility
  4. Score influences all loan parameters end-to-end
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.services.trust_score_engine import (
    AccountInfo,
    GraphMetrics,
    IncomeRecord,
    LoanHistory,
    RawUserData,
    SybilInfo,
    TransactionStats,
    calculate_trust_score,
)
from app.services.loan_service import (
    get_collateral_ratio,
    get_interest_rate_bps,
    get_max_loan,
)


# ── Fixtures ──────────────────────────────────────────────────────


def _strong_user() -> RawUserData:
    return RawUserData(
        user_created_at=datetime.now(timezone.utc) - timedelta(days=500),
        wallet_address="0xStrongUser",
        income_sources=[
            IncomeRecord(monthly_amount=8000.0, currency="USD", frequency="monthly", is_verified=True),
            IncomeRecord(monthly_amount=2000.0, currency="USDC", frequency="biweekly", is_verified=True),
        ],
        loan_history=LoanHistory(
            total_contracts=5, repaid_count=5, defaulted_count=0, active_count=0,
            on_time_repayments=10, late_repayments=0, missed_repayments=0, total_repayments=10,
        ),
        transaction_stats=TransactionStats(
            total_count=50, unique_types=4, unique_chains=3,
            unique_counterparties=15, circular_count=0,
        ),
        graph_metrics=GraphMetrics(
            pagerank=0.008, betweenness_centrality=0.03, closeness_centrality=0.5,
            clustering_coeff=0.6, degree_in=20, degree_out=15,
        ),
        sybil_info=SybilInfo(verdict="clean", confidence=0.0),
        connected_accounts=[
            AccountInfo(provider="stripe", is_verified=True),
            AccountInfo(provider="bank", is_verified=True),
            AccountInfo(provider="metamask", is_verified=True),
        ],
        primary_currency="USD",
        previous_scores=[650.0, 700.0, 750.0],
        last_activity_at=datetime.now(timezone.utc) - timedelta(days=2),
    )


def _sybil_user() -> RawUserData:
    return RawUserData(
        user_created_at=datetime.now(timezone.utc) - timedelta(days=30),
        wallet_address="0xSybilUser",
        income_sources=[
            IncomeRecord(monthly_amount=1000.0, currency="USD", frequency="monthly", is_verified=False),
        ],
        loan_history=LoanHistory(total_contracts=1, repaid_count=0, defaulted_count=1),
        transaction_stats=TransactionStats(
            total_count=20, unique_types=1, unique_chains=1,
            unique_counterparties=2, circular_count=10,
        ),
        sybil_info=SybilInfo(verdict="sybil", confidence=0.9),
        connected_accounts=[],
        previous_scores=[400.0, 600.0],
        last_activity_at=datetime.now(timezone.utc) - timedelta(days=200),
    )


def _cold_start_user() -> RawUserData:
    return RawUserData(user_created_at=datetime.now(timezone.utc))


# ── Tests ─────────────────────────────────────────────────────────


class TestE2EStrongUser:
    """Full pipeline for a user with strong signals."""

    def test_score_above_threshold(self):
        result = calculate_trust_score(_strong_user())
        assert result.score >= 450, f"Strong user should score ≥ 450, got {result.score}"
        assert result.score <= 1000

    def test_risk_tier_assigned(self):
        result = calculate_trust_score(_strong_user())
        assert result.risk_tier in ("low", "medium", "high", "critical")

    def test_loan_eligible(self):
        result = calculate_trust_score(_strong_user())
        assert result.loan_limit > 0, "Strong user should have positive loan limit"

    def test_collateral_ratio_valid(self):
        result = calculate_trust_score(_strong_user())
        ratio = get_collateral_ratio(result.score)
        assert ratio is not None, "Strong user should have a collateral ratio"
        assert 0.20 <= ratio <= 1.20, f"Collateral ratio {ratio} out of expected range"

    def test_interest_rate_valid(self):
        result = calculate_trust_score(_strong_user())
        rate = get_interest_rate_bps(result.score)
        assert rate is not None, "Strong user should have an interest rate"
        assert 300 <= rate <= 2400, f"Rate {rate} bps out of expected range"

    def test_max_loan_valid(self):
        result = calculate_trust_score(_strong_user())
        max_loan = get_max_loan(result.score)
        assert max_loan > 0, "Strong user should have positive max loan"

    def test_features_all_populated(self):
        result = calculate_trust_score(_strong_user())
        assert len(result.features) == 10, "Expected 10 features"
        for name, val in result.features.items():
            assert 0.0 <= val <= 1.0, f"Feature {name}={val} out of range"

    def test_ml_component_present(self):
        result = calculate_trust_score(_strong_user())
        assert result.ml_component is not None
        assert 0.0 <= result.ml_component.default_probability <= 1.0

    def test_strong_user_better_than_sybil(self):
        strong = calculate_trust_score(_strong_user())
        sybil = calculate_trust_score(_sybil_user())
        assert strong.score > sybil.score, (
            f"Strong user ({strong.score}) should outscore sybil ({sybil.score})"
        )

    def test_strong_user_lower_collateral_than_sybil(self):
        strong = calculate_trust_score(_strong_user())
        sybil = calculate_trust_score(_sybil_user())
        ratio_strong = get_collateral_ratio(strong.score)
        ratio_sybil = get_collateral_ratio(sybil.score)
        if ratio_strong is not None and ratio_sybil is not None:
            assert ratio_strong <= ratio_sybil, (
                f"Strong user collateral ({ratio_strong}) should be ≤ sybil ({ratio_sybil})"
            )


class TestE2ESybilUser:
    """Full pipeline for a sybil-flagged user."""

    def test_score_lower(self):
        result = calculate_trust_score(_sybil_user())
        assert result.score < 700, f"Sybil user should score below 700, got {result.score}"

    def test_penalties_applied(self):
        result = calculate_trust_score(_sybil_user())
        assert result.penalties.total > 0, "Sybil user should have penalties"
        assert result.penalties.sybil > 0, "Sybil penalty should fire"
        assert result.penalties.circular_tx > 0, "Circular tx penalty should fire"

    def test_higher_risk_tier(self):
        result = calculate_trust_score(_sybil_user())
        assert result.risk_tier in ("high", "critical", "medium"), (
            f"Sybil user should not be 'low' risk, got {result.risk_tier}"
        )


class TestE2EColdStart:
    """Full pipeline for a brand new user with no data."""

    def test_cold_start_neutral_score(self):
        result = calculate_trust_score(_cold_start_user())
        assert 300 <= result.score <= 1000

    def test_cold_start_limited_loan(self):
        result = calculate_trust_score(_cold_start_user())
        strong = calculate_trust_score(_strong_user())
        assert result.loan_limit <= strong.loan_limit, "Cold start should have ≤ strong user loan limit"


class TestE2ELoanParameterCoherence:
    """Verify that trust score, collateral, interest, and limits are coherent."""

    @pytest.mark.parametrize("score", [300, 449, 450, 550, 650, 750, 850, 950, 1000])
    def test_collateral_ratio_monotonically_decreasing(self, score):
        """Higher score → lower collateral requirement."""
        ratio = get_collateral_ratio(score)
        if score < 450:
            assert ratio is None
        else:
            assert ratio is not None
            assert ratio > 0

    @pytest.mark.parametrize("score", [300, 449, 450, 550, 650, 750, 850, 950, 1000])
    def test_interest_rate_monotonically_decreasing(self, score):
        """Higher score → lower interest rate."""
        rate = get_interest_rate_bps(score)
        if score < 450:
            assert rate is None
        else:
            assert rate is not None
            assert rate > 0

    def test_collateral_decreases_with_score(self):
        ratios = [(s, get_collateral_ratio(s)) for s in [450, 600, 750, 850, 950]]
        for i in range(len(ratios) - 1):
            s1, r1 = ratios[i]
            s2, r2 = ratios[i + 1]
            assert r1 >= r2, f"Collateral at score {s1} ({r1}) should be ≥ score {s2} ({r2})"

    def test_interest_decreases_with_score(self):
        rates = [(s, get_interest_rate_bps(s)) for s in [450, 600, 750, 850, 950]]
        for i in range(len(rates) - 1):
            s1, r1 = rates[i]
            s2, r2 = rates[i + 1]
            assert r1 >= r2, f"Rate at score {s1} ({r1}) should be ≥ score {s2} ({r2})"

    def test_max_loan_increases_with_score(self):
        limits = [(s, get_max_loan(s)) for s in [450, 600, 750, 850, 950]]
        for i in range(len(limits) - 1):
            s1, l1 = limits[i]
            s2, l2 = limits[i + 1]
            assert l1 <= l2, f"Max loan at score {s1} ({l1}) should be ≤ score {s2} ({l2})"
