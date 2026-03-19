"""
Graph Visualization Engine
============================
Builds user relationship graphs from transactions/guarantees for
frontend visualization. Returns nodes + edges + suspicious clusters.
Designed for demo speed — works from in-memory mock data when no DB.
"""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field


@dataclass
class GraphNode:
    id: str
    label: str
    score: float
    risk: str
    is_suspicious: bool = False
    cluster_id: int | None = None


@dataclass
class GraphEdge:
    source: str
    target: str
    weight: float = 1.0
    edge_type: str = "trust"


@dataclass
class SuspiciousCluster:
    cluster_id: int
    node_ids: list[str]
    reason: str
    severity: str


@dataclass
class GraphData:
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    clusters: list[SuspiciousCluster]
    total_nodes: int
    total_edges: int


def _risk_from_score(s: float) -> str:
    if s >= 750:
        return "low"
    if s >= 600:
        return "medium"
    if s >= 450:
        return "high"
    return "critical"


def generate_demo_graph(user_id: str | None = None) -> GraphData:
    """Generate a realistic demo trust graph with suspicious clusters."""
    rng = random.Random(42)

    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []

    main_users = [
        ("user_main", "You", 847, None),
        ("user_alex", "Alex M.", 762, None),
        ("user_priya", "Priya S.", 691, None),
        ("user_james", "James T.", 823, None),
        ("user_sarah", "Sarah K.", 580, None),
        ("user_dev", "Dev R.", 715, None),
        ("user_lisa", "Lisa N.", 890, None),
        ("user_mark", "Mark C.", 650, None),
        ("user_anna", "Anna W.", 720, None),
        ("user_tom", "Tom B.", 800, None),
    ]

    for uid, label, score, _ in main_users:
        nodes.append(GraphNode(
            id=uid, label=label, score=float(score),
            risk=_risk_from_score(score),
        ))

    trust_edges = [
        ("user_main", "user_alex"), ("user_main", "user_priya"),
        ("user_main", "user_lisa"), ("user_alex", "user_james"),
        ("user_alex", "user_dev"), ("user_priya", "user_sarah"),
        ("user_james", "user_lisa"), ("user_james", "user_tom"),
        ("user_dev", "user_mark"), ("user_lisa", "user_anna"),
        ("user_mark", "user_anna"), ("user_tom", "user_dev"),
        ("user_sarah", "user_mark"), ("user_anna", "user_tom"),
    ]
    for src, tgt in trust_edges:
        edges.append(GraphEdge(
            source=src, target=tgt,
            weight=round(rng.uniform(0.5, 1.0), 2), edge_type="trust",
        ))

    sybil_ids = []
    for i in range(4):
        sid = f"sybil_{i}"
        score = rng.uniform(300, 450)
        sybil_ids.append(sid)
        nodes.append(GraphNode(
            id=sid, label=f"Sybil-{i+1}", score=round(score, 1),
            risk="critical", is_suspicious=True, cluster_id=1,
        ))

    for i, s1 in enumerate(sybil_ids):
        for s2 in sybil_ids[i+1:]:
            edges.append(GraphEdge(
                source=s1, target=s2, weight=0.95, edge_type="suspicious",
            ))

    edges.append(GraphEdge(source="user_sarah", target="sybil_0", weight=0.3, edge_type="transaction"))

    low_ids = []
    for i in range(3):
        lid = f"low_trust_{i}"
        score = rng.uniform(400, 520)
        low_ids.append(lid)
        nodes.append(GraphNode(
            id=lid, label=f"Risky-{i+1}", score=round(score, 1),
            risk="high", is_suspicious=True, cluster_id=2,
        ))
    for i, l1 in enumerate(low_ids):
        for l2 in low_ids[i+1:]:
            edges.append(GraphEdge(
                source=l1, target=l2, weight=0.8, edge_type="suspicious",
            ))
    edges.append(GraphEdge(source="user_mark", target="low_trust_0", weight=0.4, edge_type="transaction"))

    clusters = [
        SuspiciousCluster(
            cluster_id=1, node_ids=sybil_ids,
            reason="Shared funding source and identical transaction patterns",
            severity="critical",
        ),
        SuspiciousCluster(
            cluster_id=2, node_ids=low_ids,
            reason="Unusually dense connections with similar low trust scores",
            severity="high",
        ),
    ]

    return GraphData(
        nodes=nodes, edges=edges, clusters=clusters,
        total_nodes=len(nodes), total_edges=len(edges),
    )
