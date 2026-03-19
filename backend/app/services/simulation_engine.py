"""
Score Simulation Engine
========================
Lightweight, sub-50ms credit score simulator for interactive "what-if" analysis.
Uses simplified heuristic scoring (no ML, no DB) with slight randomness.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

FEATURE_WEIGHTS = {
    "income":             0.22,
    "income_stability":   0.18,
    "wallet_age":         0.15,
    "platform_score":     0.20,
    "repayment_history":  0.25,
}

SCORE_FLOOR = 300
SCORE_CEIL = 1000


@dataclass
class FeatureImpact:
    feature: str
    value: float
    weight: float
    contribution: float
    direction: str


@dataclass
class SimulationResult:
    score: float
    risk_tier: str
    delta: float
    feature_impacts: list[FeatureImpact]
    loan_limit: float
    raw_weighted: float


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _classify(score: float) -> str:
    if score >= 750:
        return "low"
    if score >= 600:
        return "medium"
    if score >= 450:
        return "high"
    return "critical"


def _loan_limit(tier: str, score: float) -> float:
    caps = {"low": 10_000, "medium": 5_000, "high": 1_500, "critical": 0}
    base = caps.get(tier, 0)
    factor = (score - SCORE_FLOOR) / (SCORE_CEIL - SCORE_FLOOR)
    return round(base * factor, 2)


def simulate_credit_score(
    income: float = 0.5,
    income_stability: float = 0.5,
    wallet_age: float = 0.5,
    platform_score: float = 0.5,
    repayment_history: float = 0.5,
    baseline_score: float | None = None,
) -> SimulationResult:
    """
    Simulate a credit score from 5 normalized (0-1) inputs.
    Returns score, delta from baseline, and per-feature impact breakdown.
    """
    features = {
        "income": _clamp(income),
        "income_stability": _clamp(income_stability),
        "wallet_age": _clamp(wallet_age),
        "platform_score": _clamp(platform_score),
        "repayment_history": _clamp(repayment_history),
    }

    raw = sum(features[k] * FEATURE_WEIGHTS[k] for k in FEATURE_WEIGHTS)

    noise = random.uniform(-0.03, 0.03)
    raw_noisy = _clamp(raw + noise)

    transformed = _sigmoid(6.0 * (raw_noisy - 0.45))
    score = round(SCORE_FLOOR + (SCORE_CEIL - SCORE_FLOOR) * transformed, 1)

    tier = _classify(score)
    limit = _loan_limit(tier, score)
    delta = round(score - (baseline_score or 650.0), 1)

    impacts = []
    for feat, val in features.items():
        w = FEATURE_WEIGHTS[feat]
        contrib = round(val * w, 4)
        direction = "positive" if val >= 0.5 else "negative"
        impacts.append(FeatureImpact(
            feature=feat, value=round(val, 3), weight=w,
            contribution=contrib, direction=direction,
        ))

    impacts.sort(key=lambda x: abs(x.contribution), reverse=True)

    return SimulationResult(
        score=score,
        risk_tier=tier,
        delta=delta,
        feature_impacts=impacts,
        loan_limit=limit,
        raw_weighted=round(raw, 4),
    )
