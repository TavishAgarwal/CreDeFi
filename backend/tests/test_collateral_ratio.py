"""
Unit tests for the dynamic collateral ratio functions.

These functions mirror the on-chain getCollateralRatioBps() logic.
"""

import sys
import types
from unittest.mock import MagicMock

import pytest

# Stub out the deep dependency tree that pulls in web3 etc.
# We only need the pure functions (no blockchain calls).
for mod_name in [
    "web3", "app.contracts", "app.contracts.client",
    "app.services.blockchain",
]:
    sys.modules.setdefault(mod_name, types.ModuleType(mod_name))

# Now we can safely patch the symbols loan_service expects
blockchain_mod = sys.modules["app.services.blockchain"]
blockchain_mod.ChainTxReceipt = MagicMock  # type: ignore[attr-defined]
blockchain_mod.blockchain_client = MagicMock()  # type: ignore[attr-defined]

from app.services.loan_service import (  # noqa: E402
    get_collateral_ratio,
    get_interest_rate_bps,
    get_max_loan,
)


# ═══════════════════════════════════════════════════════════════════
# get_collateral_ratio
# ═══════════════════════════════════════════════════════════════════


class TestGetCollateralRatio:
    """Trust score → collateral ratio mapping."""

    @pytest.mark.parametrize("score", [0, 100, 300, 449, 449.9])
    def test_not_eligible_below_450(self, score: float):
        assert get_collateral_ratio(score) is None

    @pytest.mark.parametrize("score", [450, 500, 599])
    def test_120_percent_for_450_to_599(self, score: float):
        assert get_collateral_ratio(score) == 1.20

    @pytest.mark.parametrize("score", [600, 650, 749])
    def test_80_percent_for_600_to_749(self, score: float):
        assert get_collateral_ratio(score) == 0.80

    @pytest.mark.parametrize("score", [750, 800, 849])
    def test_60_percent_for_750_to_849(self, score: float):
        assert get_collateral_ratio(score) == 0.60

    @pytest.mark.parametrize("score", [850, 900, 949])
    def test_40_percent_for_850_to_949(self, score: float):
        assert get_collateral_ratio(score) == 0.40

    @pytest.mark.parametrize("score", [950, 975, 1000])
    def test_20_percent_for_950_to_1000(self, score: float):
        assert get_collateral_ratio(score) == 0.20

    def test_boundary_transitions(self):
        """Each boundary should transition to the next tier."""
        assert get_collateral_ratio(449) is None
        assert get_collateral_ratio(450) == 1.20

        assert get_collateral_ratio(599) == 1.20
        assert get_collateral_ratio(600) == 0.80

        assert get_collateral_ratio(749) == 0.80
        assert get_collateral_ratio(750) == 0.60

        assert get_collateral_ratio(849) == 0.60
        assert get_collateral_ratio(850) == 0.40

        assert get_collateral_ratio(949) == 0.40
        assert get_collateral_ratio(950) == 0.20


# ═══════════════════════════════════════════════════════════════════
# get_interest_rate_bps
# ═══════════════════════════════════════════════════════════════════


class TestGetInterestRateBps:
    def test_not_eligible_below_450(self):
        assert get_interest_rate_bps(0) is None
        assert get_interest_rate_bps(449) is None

    def test_2400_bps_for_450_to_599(self):
        assert get_interest_rate_bps(500) == 2400

    def test_1200_bps_for_600_to_749(self):
        assert get_interest_rate_bps(700) == 1200

    def test_800_bps_for_750_to_849(self):
        assert get_interest_rate_bps(800) == 800

    def test_500_bps_for_850_to_949(self):
        assert get_interest_rate_bps(900) == 500

    def test_300_bps_for_950_to_1000(self):
        assert get_interest_rate_bps(1000) == 300


# ═══════════════════════════════════════════════════════════════════
# get_max_loan
# ═══════════════════════════════════════════════════════════════════


class TestGetMaxLoan:
    def test_zero_below_450(self):
        assert get_max_loan(0) == 0.0
        assert get_max_loan(449) == 0.0

    def test_1500_for_450_to_599(self):
        assert get_max_loan(500) == 1_500.0

    def test_5000_for_600_to_749(self):
        assert get_max_loan(700) == 5_000.0

    def test_10000_for_750_to_849(self):
        assert get_max_loan(800) == 10_000.0

    def test_25000_for_850_to_949(self):
        assert get_max_loan(900) == 25_000.0

    def test_50000_for_950_to_1000(self):
        assert get_max_loan(1000) == 50_000.0
