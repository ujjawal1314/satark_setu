"""
Tests for detection_engine.py
"""

import os
import sys

import pandas as pd


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from detection_engine import SatarkSetuDetector


class TestSatarkSetuDetector:
    def test_detector_initialization(self, sample_borrower_data, sample_transaction_data, sample_regional_data):
        detector = SatarkSetuDetector(sample_borrower_data, sample_transaction_data, sample_regional_data)
        assert detector is not None
        assert detector.borrower_df is not None
        assert detector.txn_df is not None

    def test_build_graph(self, sample_borrower_data, sample_transaction_data, sample_regional_data):
        detector = SatarkSetuDetector(sample_borrower_data, sample_transaction_data, sample_regional_data)
        stats = detector.build_graph()
        assert stats["nodes"] > 0
        assert stats["edges"] > 0

    def test_behavioral_flags(self, sample_borrower_data, sample_transaction_data, sample_regional_data):
        detector = SatarkSetuDetector(sample_borrower_data, sample_transaction_data, sample_regional_data)
        detector.build_graph()
        flags = detector.detect_behavioral_anomalies("BORR_00001")
        assert isinstance(flags, list)

    def test_contextual_flags(self, sample_borrower_data, sample_transaction_data, sample_regional_data):
        detector = SatarkSetuDetector(sample_borrower_data, sample_transaction_data, sample_regional_data)
        detector.build_graph()
        flags = detector.detect_contextual_anomalies("BORR_00001")
        assert isinstance(flags, list)

    def test_calculate_risk_score(self, sample_borrower_data, sample_transaction_data, sample_regional_data):
        detector = SatarkSetuDetector(sample_borrower_data, sample_transaction_data, sample_regional_data)
        detector.build_graph()
        score = detector.calculate_risk_score("BORR_00001")
        assert isinstance(score, int)
        assert 0 <= score <= 100

    def test_calculate_health_score(self, sample_borrower_data, sample_transaction_data, sample_regional_data):
        detector = SatarkSetuDetector(sample_borrower_data, sample_transaction_data, sample_regional_data)
        detector.build_graph()
        score = detector.calculate_health_score("BORR_00002")
        assert isinstance(score, int)
        assert 0 <= score <= 100

    def test_detect_stress_clusters(self, sample_borrower_data, sample_transaction_data, sample_regional_data):
        detector = SatarkSetuDetector(sample_borrower_data, sample_transaction_data, sample_regional_data)
        detector.build_graph()
        clusters = detector.detect_stress_clusters()
        assert isinstance(clusters, list)

    def test_get_flagged_accounts(self, sample_borrower_data, sample_transaction_data, sample_regional_data):
        detector = SatarkSetuDetector(sample_borrower_data, sample_transaction_data, sample_regional_data)
        detector.build_graph()
        flagged = detector.get_flagged_accounts(threshold=0)
        assert isinstance(flagged, list)
        assert flagged
        assert "borrower_id" in flagged[0]
        assert "risk_score" in flagged[0]
        assert "health_score" in flagged[0]

    def test_empty_graph_handling(self, sample_regional_data):
        empty_borrowers = pd.DataFrame(
            columns=[
                "borrower_id",
                "name",
                "loan_scheme",
                "borrower_category",
                "region",
                "loan_amount",
                "amount_band",
                "emi_amount",
                "outstanding_amount",
                "current_balance",
                "repayment_consistency",
                "inflow_stability",
                "balance_trend",
                "missed_payments_90d",
                "days_past_due",
                "avg_monthly_inflow",
                "avg_monthly_outflow",
                "regional_stress_factor",
                "peer_score",
            ]
        )
        empty_txn = pd.DataFrame(columns=["transaction_id", "borrower_id", "timestamp", "transaction_type", "amount", "status", "balance_after"])
        detector = SatarkSetuDetector(empty_borrowers, empty_txn, sample_regional_data)
        stats = detector.build_graph()
        assert stats["nodes"] == 0
        assert stats["edges"] == 0


class TestDetectorWithRealData:
    def test_real_data_detection(self, real_data):
        borrowers, transactions, regional = real_data
        detector = SatarkSetuDetector(borrowers, transactions, regional)
        detector.build_graph()
        summary = detector.portfolio_summary()
        assert summary["total_borrowers"] > 0
        assert summary["high_risk_borrowers"] >= 0
        flagged = detector.get_flagged_accounts(threshold=45)
        assert isinstance(flagged, list)
