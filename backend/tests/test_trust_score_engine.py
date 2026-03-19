"""
Tests for the CreDeFi AI Trust Score Engine.

These tests cover the pure-computation module (no DB, no I/O).
"""

import math
from datetime import datetime, timedelta, timezone

import pytest

from app.services.trust_score_engine import (
    FEATURE_WEIGHTS,
    SCORE_CEIL,
    SCORE_FLOOR,
    AccountInfo,
    FeatureExtractor,
    GraphMetrics,
    IncomeRecord,
    LoanHistory,
    PenaltyEngine,
    RawUserData,
    SybilInfo,
    TransactionStats,
    calculate_trust_score,
    classify_risk,
    compute_loan_limit,
    map_to_score_range,
)


# ═══════════════════════════════════════════════════════════════════
# Weights & Constants
# ═══════════════════════════════════════════════════════════════════


class TestConstants:
    def test_weights_sum_to_one(self):
        assert abs(sum(FEATURE_WEIGHTS.values()) - 1.0) < 1e-9

    def test_score_floor_less_than_ceil(self):
        assert SCORE_FLOOR < SCORE_CEIL

    def test_all_ten_factors_present(self):
        expected = {
            "loan_reliability", "income", "income_stability",
            "graph_reputation", "currency_risk", "platform_quality",
            "wallet_age", "transaction_diversity", "growth_trend",
            "account_behavior",
        }
        assert set(FEATURE_WEIGHTS.keys()) == expected


# ═══════════════════════════════════════════════════════════════════
# Feature Extraction
# ═══════════════════════════════════════════════════════════════════


class TestFeatureExtractor:
    def test_loan_reliability_no_history(self):
        """No loan history should return neutral (0.5) prior."""
        h = LoanHistory()
        assert FeatureExtractor.loan_reliability(h) == 0.5

    def test_loan_reliability_perfect(self):
        h = LoanHistory(
            total_contracts=5, repaid_count=5, defaulted_count=0,
            on_time_repayments=10, total_repayments=10,
        )
        assert FeatureExtractor.loan_reliability(h) == 1.0

    def test_loan_reliability_with_defaults(self):
        h = LoanHistory(
            total_contracts=3, repaid_count=1, defaulted_count=2,
            on_time_repayments=5, total_repayments=10,
        )
        score = FeatureExtractor.loan_reliability(h)
        assert 0.0 <= score < 0.5  # should be penalized

    def test_income_no_sources(self):
        assert FeatureExtractor.income([]) == 0.0

    def test_income_log_scaling(self):
        """Higher income should give higher score, with log saturation."""
        low = FeatureExtractor.income([
            IncomeRecord(monthly_amount=1000, currency="USD", frequency="monthly", is_verified=True)
        ])
        high = FeatureExtractor.income([
            IncomeRecord(monthly_amount=40000, currency="USD", frequency="monthly", is_verified=True)
        ])
        assert high > low
        assert 0.0 <= low <= 1.0
        assert 0.0 <= high <= 1.0

    def test_income_unverified_penalty(self):
        """Unverified income should produce lower score than verified."""
        verified = FeatureExtractor.income([
            IncomeRecord(monthly_amount=5000, currency="USD", frequency="monthly", is_verified=True)
        ])
        unverified = FeatureExtractor.income([
            IncomeRecord(monthly_amount=5000, currency="USD", frequency="monthly", is_verified=False)
        ])
        assert verified > unverified

    def test_income_stability_no_sources(self):
        assert FeatureExtractor.income_stability([]) == 0.0

    def test_income_stability_monthly_best(self):
        score = FeatureExtractor.income_stability([
            IncomeRecord(monthly_amount=5000, currency="USD", frequency="monthly", is_verified=True)
        ])
        assert score == 1.0

    def test_wallet_age_brand_new(self):
        """Brand new account → near-zero wallet age signal."""
        score = FeatureExtractor.wallet_age(datetime.now(timezone.utc))
        assert score < 0.01

    def test_wallet_age_old_account(self):
        """2-year-old account → max wallet age signal."""
        score = FeatureExtractor.wallet_age(
            datetime.now(timezone.utc) - timedelta(days=730)
        )
        assert score >= 0.99

    def test_currency_risk_usd_is_safest(self):
        assert FeatureExtractor.currency_risk("USD") == 1.0

    def test_currency_risk_unknown_is_low(self):
        assert FeatureExtractor.currency_risk("SHITCOIN") == 0.40

    def test_platform_quality_no_accounts(self):
        assert FeatureExtractor.platform_quality([]) == 0.0

    def test_platform_quality_bank_highest(self):
        bank = FeatureExtractor.platform_quality([AccountInfo(provider="bank", is_verified=True)])
        metamask = FeatureExtractor.platform_quality([AccountInfo(provider="metamask", is_verified=True)])
        assert bank > metamask

    def test_transaction_diversity_no_txs(self):
        assert FeatureExtractor.transaction_diversity(TransactionStats()) == 0.0

    def test_growth_trend_insufficient_history(self):
        """Fewer than 2 previous scores → neutral (0.5)."""
        assert FeatureExtractor.growth_trend([]) == 0.5
        assert FeatureExtractor.growth_trend([500.0]) == 0.5

    def test_growth_trend_improving(self):
        score = FeatureExtractor.growth_trend([500.0, 600.0, 700.0])
        assert score > 0.5  # upward trend

    def test_growth_trend_declining(self):
        score = FeatureExtractor.growth_trend([700.0, 600.0, 500.0])
        assert score < 0.5  # downward trend

    def test_account_behavior_no_accounts(self):
        assert FeatureExtractor.account_behavior([]) == 0.0

    def test_extract_all_returns_ten_keys(self):
        data = RawUserData(user_created_at=datetime.now(timezone.utc))
        features = FeatureExtractor.extract_all(data)
        assert len(features) == 10
        assert set(features.keys()) == set(FEATURE_WEIGHTS.keys())

    def test_all_features_in_zero_one_range(self):
        data = RawUserData(user_created_at=datetime.now(timezone.utc))
        features = FeatureExtractor.extract_all(data)
        for key, val in features.items():
            assert 0.0 <= val <= 1.0, f"Feature {key}={val} out of [0,1] range"


