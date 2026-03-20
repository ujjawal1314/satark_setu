"""
Tests for data_generator.py
"""

import os
import sys

import pandas as pd


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestDataGenerator:
    def test_borrowers_file_exists(self):
        assert os.path.exists("borrowers.csv"), "borrowers.csv not found"

    def test_transactions_file_exists(self):
        assert os.path.exists("loan_transactions.csv"), "loan_transactions.csv not found"

    def test_regional_context_exists(self):
        assert os.path.exists("regional_context.csv"), "regional_context.csv not found"

    def test_borrowers_structure(self):
        df = pd.read_csv("borrowers.csv")
        required = [
            "borrower_id",
            "name",
            "loan_scheme",
            "region",
            "loan_amount",
            "peer_score",
            "regional_stress_factor",
        ]
        for column in required:
            assert column in df.columns
        assert len(df) > 0

    def test_transactions_structure(self):
        df = pd.read_csv("loan_transactions.csv")
        required = ["transaction_id", "borrower_id", "timestamp", "transaction_type", "amount", "status", "balance_after"]
        for column in required:
            assert column in df.columns
        assert len(df) > 0

    def test_regional_context_structure(self):
        df = pd.read_csv("regional_context.csv")
        required = ["region", "regional_stress_factor", "npa_rate", "peer_health_baseline"]
        for column in required:
            assert column in df.columns
        assert len(df) > 0

    def test_borrower_id_format(self):
        df = pd.read_csv("borrowers.csv")
        for borrower_id in df["borrower_id"].head(100):
            assert borrower_id.startswith("BORR_")

    def test_positive_amounts(self):
        borrowers = pd.read_csv("borrowers.csv")
        txns = pd.read_csv("loan_transactions.csv")
        assert (borrowers["loan_amount"] > 0).all()
        assert (borrowers["emi_amount"] > 0).all()
        assert (txns["amount"] >= 0).all()
