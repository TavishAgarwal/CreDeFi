"""
Stripe / Income Integration Service
=====================================
- Fetches payment history from Stripe API (balance transactions)
- Calculates monthly income and payment consistency
- Normalizes into IncomeSource table entries
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.models.core import ConnectedAccount, IncomeSource
from app.models.enums import AccountProvider, IncomeFrequency

logger = get_logger(__name__)

STRIPE_API = "https://api.stripe.com/v1"


class StripeService:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def sync_income(self, user_id: uuid.UUID) -> list[IncomeSource]:
        """Fetch Stripe balance transactions and derive monthly income metrics."""
        api_key = await self._get_api_key(user_id)
        if not api_key:
            api_key = settings.STRIPE_SECRET_KEY
        if not api_key:
            logger.warning("No Stripe API key configured for user %s", user_id)
            return []

        transactions = await self._fetch_balance_transactions(api_key)
        if not transactions:
            return []

        monthly_totals = self._aggregate_monthly(transactions)
        frequency = self._detect_frequency(monthly_totals)
        avg_monthly = (
            sum(monthly_totals.values()) / len(monthly_totals)
            if monthly_totals else 0.0
        )

        existing = await self._s.scalar(
            select(IncomeSource).where(
                IncomeSource.user_id == user_id,
                IncomeSource.source_name == "Stripe Payments",
            )
        )

        if existing:
            existing.monthly_amount = round(avg_monthly / 100, 2)  # cents → dollars
            existing.frequency = frequency
            existing.is_verified = True
            existing.verification_source = "stripe_api"
            existing.last_verified_at = datetime.now(timezone.utc)
            await self._s.flush()
            return [existing]

        source = IncomeSource(
            user_id=user_id,
            source_name="Stripe Payments",
            frequency=frequency,
            currency="USD",
            monthly_amount=round(avg_monthly / 100, 2),
            is_verified=True,
            verification_source="stripe_api",
            last_verified_at=datetime.now(timezone.utc),
        )
        self._s.add(source)

        account = await self._s.scalar(
            select(ConnectedAccount).where(
                ConnectedAccount.user_id == user_id,
                ConnectedAccount.provider == AccountProvider.STRIPE,
            )
        )
        if not account:
            account = ConnectedAccount(
                user_id=user_id,
                provider=AccountProvider.STRIPE,
                account_identifier="stripe_connected",
                is_verified=True,
                metadata_json={"tx_count": len(transactions)},
            )
            self._s.add(account)

        await self._s.flush()
        return [source]

    async def _fetch_balance_transactions(self, api_key: str) -> list[dict]:
        """Fetch up to 100 recent balance transactions from Stripe."""
        txs = []
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{STRIPE_API}/balance_transactions",
                params={"limit": 100, "type": "charge"},
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=15.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                txs = data.get("data", [])
            else:
                logger.error("Stripe API error: %s %s", resp.status_code, resp.text[:200])
        return txs

    @staticmethod
    def _aggregate_monthly(transactions: list[dict]) -> dict[str, int]:
        """Group transaction amounts by month. Returns {YYYY-MM: total_cents}."""
        monthly: dict[str, int] = defaultdict(int)
        for tx in transactions:
            ts = tx.get("created", 0)
            amount = tx.get("net", 0)  # net after fees
            if ts and amount > 0:
                dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                key = dt.strftime("%Y-%m")
                monthly[key] += amount
        return dict(monthly)

    @staticmethod
    def _detect_frequency(monthly_totals: dict[str, int]) -> IncomeFrequency:
        """Infer payment frequency based on active months ratio."""
        if not monthly_totals:
            return IncomeFrequency.IRREGULAR

        months_sorted = sorted(monthly_totals.keys())
        if len(months_sorted) >= 6:
            start = datetime.strptime(months_sorted[0], "%Y-%m")
            end = datetime.strptime(months_sorted[-1], "%Y-%m")
            span = (end.year - start.year) * 12 + (end.month - start.month) + 1
            ratio = len(months_sorted) / max(span, 1)
            if ratio >= 0.9:
                return IncomeFrequency.MONTHLY
            if ratio >= 0.6:
                return IncomeFrequency.BIWEEKLY
            return IncomeFrequency.IRREGULAR

        if len(months_sorted) >= 3:
            return IncomeFrequency.MONTHLY
        return IncomeFrequency.IRREGULAR

    async def _get_api_key(self, user_id: uuid.UUID) -> str | None:
        """Check if user has a stored Stripe API key in their connected account."""
        account = await self._s.scalar(
            select(ConnectedAccount).where(
                ConnectedAccount.user_id == user_id,
                ConnectedAccount.provider == AccountProvider.STRIPE,
            )
        )
        if not account or not account.metadata_json:
            return None
        enc = account.metadata_json.get("api_key_enc")
        if not enc:
            return None
        from app.utils.crypto import decrypt_token
        return decrypt_token(enc)