# ═══════════════════════════════════════════════════════════════════
# Penalty Engine
# ═══════════════════════════════════════════════════════════════════


class TestPenaltyEngine:
    def test_no_penalties_for_clean_user(self, strong_user_data):
        features = FeatureExtractor.extract_all(strong_user_data)
        penalties = PenaltyEngine.calculate(strong_user_data, features)
        # Clean user should have minimal penalties
        assert penalties.circular_tx == 0.0
        assert penalties.sybil == 0.0
        # Strong user may trigger a tiny gaming penalty since many features are high
        assert penalties.gaming <= 0.10

    def test_circular_tx_penalty_high_ratio(self):
        ts = TransactionStats(total_count=10, circular_count=5)
        assert PenaltyEngine.circular_transactions(ts) == 0.20

    def test_circular_tx_penalty_medium_ratio(self):
        ts = TransactionStats(total_count=10, circular_count=2)
        assert PenaltyEngine.circular_transactions(ts) == 0.10

    def test_circular_tx_no_penalty_clean(self):
        ts = TransactionStats(total_count=100, circular_count=1)
        assert PenaltyEngine.circular_transactions(ts) == 0.0

    def test_sybil_penalty_sybil_verdict(self):
        info = SybilInfo(verdict="sybil", confidence=0.9)
        penalty = PenaltyEngine.sybil_penalty(info)
        assert penalty == pytest.approx(0.35 * 0.9)

    def test_sybil_penalty_suspicious_verdict(self):
        info = SybilInfo(verdict="suspicious", confidence=0.7)
        penalty = PenaltyEngine.sybil_penalty(info)
        assert penalty == pytest.approx(0.15 * 0.7)

    def test_sybil_penalty_clean(self):
        info = SybilInfo(verdict="clean", confidence=0.0)
        assert PenaltyEngine.sybil_penalty(info) == 0.0

    def test_velocity_change_large_jump(self):
        scores = [400.0, 800.0]  # 400-point jump = 40% of range
        assert PenaltyEngine.velocity_change(scores) == 0.15

    def test_velocity_change_normal(self):
        scores = [650.0, 670.0]  # small change
        assert PenaltyEngine.velocity_change(scores) == 0.0

    def test_score_decay_long_idle(self):
        old_date = datetime.now(timezone.utc) - timedelta(days=200)
        assert PenaltyEngine.score_decay(old_date) == 0.12

    def test_score_decay_recent_activity(self):
        recent = datetime.now(timezone.utc) - timedelta(days=5)
        assert PenaltyEngine.score_decay(recent) == 0.0

    def test_gaming_detection_too_perfect(self):
        features = {k: 0.99 for k in FEATURE_WEIGHTS}
        assert PenaltyEngine.gaming_detection(features) == 0.15

    def test_gaming_detection_normal(self):
        features = {
            "loan_reliability": 0.7, "income": 0.6, "income_stability": 0.5,
            "graph_reputation": 0.4, "currency_risk": 0.8, "platform_quality": 0.3,
            "wallet_age": 0.5, "transaction_diversity": 0.4,
            "growth_trend": 0.5, "account_behavior": 0.3,
        }
        assert PenaltyEngine.gaming_detection(features) == 0.0

    def test_penalty_total_capped_at_60_percent(self):
        """Even with maximum penalties, total should not exceed 0.60."""
        data = RawUserData(
            user_created_at=datetime.now(timezone.utc) - timedelta(days=10),
            sybil_info=SybilInfo(verdict="sybil", confidence=1.0),
            transaction_stats=TransactionStats(total_count=10, circular_count=5),
            previous_scores=[300.0, 900.0],
            last_activity_at=datetime.now(timezone.utc) - timedelta(days=365),
        )
        features = {k: 0.99 for k in FEATURE_WEIGHTS}
        penalties = PenaltyEngine.calculate(data, features)
        assert penalties.total <= 0.60


