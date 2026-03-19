import uuid

from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class TrustGraphEdge(TimestampMixin, Base):
    """Directed edge in the social trust graph: source_user trusts target_user."""
    __tablename__ = "trust_graph_edges"
    __table_args__ = (
        UniqueConstraint("source_user_id", "target_user_id", name="uq_trust_edge"),
        Index("ix_trust_graph_target", "target_user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    target_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    edge_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="trust"
    )
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    source_user: Mapped["User"] = relationship(foreign_keys=[source_user_id])
    target_user: Mapped["User"] = relationship(foreign_keys=[target_user_id])

    def __repr__(self) -> str:
        return f"<TrustGraphEdge {self.source_user_id}->{self.target_user_id} w={self.weight}>"


class GraphFeatureVector(TimestampMixin, Base):
    """Pre-computed graph-level features per user (PageRank, centrality, etc.)."""
    __tablename__ = "graph_feature_vectors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    pagerank: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    betweenness_centrality: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    closeness_centrality: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    degree_in: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    degree_out: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    clustering_coeff: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    community_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(
        ARRAY(Float), nullable=True
    )
    model_version: Mapped[str] = mapped_column(String(50), nullable=False, default="v1")

    user: Mapped["User"] = relationship(back_populates="graph_features")

    def __repr__(self) -> str:
        return f"<GraphFeatureVector user={self.user_id} pr={self.pagerank:.4f}>"


from app.models.user import User  # noqa: E402, F401
