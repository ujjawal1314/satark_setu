"""
SatarkSetu — FastAPI Backend
Serves AI risk analysis for any borrower on demand
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from dotenv import load_dotenv
from model import RiskNet
from pipeline import engineer_features, risk_band, recovery_action
import os
import numpy as np
import traceback

# ─────────────────────────────────────────────
# STARTUP — load env, connect Supabase, load model
# ─────────────────────────────────────────────
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Load RiskNet ONCE at startup — stays in memory
model = RiskNet()
print("✅ RiskNet model loaded and ready")

app = FastAPI(title="SatarkSetu Risk API", version="1.0.0")

# Allow Streamlit to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "SatarkSetu API is running"}


def compute_risk_score(borrower: dict, transactions: list, regional: dict) -> float:
    # EMI behaviour from transactions
    emi_txns = [t for t in transactions if t.get('transaction_type') == 'EMI_PAYMENT']
    total = len(emi_txns) if emi_txns else 1
    miss_rate = sum(1 for t in emi_txns if t.get('status') == 'MISSED') / total
    delay_rate = sum(1 for t in emi_txns if t.get('status') == 'DELAYED') / total
    
    # Core risk signal — weighted combination of real features
    repayment  = float(borrower.get('repayment_consistency', 0.8))
    missed     = float(borrower.get('missed_payments_90d', 0))
    dpd        = float(borrower.get('days_past_due', 0))
    peer       = float(borrower.get('peer_score', 80))
    stress     = float(borrower.get('regional_stress_factor', 0.5))
    inflow_st  = float(borrower.get('inflow_stability', 0.8))
    
    # Normalise days past due to 0-1
    dpd_norm = min(dpd / 90.0, 1.0)
    # Normalise missed payments to 0-1
    missed_norm = min(missed / 4.0, 1.0)
    # Peer score — lower is riskier, normalise inverted
    peer_norm = 1.0 - (peer / 100.0)
    
    # Weighted risk score
    risk = (
        missed_norm    * 0.30 +
        dpd_norm       * 0.25 +
        miss_rate      * 0.15 +
        delay_rate     * 0.10 +
        (1 - repayment)* 0.10 +
        stress         * 0.05 +
        peer_norm      * 0.03 +
        (1 - inflow_st)* 0.02
    )
    
    return round(float(min(max(risk, 0.0), 1.0)), 4)


@app.get("/analyze/{borrower_id}")
def analyze_borrower(borrower_id: str):
    """
    Run AI risk analysis for a single borrower.
    Called when user clicks 'AI Risk Analysis' button.
    """
    try:
        # 1. Fetch borrower from Supabase
        borrower_res = supabase.table("borrowers") \
            .select("*") \
            .eq("borrower_id", borrower_id) \
            .single() \
            .execute()

        if not borrower_res.data:
            raise HTTPException(status_code=404, detail=f"Borrower {borrower_id} not found")

        borrower = borrower_res.data
        
        numeric_fields = [
            'loan_amount', 'outstanding_amount', 'emi_amount',
            'avg_monthly_inflow', 'avg_monthly_outflow', 'current_balance',
            'repayment_consistency', 'inflow_stability', 'balance_trend',
            'missed_payments_90d', 'days_past_due', 'peer_score',
            'regional_stress_factor'
        ]
        for field in numeric_fields:
            if borrower.get(field) is None:
                borrower[field] = 0.0

        # 2. Fetch transactions for this borrower
        try:
            txn_res = supabase.table("loan_transactions") \
                .select("*") \
                .eq("borrower_id", borrower_id) \
                .execute()
            transactions = txn_res.data or []
        except:
            transactions = []

        # 3. Fetch regional context
        try:
            region_res = supabase.table("regional_context") \
                .select("*") \
                .eq("region", borrower.get("region", "")) \
                .single() \
                .execute()
            regional = region_res.data or {}
        except:
            regional = {}

        # 4. Engineer features
        features = engineer_features(borrower, transactions, regional)

        # 5. Run model inference
        probability = compute_risk_score(borrower, transactions, regional)
        band        = risk_band(probability)
        action      = recovery_action(probability)

        # 6. Return result
        emi_txns = [t for t in transactions if t.get('transaction_type') == 'EMI_PAYMENT']
        miss_rate = sum(1 for t in emi_txns if t.get('status') == 'MISSED') / (len(emi_txns) or 1)
        
        return {
            "borrower_id":      borrower_id,
            "name":             borrower.get("name", "Unknown"),
            "region":           borrower.get("region", "Unknown"),
            "loan_scheme":      borrower.get("loan_scheme", "Unknown"),
            "loan_amount":      borrower.get("loan_amount", 0),
            "outstanding_amount": borrower.get("outstanding_amount", 0),
            "missed_payments":  borrower.get("missed_payments_90d", 0),
            "days_past_due":    borrower.get("days_past_due", 0),
            "risk_probability": round(probability, 4),
            "risk_band":        band,
            "recovery_action":  action,
            "key_signals": {
                "repayment_consistency": round(float(borrower.get("repayment_consistency", 0)), 2),
                "peer_score": round(float(borrower.get("peer_score", 0)), 1),
                "regional_stress": round(float(borrower.get("regional_stress_factor", 0)), 2),
                "txn_miss_rate": round(float(miss_rate if miss_rate > 0 else borrower.get("missed_payments_90d", 0) / 6.0), 3),
                "buffer_ratio": round(float(borrower.get("current_balance", 0) / (borrower.get("emi_amount", 1) + 1)), 2),
                "inflow_stability": round(float(borrower.get("inflow_stability", 0)), 2),
                "days_past_due": int(borrower.get("days_past_due", 0)),
            }
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/narrative/{borrower_id}")
def get_narrative(borrower_id: str):
    try:
        borrower_res = supabase.table("borrowers").select("*").eq("borrower_id", borrower_id).single().execute()
        if not borrower_res.data:
            raise HTTPException(status_code=404, detail=f"Borrower {borrower_id} not found")
        borrower = borrower_res.data
        
        try:
            txn_res = supabase.table("loan_transactions").select("*").eq("borrower_id", borrower_id).execute()
            transactions = txn_res.data or []
        except:
            transactions = []
            
        try:
            region_res = supabase.table("regional_context").select("*").eq("region", borrower.get("region", "")).single().execute()
            regional = region_res.data or {}
        except:
            regional = {}
            
        probability = compute_risk_score(borrower, transactions, regional)
        band = risk_band(probability)
        
        missed = int(borrower.get('missed_payments_90d', 0))
        dpd    = int(borrower.get('days_past_due', 0))
        region = borrower.get('region', 'the region')
        scheme = borrower.get('loan_scheme', 'the scheme')
        stress = float(borrower.get('regional_stress_factor', 0.5))
        peer   = float(borrower.get('peer_score', 80))
        repay  = float(borrower.get('repayment_consistency', 0.8))
        
        narrative = f"""
