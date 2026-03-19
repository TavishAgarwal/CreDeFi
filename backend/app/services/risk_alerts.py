"""
Risk Alerts Service
====================
Generates contextual risk alerts for the dashboard based on
user features. Pure computation, no DB access.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RiskAlert:
    severity: str
    title: str
    message: str
    category: str
    action: str | None = None


def generate_alerts(
    score: float = 650,
    income: float = 0.5,
    income_stability: float = 0.5,
    wallet_age: float = 0.5,
    platform_count: int = 2,
    repayment_ratio: float = 1.0,
    sybil_risk: float = 0.0,
    active_loans: int = 0,
) -> list[RiskAlert]:
    """Generate context-aware risk alerts for the user dashboard."""
    alerts: list[RiskAlert] = []

    if income_stability < 0.3:
        alerts.append(RiskAlert(
            severity="warning",
            title="Income Instability Detected",
            message="Your income pattern shows irregular payments. Consistent monthly income improves your trust score significantly.",
            category="income",
            action="Connect a payment platform like Stripe to verify regular income",
        ))

    if wallet_age < 0.2:
        alerts.append(RiskAlert(
            severity="info",
            title="New Wallet Detected",
            message="Your wallet is relatively new. Wallet age contributes to your trust score — older wallets are seen as more trustworthy.",
            category="wallet",
            action="Continue using your wallet regularly to build history",
        ))

    if platform_count < 2:
        alerts.append(RiskAlert(
            severity="warning",
            title="Limited Platform Connections",
            message="Connecting more verified platforms significantly boosts your score. Each verified platform adds up to 10% to your trust rating.",
            category="identity",
            action="Connect GitHub, Stripe, or other professional platforms",
        ))

    if repayment_ratio < 0.8 and active_loans > 0:
        alerts.append(RiskAlert(
            severity="error",
            title="Repayment Risk",
            message="You have missed or late payments on record. This heavily impacts your trust score and loan eligibility.",
            category="repayment",
            action="Prioritize catching up on overdue payments",
        ))

    if sybil_risk > 0.5:
        alerts.append(RiskAlert(
            severity="error",
            title="Identity Verification Issue",
            message="Our fraud detection system has flagged unusual patterns. This may affect your borrowing ability.",
            category="sybil",
            action="Verify your identity through additional platforms",
        ))

    if score < 450:
        alerts.append(RiskAlert(
            severity="error",
            title="Trust Score Below Threshold",
            message="Your current trust score is too low for loan eligibility. Focus on building your profile before applying.",
            category="score",
            action="Follow the improvement suggestions below",
        ))
    elif score < 600:
        alerts.append(RiskAlert(
            severity="warning",
            title="Limited Loan Access",
            message="Your trust score qualifies you for small loans only. Improving your score unlocks better rates and higher amounts.",
            category="score",
        ))

    if income < 0.2:
        alerts.append(RiskAlert(
            severity="warning",
            title="Low Verified Income",
            message="Low income verification limits your borrowing capacity. Connecting income sources can dramatically improve your profile.",
            category="income",
            action="Link your Stripe or PayPal account for income verification",
        ))

    if active_loans >= 3:
        alerts.append(RiskAlert(
            severity="info",
            title="Maximum Active Loans",
            message="You have reached the maximum number of concurrent loans. Repay existing loans before requesting new ones.",
            category="loans",
        ))

    if not alerts:
        alerts.append(RiskAlert(
            severity="success",
            title="Profile in Good Standing",
            message="No risk issues detected. Your profile is healthy and you have access to all platform features.",
            category="general",
        ))

    alerts.sort(key=lambda a: {"error": 0, "warning": 1, "info": 2, "success": 3}.get(a.severity, 4))

    return alerts
