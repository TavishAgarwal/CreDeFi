"""
Risk Mitigation Models
=======================
Tables for default tracking, reputation slashing, identity linking,
and social guarantees.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class DefaultEvent(TimestampMixin, Base):
    """Records every loan default with severity and on-chain context."""
    __tablename__ = "default_events"
    __table_args__ = (
        Index("ix_default_events_user", "borrower_id"),
        Index("ix_default_events_contract", "contract_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    borrower_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("loan_contracts.id", ondelete="CASCADE"),
        nullable=False,
    )
    principal_owed: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    interest_owed: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    missed_installments: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    days_overdue: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False, default="standard"
    )
    on_chain_tx_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    on_chain_block: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    borrower: Mapped["User"] = relationship(foreign_keys=[borrower_id])

    def __repr__(self) -> str:
        return f"<DefaultEvent borrower={self.borrower_id} severity={self.severity}>"


class ReputationPenalty(TimestampMixin, Base):
    """Tracks every reputation slash applied to a user."""
    __tablename__ = "reputation_penalties"
    __table_args__ = (
        Index("ix_rep_penalties_user", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(String(100), nullable=False)
    score_before: Mapped[float] = mapped_column(Float, nullable=False)
    score_after: Mapped[float] = mapped_column(Float, nullable=False)
    penalty_points: Mapped[float] = mapped_column(Float, nullable=False)
    source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    source_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="default"
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user: Mapped["User"] = relationship(foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<ReputationPenalty user={self.user_id} -{self.penalty_points}pts>"


class IdentityLink(TimestampMixin, Base):
    """
    Links a user to verified identity sources (GitHub, email, wallet).
    The combination of all links produces an identity confidence score.
    """
    __tablename__ = "identity_links"
    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_identity_link"),
        Index("ix_identity_links_user", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    identifier: Mapped[str] = mapped_column(String(320), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verification_method: Mapped[str | None] = mapped_column(String(100), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    confidence_weight: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    user: Mapped["User"] = relationship(foreign_keys=[user_id])

    def __repr__(self) -> str:
        v = "V" if self.is_verified else "?"
        return f"<IdentityLink {self.provider}:{self.identifier} [{v}]>"


class SocialGuarantee(TimestampMixin, Base):
    """
    A user (guarantor) vouches for another user (borrower).
    If the borrower defaults, the guarantor's reputation is slashed.
    """
    __tablename__ = "social_guarantees"
    __table_args__ = (
        UniqueConstraint(
            "guarantor_id", "borrower_id", "contract_id",
            name="uq_social_guarantee",
        ),
        Index("ix_social_guarantees_borrower", "borrower_id"),
        Index("ix_social_guarantees_guarantor", "guarantor_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    guarantor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    borrower_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    contract_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("loan_contracts.id", ondelete="SET NULL"),
        nullable=True,
    )
    stake_amount: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    slashed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    slashed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    vouch_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    guarantor: Mapped["User"] = relationship(foreign_keys=[guarantor_id])
    borrower: Mapped["User"] = relationship(foreign_keys=[borrower_id])

    def __repr__(self) -> str:
        return f"<SocialGuarantee {self.guarantor_id} vouches for {self.borrower_id}>"


class RepaymentBehavior(TimestampMixin, Base):
    """
    Aggregate repayment statistics per user, updated after every payment event.
    Used as a fast-lookup cache for the risk engine.
    """
    __tablename__ = "repayment_behaviors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True,
    )
    total_loans: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    loans_repaid: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    loans_defaulted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    loans_active: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_installments: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    on_time_payments: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    late_payments: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    missed_payments: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_borrowed: Mapped[float] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    total_repaid: Mapped[float] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    avg_days_to_repay: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    longest_streak_on_time: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_streak_on_time: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    default_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_default_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reliability_score: Mapped[float] = mapped_column(
        Float, default=0.5, nullable=False
    )

    user: Mapped["User"] = relationship(foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<RepaymentBehavior user={self.user_id} reliability={self.reliability_score:.2f}>"


from app.models.user import User  # noqa: E402, F401
