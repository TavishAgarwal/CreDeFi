import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import SybilVerdict
from app.models.mixins import TimestampMixin


class SybilAnalysis(TimestampMixin, Base):
    __tablename__ = "sybil_analyses"
    __table_args__ = (
        Index("ix_sybil_analyses_verdict", "verdict"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    verdict: Mapped[SybilVerdict] = mapped_column(
        nullable=False, default=SybilVerdict.CLEAN
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False, default="v1")
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    features_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    analyzed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship(back_populates="sybil_analyses")
    clusters: Mapped[list["WalletCluster"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", lazy="selectin"
    )
    fingerprints: Mapped[list["SessionFingerprint"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<SybilAnalysis user={self.user_id} verdict={self.verdict.value}>"


class WalletCluster(TimestampMixin, Base):
    __tablename__ = "wallet_clusters"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sybil_analyses.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    cluster_label: Mapped[str] = mapped_column(String(100), nullable=False)
    wallet_addresses: Mapped[list[str]] = mapped_column(
        ARRAY(String(128)), nullable=False
    )
    shared_funding_source: Mapped[str | None] = mapped_column(String(128), nullable=True)
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    num_wallets: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    analysis: Mapped["SybilAnalysis"] = relationship(back_populates="clusters")

    def __repr__(self) -> str:
        return f"<WalletCluster {self.cluster_label} wallets={self.num_wallets}>"


class SessionFingerprint(TimestampMixin, Base):
    __tablename__ = "session_fingerprints"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sybil_analyses.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    ip_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    device_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    browser_fingerprint: Mapped[str | None] = mapped_column(String(256), nullable=True)
    geo_country: Mapped[str | None] = mapped_column(String(3), nullable=True)
    geo_region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    captured_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    analysis: Mapped["SybilAnalysis"] = relationship(back_populates="fingerprints")

    def __repr__(self) -> str:
        return f"<SessionFingerprint ip={self.ip_hash} device={self.device_hash}>"


from app.models.user import User  # noqa: E402, F401
