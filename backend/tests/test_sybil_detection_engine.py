"""
Tests for the CreDeFi Sybil Detection Engine.

These tests cover the pure-computation module (no DB, no I/O).
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.services.sybil_detection_engine import (
    DETECTOR_WEIGHTS,
    SYBIL_THRESHOLD,
    SUSPICIOUS_THRESHOLD,
    BehavioralSimilarityDetector,
    ContributionQualityDetector,
    GitHubProfile,
    GraphAnomalyDetector,
    SessionFingerprintDetector,
    SybilRawData,
    TxRecord,
    WalletClusteringDetector,
    FingerprintRecord,
    PeerFingerprint,
    PeerFundingInfo,
    run_sybil_analysis,
)


# ═══════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════


class TestConstants:
    def test_detector_weights_sum_to_one(self):
        assert abs(sum(DETECTOR_WEIGHTS.values()) - 1.0) < 1e-9

    def test_sybil_threshold_above_suspicious(self):
        assert SYBIL_THRESHOLD > SUSPICIOUS_THRESHOLD

    def test_five_detectors_present(self):
        expected = {
            "wallet_clustering", "graph_anomaly", "session_fingerprint",
            "behavioral_similarity", "contribution_quality",
        }
        assert set(DETECTOR_WEIGHTS.keys()) == expected


# ═══════════════════════════════════════════════════════════════════
# Individual Detectors
# ═══════════════════════════════════════════════════════════════════


class TestWalletClusteringDetector:
    def test_no_funding_data_returns_zero(self):
        data = SybilRawData(
            user_id=uuid.uuid4(),
            wallet_addresses=["0xTest"],
            transactions=[],
            fingerprints=[],
            peer_fingerprints=[],
            peer_funding=[],
        )
        score, clusters, detail = WalletClusteringDetector.detect(data)
        assert score == 0.0
        assert len(clusters) == 0

    def test_shared_funding_source_detected(self):
        user_id = uuid.uuid4()
        other_user = uuid.uuid4()
        now = datetime.now(timezone.utc)
        data = SybilRawData(
            user_id=user_id,
            wallet_addresses=["0xMyWallet"],
            transactions=[
                TxRecord(
                    from_address="0xSharedFunder", to_address="0xMyWallet",
                    amount=1000.0, currency="ETH", tx_type="transfer",
                    timestamp=now,
                ),
            ],
            fingerprints=[],
            peer_fingerprints=[],
            peer_funding=[
                PeerFundingInfo(user_id=other_user, funding_address="0xSharedFunder"),
            ],
        )
        score, clusters, detail = WalletClusteringDetector.detect(data)
        assert score > 0.0
        assert len(clusters) >= 1
        assert clusters[0].shared_funding_source == "0xSharedFunder"


class TestGraphAnomalyDetector:
    def test_no_transactions(self):
        data = SybilRawData(
            user_id=uuid.uuid4(),
            wallet_addresses=["0xTest"],
            transactions=[],
            fingerprints=[],
            peer_fingerprints=[],
            peer_funding=[],
        )
        score, detail = GraphAnomalyDetector.detect(data)
        assert score == 0.0

    def test_self_loops_increase_score(self):
        now = datetime.now(timezone.utc)
        data = SybilRawData(
            user_id=uuid.uuid4(),
            wallet_addresses=["0xLooper"],
            transactions=[
                TxRecord(
                    from_address="0xLooper", to_address="0xLooper",
                    amount=100.0, currency="ETH", tx_type="transfer",
                    timestamp=now - timedelta(hours=i),
                )
                for i in range(10)
            ],
            fingerprints=[],
            peer_fingerprints=[],
            peer_funding=[],
        )
        score, detail = GraphAnomalyDetector.detect(data)
        assert score > 0.0
        assert "self_loops=10" in detail


class TestSessionFingerprintDetector:
    def test_no_fingerprints(self):
        data = SybilRawData(
            user_id=uuid.uuid4(),
            wallet_addresses=["0xTest"],
            transactions=[],
            fingerprints=[],
            peer_fingerprints=[],
            peer_funding=[],
        )
        score, detail = SessionFingerprintDetector.detect(data)
        assert score == 0.0

    def test_ip_and_device_overlap_flagged(self):
        user_id = uuid.uuid4()
        other = uuid.uuid4()
        now = datetime.now(timezone.utc)
        data = SybilRawData(
            user_id=user_id,
            wallet_addresses=["0xTest"],
            transactions=[],
            fingerprints=[
                FingerprintRecord(
                    ip_hash="shared_ip", device_hash="shared_dev",
                    browser_fingerprint="bf1", geo_country="US",
                    captured_at=now,
                ),
            ],
            peer_fingerprints=[
                PeerFingerprint(user_id=other, ip_hash="shared_ip", device_hash="shared_dev"),
            ],
            peer_funding=[],
        )
        score, detail = SessionFingerprintDetector.detect(data)
        assert score > 0.0
        assert "both_overlaps=1" in detail


class TestBehavioralSimilarityDetector:
    def test_insufficient_transactions(self):
        data = SybilRawData(
            user_id=uuid.uuid4(),
            wallet_addresses=["0xTest"],
            transactions=[
                TxRecord(
                    from_address="0xTest", to_address="0xOther",
                    amount=100.0, currency="ETH", tx_type="transfer",
                    timestamp=datetime.now(timezone.utc),
                ),
            ],
            fingerprints=[],
            peer_fingerprints=[],
            peer_funding=[],
        )
        score, detail = BehavioralSimilarityDetector.detect(data)
        assert score == 0.0

    def test_perfectly_regular_intervals_flagged(self):
        """Bot-like transactions at exactly 10-minute intervals."""
        now = datetime.now(timezone.utc)
        data = SybilRawData(
            user_id=uuid.uuid4(),
            wallet_addresses=["0xBot"],
            transactions=[
                TxRecord(
                    from_address="0xBot", to_address="0xTarget",
                    amount=50.0, currency="ETH", tx_type="transfer",
                    timestamp=now - timedelta(minutes=i * 10),
                )
                for i in range(20)
            ],
            fingerprints=[],
            peer_fingerprints=[],
            peer_funding=[],
        )
        score, detail = BehavioralSimilarityDetector.detect(data)
        assert score > 0.3  # should show behavioral risk

    def test_burst_detection(self):
        """Many transactions within seconds of each other."""
        now = datetime.now(timezone.utc)
        data = SybilRawData(
            user_id=uuid.uuid4(),
            wallet_addresses=["0xBurster"],
            transactions=[
                TxRecord(
                    from_address="0xBurster", to_address="0xTarget",
                    amount=10.0, currency="ETH", tx_type="transfer",
                    timestamp=now - timedelta(seconds=i * 5),
                )
                for i in range(20)
            ],
            fingerprints=[],
            peer_fingerprints=[],
            peer_funding=[],
        )
        score, detail = BehavioralSimilarityDetector.detect(data)
        assert score > 0.0
        assert "burst_risk" in detail


class TestContributionQualityDetector:
    def test_no_github_profile_neutral(self):
        data = SybilRawData(
            user_id=uuid.uuid4(),
            wallet_addresses=["0xTest"],
            transactions=[],
            fingerprints=[],
            peer_fingerprints=[],
            peer_funding=[],
            github_profile=None,
        )
        score, detail = ContributionQualityDetector.detect(data)
        assert score == 0.5  # neutral

    def test_active_dev_low_risk(self):
        data = SybilRawData(
            user_id=uuid.uuid4(),
            wallet_addresses=["0xDev"],
            transactions=[],
            fingerprints=[],
            peer_fingerprints=[],
            peer_funding=[],
            github_profile=GitHubProfile(
                repos_count=25, total_commits=600,
                account_age_days=1000, has_original_repos=True,
                stars_received=100,
            ),
        )
        score, detail = ContributionQualityDetector.detect(data)
        assert score < 0.3  # low risk for active devs

    def test_empty_github_high_risk(self):
        data = SybilRawData(
            user_id=uuid.uuid4(),
            wallet_addresses=["0xEmpty"],
            transactions=[],
            fingerprints=[],
            peer_fingerprints=[],
            peer_funding=[],
            github_profile=GitHubProfile(
                repos_count=0, total_commits=0,
                account_age_days=5, has_original_repos=False,
                stars_received=0,
            ),
        )
        score, detail = ContributionQualityDetector.detect(data)
        assert score > 0.6  # high risk for empty profiles


# ═══════════════════════════════════════════════════════════════════
# End-to-End Ensemble
# ═══════════════════════════════════════════════════════════════════


class TestRunSybilAnalysis:
    def test_clean_user_verdict(self, clean_sybil_data):
        result = run_sybil_analysis(clean_sybil_data)
        assert result.verdict == "clean"
        assert result.risk_score < SUSPICIOUS_THRESHOLD
        assert len(result.detectors) == 5

    def test_suspicious_user_flagged(self, suspicious_sybil_data):
        result = run_sybil_analysis(suspicious_sybil_data)
        # Should at least be suspicious (self-loops, shared fingerprints)
        assert result.risk_score > 0.2
        assert len(result.detectors) == 5
        assert all(d.score >= 0.0 for d in result.detectors)

    def test_result_has_all_fields(self, clean_sybil_data):
        result = run_sybil_analysis(clean_sybil_data)
        assert result.verdict in ("clean", "suspicious", "sybil")
        assert 0.0 <= result.risk_score <= 1.0
        assert len(result.features) == 5
        assert result.model_version == "sybil-v1"

    def test_multi_detector_amplification(self):
        """When many detectors fire, the score should be amplified."""
        now = datetime.now(timezone.utc)
        user_id = uuid.uuid4()
        others = [uuid.uuid4() for _ in range(6)]

        # Build a maximally suspicious user
        data = SybilRawData(
            user_id=user_id,
            wallet_addresses=["0xMaxSus"],
            transactions=[
                # Self-loops
                TxRecord(
                    from_address="0xMaxSus", to_address="0xMaxSus",
                    amount=100.0, currency="ETH", tx_type="transfer",
                    timestamp=now - timedelta(seconds=i * 5),
                )
                for i in range(15)
            ],
            fingerprints=[
                FingerprintRecord(
                    ip_hash="ip_sus", device_hash="dev_sus",
                    browser_fingerprint="bf_sus", geo_country="XX",
                    captured_at=now,
                ),
            ],
            peer_fingerprints=[
                PeerFingerprint(user_id=uid, ip_hash="ip_sus", device_hash="dev_sus")
                for uid in others
            ],
            peer_funding=[
                PeerFundingInfo(user_id=uid, funding_address="0xSameFunder")
                for uid in others
            ],
            github_profile=GitHubProfile(
                repos_count=0, total_commits=0, account_age_days=1,
                has_original_repos=False, stars_received=0,
            ),
            account_age_days=2,
        )
        result = run_sybil_analysis(data)
        # With this many red flags, should be flagged as sybil or at least suspicious
        assert result.risk_score > SUSPICIOUS_THRESHOLD
