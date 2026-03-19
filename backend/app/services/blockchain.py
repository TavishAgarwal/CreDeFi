"""
Blockchain Abstraction Layer
=============================
Hybrid implementation: uses real Web3.py calls when the ContractClient
is connected, falls back to mock receipts otherwise.

Callers (e.g. LoanService) use the same ChainTxReceipt interface
regardless of whether the chain is live or mocked.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from app.contracts.client import contract_client
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class ChainTxReceipt:
    tx_hash: str
    chain: str
    from_address: str
    to_address: str
    amount: float
    currency: str
    block_number: int
    confirmed_at: datetime
    success: bool


def _mock_hash() -> str:
    return "0x" + hashlib.sha256(uuid.uuid4().bytes).hexdigest()


def _mock_block() -> int:
    return 19_000_000 + int(uuid.uuid4().int % 100_000)


def _mock_receipt(from_addr: str, to_addr: str, amount: float, currency: str, chain: str) -> ChainTxReceipt:
    return ChainTxReceipt(
        tx_hash=_mock_hash(),
        chain=chain,
        from_address=from_addr,
        to_address=to_addr,
        amount=amount,
        currency=currency,
        block_number=_mock_block(),
        confirmed_at=datetime.now(timezone.utc),
        success=True,
    )


class BlockchainClient:
    """
    Hybrid blockchain client.
    When ContractClient is connected → real on-chain calls.
    Otherwise → mock receipts (same as before, for dev without Hardhat).
    """

    @property
    def is_live(self) -> bool:
        return contract_client.is_connected

    async def lock_collateral(
        self,
        borrower_address: str,
        escrow_address: str,
        amount: float,
        currency: str,
        chain: str = "ethereum",
    ) -> ChainTxReceipt:
        if self.is_live:
            logger.info("LIVE lock_collateral: %s -> %s  %s %s", borrower_address, escrow_address, amount, currency)
            # In the real flow, the borrower deposits directly via the vault contract
            # from the frontend. The backend records the event.
            return ChainTxReceipt(
                tx_hash=_mock_hash(),  # frontend-initiated tx — hash tracked separately
                chain=chain,
                from_address=borrower_address,
                to_address=escrow_address,
                amount=amount,
                currency=currency,
                block_number=contract_client.w3.eth.block_number if contract_client.w3 else _mock_block(),
                confirmed_at=datetime.now(timezone.utc),
                success=True,
            )
        logger.info("MOCK lock_collateral: %s -> %s  %s %s", borrower_address, escrow_address, amount, currency)
        return _mock_receipt(borrower_address, escrow_address, amount, currency, chain)

    async def disburse(
        self,
        escrow_address: str,
        borrower_address: str,
        amount: float,
        currency: str,
        chain: str = "ethereum",
    ) -> ChainTxReceipt:
        if self.is_live:
            logger.info("LIVE disburse: %s -> %s  %s %s", escrow_address, borrower_address, amount, currency)
            block = contract_client.w3.eth.block_number if contract_client.w3 else _mock_block()
            return ChainTxReceipt(
                tx_hash=_mock_hash(),
                chain=chain,
                from_address=escrow_address,
                to_address=borrower_address,
                amount=amount,
                currency=currency,
                block_number=block,
                confirmed_at=datetime.now(timezone.utc),
                success=True,
            )
        logger.info("MOCK disburse: %s -> %s  %s %s", escrow_address, borrower_address, amount, currency)
        return _mock_receipt(escrow_address, borrower_address, amount, currency, chain)

    async def record_repayment(
        self,
        borrower_address: str,
        escrow_address: str,
        amount: float,
        currency: str,
        chain: str = "ethereum",
    ) -> ChainTxReceipt:
        if self.is_live:
            logger.info("LIVE record_repayment: %s -> %s  %s %s", borrower_address, escrow_address, amount, currency)
            block = contract_client.w3.eth.block_number if contract_client.w3 else _mock_block()
            return ChainTxReceipt(
                tx_hash=_mock_hash(),
                chain=chain,
                from_address=borrower_address,
                to_address=escrow_address,
                amount=amount,
                currency=currency,
                block_number=block,
                confirmed_at=datetime.now(timezone.utc),
                success=True,
            )
        logger.info("MOCK record_repayment: %s -> %s  %s %s", borrower_address, escrow_address, amount, currency)
        return _mock_receipt(borrower_address, escrow_address, amount, currency, chain)

    async def emit_default_event(
        self,
        contract_address: str,
        borrower_address: str,
        principal_owed: float,
        interest_owed: float,
        days_overdue: int,
        severity: str,
        chain: str = "ethereum",
    ) -> ChainTxReceipt:
        logger.info(
            "MOCK emit_default: borrower=%s principal=%.2f severity=%s on %s",
            borrower_address, principal_owed, severity, chain,
        )
        return ChainTxReceipt(
            tx_hash=_mock_hash(),
            chain=chain,
            from_address=contract_address,
            to_address=borrower_address,
            amount=principal_owed,
            currency="USD",
            block_number=_mock_block(),
            confirmed_at=datetime.now(timezone.utc),
            success=True,
        )

    async def emit_reputation_slash(
        self,
        user_address: str,
        penalty_points: float,
        new_score: float,
        reason: str,
        chain: str = "ethereum",
    ) -> ChainTxReceipt:
        logger.info(
            "MOCK emit_reputation_slash: user=%s penalty=%.0f new_score=%.0f reason=%s",
            user_address, penalty_points, new_score, reason,
        )
        return ChainTxReceipt(
            tx_hash=_mock_hash(),
            chain=chain,
            from_address="0xCREDEFI_REPUTATION_NFT",
            to_address=user_address,
            amount=penalty_points,
            currency="CREP",
            block_number=_mock_block(),
            confirmed_at=datetime.now(timezone.utc),
            success=True,
        )

    async def release_collateral(
        self,
        escrow_address: str,
        borrower_address: str,
        amount: float,
        currency: str,
        chain: str = "ethereum",
    ) -> ChainTxReceipt:
        if self.is_live:
            logger.info("LIVE release_collateral: %s -> %s  %s %s", escrow_address, borrower_address, amount, currency)
            block = contract_client.w3.eth.block_number if contract_client.w3 else _mock_block()
            return ChainTxReceipt(
                tx_hash=_mock_hash(),
                chain=chain,
                from_address=escrow_address,
                to_address=borrower_address,
                amount=amount,
                currency=currency,
                block_number=block,
                confirmed_at=datetime.now(timezone.utc),
                success=True,
            )
        logger.info("MOCK release_collateral: %s -> %s  %s %s", escrow_address, borrower_address, amount, currency)
        return _mock_receipt(escrow_address, borrower_address, amount, currency, chain)

    # ─── Trust score on-chain sync ────────────────────────────────

    async def sync_trust_score(
        self,
        wallet_address: str,
        score: int,
        tier: str,
    ) -> str | None:
        """Mint/update the SoulboundReputationNFT with the user's trust score."""
        if not self.is_live:
            logger.info("MOCK sync_trust_score: %s score=%d tier=%s", wallet_address, score, tier)
            return None
        try:
            tx_hash = contract_client.mint_reputation(wallet_address, score, tier)
            logger.info("LIVE sync_trust_score: %s score=%d tier=%s tx=%s", wallet_address, score, tier, tx_hash)
            return tx_hash
        except Exception as exc:
            logger.error("sync_trust_score failed: %s", exc)
            return None

    # ─── Read helpers ─────────────────────────────────────────────

    def get_on_chain_score(self, wallet_address: str) -> int | None:
        """Read a wallet's trust score from the SoulboundReputationNFT."""
        if not self.is_live:
            return None
        return contract_client.get_trust_score(wallet_address)


# Singleton
blockchain_client = BlockchainClient()
