"""
Smoke test for Gemini borrower-health explanations.
"""

import os

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        return None

from gemini_explainer import GeminiExplainer


load_dotenv()

print("=" * 60)
print("GEMINI BORROWER HEALTH TEST")
print("=" * 60)

api_key = os.getenv("GEMINI_API_KEY")
if api_key and api_key != "your_api_key_here":
    print("✅ API key found")
else:
    print("⚠️ API key missing or placeholder; fallback mode will be used")

explainer = GeminiExplainer()
borrower_data = {"borrower_id": "BORR_00021", "risk_score": 74, "health_score": 26, "peer_score": 61}

print("\nBorrower health explanation:")
print(explainer.explain_borrower_health(borrower_data, ["missed_emi_events"], ["high_regional_npa_pressure"]))

print("\nRecovery narrative:")
print(explainer.generate_recovery_narrative(borrower_data, ["cashflow_coverage_stress"], ["below_peer_cohort"]))

print("\nBorrower guidance:")
print(explainer.generate_borrower_guidance(borrower_data))

print("\nCohort cluster explanation:")
print(explainer.explain_cohort_cluster("Jharkhand-Mudra", 14, "Jharkhand", "Mudra", 64))

print("\n✅ Gemini borrower-health smoke test complete")
