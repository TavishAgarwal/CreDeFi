import uuid

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(320), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(1024), nullable=False)
    wallet_address: Mapped[str | None] = mapped_column(
        String(44), unique=True, index=True, nullable=True
    )
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # --- relationships ---
    connected_accounts: Mapped[list["ConnectedAccount"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    income_sources: Mapped[list["IncomeSource"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    trust_scores: Mapped[list["TrustScore"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    loan_requests: Mapped[list["LoanRequest"]] = relationship(
        back_populates="borrower", foreign_keys="LoanRequest.borrower_id",
        cascade="all, delete-orphan", lazy="selectin",
    )
    sybil_analyses: Mapped[list["SybilAnalysis"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    graph_features: Mapped[list["GraphFeatureVector"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    github_metrics: Mapped[list["GitHubMetrics"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    wallet_metrics: Mapped[list["WalletMetrics"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"


# Resolve forward refs at import time
from app.models.core import ConnectedAccount, IncomeSource, TrustScore  # noqa: E402, F401
from app.models.loan import LoanRequest  # noqa: E402, F401
from app.models.sybil import SybilAnalysis  # noqa: E402, F401
from app.models.graph import GraphFeatureVector  # noqa: E402, F401
from app.models.integrations import GitHubMetrics, WalletMetrics  # noqa: E402, F401
