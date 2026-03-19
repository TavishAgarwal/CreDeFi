"""
CreDeFi AI Trust Scoring Engine
================================
Pure-computation module — no DB access, no I/O.

Pipeline:
  RawUserData -> FeatureExtractor (10 normalised 0-1 signals)
              -> WeightedScorer   (dot product with report weights)
              -> PenaltyEngine    (anti-fraud deductions)
              -> sigmoid mapping  (300–1000 range)
              -> risk tier + loan limit
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

import numpy as np

# ═══════════════════════════════════════════════════════════════════════
# Constants — exact weights from the CreDeFi report
# ═══════════════════════════════════════════════════════════════════════

FEATURE_WEIGHTS: dict[str, float] = {
    "loan_reliability":      0.16,
    "income":                0.13,
    "income_stability":      0.12,
    "graph_reputation":      0.12,
    "currency_risk":         0.12,
    "platform_quality":      0.10,
    "wallet_age":            0.08,
    "transaction_diversity": 0.06,
    "growth_trend":          0.06,
    "account_behavior":      0.05,
}
assert abs(sum(FEATURE_WEIGHTS.values()) - 1.0) < 1e-9

SCORE_FLOOR = 300
SCORE_CEIL = 1000
SIGMOID_K = 6.0           # steepness of sigmoid
SIGMOID_MIDPOINT = 0.45   # raw score where sigmoid output ≈ 0.5

INCOME_LOG_CAP = 50_000   # monthly income saturation point (USD)
UNVERIFIED_INCOME_PENALTY = 0.40
WALLET_AGE_CAP_DAYS = 730  # 2 years to reach max wallet age signal

PLATFORM_QUALITY: dict[str, float] = {
    "bank":     1.0,
    "stripe":   0.90,
    "paypal":   0.80,
    "mpesa":    0.70,
    "metamask": 0.55,
    "phantom":  0.50,
}

CURRENCY_RISK: dict[str, float] = {
    "USD":  1.00,
    "USDC": 0.98,
    "USDT": 0.95,
    "KES":  0.80,
    "ETH":  0.55,
    "SOL":  0.50,
}
DEFAULT_CURRENCY_RISK = 0.40

FREQUENCY_STABILITY: dict[str, float] = {
    "monthly":  1.00,
    "biweekly": 0.85,
    "weekly":   0.70,
    "daily":    0.55,
    "irregular": 0.30,
}

# Loan-limit tiers keyed by risk tier
LOAN_LIMIT_BY_TIER: dict[str, float] = {
    "low":      10_000.0,
    "medium":    5_000.0,
    "high":      1_500.0,
    "critical":    0.0,
}


# ═══════════════════════════════════════════════════════════════════════
# Data Transfer Objects — everything the engine needs from the DB layer
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class IncomeRecord:
    monthly_amount: float
    currency: str
    frequency: str       # IncomeFrequency value
    is_verified: bool


@dataclass
class LoanHistory:
    total_contracts: int = 0
    repaid_count: int = 0
    defaulted_count: int = 0
    active_count: int = 0
    on_time_repayments: int = 0
    late_repayments: int = 0
    missed_repayments: int = 0
    total_repayments: int = 0


@dataclass
class TransactionStats:
    total_count: int = 0
    unique_types: int = 0
    unique_chains: int = 0
    unique_counterparties: int = 0
    circular_count: int = 0            # from == to (anti-fraud)


@dataclass
class GraphMetrics:
    pagerank: float = 0.0
    betweenness_centrality: float = 0.0
    closeness_centrality: float = 0.0
    clustering_coeff: float = 0.0
    degree_in: int = 0
    degree_out: int = 0


@dataclass
class SybilInfo:
    verdict: str = "clean"             # SybilVerdict value
    confidence: float = 0.0


@dataclass
class AccountInfo:
    provider: str
    is_verified: bool


@dataclass
class RawUserData:
    """Everything the engine needs, pre-fetched by the service layer."""
    user_created_at: datetime
    wallet_address: str | None = None
    income_sources: list[IncomeRecord] = field(default_factory=list)
    loan_history: LoanHistory = field(default_factory=LoanHistory)
    transaction_stats: TransactionStats = field(default_factory=TransactionStats)
    graph_metrics: GraphMetrics = field(default_factory=GraphMetrics)
    sybil_info: SybilInfo = field(default_factory=SybilInfo)
    connected_accounts: list[AccountInfo] = field(default_factory=list)
    primary_currency: str = "USD"
    previous_scores: list[float] = field(default_factory=list)
    last_activity_at: datetime | None = None


# ═══════════════════════════════════════════════════════════════════════
# Feature extraction — each returns a normalised 0 → 1 signal
# ═══════════════════════════════════════════════════════════════════════

class FeatureExtractor:

    @staticmethod
    def loan_reliability(h: LoanHistory) -> float:
        if h.total_repayments == 0 and h.total_contracts == 0:
            return 0.5  # no history → neutral prior

        repay_ratio = (
            h.on_time_repayments / h.total_repayments
            if h.total_repayments > 0 else 0.5
        )
        default_penalty = min(h.defaulted_count * 0.25, 1.0)
        return float(np.clip(repay_ratio - default_penalty, 0.0, 1.0))

    @staticmethod
    def income(sources: list[IncomeRecord]) -> float:
        if not sources:
            return 0.0
        total = sum(s.monthly_amount for s in sources)
        normalised = math.log1p(total) / math.log1p(INCOME_LOG_CAP)
        normalised = min(normalised, 1.0)

        verified_share = (
            sum(s.monthly_amount for s in sources if s.is_verified) / total
            if total > 0 else 0.0
        )
        penalty = UNVERIFIED_INCOME_PENALTY * (1.0 - verified_share)
        return float(np.clip(normalised - penalty, 0.0, 1.0))

    @staticmethod
    def income_stability(sources: list[IncomeRecord]) -> float:
        if not sources:
            return 0.0
        scores = [
            FREQUENCY_STABILITY.get(s.frequency, 0.3) for s in sources
        ]
        weights = [s.monthly_amount for s in sources]
        total_w = sum(weights)
        if total_w == 0:
            return 0.0
        return float(np.clip(
            sum(s * w for s, w in zip(scores, weights)) / total_w, 0.0, 1.0
        ))

    @staticmethod
    def graph_reputation(g: GraphMetrics) -> float:
        pr_norm = min(g.pagerank / 0.01, 1.0)       # 0.01 ≈ high pagerank
        cc_norm = g.clustering_coeff                  # already 0-1
        bc_norm = min(g.betweenness_centrality / 0.05, 1.0)
        degree_norm = min((g.degree_in + g.degree_out) / 50, 1.0)
        return float(np.clip(
            0.35 * pr_norm + 0.25 * cc_norm + 0.20 * bc_norm + 0.20 * degree_norm,
            0.0, 1.0,
        ))

    @staticmethod
    def currency_risk(primary_currency: str) -> float:
        return CURRENCY_RISK.get(primary_currency, DEFAULT_CURRENCY_RISK)

    @staticmethod
    def platform_quality(accounts: list[AccountInfo]) -> float:
        if not accounts:
            return 0.0
        scores = []
        for a in accounts:
            base = PLATFORM_QUALITY.get(a.provider, 0.40)
            if a.is_verified:
                scores.append(base)
            else:
                scores.append(base * 0.5)
        return float(np.clip(max(scores), 0.0, 1.0))

    @staticmethod
    def wallet_age(user_created_at: datetime) -> float:
        age_days = (datetime.now(timezone.utc) - user_created_at).days
        return float(np.clip(age_days / WALLET_AGE_CAP_DAYS, 0.0, 1.0))

    @staticmethod
    def transaction_diversity(ts: TransactionStats) -> float:
        if ts.total_count == 0:
            return 0.0
        type_score = min(ts.unique_types / 4, 1.0)
        chain_score = min(ts.unique_chains / 3, 1.0) if ts.unique_chains > 0 else 0.0
        cparty_score = min(ts.unique_counterparties / 10, 1.0)
        return float(np.clip(
            0.40 * type_score + 0.30 * chain_score + 0.30 * cparty_score,
            0.0, 1.0,
        ))

    @staticmethod
    def growth_trend(previous_scores: list[float]) -> float:
        if len(previous_scores) < 2:
            return 0.5  # neutral when insufficient history
        recent = previous_scores[-3:]
        diffs = [recent[i + 1] - recent[i] for i in range(len(recent) - 1)]
        avg_diff = sum(diffs) / len(diffs)
        normalised = (avg_diff / SCORE_CEIL) * 10.0  # scale small deltas
        return float(np.clip(0.5 + normalised, 0.0, 1.0))

    @staticmethod
    def account_behavior(accounts: list[AccountInfo]) -> float:
        if not accounts:
            return 0.0
        n = len(accounts)
        verified_ratio = sum(1 for a in accounts if a.is_verified) / n
        diversity = min(n / 4, 1.0)
        return float(np.clip(0.60 * verified_ratio + 0.40 * diversity, 0.0, 1.0))

    @classmethod
    def extract_all(cls, data: RawUserData) -> dict[str, float]:
        return {
            "loan_reliability":      cls.loan_reliability(data.loan_history),
            "income":                cls.income(data.income_sources),
            "income_stability":      cls.income_stability(data.income_sources),
            "graph_reputation":      cls.graph_reputation(data.graph_metrics),
            "currency_risk":         cls.currency_risk(data.primary_currency),
            "platform_quality":      cls.platform_quality(data.connected_accounts),
            "wallet_age":            cls.wallet_age(data.user_created_at),
            "transaction_diversity": cls.transaction_diversity(data.transaction_stats),
            "growth_trend":          cls.growth_trend(data.previous_scores),
            "account_behavior":      cls.account_behavior(data.connected_accounts),
        }


# ═══════════════════════════════════════════════════════════════════════
# Anti-fraud penalty engine
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class PenaltyBreakdown:
    circular_tx: float = 0.0
    sybil: float = 0.0
    velocity: float = 0.0
    decay: float = 0.0
    gaming: float = 0.0

    @property
    def total(self) -> float:
        return min(
            self.circular_tx + self.sybil + self.velocity + self.decay + self.gaming,
            0.60,  # cap total penalty at 60 % of raw score
        )


class PenaltyEngine:

    @staticmethod
    def circular_transactions(ts: TransactionStats) -> float:
        if ts.total_count == 0:
            return 0.0
        ratio = ts.circular_count / ts.total_count
        if ratio > 0.30:
            return 0.20
        if ratio > 0.10:
            return 0.10
        return 0.0

    @staticmethod
    def sybil_penalty(info: SybilInfo) -> float:
        if info.verdict == "sybil":
            return 0.35 * info.confidence
        if info.verdict == "suspicious":
            return 0.15 * info.confidence
        return 0.0

    @staticmethod
    def velocity_change(previous_scores: list[float]) -> float:
        """Penalise suspiciously large score jumps between consecutive runs."""
        if len(previous_scores) < 2:
            return 0.0
        last_delta = abs(previous_scores[-1] - previous_scores[-2])
        normalised_jump = last_delta / SCORE_CEIL
        if normalised_jump > 0.25:
            return 0.15
        if normalised_jump > 0.15:
            return 0.08
        return 0.0

    @staticmethod
    def score_decay(last_activity_at: datetime | None) -> float:
        if last_activity_at is None:
            return 0.10
        idle_days = (datetime.now(timezone.utc) - last_activity_at).days
        if idle_days > 180:
            return 0.12
        if idle_days > 90:
            return 0.06
        if idle_days > 30:
            return 0.02
        return 0.0

    @staticmethod
    def gaming_detection(features: dict[str, float]) -> float:
        """
        Detect artificially inflated profiles: if many feature signals are
        suspiciously perfect (>0.95) but the user has minimal history,
        apply a penalty.
        """
        high_signals = sum(1 for v in features.values() if v > 0.95)
        low_signals = sum(1 for v in features.values() if v < 0.15)
        if high_signals >= 7 and low_signals == 0:
            return 0.15  # likely manipulated
        if high_signals >= 5:
            return 0.05
        return 0.0

    @classmethod
    def calculate(
        cls,
        data: RawUserData,
        features: dict[str, float],
    ) -> PenaltyBreakdown:
        return PenaltyBreakdown(
            circular_tx=cls.circular_transactions(data.transaction_stats),
            sybil=cls.sybil_penalty(data.sybil_info),
            velocity=cls.velocity_change(data.previous_scores),
            decay=cls.score_decay(data.last_activity_at),
            gaming=cls.gaming_detection(features),
        )


# ═══════════════════════════════════════════════════════════════════════
# Score mapping & risk classification
# ═══════════════════════════════════════════════════════════════════════

def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def map_to_score_range(raw: float) -> float:
    """Map a 0-1 raw score to the 300–1000 CreDeFi range via sigmoid."""
    transformed = _sigmoid(SIGMOID_K * (raw - SIGMOID_MIDPOINT))
    return round(SCORE_FLOOR + (SCORE_CEIL - SCORE_FLOOR) * transformed, 1)


def classify_risk(score: float) -> str:
    if score >= 750:
        return "low"
    if score >= 600:
        return "medium"
    if score >= 450:
        return "high"
    return "critical"


def compute_loan_limit(risk_tier: str, score: float) -> float:
    base = LOAN_LIMIT_BY_TIER.get(risk_tier, 0.0)
    score_factor = (score - SCORE_FLOOR) / (SCORE_CEIL - SCORE_FLOOR)
    return round(base * score_factor, 2)


# ═══════════════════════════════════════════════════════════════════════
# Top-level engine entry point
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class ScoreResult:
    score: float
    risk_tier: str
    loan_limit: float
    features: dict[str, float]
    penalties: PenaltyBreakdown
    raw_weighted: float
    model_version: str = "v2"


def calculate_trust_score(data: RawUserData) -> ScoreResult:
    features = FeatureExtractor.extract_all(data)

    feature_vec = np.array([features[k] for k in FEATURE_WEIGHTS])
    weight_vec = np.array(list(FEATURE_WEIGHTS.values()))
    raw_weighted = float(np.dot(feature_vec, weight_vec))

    penalties = PenaltyEngine.calculate(data, features)
    penalised = max(raw_weighted - penalties.total, 0.0)

    final_score = map_to_score_range(penalised)
    risk_tier = classify_risk(final_score)
    loan_limit = compute_loan_limit(risk_tier, final_score)

    return ScoreResult(
        score=final_score,
        risk_tier=risk_tier,
        loan_limit=loan_limit,
        features=features,
        penalties=penalties,
        raw_weighted=round(raw_weighted, 4),
    )
