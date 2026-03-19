"""
AI Loan Recommendation Engine
===============================
Generates human-readable loan recommendations based on trust score,
income, and stability. Pure computation, no DB access.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LoanRecommendation:
    recommended_amount: float
    recommended_interest: float
    risk_level: str
    reasoning: str
    collateral_ratio: float
    max_term_days: int
    monthly_payment: float
    confidence: str


def recommend_loan(
    score: float = 650.0,
    income: float = 0.5,
    stability: float = 0.5,
) -> LoanRecommendation:
    """Generate a loan recommendation from score + income + stability."""
    if score >= 750:
        risk = "low"
        base_amount = 10_000
        base_rate = 5.0
        collateral = 0.0
        max_term = 365
    elif score >= 600:
        risk = "medium"
        base_amount = 5_000
        base_rate = 12.0
        collateral = 0.50
        max_term = 180
    elif score >= 450:
        risk = "high"
        base_amount = 1_500
        base_rate = 24.0
        collateral = 1.20
        max_term = 90
    else:
        return LoanRecommendation(
            recommended_amount=0,
            recommended_interest=0,
            risk_level="critical",
            reasoning="Your current trust score is below the minimum threshold for lending. "
                      "We recommend connecting more platforms and building your repayment history.",
            collateral_ratio=0,
            max_term_days=0,
            monthly_payment=0,
            confidence="low",
        )

    income_mult = 0.5 + income * 1.0
    amount = round(base_amount * income_mult, -2)

    stability_adj = (1.0 - stability) * 5.0
    interest = round(base_rate + stability_adj, 2)

    monthly = round(amount * (1 + interest / 100 * (max_term / 365)) / max(max_term / 30, 1), 2)

    reasons = []
    if score >= 750:
        reasons.append(f"Your trust score of {score:.0f} qualifies you for our best rates")
    elif score >= 600:
        reasons.append(f"Your trust score of {score:.0f} places you in the standard lending tier")
    else:
        reasons.append(f"Your trust score of {score:.0f} qualifies you for a limited loan")

    if income >= 0.7:
        reasons.append("Strong income supports a higher loan amount")
    elif income < 0.3:
        reasons.append("Consider increasing verified income sources for better terms")

    if stability >= 0.7:
        reasons.append("Consistent payment patterns earned you a lower interest rate")
    elif stability < 0.3:
        reasons.append("Improving payment consistency could reduce your interest rate by up to 5%")
        interest = min(interest + 2, 30)

    if collateral > 0:
        reasons.append(f"A {collateral*100:.0f}% collateral deposit is required for this risk tier")
    else:
        reasons.append("No collateral required at this trust level")

    confidence = "high" if score >= 700 and income >= 0.5 else "medium" if score >= 500 else "low"

    return LoanRecommendation(
        recommended_amount=amount,
        recommended_interest=interest,
        risk_level=risk,
        reasoning=". ".join(reasons) + ".",
        collateral_ratio=collateral,
        max_term_days=max_term,
        monthly_payment=monthly,
        confidence=confidence,
    )
