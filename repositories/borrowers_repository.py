from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from db import get_supabase


class BorrowerRepository:
    """Borrower status store with Supabase support and in-memory fallback."""

    def __init__(self) -> None:
        self.client = get_supabase()
        self._fallback_borrowers: Dict[str, Dict] = {}
        self._fallback_actions: List[Dict] = []

    def _disable_remote(self) -> None:
        self.client = None

    def _now(self) -> str:
        return datetime.utcnow().isoformat()

    def ensure_borrower(self, borrower_id: str, name: Optional[str] = None, status: str = "ACTIVE") -> Dict:
        existing = self.get_borrower(borrower_id)
        if existing:
            return existing

        payload = {
            "borrower_id": borrower_id,
            "name": name or borrower_id,
            "risk_score": 0,
            "health_score": 100,
            "status": status,
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        if self.client:
            try:
                self.client.table("borrowers").upsert(payload, on_conflict="borrower_id").execute()
                return self.get_borrower(borrower_id) or payload
            except Exception:
                self._disable_remote()

        self._fallback_borrowers[borrower_id] = payload
        return payload

    def get_borrower(self, borrower_id: str) -> Optional[Dict]:
        if self.client:
            try:
                res = self.client.table("borrowers").select("*").eq("borrower_id", borrower_id).limit(1).execute()
                rows = res.data or []
                return rows[0] if rows else None
            except Exception:
                self._disable_remote()
        return self._fallback_borrowers.get(borrower_id)

    def upsert_borrower_risk(
        self,
        borrower_id: str,
        risk_score: int,
        health_score: int,
        name: Optional[str] = None,
        default_status: str = "ACTIVE",
    ) -> Dict:
        existing = self.ensure_borrower(borrower_id, name, status=default_status)
        payload = {
            "borrower_id": borrower_id,
            "name": existing.get("name") or name or borrower_id,
            "risk_score": int(risk_score),
            "health_score": int(health_score),
            "status": existing.get("status", default_status),
            "updated_at": self._now(),
        }
        if self.client:
            try:
                self.client.table("borrowers").upsert(payload, on_conflict="borrower_id").execute()
                return self.get_borrower(borrower_id) or payload
            except Exception:
                self._disable_remote()

        merged = {**existing, **payload}
        self._fallback_borrowers[borrower_id] = merged
        return merged

    def set_status(self, borrower_id: str, status: str, reason: str, performed_by: str = "system") -> Dict:
        borrower = self.ensure_borrower(borrower_id)
        update = {"status": status, "updated_at": self._now()}
        if self.client:
            try:
                self.client.table("borrowers").update(update).eq("borrower_id", borrower_id).execute()
                self.client.table("borrower_actions").insert(
                    {
                        "borrower_id": borrower_id,
                        "action_type": status,
                        "reason": reason,
                        "performed_by": performed_by,
                        "timestamp": self._now(),
                    }
                ).execute()
                return self.get_borrower(borrower_id) or {**borrower, **update}
            except Exception:
                self._disable_remote()

        borrower.update(update)
        self._fallback_borrowers[borrower_id] = borrower
        self._fallback_actions.append(
            {
                "borrower_id": borrower_id,
                "action_type": status,
                "reason": reason,
                "performed_by": performed_by,
                "timestamp": self._now(),
            }
        )
        return borrower

    def list_borrowers(self) -> List[Dict]:
        if self.client:
            try:
                res = self.client.table("borrowers").select("*").order("risk_score", desc=True).execute()
                return res.data or []
            except Exception:
                self._disable_remote()
        return list(self._fallback_borrowers.values())

    def status_count(self, status: str) -> int:
        if self.client:
            try:
                res = self.client.table("borrowers").select("borrower_id", count="exact").eq("status", status).execute()
                return int(res.count or 0)
            except Exception:
                self._disable_remote()
        return len([row for row in self._fallback_borrowers.values() if row.get("status") == status])
