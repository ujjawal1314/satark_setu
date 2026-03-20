from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import networkx as nx
import numpy as np
import pandas as pd


def _clip(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return float(max(low, min(high, value)))


@dataclass
class BorrowerAnalysis:
    borrower_id: str
    name: str
    region: str
    loan_scheme: str
    risk_score: int
    health_score: int
    peer_score: int
    regional_stress_factor: float
    risk_level: str
    behavioral_flags: List[str]
    contextual_flags: List[str]
    recommendation: str
    graph_degree: int
    gnn_risk_score: int

    def as_dict(self) -> Dict:
        return {
            "borrower_id": self.borrower_id,
            "name": self.name,
            "region": self.region,
            "loan_scheme": self.loan_scheme,
            "risk_score": self.risk_score,
            "health_score": self.health_score,
            "peer_score": self.peer_score,
            "regional_stress_factor": self.regional_stress_factor,
            "risk_level": self.risk_level,
            "behavioral_flags": self.behavioral_flags,
            "contextual_flags": self.contextual_flags,
            "recommendation": self.recommendation,
            "graph_degree": self.graph_degree,
            "gnn_risk_score": self.gnn_risk_score,
        }


class SatarkSetuDetector:
    """Borrower-health scoring engine for SatarkSetu."""

    def __init__(self, borrower_df: pd.DataFrame, txn_df: pd.DataFrame, regional_df: Optional[pd.DataFrame] = None):
        self.borrower_df = borrower_df.copy()
        self.txn_df = txn_df.copy()
        self.regional_df = regional_df.copy() if regional_df is not None else self._derive_regional_context(self.borrower_df)

        self.txn_df["timestamp"] = pd.to_datetime(self.txn_df["timestamp"])
        self.borrower_df["loan_amount"] = self.borrower_df["loan_amount"].astype(float)
        self.borrower_df["emi_amount"] = self.borrower_df["emi_amount"].astype(float)
        self.borrower_df["outstanding_amount"] = self.borrower_df["outstanding_amount"].astype(float)
        self.borrower_df["current_balance"] = self.borrower_df["current_balance"].astype(float)
        self.borrower_df["regional_stress_factor"] = self.borrower_df["regional_stress_factor"].astype(float)
        self.borrower_df["repayment_consistency"] = self.borrower_df["repayment_consistency"].astype(float)
        self.borrower_df["inflow_stability"] = self.borrower_df["inflow_stability"].astype(float)
        self.borrower_df["balance_trend"] = self.borrower_df["balance_trend"].astype(float)

        self.regional_lookup = self.regional_df.set_index("region").to_dict("index")
        self.borrower_lookup = self.borrower_df.set_index("borrower_id")
        self.graph = nx.Graph()
        self.analysis_cache: Dict[str, BorrowerAnalysis] = {}

    def _derive_regional_context(self, borrower_df: pd.DataFrame) -> pd.DataFrame:
        grouped = borrower_df.groupby("region", as_index=False).agg(
            regional_stress_factor=("regional_stress_factor", "mean"),
            peer_health_baseline=("peer_score", "mean"),
        )
        grouped["npa_rate"] = grouped["regional_stress_factor"] * 10
        grouped["economic_stress_index"] = grouped["regional_stress_factor"]
        return grouped

    def build_graph(self) -> Dict[str, object]:
        self.graph = nx.Graph()

        for row in self.borrower_df.itertuples(index=False):
            borrower_id = row.borrower_id
            scheme_node = f"SCHEME::{row.loan_scheme}"
            region_node = f"REGION::{row.region}"
            category_node = f"CATEGORY::{row.borrower_category}"

            self.graph.add_node(borrower_id, type="borrower")
            self.graph.add_node(scheme_node, type="scheme")
            self.graph.add_node(region_node, type="region")
            self.graph.add_node(category_node, type="category")

            self.graph.add_edge(borrower_id, scheme_node, relation="loan_scheme")
            self.graph.add_edge(borrower_id, region_node, relation="region")
            self.graph.add_edge(borrower_id, category_node, relation="borrower_category")

        for (_, group) in self.borrower_df.groupby(["loan_scheme", "region", "amount_band"]):
            borrowers = group["borrower_id"].tolist()
            for left, right in zip(borrowers, borrowers[1:]):
                self.graph.add_edge(left, right, relation="peer")

        self._compute_gnn_embeddings()

        return {
            "database": "networkx",
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "node_types": pd.Series(nx.get_node_attributes(self.graph, "type")).value_counts().to_dict(),
        }

    def _compute_gnn_embeddings(self) -> None:
        node_risk = {}
        for node in self.graph.nodes:
            if str(node).startswith("SCHEME::") or str(node).startswith("REGION::") or str(node).startswith("CATEGORY::"):
                node_risk[node] = 45.0
            else:
                try:
                    base_h = self._base_health_score(node)
                    node_risk[node] = _clip(100.0 - base_h)
                except Exception:
                    node_risk[node] = 45.0

        for _ in range(2):
            new_risk = {}
            for node in self.graph.nodes:
                neighbors = list(self.graph.neighbors(node))
                if not neighbors:
                    new_risk[node] = node_risk[node]
                else:
                    neighbor_risks = [node_risk[n] for n in neighbors]
                    new_risk[node] = 0.65 * node_risk[node] + 0.35 * float(np.mean(neighbor_risks))
            node_risk = new_risk

        self.gnn_risk_embeddings = node_risk

    def _borrower_row(self, borrower_id: str) -> pd.Series:
        return self.borrower_lookup.loc[borrower_id]

    def _borrower_txns(self, borrower_id: str) -> pd.DataFrame:
        return self.txn_df[self.txn_df["borrower_id"] == borrower_id].sort_values("timestamp")

    def extract_behavioral_features(self, borrower_id: str) -> Dict[str, float]:
        row = self._borrower_row(borrower_id)
        txns = self._borrower_txns(borrower_id)
        emi_txns = txns[txns["transaction_type"] == "EMI_PAYMENT"]
        inflows = txns[txns["transaction_type"] == "BUSINESS_INFLOW"]["amount"]
        outflows = txns[txns["transaction_type"] == "BUSINESS_OUTFLOW"]["amount"]

        payment_delay_ratio = float((emi_txns["status"] != "ON_TIME").mean()) if not emi_txns.empty else 0.0
        missed_ratio = float((emi_txns["status"] == "MISSED").mean()) if not emi_txns.empty else 0.0
        coverage_ratio = float(inflows.sum() / max(row["emi_amount"] * max(len(emi_txns), 1), 1.0))
        inflow_volatility = float(inflows.std(ddof=0) / max(inflows.mean(), 1.0)) if len(inflows) > 1 else 0.0
        net_cashflow = float(inflows.sum() - outflows.sum())

        return {
            "payment_delay_ratio": payment_delay_ratio,
            "missed_ratio": missed_ratio,
            "coverage_ratio": coverage_ratio,
            "inflow_volatility": inflow_volatility,
            "net_cashflow": net_cashflow,
            "days_past_due": float(row["days_past_due"]),
            "missed_payments_90d": float(row["missed_payments_90d"]),
            "repayment_consistency": float(row["repayment_consistency"]),
            "inflow_stability": float(row["inflow_stability"]),
            "balance_trend": float(row["balance_trend"]),
        }

    def _base_health_score(self, borrower_id: str) -> float:
        row = self._borrower_row(borrower_id)
        features = self.extract_behavioral_features(borrower_id)

        health = 100.0
        health -= features["payment_delay_ratio"] * 22
        health -= features["missed_ratio"] * 28
        health -= features["missed_payments_90d"] * 4.8
        health -= min(features["days_past_due"], 90) * 0.34
        health -= max(0.0, 0.72 - features["repayment_consistency"]) * 45
        health -= max(0.0, 0.7 - features["inflow_stability"]) * 32
        health -= max(0.0, -features["balance_trend"]) * 55
        health -= max(0.0, 1.0 - features["coverage_ratio"]) * 18
        health -= max(0.0, features["inflow_volatility"] - 0.35) * 14
        health += min(8.0, max(0.0, row["current_balance"] / max(row["emi_amount"] * 6, 1.0)))
        return _clip(health)

    def _peer_baseline(self, borrower_id: str) -> float:
        row = self._borrower_row(borrower_id)
        peers = self.borrower_df[
            (self.borrower_df["loan_scheme"] == row["loan_scheme"])
            & (self.borrower_df["amount_band"] == row["amount_band"])
            & (self.borrower_df["borrower_id"] != borrower_id)
        ]
        if peers.empty:
            return float(row["peer_score"])
        peer_scores = [self._base_health_score(peer_id) for peer_id in peers["borrower_id"].head(40)]
        return float(np.mean(peer_scores))

    def detect_behavioral_anomalies(self, borrower_id: str) -> List[str]:
        features = self.extract_behavioral_features(borrower_id)
        flags: List[str] = []
        if features["payment_delay_ratio"] >= 0.34:
            flags.append("repayment_delay_pattern")
        if features["missed_ratio"] >= 0.16 or features["missed_payments_90d"] >= 2:
            flags.append("missed_emi_events")
        if features["coverage_ratio"] < 1.05:
            flags.append("cashflow_coverage_stress")
        if features["inflow_stability"] < 0.62 or features["inflow_volatility"] > 0.42:
            flags.append("unstable_business_inflows")
        if features["balance_trend"] < -0.12:
            flags.append("declining_balance_trend")
        if features["days_past_due"] >= 30:
            flags.append("rising_days_past_due")
        return flags

    def detect_contextual_anomalies(self, borrower_id: str) -> List[str]:
        row = self._borrower_row(borrower_id)
        base_health = self._base_health_score(borrower_id)
        peer_baseline = self._peer_baseline(borrower_id)
        region_meta = self.regional_lookup.get(row["region"], {})
        regional_stress = float(region_meta.get("regional_stress_factor", row["regional_stress_factor"]))
        flags: List[str] = []
        if peer_baseline - base_health > 12:
            flags.append("below_peer_cohort")
        if regional_stress >= 0.65:
            flags.append("high_regional_npa_pressure")
        if row["outstanding_amount"] / max(row["loan_amount"], 1.0) > 0.72:
            flags.append("high_outstanding_exposure")
        if row["loan_scheme"] in {"PMEGP", "Mudra"} and regional_stress > 0.55:
            flags.append("scheme_region_stress_overlap")
        return flags

    def calculate_health_score(self, borrower_id: str) -> int:
        analysis = self.analyze_borrower(borrower_id)
        return analysis.health_score

    def calculate_risk_score(self, borrower_id: str) -> int:
        analysis = self.analyze_borrower(borrower_id)
        return analysis.risk_score

    def risk_level(self, risk_score: int) -> str:
        if risk_score >= 70:
            return "High Risk"
        if risk_score >= 45:
            return "Moderate Risk"
        return "Low Risk"

    def recommendation_for(self, risk_score: int, behavioral_flags: List[str], contextual_flags: List[str]) -> str:
        if risk_score >= 70:
            return "Start assisted recovery outreach, review restructuring eligibility, and place the borrower on the priority watchlist."
        if risk_score >= 45:
            return "Monitor monthly cash-flow performance, send proactive reminders, and assign follow-up from the branch recovery team."
        if "high_regional_npa_pressure" in contextual_flags:
            return "Maintain normal servicing while tracking regional pressure; use supportive nudges instead of escalation."
        return "Borrower appears stable. Continue routine portfolio monitoring."

    def analyze_borrower(self, borrower_id: str) -> BorrowerAnalysis:
        if borrower_id in self.analysis_cache:
            return self.analysis_cache[borrower_id]

        row = self._borrower_row(borrower_id)
        base_health = self._base_health_score(borrower_id)
        peer_score = self._peer_baseline(borrower_id)
        region_meta = self.regional_lookup.get(row["region"], {})
        regional_stress = float(region_meta.get("regional_stress_factor", row["regional_stress_factor"]))
        regional_adjustment = (0.45 - regional_stress) * 20
        peer_deviation_adjustment = max(0.0, peer_score - base_health) * 0.42
        adjusted_health = _clip(base_health + regional_adjustment - peer_deviation_adjustment)
        base_risk_score = int(round(_clip(100 - adjusted_health)))
        
        gnn_risk = 0
        if hasattr(self, "gnn_risk_embeddings") and borrower_id in self.gnn_risk_embeddings:
            gnn_risk = int(round(self.gnn_risk_embeddings[borrower_id]))
            
        final_risk_score = int(0.7 * base_risk_score + 0.3 * gnn_risk)
        final_health_score = 100 - final_risk_score

        behavioral_flags = self.detect_behavioral_anomalies(borrower_id)
        contextual_flags = self.detect_contextual_anomalies(borrower_id)
        risk_level = self.risk_level(final_risk_score)
        recommendation = self.recommendation_for(final_risk_score, behavioral_flags, contextual_flags)
        graph_degree = self.graph.degree(borrower_id) if borrower_id in self.graph else 0

        analysis = BorrowerAnalysis(
            borrower_id=borrower_id,
            name=str(row["name"]),
            region=str(row["region"]),
            loan_scheme=str(row["loan_scheme"]),
            risk_score=final_risk_score,
            health_score=final_health_score,
            peer_score=int(round(peer_score)),
            regional_stress_factor=round(regional_stress, 2),
            risk_level=risk_level,
            behavioral_flags=behavioral_flags,
            contextual_flags=contextual_flags,
            recommendation=recommendation,
            graph_degree=graph_degree,
            gnn_risk_score=gnn_risk,
        )
        self.analysis_cache[borrower_id] = analysis
        return analysis

    def get_flagged_borrowers(self, threshold: int = 45) -> List[Dict]:
        flagged = []
        for borrower_id in self.borrower_df["borrower_id"]:
            analysis = self.analyze_borrower(borrower_id)
            if analysis.risk_score >= threshold:
                flagged.append(analysis.as_dict())
        return sorted(flagged, key=lambda row: row["risk_score"], reverse=True)

    def get_flagged_accounts(self, threshold: int = 45) -> List[Dict]:
        return self.get_flagged_borrowers(threshold)

    def detect_stress_clusters(self) -> List[Dict]:
        cluster_rows = []
        for (region, scheme), group in self.borrower_df.groupby(["region", "loan_scheme"]):
            risks = [self.calculate_risk_score(borrower_id) for borrower_id in group["borrower_id"]]
            if len(group) >= 8 and np.mean(risks) >= 48:
                cluster_rows.append(
                    {
                        "cluster_id": f"{region}-{scheme}".replace(" ", "_"),
                        "region": region,
                        "loan_scheme": scheme,
                        "borrower_count": int(len(group)),
                        "average_risk": round(float(np.mean(risks)), 1),
                        "average_health": round(float(100 - np.mean(risks)), 1),
                    }
                )
        return sorted(cluster_rows, key=lambda row: row["average_risk"], reverse=True)

    def detect_mule_rings(self) -> List[Dict]:
        return self.detect_stress_clusters()

    def portfolio_summary(self) -> Dict[str, float]:
        analyses = [self.analyze_borrower(borrower_id) for borrower_id in self.borrower_df["borrower_id"]]
        risks = np.array([analysis.risk_score for analysis in analyses])
        health = np.array([analysis.health_score for analysis in analyses])
        return {
            "total_borrowers": int(len(analyses)),
            "average_risk": round(float(risks.mean()), 1),
            "average_health": round(float(health.mean()), 1),
            "high_risk_borrowers": int((risks >= 70).sum()),
            "moderate_risk_borrowers": int(((risks >= 45) & (risks < 70)).sum()),
            "low_risk_borrowers": int((risks < 45).sum()),
        }

    def get_networkx_graph(self) -> nx.Graph:
        return self.graph


if __name__ == "__main__":
    borrowers = pd.read_csv("borrowers.csv")
    transactions = pd.read_csv("loan_transactions.csv")
    regional = pd.read_csv("regional_context.csv")

    detector = SatarkSetuDetector(borrowers, transactions, regional)
    stats = detector.build_graph()
    print("SatarkSetu detector ready")
    print(stats)
    print(detector.get_flagged_borrowers(threshold=60)[:5])
