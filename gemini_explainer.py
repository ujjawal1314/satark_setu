from __future__ import annotations

import json
import os
import sys
from typing import Iterable, Optional

try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover
    genai = None

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    def load_dotenv():
        return None


if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

load_dotenv()


class GeminiExplainer:
    def __init__(self):
        self.api_available = False
        self.model = None
        self.text_model = None

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your_api_key_here" or genai is None:
            return

        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(
                "gemini-2.5-flash",
                generation_config={"response_mime_type": "application/json"},
            )
            self.text_model = genai.GenerativeModel("gemini-2.5-flash")
            self.api_available = True
        except Exception:
            self.model = None
            self.text_model = None
            self.api_available = False

    def _risk_tone(self, risk_score: int) -> str:
        if risk_score >= 70:
            return "high risk"
        if risk_score >= 45:
            return "moderate risk"
        return "low risk"

    def _flags_to_text(self, flags: Optional[Iterable[str]]) -> str:
        values = [str(flag) for flag in (flags or []) if flag]
        return ", ".join(values) if values else "none"

    def _fallback_borrower_explanation(self, borrower_data, behavioral_flags, contextual_flags, cohort_data=None) -> str:
        borrower_id = borrower_data.get("borrower_id", "Unknown")
        risk_score = int(borrower_data.get("risk_score", 0))
        health_score = int(borrower_data.get("health_score", max(0, 100 - risk_score)))
        peer_score = int(borrower_data.get("peer_score", health_score))
        tone = self._risk_tone(risk_score)

        recommendation = (
            "Priority outreach and restructuring review are recommended."
            if risk_score >= 70
            else "Active monitoring and borrower follow-up are recommended."
            if risk_score >= 45
            else "Routine monitoring is sufficient at this stage."
        )

        cohort_line = ""
        if cohort_data:
            size = cohort_data.get("size")
            region = cohort_data.get("region")
            scheme = cohort_data.get("loan_scheme")
            parts = [part for part in [scheme, region] if part]
            label = " / ".join(parts) if parts else "peer cohort"
            cohort_line = f"The borrower is being compared against the {label} cohort"
            if size:
                cohort_line += f" ({size} borrowers)"
            cohort_line += ". "

        return (
            f"Borrower `{borrower_id}` is currently classified as {tone} with a risk score of {risk_score}/100 "
            f"and a health score of {health_score}/100. "
            f"Behavioral signals: {self._flags_to_text(behavioral_flags)}. "
            f"Contextual signals: {self._flags_to_text(contextual_flags)}. "
            f"{cohort_line}"
            f"The peer benchmark is {peer_score}/100, which helps separate borrower-specific stress from wider regional or cohort pressure. "
            f"{recommendation}"
        )

    def explain_borrower_health(self, borrower_data, behavioral_flags=None, contextual_flags=None, cohort_data=None):
        borrower_id = borrower_data.get("borrower_id", "Unknown")
        risk_score = int(borrower_data.get("risk_score", 0))

        if not self.api_available:
            return self._fallback_borrower_explanation(borrower_data, behavioral_flags, contextual_flags, cohort_data)

        prompt = f"""Analyze this borrower health case and return JSON.
Borrower ID: {borrower_id}
Risk Score: {risk_score}
Health Score: {borrower_data.get('health_score')}
Peer Score: {borrower_data.get('peer_score')}
Behavioral Flags: {self._flags_to_text(behavioral_flags)}
Contextual Flags: {self._flags_to_text(contextual_flags)}
Cohort Data: {json.dumps(cohort_data or {})}

Return JSON with:
{{
  "analysis": "One concise paragraph",
  "action": "One sentence recommendation"
}}"""
        try:
            response = self.model.generate_content(prompt)
            data = json.loads(response.text)
            return f"{data.get('analysis', '')} {data.get('action', '')}".strip()
        except Exception:
            return self._fallback_borrower_explanation(borrower_data, behavioral_flags, contextual_flags, cohort_data)

    def explain_cohort_cluster(self, cluster_id, borrower_count, region, loan_scheme, average_risk):
        if not self.api_available:
            return (
                f"Cluster `{cluster_id}` represents {borrower_count} borrowers in {region} under {loan_scheme} "
                f"with an average risk of {average_risk}/100. This cluster should be reviewed as a regional or scheme-level stress pocket."
            )

        prompt = f"""Explain this borrower stress cluster in plain language and return JSON.
Cluster ID: {cluster_id}
Borrowers: {borrower_count}
Region: {region}
Loan Scheme: {loan_scheme}
Average Risk: {average_risk}

Return JSON:
{{"summary": "2 sentences", "recommended_action": "1 sentence"}}"""
        try:
            response = self.model.generate_content(prompt)
            data = json.loads(response.text)
            return f"{data.get('summary', '')} {data.get('recommended_action', '')}".strip()
        except Exception:
            return (
                f"Cluster `{cluster_id}` in {region} / {loan_scheme} shows above-normal portfolio stress. "
                "Targeted borrower outreach and portfolio review are recommended."
            )

    def generate_borrower_guidance(self, borrower_data, behavioral_flags=None, contextual_flags=None):
        borrower_id = borrower_data.get("borrower_id", "Unknown")
        risk_score = int(borrower_data.get("risk_score", 0))
        if not self.api_available:
            return (
                f"Borrower guidance for `{borrower_id}`: maintain repayment discipline, monitor monthly cash flow, "
                f"and contact the bank early if business inflows weaken. Current risk: {risk_score}/100."
            )

        prompt = f"""Generate supportive borrower guidance.
Borrower ID: {borrower_id}
Risk Score: {risk_score}
Behavioral Flags: {self._flags_to_text(behavioral_flags)}
Contextual Flags: {self._flags_to_text(contextual_flags)}

Return JSON:
{{"guidance": "3 short actionable sentences"}}"""
        try:
            response = self.model.generate_content(prompt)
            data = json.loads(response.text)
            return data.get("guidance", "")
        except Exception:
            return (
                f"Borrower guidance for `{borrower_id}`: maintain repayment discipline, monitor monthly cash flow, "
                "and contact the bank early if business inflows weaken."
            )

    def generate_recovery_narrative(self, borrower_data, behavioral_flags=None, contextual_flags=None):
        borrower_id = borrower_data.get("borrower_id", "Unknown")
        risk_score = int(borrower_data.get("risk_score", 0))
        if not self.api_available:
            return (
                f"Recovery note for `{borrower_id}`: risk is {risk_score}/100 with behavioral indicators "
                f"{self._flags_to_text(behavioral_flags)} and contextual indicators {self._flags_to_text(contextual_flags)}. "
                "The case should be reviewed for proactive support, repayment planning, and regional context before escalation."
            )

        prompt = f"""Write a concise recovery case narrative and return JSON.
Borrower ID: {borrower_id}
Risk Score: {risk_score}
Behavioral Flags: {self._flags_to_text(behavioral_flags)}
Contextual Flags: {self._flags_to_text(contextual_flags)}

Return JSON:
{{"summary": "2 sentences", "recommendation": "1 sentence"}}"""
        try:
            response = self.model.generate_content(prompt)
            data = json.loads(response.text)
            return f"{data.get('summary', '')} {data.get('recommendation', '')}".strip()
        except Exception:
            return (
                f"Recovery note for `{borrower_id}`: risk is {risk_score}/100 with behavioral indicators "
                f"{self._flags_to_text(behavioral_flags)} and contextual indicators {self._flags_to_text(contextual_flags)}. "
                "The case should be reviewed for proactive support."
            )

    def suggest_investigation_steps(self, borrower_data, flags=None):
        borrower_id = borrower_data.get("borrower_id", "Unknown")
        steps = [
            f"Review the last 90 days of repayment behavior for `{borrower_id}`.",
            "Compare recent cash-flow stability against the peer cohort baseline.",
            "Decide whether early support or restructuring review is appropriate.",
        ]
        if not self.api_available:
            return "\n".join(f"- {step}" for step in steps)
        try:
            prompt = f"Suggest 3 brief investigation steps for borrower {borrower_id} with flags {self._flags_to_text(flags)}."
            response = self.text_model.generate_content(prompt)
            return response.text
        except Exception:
            return "\n".join(f"- {step}" for step in steps)

    def explain_prevention_tips(self, topic: str) -> str:
        fallback = (
            "- Track monthly cash flow against EMI obligations.\n"
            "- Contact the bank before missed payments start accumulating.\n"
            "- Use peer and regional context to interpret stress early."
        )
        if not self.api_available:
            return fallback
        try:
            prompt = f"Provide 3 concise prevention tips about '{topic}' for borrower health monitoring."
            response = self.text_model.generate_content(prompt)
            return response.text
        except Exception:
            return fallback
