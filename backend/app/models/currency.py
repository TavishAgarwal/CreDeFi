import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class ExchangeRate(TimestampMixin, Base):
    __tablename__ = "exchange_rates"
    __table_args__ = (
        UniqueConstraint(
            "base_currency", "quote_currency", "fetched_at",
            name="uq_exchange_rate_pair_time",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    base_currency: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    quote_currency: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    rate: Mapped[float] = mapped_column(Numeric(24, 12), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    def __repr__(self) -> str:
        return f"<ExchangeRate {self.base_currency}/{self.quote_currency} = {self.rate}>"


class CurrencyConfig(TimestampMixin, Base):
    __tablename__ = "currency_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(
        String(10), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False)
    decimals: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    is_fiat: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    chain: Mapped[str | None] = mapped_column(String(50), nullable=True)
    contract_address: Mapped[str | None] = mapped_column(String(128), nullable=True)
    min_loan_amount: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    max_loan_amount: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)

    def __repr__(self) -> str:
        return f"<CurrencyConfig {self.code} ({self.name})>"
