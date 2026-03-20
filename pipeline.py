"""
SatarkSetu — Feature Engineering
Transforms raw borrower + transaction + regional data into model input
"""

import numpy as np


FEATURES = [
    'repayment_consistency', 'inflow_stability', 'balance_trend',
    'missed_payments_90d', 'days_past_due',
    'txn_miss_rate', 'txn_delay_rate', 'txn_ontime_rate',
    'inflow_volatility', 'balance_trajectory',
    'emi_to_inflow_ratio', 'outstanding_to_loan', 'buffer_ratio',
    'inflow_outflow_gap',
    'regional_stress_factor', 'peer_score', 'peer_regional_gap',
    'npa_rate', 'economic_stress_index',
]


def engineer_features(borrower: dict, transactions: list, regional: dict) -> list:
    """
    Build the 19-feature vector for one borrower.

    Args:
        borrower    : dict of borrower row from Supabase
        transactions: list of transaction dicts for this borrower
        regional    : dict of regional context for borrower's region

    Returns:
        list of 19 floats ready for model input
    """

    # --- Transaction-derived features ---
    emi_txns = [t for t in transactions if t['transaction_type'] == 'EMI_PAYMENT']
    total    = len(emi_txns) if emi_txns else 1

    txn_miss_rate   = sum(1 for t in emi_txns if t['status'] == 'MISSED')  / total
    txn_delay_rate  = sum(1 for t in emi_txns if t['status'] == 'DELAYED') / total
    txn_ontime_rate = sum(1 for t in emi_txns if t['status'] == 'ON_TIME') / total

    inflow_txns = [t for t in transactions if t['transaction_type'] == 'BUSINESS_INFLOW']
    amounts     = [t['amount'] for t in inflow_txns]
    inflow_volatility = float(np.std(amounts)) if len(amounts) > 1 else 0.0

    sorted_txns       = sorted(transactions, key=lambda t: t['timestamp'])
    first_bal         = sorted_txns[0]['balance_after']  if sorted_txns else 0
    last_bal          = sorted_txns[-1]['balance_after'] if sorted_txns else 0
    balance_trajectory = (last_bal - first_bal) / (abs(first_bal) + 1)

    # --- Ratio features ---
    emi_to_inflow_ratio = borrower.get('emi_amount', 0) / (borrower.get('avg_monthly_inflow', 0) + 1)
    outstanding_to_loan = borrower.get('outstanding_amount', 0) / (borrower.get('loan_amount', 0) + 1)
    buffer_ratio        = borrower.get('current_balance', 0) / (borrower.get('emi_amount', 0) + 1)
    inflow_outflow_gap  = borrower.get('avg_monthly_inflow', 0) - borrower.get('avg_monthly_outflow', 0)

    # --- Contextual features ---
    peer_health_baseline = regional.get('peer_health_baseline', borrower.get('peer_score', 0))
    peer_regional_gap    = borrower.get('peer_score', 0) - peer_health_baseline

    features = [
        borrower.get('repayment_consistency', 0),
        borrower.get('inflow_stability', 0),
        borrower.get('balance_trend', 0),
        borrower.get('missed_payments_90d', 0),
        borrower.get('days_past_due', 0),
        txn_miss_rate,
        txn_delay_rate,
        txn_ontime_rate,
        inflow_volatility,
        balance_trajectory,
        emi_to_inflow_ratio,
        outstanding_to_loan,
        buffer_ratio,
        inflow_outflow_gap,
        borrower.get('regional_stress_factor', 0),
        borrower.get('peer_score', 0),
        peer_regional_gap,
        regional.get('npa_rate', 0),
        regional.get('economic_stress_index', 0),
    ]

    return [float(f) for f in features]


def risk_band(probability: float) -> str:
    if probability >= 0.60:   return 'CRITICAL'
    elif probability >= 0.40: return 'HIGH'
    elif probability >= 0.20: return 'MODERATE'
    else:                     return 'LOW'


def recovery_action(probability: float) -> str:
    if probability >= 0.60:
        return 'Immediate Intervention: Restructuring / Legal Notice Review'
    elif probability >= 0.40:
        return 'Proactive Outreach: Restructure EMI / Offer Moratorium'
    elif probability >= 0.20:
        return 'Soft Alert: Relationship Manager Check-in'
    else:
        return 'Monitor: Standard Portfolio Review'
