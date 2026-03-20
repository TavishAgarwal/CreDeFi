from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_log import log_admin_action
from app.core.deps import get_current_user, require_admin
from app.db.session import get_session
from app.models.user import User
from app.schemas.graph import (
    GraphComputeResponse,
    GraphRecomputeAllResponse,
    NodeMetricsResponse,
)
from app.services.trust_graph_service import TrustGraphService

router = APIRouter(prefix="/graph", tags=["graph"])


@router.post("/compute", response_model=GraphComputeResponse)
async def compute_graph(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """C3/C4: Now requires authentication. Computes graph for the caller's own account."""
    svc = TrustGraphService(session)
    try:
        node, graph = await svc.compute_for_user(user.id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )

    return GraphComputeResponse(
        user_id=node.node_id,
        reputation_score=node.reputation_score,
        metrics=NodeMetricsResponse(
            node_id=node.node_id,
            pagerank=node.pagerank,
            betweenness_centrality=node.betweenness_centrality,
            closeness_centrality=node.closeness_centrality,
            clustering_coeff=node.clustering_coeff,
            degree_in=node.degree_in,
            degree_out=node.degree_out,
            reciprocity=node.reciprocity,
            edge_diversity=node.edge_diversity,
            community_id=node.community_id,
            reputation_score=node.reputation_score,
        ),
        total_nodes=graph.total_nodes,
        total_edges=graph.total_edges,
        model_version=graph.model_version,
    )


@router.post("/recompute-all", response_model=GraphRecomputeAllResponse)
async def recompute_all(
    user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    """H5: Requires admin role — recomputes the graph for all users."""
    svc = TrustGraphService(session)
    result = await svc.recompute_all()
    log_admin_action("graph_recompute_all", admin_id=str(user.id), detail=f"nodes={result.total_nodes}")
    return GraphRecomputeAllResponse(
        total_nodes=result.total_nodes,
        total_edges=result.total_edges,
        model_version=result.model_version,
    )
