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
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import AccountProvider, IncomeFrequency, RiskTier
from app.models.mixins import TimestampMixin


class ConnectedAccount(TimestampMixin, Base):
    __tablename__ = "connected_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    provider: Mapped[AccountProvider] = mapped_column(nullable=False)
    account_identifier: Mapped[str] = mapped_column(String(256), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    user: Mapped["User"] = relationship(back_populates="connected_accounts")

    def __repr__(self) -> str:
        return f"<ConnectedAccount {self.provider.value}:{self.account_identifier}>"


class IncomeSource(TimestampMixin, Base):
    __tablename__ = "income_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    source_name: Mapped[str] = mapped_column(String(200), nullable=False)
    frequency: Mapped[IncomeFrequency] = mapped_column(nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    monthly_amount: Mapped[float] = mapped_column(
        Numeric(18, 2), nullable=False
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verification_source: Mapped[str | None] = mapped_column(String(200), nullable=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship(back_populates="income_sources")

    def __repr__(self) -> str:
        return f"<IncomeSource {self.source_name} ({self.monthly_amount} {self.currency}/mo)>"


class TrustScore(TimestampMixin, Base):
    __tablename__ = "trust_scores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_tier: Mapped[RiskTier] = mapped_column(nullable=False)

    repayment_component: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    identity_component: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    social_component: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    income_component: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    model_version: Mapped[str] = mapped_column(String(50), nullable=False, default="v1")
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="trust_scores")

    def __repr__(self) -> str:
        return f"<TrustScore user={self.user_id} score={self.score} tier={self.risk_tier.value}>"


from app.models.user import User  # noqa: E402, F401
