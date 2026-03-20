"""
Pytest configuration and fixtures
"""

from datetime import datetime, timedelta
import os
import sys

import networkx as nx
import pandas as pd
import pytest


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def sample_borrower_data():
    now = datetime.now()
    return pd.DataFrame(
        {
            "borrower_id": [f"BORR_{i:05d}" for i in range(1, 7)],
            "name": [f"Borrower {i}" for i in range(1, 7)],
            "loan_scheme": ["Mudra", "Mudra", "MSME", "MSME", "PMEGP", "PMEGP"],
            "borrower_category": ["Micro Enterprise", "Micro Enterprise", "Small Business", "Small Business", "Women-led", "Women-led"],
            "region": ["Jharkhand", "Jharkhand", "West Bengal", "West Bengal", "Bihar", "Bihar"],
            "loan_amount": [250000, 420000, 1200000, 1250000, 800000, 820000],
            "amount_band": ["small", "small", "mid", "mid", "mid", "mid"],
            "emi_amount": [7200, 8600, 24000, 25000, 16500, 17200],
            "outstanding_amount": [220000, 330000, 900000, 960000, 710000, 720000],
            "current_balance": [42000, 38000, 94000, 89000, 52000, 48000],
            "repayment_consistency": [0.61, 0.88, 0.74, 0.91, 0.58, 0.69],
            "inflow_stability": [0.57, 0.83, 0.71, 0.86, 0.54, 0.66],
            "balance_trend": [-0.18, 0.08, -0.06, 0.09, -0.21, -0.04],
            "missed_payments_90d": [2, 0, 1, 0, 3, 1],
            "days_past_due": [38, 4, 19, 0, 44, 12],
            "avg_monthly_inflow": [21000, 36000, 98000, 125000, 39000, 46000],
            "avg_monthly_outflow": [20000, 28000, 93000, 99000, 38000, 43000],
            "regional_stress_factor": [0.78, 0.78, 0.49, 0.49, 0.72, 0.72],
            "peer_score": [71, 71, 82, 82, 74, 74],
        }
    )


@pytest.fixture
def sample_transaction_data():
    now = datetime.now()
    rows = []
    for idx, borrower_id in enumerate([f"BORR_{i:05d}" for i in range(1, 7)], start=1):
        rows.extend(
            [
                {
                    "transaction_id": f"T{idx}A",
                    "borrower_id": borrower_id,
                    "timestamp": now - timedelta(days=30),
                    "transaction_type": "BUSINESS_INFLOW",
                    "amount": 30000 + idx * 1000,
                    "status": "POSTED",
                    "balance_after": 55000 + idx * 500,
                },
                {
                    "transaction_id": f"T{idx}B",
                    "borrower_id": borrower_id,
                    "timestamp": now - timedelta(days=22),
                    "transaction_type": "BUSINESS_OUTFLOW",
                    "amount": 22000 + idx * 900,
                    "status": "POSTED",
                    "balance_after": 39000 + idx * 400,
                },
                {
                    "transaction_id": f"T{idx}C",
                    "borrower_id": borrower_id,
                    "timestamp": now - timedelta(days=5),
                    "transaction_type": "EMI_PAYMENT",
                    "amount": 8000 + idx * 700,
                    "status": "DELAYED" if idx % 2 else "ON_TIME",
                    "balance_after": 27000 + idx * 300,
                },
            ]
        )
    return pd.DataFrame(rows)


@pytest.fixture
def sample_regional_data():
    return pd.DataFrame(
        {
            "region": ["Jharkhand", "West Bengal", "Bihar"],
            "regional_stress_factor": [0.78, 0.49, 0.72],
            "npa_rate": [8.9, 5.6, 8.1],
            "economic_stress_index": [0.81, 0.53, 0.74],
            "peer_health_baseline": [71.0, 82.0, 74.0],
        }
    )


@pytest.fixture
def sample_graph():
    graph = nx.Graph()
    graph.add_edge("BORR_00001", "SCHEME::Mudra")
    graph.add_edge("BORR_00001", "REGION::Jharkhand")
    graph.add_edge("BORR_00002", "SCHEME::Mudra")
    graph.add_edge("BORR_00002", "REGION::Jharkhand")
    graph.add_edge("BORR_00001", "BORR_00002")
    return graph


@pytest.fixture
def real_data():
    try:
        borrowers = pd.read_csv("borrowers.csv")
        transactions = pd.read_csv("loan_transactions.csv")
        regional = pd.read_csv("regional_context.csv")
        return borrowers, transactions, regional
    except FileNotFoundError:
        pytest.skip("Generated SatarkSetu demo data not found")
