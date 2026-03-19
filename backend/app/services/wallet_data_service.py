"""
Web3 Wallet Data Service (Alchemy)
====================================
- Fetches transaction history, wallet age, token balances
- Uses Alchemy Enhanced APIs
- Persists into WalletMetrics table
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.models.core import ConnectedAccount
from app.models.enums import AccountProvider
from app.models.integrations import WalletMetrics

logger = get_logger(__name__)


def _alchemy_url() -> str:
    return f"https://{settings.ALCHEMY_NETWORK}.g.alchemy.com/v2/{settings.ALCHEMY_API_KEY}"


class WalletDataService:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def sync_wallet(
        self, user_id: uuid.UUID, wallet_address: str | None = None
    ) -> WalletMetrics | None:
        """Fetch on-chain data for a wallet and persist WalletMetrics."""
        if not wallet_address:
            from app.models.user import User
            user = await self._s.scalar(select(User).where(User.id == user_id))
            if user:
                wallet_address = user.wallet_address
        if not wallet_address:
            logger.warning("No wallet address for user %s", user_id)
            return None

        if not settings.ALCHEMY_API_KEY:
            logger.warning("No Alchemy API key configured — using mock data")
            return await self._store_mock_metrics(user_id, wallet_address)

        balance = await self._get_eth_balance(wallet_address)
        tx_count = await self._get_transaction_count(wallet_address)
        transfers = await self._get_asset_transfers(wallet_address)
        token_balances = await self._get_token_balances(wallet_address)

        counterparties: set[str] = set()
        first_ts: datetime | None = None
        last_ts: datetime | None = None
        defi_count = 0

        for t in transfers:
            addr_from = t.get("from", "")
            addr_to = t.get("to", "")
            if addr_from and addr_from.lower() != wallet_address.lower():
                counterparties.add(addr_from.lower())
            if addr_to and addr_to.lower() != wallet_address.lower():
                counterparties.add(addr_to.lower())

            block_ts = t.get("metadata", {}).get("blockTimestamp")
            if block_ts:
                dt = datetime.fromisoformat(block_ts.replace("Z", "+00:00"))
                if first_ts is None or dt < first_ts:
                    first_ts = dt
                if last_ts is None or dt > last_ts:
                    last_ts = dt

            category = t.get("category", "")
            if category in ("erc20", "erc721", "erc1155", "internal"):
                defi_count += 1

        age_days = 0
        if first_ts:
            age_days = (datetime.now(timezone.utc) - first_ts).days

        nft_count = sum(
            1 for tb in token_balances
            if tb.get("tokenBalance") and tb.get("contractAddress")
        )

        return await self._upsert_metrics(
            user_id=user_id,
            wallet_address=wallet_address,
            total_transactions=tx_count,
            unique_counterparties=len(counterparties),
            wallet_age_days=age_days,
            eth_balance=balance,
            total_token_value_usd=0.0,
            nft_count=nft_count,
            defi_interactions=defi_count,
            token_balances={tb.get("contractAddress", ""): tb.get("tokenBalance", "0") for tb in token_balances[:20]},
            first_tx=first_ts,
            last_tx=last_ts,
        )

    # ── Alchemy JSON-RPC / Enhanced API calls ─────────────────────

    async def _get_eth_balance(self, address: str) -> float:
        try:
            data = await self._rpc_call("eth_getBalance", [address, "latest"])
            wei = int(data, 16) if isinstance(data, str) else 0
            return wei / 1e18
        except Exception as e:
            logger.error("Failed to fetch ETH balance: %s", e)
            return 0.0

    async def _get_transaction_count(self, address: str) -> int:
        try:
            data = await self._rpc_call("eth_getTransactionCount", [address, "latest"])
            return int(data, 16) if isinstance(data, str) else 0
        except Exception as e:
            logger.error("Failed to fetch tx count: %s", e)
            return 0

    async def _get_asset_transfers(self, address: str) -> list[dict]:
        """Uses Alchemy's alchemy_getAssetTransfers for enriched transfer history."""
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "alchemy_getAssetTransfers",
                "params": [{
                    "fromAddress": address,
                    "category": ["external", "internal", "erc20", "erc721"],
                    "maxCount": "0x64",  # 100
                    "order": "desc",
                }],
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(_alchemy_url(), json=payload, timeout=20.0)
                resp.raise_for_status()
                result = resp.json().get("result", {})
                transfers = result.get("transfers", [])

            incoming_payload = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "alchemy_getAssetTransfers",
                "params": [{
                    "toAddress": address,
                    "category": ["external", "internal", "erc20"],
                    "maxCount": "0x64",
                    "order": "desc",
                }],
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(_alchemy_url(), json=incoming_payload, timeout=20.0)
                resp.raise_for_status()
                result = resp.json().get("result", {})
                transfers.extend(result.get("transfers", []))

            return transfers
        except Exception as e:
            logger.error("Failed to fetch asset transfers: %s", e)
            return []

    async def _get_token_balances(self, address: str) -> list[dict]:
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "alchemy_getTokenBalances",
                "params": [address, "erc20"],
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(_alchemy_url(), json=payload, timeout=15.0)
                resp.raise_for_status()
                result = resp.json().get("result", {})
                return result.get("tokenBalances", [])
        except Exception as e:
            logger.error("Failed to fetch token balances: %s", e)
            return []

    async def _rpc_call(self, method: str, params: list) -> str:
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        async with httpx.AsyncClient() as client:
            resp = await client.post(_alchemy_url(), json=payload, timeout=15.0)
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                raise ValueError(data["error"].get("message", "RPC error"))
            return data.get("result", "0x0")

    # ── Persistence ───────────────────────────────────────────────

    async def _upsert_metrics(self, user_id: uuid.UUID, wallet_address: str, **kwargs) -> WalletMetrics:
        existing = await self._s.scalar(
            select(WalletMetrics).where(
                WalletMetrics.user_id == user_id,
                WalletMetrics.wallet_address == wallet_address,
            )
        )
        now = datetime.now(timezone.utc)

        if existing:
            for k, v in kwargs.items():
                if k == "first_tx":
                    existing.first_tx_timestamp = v
                elif k == "last_tx":
                    existing.last_tx_timestamp = v
                else:
                    setattr(existing, k, v)
            existing.last_synced_at = now
            await self._s.flush()
            return existing

        metrics = WalletMetrics(
            user_id=user_id,
            wallet_address=wallet_address,
            total_transactions=kwargs.get("total_transactions", 0),
            unique_counterparties=kwargs.get("unique_counterparties", 0),
            wallet_age_days=kwargs.get("wallet_age_days", 0),
            eth_balance=kwargs.get("eth_balance", 0.0),
            total_token_value_usd=kwargs.get("total_token_value_usd", 0.0),
            nft_count=kwargs.get("nft_count", 0),
            defi_interactions=kwargs.get("defi_interactions", 0),
            token_balances=kwargs.get("token_balances"),
            first_tx_timestamp=kwargs.get("first_tx"),
            last_tx_timestamp=kwargs.get("last_tx"),
            last_synced_at=now,
        )
        self._s.add(metrics)

        account = await self._s.scalar(
            select(ConnectedAccount).where(
                ConnectedAccount.user_id == user_id,
                ConnectedAccount.provider == AccountProvider.METAMASK,
            )
        )
        if not account:
            account = ConnectedAccount(
                user_id=user_id,
                provider=AccountProvider.METAMASK,
                account_identifier=wallet_address,
                is_verified=True,
                metadata_json={"chain": "ethereum"},
            )
            self._s.add(account)

        await self._s.flush()
        return metrics

    async def _store_mock_metrics(self, user_id: uuid.UUID, wallet_address: str) -> WalletMetrics:
        """Fallback mock data when no Alchemy key is present."""
        return await self._upsert_metrics(
            user_id=user_id,
            wallet_address=wallet_address,
            total_transactions=42,
            unique_counterparties=15,
            wallet_age_days=365,
            eth_balance=2.3,
            total_token_value_usd=8500.0,
            nft_count=3,
            defi_interactions=12,
            token_balances={"mock": "true"},
            first_tx=datetime(2025, 3, 20, tzinfo=timezone.utc),
            last_tx=datetime.now(timezone.utc),
        )
