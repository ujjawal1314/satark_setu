"""
Tests for gemini_explainer.py
"""

import os
import sys


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gemini_explainer import GeminiExplainer


class TestGeminiExplainer:
    def test_initialization(self):
        explainer = GeminiExplainer()
        assert explainer is not None

    def test_explain_borrower_health_basic(self):
        explainer = GeminiExplainer()
        borrower_data = {"borrower_id": "BORR_00001", "risk_score": 75, "health_score": 25, "peer_score": 62}
        explanation = explainer.explain_borrower_health(
            borrower_data,
            behavioral_flags=["missed_emi_events", "declining_balance_trend"],
            contextual_flags=["high_regional_npa_pressure"],
        )
        assert isinstance(explanation, str)
        assert "BORR_00001" in explanation

    def test_fallback_borrower_explanation(self):
        explainer = GeminiExplainer()
        borrower_data = {"borrower_id": "BORR_00001", "risk_score": 82, "health_score": 18, "peer_score": 64}
        explanation = explainer._fallback_borrower_explanation(
            borrower_data,
            ["missed_emi_events"],
            ["below_peer_cohort"],
            {"region": "Jharkhand", "loan_scheme": "Mudra", "size": 16},
        )
        assert "BORR_00001" in explanation
        assert len(explanation) > 80

    def test_generate_recovery_narrative(self):
        explainer = GeminiExplainer()
        borrower_data = {"borrower_id": "BORR_00001", "risk_score": 68}
        narrative = explainer.generate_recovery_narrative(
            borrower_data,
            behavioral_flags=["cashflow_coverage_stress"],
            contextual_flags=["high_regional_npa_pressure"],
        )
        assert isinstance(narrative, str)
        assert len(narrative) > 20

    def test_generate_borrower_guidance(self):
        explainer = GeminiExplainer()
        borrower_data = {"borrower_id": "BORR_00001", "risk_score": 54}
        guidance = explainer.generate_borrower_guidance(borrower_data)
        assert isinstance(guidance, str)
        assert "BORR_00001" in guidance

    def test_explain_cohort_cluster(self):
        explainer = GeminiExplainer()
        explanation = explainer.explain_cohort_cluster("Jharkhand-Mudra", 18, "Jharkhand", "Mudra", 63)
        assert isinstance(explanation, str)
        assert "Jharkhand" in explanation

    def test_suggest_investigation_steps(self):
        explainer = GeminiExplainer()
        steps = explainer.suggest_investigation_steps({"borrower_id": "BORR_00001"}, ["missed_emi_events"])
        assert isinstance(steps, str)
        assert "BORR_00001" in steps
