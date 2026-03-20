from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from db import get_supabase


class AccountRepository:
    """Supabase-backed repository with in-process fallback for local dev."""

    def __init__(self) -> None:
        self.client = get_supabase()
        self._fallback_accounts: Dict[str, Dict] = {}
        self._fallback_transactions: List[Dict] = []
        self._fallback_actions: List[Dict] = []

    def _disable_remote(self) -> None:
        """Switch to fallback mode if Supabase becomes unavailable."""
        self.client = None

    def _now(self) -> str:
        return datetime.utcnow().isoformat()

    def ensure_account(self, account_id: str, name: Optional[str] = None, status: str = "ACTIVE") -> Dict:
        existing = self.get_account(account_id)
        if existing:
            return existing
        payload = {
            "account_id": account_id,
            "name": name or account_id,
            "risk_score": 0,
            "status": status,
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        if self.client:
            try:
                self.client.table("accounts").upsert(payload, on_conflict="account_id").execute()
                return self.get_account(account_id) or payload
            except Exception:
                self._disable_remote()
        self._fallback_accounts[account_id] = payload
        return payload

    def upsert_account_risk(
        self,
        account_id: str,
        risk_score: int,
        name: Optional[str] = None,
        default_status: str = "ACTIVE",
    ) -> Dict:
        existing = self.ensure_account(account_id, name, status=default_status)
        payload = {
            "account_id": account_id,
            "name": existing.get("name") or name or account_id,
            "risk_score": int(risk_score),
            "status": existing.get("status", "ACTIVE"),
            "updated_at": self._now(),
        }
        if self.client:
            try:
                self.client.table("accounts").upsert(payload, on_conflict="account_id").execute()
                return self.get_account(account_id) or payload
            except Exception:
                self._disable_remote()
        merged = {**existing, **payload}
        self._fallback_accounts[account_id] = merged
        return merged

    def get_account(self, account_id: str) -> Optional[Dict]:
        if self.client:
            try:
                res = self.client.table("accounts").select("*").eq("account_id", account_id).limit(1).execute()
                rows = res.data or []
                return rows[0] if rows else None
            except Exception:
                self._disable_remote()
        return self._fallback_accounts.get(account_id)

    def freeze_account(self, account_id: str, reason: str, performed_by: str = "system") -> Dict:
        account = self.ensure_account(account_id)
        if self.client:
            try:
                self.client.table("accounts").update({"status": "FROZEN", "updated_at": self._now()}).eq("account_id", account_id).execute()
                self.client.table("account_actions").insert({
                    "account_id": account_id,
                    "action_type": "FREEZE",
                    "reason": reason,
                    "performed_by": performed_by,
                    "timestamp": self._now(),
                }).execute()
                return self.get_account(account_id) or account
            except Exception:
                self._disable_remote()
        account["status"] = "FROZEN"
        account["updated_at"] = self._now()
        self._fallback_accounts[account_id] = account
        self._fallback_actions.append({
            "account_id": account_id,
            "action_type": "FREEZE",
            "reason": reason,
            "performed_by": performed_by,
            "timestamp": self._now(),
        })
        return account

    def unfreeze_account(self, account_id: str, reason: str, performed_by: str = "system") -> Dict:
        account = self.ensure_account(account_id)
        if self.client:
            try:
                self.client.table("accounts").update({"status": "ACTIVE", "updated_at": self._now()}).eq("account_id", account_id).execute()
                self.client.table("account_actions").insert({
                    "account_id": account_id,
                    "action_type": "UNFREEZE",
                    "reason": reason,
                    "performed_by": performed_by,
                    "timestamp": self._now(),
                }).execute()
                return self.get_account(account_id) or account
            except Exception:
                self._disable_remote()
        account["status"] = "ACTIVE"
        account["updated_at"] = self._now()
        self._fallback_accounts[account_id] = account
        self._fallback_actions.append({
            "account_id": account_id,
            "action_type": "UNFREEZE",
            "reason": reason,
            "performed_by": performed_by,
            "timestamp": self._now(),
        })
        return account

    def log_transaction(self, txn: Dict) -> None:
        if self.client:
            try:
                self.client.table("transactions").insert(txn).execute()
                return
            except Exception:
                self._disable_remote()
        self._fallback_transactions.append(txn)

    def list_accounts(self) -> List[Dict]:
        if self.client:
            try:
                res = self.client.table("accounts").select("*").order("risk_score", desc=True).execute()
                return res.data or []
            except Exception:
                self._disable_remote()
        return list(self._fallback_accounts.values())

    def blocked_transactions_count(self) -> int:
        if self.client:
            try:
                res = self.client.table("transactions").select("txn_id", count="exact").eq("status", "BLOCKED").execute()
                return int(res.count or 0)
            except Exception:
                self._disable_remote()
        return len([t for t in self._fallback_transactions if t.get("status") == "BLOCKED"])

    def frozen_accounts_count(self) -> int:
        if self.client:
            try:
                res = self.client.table("accounts").select("account_id", count="exact").eq("status", "FROZEN").execute()
                return int(res.count or 0)
            except Exception:
                self._disable_remote()
        return len([a for a in self._fallback_accounts.values() if a.get("status") == "FROZEN"])
