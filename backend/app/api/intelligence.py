"""
AI Credit Intelligence API
============================
Demo-ready endpoints for:
  - Score simulation (POST /simulate-score)
  - Loan recommendation (POST /loan/recommend)
  - Graph visualization (GET /graph/user/{id}, GET /graph/suspicious-clusters)
  - Dashboard with risk alerts (GET /dashboard)
  - Enhanced breakdown with suggestions

All endpoints work in demo mode (no DB required) with realistic mock data.
"""

from __future__ import annotations

import asyncio
import random

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.services.graph_viz_engine import generate_demo_graph
from app.services.loan_recommender import recommend_loan
from app.services.risk_alerts import generate_alerts
from app.services.simulation_engine import simulate_credit_score

router = APIRouter(tags=["intelligence"])


# ═══════════════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════════════

class SimulateRequest(BaseModel):
    income: float = Field(0.5, ge=0, le=1)
    income_stability: float = Field(0.5, ge=0, le=1)
    wallet_age: float = Field(0.5, ge=0, le=1)
    platform_score: float = Field(0.5, ge=0, le=1)
    repayment_history: float = Field(0.5, ge=0, le=1)
    baseline_score: float | None = None


class FeatureImpactResponse(BaseModel):
    feature: str
    value: float
    weight: float
    contribution: float
    direction: str


class SimulateResponse(BaseModel):
    score: float
    risk_tier: str
    delta: float
    feature_impacts: list[FeatureImpactResponse]
    loan_limit: float
    raw_weighted: float


class RecommendRequest(BaseModel):
    score: float = Field(650, ge=300, le=1000)
    income: float = Field(0.5, ge=0, le=1)
    stability: float = Field(0.5, ge=0, le=1)


class RecommendResponse(BaseModel):
    recommended_amount: float
    recommended_interest: float
    risk_level: str
    reasoning: str
    collateral_ratio: float
    max_term_days: int
    monthly_payment: float
    confidence: str


class GraphNodeResponse(BaseModel):
    id: str
    label: str
    score: float
    risk: str
    is_suspicious: bool
    cluster_id: int | None


class GraphEdgeResponse(BaseModel):
    source: str
    target: str
    weight: float
    edge_type: str


class ClusterResponse(BaseModel):
    cluster_id: int
    node_ids: list[str]
    reason: str
    severity: str


class GraphResponse(BaseModel):
    nodes: list[GraphNodeResponse]
    edges: list[GraphEdgeResponse]
    clusters: list[ClusterResponse]
    total_nodes: int
    total_edges: int


class AlertResponse(BaseModel):
    severity: str
    title: str
    message: str
    category: str
    action: str | None


class SuggestionResponse(BaseModel):
    text: str
    impact: str
    category: str


class DashboardResponse(BaseModel):
    score: float
    risk_tier: str
    loan_limit: float
    alerts: list[AlertResponse]
    suggestions: list[SuggestionResponse]
    positive_factors: list[str]
    negative_factors: list[str]
    feature_breakdown: list[FeatureImpactResponse]


# ═══════════════════════════════════════════════════════════════════
# POST /simulate-score
# ═══════════════════════════════════════════════════════════════════

@router.post("/simulate-score", response_model=SimulateResponse)
async def simulate_score(body: SimulateRequest):
    """Simulate a credit score from feature inputs. Responds in <50ms."""
    result = simulate_credit_score(
        income=body.income,
        income_stability=body.income_stability,
        wallet_age=body.wallet_age,
        platform_score=body.platform_score,
        repayment_history=body.repayment_history,
        baseline_score=body.baseline_score,
    )
    return SimulateResponse(
        score=result.score,
        risk_tier=result.risk_tier,
        delta=result.delta,
        feature_impacts=[
            FeatureImpactResponse(
                feature=f.feature, value=f.value, weight=f.weight,
                contribution=f.contribution, direction=f.direction,
            ) for f in result.feature_impacts
        ],
        loan_limit=result.loan_limit,
        raw_weighted=result.raw_weighted,
    )


# ═══════════════════════════════════════════════════════════════════
# POST /loan/recommend
# ═══════════════════════════════════════════════════════════════════

@router.post("/loan/recommend", response_model=RecommendResponse)
async def loan_recommend(body: RecommendRequest):
    """AI-powered loan recommendation based on score + income + stability."""
    result = recommend_loan(
        score=body.score, income=body.income, stability=body.stability,
    )
    return RecommendResponse(
        recommended_amount=result.recommended_amount,
        recommended_interest=result.recommended_interest,
        risk_level=result.risk_level,
        reasoning=result.reasoning,
        collateral_ratio=result.collateral_ratio,
        max_term_days=result.max_term_days,
        monthly_payment=result.monthly_payment,
        confidence=result.confidence,
    )


