import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import (
    LoanStatus,
    RepaymentStatus,
    RiskTier,
    TransactionStatus,
    TransactionType,
)
from app.models.mixins import TimestampMixin


class LoanRequest(TimestampMixin, Base):
    __tablename__ = "loan_requests"
    __table_args__ = (
        Index("ix_loan_requests_status", "status"),
        Index("ix_loan_requests_borrower_status", "borrower_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    borrower_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    amount_requested: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    term_days: Mapped[int] = mapped_column(Integer, nullable=False)
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[LoanStatus] = mapped_column(
        nullable=False, default=LoanStatus.PENDING
    )
    risk_tier_at_request: Mapped[RiskTier | None] = mapped_column(nullable=True)
    trust_score_at_request: Mapped[float | None] = mapped_column(Float, nullable=True)

    borrower: Mapped["User"] = relationship(
        back_populates="loan_requests", foreign_keys=[borrower_id]
    )
    contract: Mapped["LoanContract | None"] = relationship(
        back_populates="loan_request", uselist=False, lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<LoanRequest {self.id} {self.amount_requested} {self.currency} [{self.status.value}]>"


class LoanContract(TimestampMixin, Base):
    __tablename__ = "loan_contracts"
    __table_args__ = (
        Index("ix_loan_contracts_status", "status"),
        Index("ix_loan_contracts_maturity", "maturity_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    loan_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("loan_requests.id", ondelete="CASCADE"),
        unique=True, nullable=False,
    )
    lender_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    principal: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    interest_rate_bps: Mapped[int] = mapped_column(Integer, nullable=False)
    term_days: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[LoanStatus] = mapped_column(
        nullable=False, default=LoanStatus.ACTIVE
    )

    collateral_currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    collateral_amount: Mapped[float | None] = mapped_column(Numeric(18, 8), nullable=True)
    collateral_tx_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)

    disbursed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    maturity_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    on_chain_address: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    loan_request: Mapped["LoanRequest"] = relationship(back_populates="contract")
    lender: Mapped["User | None"] = relationship(foreign_keys=[lender_id])
    repayments: Mapped[list["Repayment"]] = relationship(
        back_populates="contract", cascade="all, delete-orphan", lazy="selectin"
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="contract", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<LoanContract {self.id} principal={self.principal} [{self.status.value}]>"


class Repayment(TimestampMixin, Base):
    __tablename__ = "repayments"
    __table_args__ = (
        Index("ix_repayments_contract_status", "contract_id", "status"),
        Index("ix_repayments_due", "due_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("loan_contracts.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    installment_number: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    amount_due: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    amount_paid: Mapped[float] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[RepaymentStatus] = mapped_column(
        nullable=False, default=RepaymentStatus.SCHEDULED
    )

    contract: Mapped["LoanContract"] = relationship(back_populates="repayments")

    def __repr__(self) -> str:
        return f"<Repayment #{self.installment_number} {self.amount_due} [{self.status.value}]>"


class Transaction(TimestampMixin, Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_contract", "contract_id"),
        Index("ix_transactions_type_status", "tx_type", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("loan_contracts.id", ondelete="CASCADE"),
        nullable=False,
    )
    tx_type: Mapped[TransactionType] = mapped_column(nullable=False)
    status: Mapped[TransactionStatus] = mapped_column(
        nullable=False, default=TransactionStatus.PENDING
    )
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    tx_hash: Mapped[str | None] = mapped_column(
        String(128), unique=True, nullable=True, index=True
    )
    chain: Mapped[str | None] = mapped_column(String(50), nullable=True)
    from_address: Mapped[str | None] = mapped_column(String(128), nullable=True)
    to_address: Mapped[str | None] = mapped_column(String(128), nullable=True)
    block_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    contract: Mapped["LoanContract"] = relationship(back_populates="transactions")

    def __repr__(self) -> str:
        return f"<Transaction {self.tx_type.value} {self.amount} [{self.status.value}]>"


from app.models.user import User  # noqa: E402, F401
