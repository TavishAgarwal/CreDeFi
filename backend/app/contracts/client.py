"""
Contract Client
================
Typed Python interface to CreDeFi smart contracts via Web3.py.
Falls back to mock mode when RPC is unreachable (dev without Hardhat node).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

ABI_DIR = Path(__file__).parent / "abis"


def _load_abi(name: str) -> list[dict[str, Any]]:
    """Load a contract ABI from the abis/ directory."""
    path = ABI_DIR / f"{name}.json"
    if not path.exists():
        logger.warning("ABI file not found: %s — contract calls will fail", path)
        return []
    data = json.loads(path.read_text())
    return data.get("abi", data) if isinstance(data, dict) else data


class ContractClient:
    """Web3 client for CreDeFi smart contracts."""

    def __init__(self) -> None:
        self._connected = False
        self.w3: Web3 | None = None
        self._account = None

        if not settings.RPC_URL or not settings.LOAN_CONTRACT_ADDRESS:
            logger.info("Blockchain settings not configured — running in mock mode")
            return

        try:
            self.w3 = Web3(Web3.HTTPProvider(settings.RPC_URL))
            # PoA middleware for Hardhat / other PoA chains
            self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

            if not self.w3.is_connected():
                logger.warning("Cannot connect to RPC at %s — mock mode", settings.RPC_URL)
                self.w3 = None
                return

            # Set up signer account from private key
            if settings.CHAIN_PRIVATE_KEY:
                self._account = self.w3.eth.account.from_key(settings.CHAIN_PRIVATE_KEY)
                self.w3.eth.default_account = self._account.address

            # Load contract instances
            self.loan_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(settings.LOAN_CONTRACT_ADDRESS),
                abi=_load_abi("LoanContract"),
            )
            self.vault_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(settings.VAULT_CONTRACT_ADDRESS),
                abi=_load_abi("CollateralVault"),
            )
            self.nft_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(settings.NFT_CONTRACT_ADDRESS),
                abi=_load_abi("SoulboundReputationNFT"),
            )
            self.rate_model = self.w3.eth.contract(
                address=Web3.to_checksum_address(settings.RATE_MODEL_ADDRESS),
                abi=_load_abi("InterestRateModel"),
            )

            self._connected = True
            logger.info(
                "ContractClient connected to %s | Loan=%s Vault=%s NFT=%s",
                settings.RPC_URL,
                settings.LOAN_CONTRACT_ADDRESS[:10] + "...",
                settings.VAULT_CONTRACT_ADDRESS[:10] + "...",
                settings.NFT_CONTRACT_ADDRESS[:10] + "...",
            )
        except Exception as exc:
            logger.error("ContractClient init failed: %s — mock mode", exc)
            self.w3 = None

    @property
    def is_connected(self) -> bool:
        return self._connected and self.w3 is not None

    # ─── Read methods ─────────────────────────────────────────────

    def get_trust_score(self, address: str) -> int | None:
        """Get a wallet's trust score from the SoulboundReputationNFT."""
        if not self.is_connected:
            return None
        try:
            addr = Web3.to_checksum_address(address)
            token_id = self.nft_contract.functions.tokenOfOwner(addr).call()
            rep = self.nft_contract.functions.getReputation(token_id).call()
            return rep[0]  # score field
        except Exception as exc:
            logger.debug("get_trust_score failed for %s: %s", address, exc)
            return None

    def get_loan(self, loan_id: int) -> dict[str, Any] | None:
        """Get loan details from the on-chain LoanContract."""
        if not self.is_connected:
            return None
        try:
            loan = self.loan_contract.functions.getLoan(loan_id).call()
            return {
                "borrower": loan[0],
                "lender": loan[1],
                "borrow_token": loan[2],
                "collateral_token": loan[3],
                "principal": loan[4],
                "collateral_amount": loan[5],
                "interest_rate_bps": loan[6],
                "start_time": loan[7],
                "deadline": loan[8],
                "repaid_amount": loan[9],
                "status": loan[10],
            }
        except Exception as exc:
            logger.debug("get_loan failed for id=%s: %s", loan_id, exc)
            return None

    def outstanding_debt(self, loan_id: int) -> int | None:
        """Query outstanding debt for a loan."""
        if not self.is_connected:
            return None
        try:
            return self.loan_contract.functions.outstandingDebt(loan_id).call()
        except Exception:
            return None

    def is_liquidatable(self, loan_id: int) -> bool:
        """Check if a loan is liquidatable."""
        if not self.is_connected:
            return False
        try:
            return self.loan_contract.functions.isLiquidatable(loan_id).call()
        except Exception:
            return False

    # ─── Write methods (use backend signer) ───────────────────────

    def _send_tx(self, fn) -> str:
        """Build, sign, and send a contract transaction. Returns tx hash."""
        if not self._account:
            raise RuntimeError("No signer configured (CHAIN_PRIVATE_KEY not set)")

        tx = fn.build_transaction({
            "from": self._account.address,
            "nonce": self.w3.eth.get_transaction_count(self._account.address),
            "gas": 500_000,
            "gasPrice": self.w3.eth.gas_price,
        })
        signed = self._account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)
        logger.info("TX sent: %s (status=%s)", tx_hash.hex(), receipt["status"])
        return tx_hash.hex()

    def mint_reputation(self, wallet_address: str, score: int, tier: str) -> str:
        """Mint or update a soulbound reputation NFT for a user."""
        if not self.is_connected:
            return "0xMOCK"
        addr = Web3.to_checksum_address(wallet_address)
        try:
            # Check if token already exists — update if so
            self.nft_contract.functions.tokenOfOwner(addr).call()
            # Token exists → update score
            fn = self.nft_contract.functions.updateScore(addr, score, tier)
        except Exception:
            # No token → mint new
            fn = self.nft_contract.functions.mintReputation(addr, score, tier)
        return self._send_tx(fn)

    def set_price(self, token_address: str, price_wei: int) -> str:
        """Set a token price in the LoanContract (admin only)."""
        if not self.is_connected:
            return "0xMOCK"
        addr = Web3.to_checksum_address(token_address)
        fn = self.loan_contract.functions.setPrice(addr, price_wei)
        return self._send_tx(fn)

    # ─── Wallet signature verification ────────────────────────────

    @staticmethod
    def recover_signer(message: str, signature: str) -> str:
        """Recover the Ethereum address that signed a message."""
        from eth_account.messages import encode_defunct

        w3 = Web3()
        msg = encode_defunct(text=message)
        return w3.eth.account.recover_message(msg, signature=signature)


# Singleton instance
contract_client = ContractClient()