# ═══════════════════════════════════════════════════════════════════
# GET /graph/user/{user_id}
# ═══════════════════════════════════════════════════════════════════

@router.get("/graph/user/{user_id}", response_model=GraphResponse)
async def get_user_graph(user_id: str):
    """Get the trust graph centered on a user (demo data)."""
    await asyncio.sleep(random.uniform(0.1, 0.3))
    data = generate_demo_graph(user_id)
    return GraphResponse(
        nodes=[GraphNodeResponse(
            id=n.id, label=n.label, score=n.score, risk=n.risk,
            is_suspicious=n.is_suspicious, cluster_id=n.cluster_id,
        ) for n in data.nodes],
        edges=[GraphEdgeResponse(
            source=e.source, target=e.target, weight=e.weight, edge_type=e.edge_type,
        ) for e in data.edges],
        clusters=[ClusterResponse(
            cluster_id=c.cluster_id, node_ids=c.node_ids,
            reason=c.reason, severity=c.severity,
        ) for c in data.clusters],
        total_nodes=data.total_nodes,
        total_edges=data.total_edges,
    )


# ═══════════════════════════════════════════════════════════════════
# GET /graph/suspicious-clusters
# ═══════════════════════════════════════════════════════════════════

@router.get("/graph/suspicious-clusters", response_model=list[ClusterResponse])
async def get_suspicious_clusters():
    """Get all detected suspicious clusters."""
    data = generate_demo_graph()
    return [ClusterResponse(
        cluster_id=c.cluster_id, node_ids=c.node_ids,
        reason=c.reason, severity=c.severity,
    ) for c in data.clusters]


# ═══════════════════════════════════════════════════════════════════
# GET /dashboard
# ═══════════════════════════════════════════════════════════════════

@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    score: float = Query(default=782),
    income: float = Query(default=0.7),
    stability: float = Query(default=0.8),
    wallet_age: float = Query(default=0.6),
    platforms: int = Query(default=3),
):
    """Full dashboard data with risk alerts, suggestions, and breakdown."""
    await asyncio.sleep(random.uniform(0.15, 0.35))

    sim = simulate_credit_score(
        income=income, income_stability=stability,
        wallet_age=wallet_age, platform_score=min(platforms / 6, 1.0),
        repayment_history=0.85,
    )

    alerts = generate_alerts(
        score=sim.score, income=income, income_stability=stability,
        wallet_age=wallet_age, platform_count=platforms,
    )

    positive = []
    negative = []
    for f in sim.feature_impacts:
        label = f.feature.replace("_", " ").title()
        if f.value >= 0.6:
            positive.append(f"{label}: Strong ({f.value:.0%})")
        elif f.value < 0.4:
            negative.append(f"{label}: Needs improvement ({f.value:.0%})")

    suggestions = _generate_suggestions(sim.score, income, stability, wallet_age, platforms)

    return DashboardResponse(
        score=sim.score,
        risk_tier=sim.risk_tier,
        loan_limit=sim.loan_limit,
        alerts=[AlertResponse(
            severity=a.severity, title=a.title, message=a.message,
            category=a.category, action=a.action,
        ) for a in alerts],
        suggestions=suggestions,
        positive_factors=positive,
        negative_factors=negative,
        feature_breakdown=[
            FeatureImpactResponse(
                feature=f.feature, value=f.value, weight=f.weight,
                contribution=f.contribution, direction=f.direction,
            ) for f in sim.feature_impacts
        ],
    )


def _generate_suggestions(
    score: float, income: float, stability: float,
    wallet_age: float, platforms: int,
) -> list[SuggestionResponse]:
    suggestions = []

    if stability < 0.6:
        suggestions.append(SuggestionResponse(
            text="Increase income stability by maintaining consistent monthly earnings",
            impact="high", category="income",
        ))
    if platforms < 3:
        suggestions.append(SuggestionResponse(
            text="Connect more verified platforms (GitHub, Stripe) to boost your score",
            impact="high", category="identity",
        ))
    if income < 0.5:
        suggestions.append(SuggestionResponse(
            text="Verify more income sources to increase your borrowing capacity",
            impact="medium", category="income",
        ))
    if wallet_age < 0.4:
        suggestions.append(SuggestionResponse(
            text="Your wallet is young — continue using it regularly to build trust",
            impact="medium", category="wallet",
        ))
    if score < 700:
        suggestions.append(SuggestionResponse(
            text="Make all loan repayments on time to steadily improve your score",
            impact="high", category="repayment",
        ))
    if score >= 700 and not suggestions:
        suggestions.append(SuggestionResponse(
            text="Your profile is strong! Consider vouching for trusted peers to build social capital",
            impact="low", category="social",
        ))

    return suggestions