# ═══════════════════════════════════════════════════════════════════
# Score Mapping & Risk Classification
# ═══════════════════════════════════════════════════════════════════


class TestScoreMapping:
    def test_sigmoid_midpoint(self):
        """Raw 0.45 (midpoint) should map to roughly middle of range."""
        score = map_to_score_range(0.45)
        middle = (SCORE_FLOOR + SCORE_CEIL) / 2
        assert abs(score - middle) < 10  # within 10 points of midpoint

    def test_sigmoid_low_raw(self):
        score = map_to_score_range(0.0)
        assert score >= SCORE_FLOOR
        assert score < 400

    def test_sigmoid_high_raw(self):
        score = map_to_score_range(1.0)
        assert score > 900
        assert score <= SCORE_CEIL

    def test_risk_tier_excellent(self):
        assert classify_risk(800) == "low"

    def test_risk_tier_good(self):
        assert classify_risk(650) == "medium"

    def test_risk_tier_fair(self):
        assert classify_risk(500) == "high"

    def test_risk_tier_poor(self):
        assert classify_risk(350) == "critical"

    def test_loan_limit_low_risk(self):
        limit = compute_loan_limit("low", 850)
        assert limit > 0
        assert limit <= 10_000

    def test_loan_limit_critical_is_zero(self):
        assert compute_loan_limit("critical", 350) == 0.0


# ═══════════════════════════════════════════════════════════════════
# End-to-End Engine
# ═══════════════════════════════════════════════════════════════════


class TestCalculateTrustScore:
    def test_cold_start_gets_mid_range_score(self, empty_user_data):
        """A brand-new user with no data should get a reasonable score."""
        result = calculate_trust_score(empty_user_data)
        assert SCORE_FLOOR <= result.score <= SCORE_CEIL
        # Cold start should not get extreme scores
        assert 350 < result.score < 800

    def test_strong_user_gets_high_score(self, strong_user_data):
        result = calculate_trust_score(strong_user_data)
        assert result.score >= 700
        assert result.risk_tier in ("low", "medium")
        assert result.loan_limit > 0

    def test_sybil_user_gets_low_score(self, sybil_user_data):
        result = calculate_trust_score(sybil_user_data)
        assert result.score < 600
        assert result.penalties.sybil > 0
        assert result.penalties.circular_tx > 0

    def test_result_has_all_fields(self, empty_user_data):
        result = calculate_trust_score(empty_user_data)
        assert isinstance(result.score, float)
        assert isinstance(result.risk_tier, str)
        assert isinstance(result.loan_limit, float)
        assert len(result.features) == 10
        assert result.model_version == "v2"

    def test_score_always_in_range(self, empty_user_data, strong_user_data, sybil_user_data):
        for data in [empty_user_data, strong_user_data, sybil_user_data]:
            result = calculate_trust_score(data)
            assert SCORE_FLOOR <= result.score <= SCORE_CEIL