**Borrower Risk Assessment — {band} Risk ({probability*100:.1f}%)**

This borrower has recorded {missed} missed payment(s) in the last 90 days with {dpd} days past due, indicating {"significant" if missed >= 2 else "moderate" if missed == 1 else "minimal"} repayment stress. Their repayment consistency score of {repay:.2f} {"falls below" if repay < 0.75 else "is within"} the acceptable threshold.

The borrower operates under the {scheme} scheme in {region}, which carries a regional stress factor of {stress:.2f}. Their peer score of {peer:.0f} {"is below" if peer < 78 else "is in line with"} the regional cohort baseline, {"suggesting elevated peer-level credit stress in this segment" if peer < 78 else "suggesting stable peer-level performance"}.

**Recommended Action:** {recovery_action(probability)}. {"Immediate outreach is advised to prevent NPA formation." if probability >= 0.60 else "Monitor closely over the next 30 days for further deterioration signals." if probability >= 0.40 else "Standard portfolio review protocols apply."}
        """
        
        return {"narrative": narrative.strip()}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/explain/{borrower_id}")
def explain_borrower(borrower_id: str):
    """
    Returns feature contribution breakdown for 
    explainability chart.
    """
    try:
        # Fetch borrower
        borrower_res = supabase.table("borrowers") \
            .select("*") \
            .eq("borrower_id", borrower_id) \
            .single() \
            .execute()
        
        if not borrower_res.data:
            raise HTTPException(
                status_code=404, 
                detail=f"Borrower {borrower_id} not found"
            )
        borrower = borrower_res.data
        for field in [
            'loan_amount', 'outstanding_amount', 
            'emi_amount', 'avg_monthly_inflow',
            'avg_monthly_outflow', 'current_balance',
            'repayment_consistency', 'inflow_stability',
            'balance_trend', 'missed_payments_90d',
            'days_past_due', 'peer_score',
            'regional_stress_factor'
        ]:
            if borrower.get(field) is None:
                borrower[field] = 0.0

        # Fetch transactions
        try:
            txn_res = supabase.table("loan_transactions")\
                .select("*") \
                .eq("borrower_id", borrower_id) \
                .execute()
            transactions = txn_res.data or []
        except:
            transactions = []

        # Compute individual feature contributions
        # Each weight matches compute_risk_score()
        missed     = float(
            borrower.get('missed_payments_90d', 0))
        dpd        = float(
            borrower.get('days_past_due', 0))
        repayment  = float(
            borrower.get('repayment_consistency', 0.8))
        stress     = float(
            borrower.get('regional_stress_factor', 0.5))
        peer       = float(
            borrower.get('peer_score', 80))
        inflow_st  = float(
            borrower.get('inflow_stability', 0.8))
        
        emi_txns = [
            t for t in transactions 
            if t.get('transaction_type') == 'EMI_PAYMENT'
        ]
        total = len(emi_txns) if emi_txns else 1
        miss_rate = sum(
            1 for t in emi_txns 
            if t.get('status') == 'MISSED'
        ) / total
        delay_rate = sum(
            1 for t in emi_txns 
            if t.get('status') == 'DELAYED'
        ) / total

        # Raw contributions (before normalisation)
        contributions = {
            "Missed Payments (90d)": 
                round(min(missed / 4.0, 1.0) * 0.30, 4),
            "Days Past Due":         
                round(min(dpd / 90.0, 1.0) * 0.25, 4),
            "EMI Miss Rate":         
                round(miss_rate * 0.15, 4),
            "EMI Delay Rate":        
                round(delay_rate * 0.10, 4),
            "Repayment Consistency": 
                round((1 - repayment) * 0.10, 4),
            "Regional Stress":       
                round(stress * 0.05, 4),
            "Peer Score Gap":        
                round((1 - peer / 100.0) * 0.03, 4),
            "Inflow Instability":    
                round((1 - inflow_st) * 0.02, 4),
        }

        # Convert to percentages of total risk
        total_risk = sum(contributions.values()) or 1
        percentages = {
            k: round((v / total_risk) * 100, 1)
            for k, v in contributions.items()
        }

        # Sort by contribution descending
        sorted_contributions = dict(
            sorted(
                percentages.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
        )

        # Top driver
        top_driver = max(
            contributions, key=contributions.get
        )

        return {
            "borrower_id": borrower_id,
            "feature_contributions": 
                sorted_contributions,
            "raw_contributions": {
                k: round(v, 4) 
                for k, v in contributions.items()
            },
            "top_driver": top_driver,
            "total_risk_score": round(total_risk, 4),
            "explanation_summary": (
                f"The primary driver of risk for this "
                f"borrower is {top_driver}, contributing "
                f"{sorted_contributions[top_driver]:.1f}% "
                f"of the total risk score."
            )
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=str(e)
        )


@app.get("/health")
def health():
    return {"status": "ok", "model": "RiskNet loaded"}


@app.get("/portfolio/summary")
def portfolio_summary():
    """
    Returns risk band distribution across all borrowers.
    Used for dashboard overview.
    """
    res = supabase.table("borrowers") \
        .select("borrower_id, name, region, risk_band, risk_probability, outstanding_amount, recovery_action") \
        .execute()

    borrowers = res.data or []

    bands = {"CRITICAL": [], "HIGH": [], "MODERATE": [], "LOW": []}
    for b in borrowers:
        band = b.get("risk_band", "LOW")
        if band in bands:
            bands[band].append(b)

    at_risk_exposure = sum(
        b["outstanding_amount"] for b in borrowers
        if b.get("risk_band") in ["CRITICAL", "HIGH"]
    )

    return {
        "total_borrowers": len(borrowers),
        "band_counts": {k: len(v) for k, v in bands.items()},
        "at_risk_exposure": round(at_risk_exposure, 2),
        "borrowers": borrowers,
    }


@app.get("/borrowers")
def list_borrowers():
    """Returns all borrowers — used to populate the Streamlit dropdown."""
    res = supabase.table("borrowers") \
        .select("borrower_id, name, region, loan_scheme, risk_band, risk_probability") \
        .order("risk_probability", desc=True) \
        .execute()
    return {"borrowers": res.data or []}
