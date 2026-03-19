"""
Platform-specific metric tables.
Each stores the latest snapshot fetched from an external API.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import SyncStatus
from app.models.mixins import TimestampMixin


class GitHubMetrics(TimestampMixin, Base):
    __tablename__ = "github_metrics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    github_username: Mapped[str] = mapped_column(String(256), nullable=False)
    public_repos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_stars: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_commits_last_year: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    contribution_streak_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    followers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    following: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    account_age_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    top_languages: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    commit_frequency_weekly: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship(back_populates="github_metrics")

    def __repr__(self) -> str:
        return f"<GitHubMetrics {self.github_username} repos={self.public_repos}>"


class WalletMetrics(TimestampMixin, Base):
    __tablename__ = "wallet_metrics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    wallet_address: Mapped[str] = mapped_column(String(44), nullable=False, index=True)
    chain: Mapped[str] = mapped_column(String(20), nullable=False, default="ethereum")
    total_transactions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unique_counterparties: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    wallet_age_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    eth_balance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_token_value_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    nft_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    defi_interactions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    token_balances: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    first_tx_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_tx_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship(back_populates="wallet_metrics")

    def __repr__(self) -> str:
        return f"<WalletMetrics {self.wallet_address} txs={self.total_transactions}>"


class DataSyncLog(TimestampMixin, Base):
    """Tracks sync jobs for audit and retry logic."""
    __tablename__ = "data_sync_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[SyncStatus] = mapped_column(nullable=False, default=SyncStatus.PENDING)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    records_synced: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<DataSyncLog {self.provider} status={self.status.value}>"


from app.models.user import User  # noqa: E402, F401
