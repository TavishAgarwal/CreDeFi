"""
Shared fixtures for CreDeFi backend tests.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.services.trust_score_engine import (
    AccountInfo,
    GraphMetrics,
    IncomeRecord,
    LoanHistory,
    RawUserData,
    SybilInfo,
    TransactionStats,
)
from app.services.sybil_detection_engine import (
    FingerprintRecord,
    GitHubProfile,
    PeerFingerprint,
    PeerFundingInfo,
    SybilRawData,
    TxRecord,
)


# ── Trust Score Engine Fixtures ─────────────────────────────────


@pytest.fixture
def empty_user_data() -> RawUserData:
    """Brand-new user with absolutely no data — cold start scenario."""
    return RawUserData(user_created_at=datetime.now(timezone.utc))


@pytest.fixture
def strong_user_data() -> RawUserData:
    """Well-established user with strong signals across all factors."""
    return RawUserData(
        user_created_at=datetime.now(timezone.utc) - timedelta(days=500),
        wallet_address="0xStrongUser",
        income_sources=[
            IncomeRecord(
                monthly_amount=8000.0,
                currency="USD",
                frequency="monthly",
                is_verified=True,
            ),
            IncomeRecord(
                monthly_amount=2000.0,
                currency="USDC",
                frequency="biweekly",
                is_verified=True,
            ),
        ],
        loan_history=LoanHistory(
            total_contracts=5,
            repaid_count=5,
            defaulted_count=0,
            active_count=0,
            on_time_repayments=10,
            late_repayments=0,
            missed_repayments=0,
            total_repayments=10,
        ),
        transaction_stats=TransactionStats(
            total_count=50,
            unique_types=4,
            unique_chains=3,
            unique_counterparties=15,
            circular_count=0,
        ),
        graph_metrics=GraphMetrics(
            pagerank=0.008,
            betweenness_centrality=0.03,
            closeness_centrality=0.5,
            clustering_coeff=0.6,
            degree_in=20,
            degree_out=15,
        ),
        sybil_info=SybilInfo(verdict="clean", confidence=0.0),
        connected_accounts=[
            AccountInfo(provider="stripe", is_verified=True),
            AccountInfo(provider="bank", is_verified=True),
            AccountInfo(provider="metamask", is_verified=True),
        ],
        primary_currency="USD",
        previous_scores=[650.0, 700.0, 750.0],
        last_activity_at=datetime.now(timezone.utc) - timedelta(days=2),
    )


@pytest.fixture
def sybil_user_data() -> RawUserData:
    """A user flagged as sybil with circular transactions."""
    return RawUserData(
        user_created_at=datetime.now(timezone.utc) - timedelta(days=30),
        wallet_address="0xSybilUser",
        income_sources=[
            IncomeRecord(
                monthly_amount=1000.0, currency="USD", frequency="monthly", is_verified=False
            ),
        ],
        loan_history=LoanHistory(total_contracts=1, repaid_count=0, defaulted_count=1),
        transaction_stats=TransactionStats(
            total_count=20, unique_types=1, unique_chains=1,
            unique_counterparties=2, circular_count=10,
        ),
        sybil_info=SybilInfo(verdict="sybil", confidence=0.9),
        connected_accounts=[],
        previous_scores=[400.0, 600.0],  # suspicious jump
        last_activity_at=datetime.now(timezone.utc) - timedelta(days=200),
    )


# ── Sybil Detection Engine Fixtures ────────────────────────────


@pytest.fixture
def clean_sybil_data() -> SybilRawData:
    """Legitimate user with normal transaction patterns."""
    now = datetime.now(timezone.utc)
    user_id = uuid.uuid4()
    return SybilRawData(
        user_id=user_id,
        wallet_addresses=["0xCleanWallet"],
        transactions=[
            TxRecord(
                from_address="0xFunder1",
                to_address="0xCleanWallet",
                amount=100.0 + i * 50,
                currency="USDC",
                tx_type="transfer",
                timestamp=now - timedelta(hours=i * 7 + (i % 3)),
            )
            for i in range(10)
        ],
        fingerprints=[
            FingerprintRecord(
                ip_hash="ip_clean_1", device_hash="dev_clean_1",
                browser_fingerprint="bf1", geo_country="US",
                captured_at=now,
            ),
        ],
        peer_fingerprints=[],
        peer_funding=[],
        github_profile=GitHubProfile(
            repos_count=15, total_commits=300, account_age_days=800,
            has_original_repos=True, stars_received=25,
        ),
        account_age_days=365,
    )


@pytest.fixture
def suspicious_sybil_data() -> SybilRawData:
    """User with multiple sybil red flags."""
    now = datetime.now(timezone.utc)
    user_id = uuid.uuid4()
    other_user = uuid.uuid4()
    return SybilRawData(
        user_id=user_id,
        wallet_addresses=["0xSuspect1"],
        transactions=[
            # Self-loops
            TxRecord(
                from_address="0xSuspect1", to_address="0xSuspect1",
                amount=100.0, currency="ETH", tx_type="transfer",
                timestamp=now - timedelta(seconds=i * 30),
            )
            for i in range(8)
        ] + [
            # Perfectly timed transactions (bot-like)
            TxRecord(
                from_address="0xSuspect1", to_address=f"0xTarget{i}",
                amount=50.0, currency="ETH", tx_type="transfer",
                timestamp=now - timedelta(minutes=i * 10),
            )
            for i in range(8)
        ],
        fingerprints=[
            FingerprintRecord(
                ip_hash="ip_shared", device_hash="dev_shared",
                browser_fingerprint="bf_shared", geo_country="XX",
                captured_at=now,
            ),
        ],
        peer_fingerprints=[
            PeerFingerprint(user_id=other_user, ip_hash="ip_shared", device_hash="dev_shared"),
        ],
        peer_funding=[
            PeerFundingInfo(user_id=other_user, funding_address="0xSharedFunder"),
        ],
        github_profile=None,
        account_age_days=10,
    )
