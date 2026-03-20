import os
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional

try:
    from neo4j import GraphDatabase
except ImportError:  # pragma: no cover
    GraphDatabase = None


class Neo4jService:
    """Neo4j service for persistent Account/TRANSFERRED_TO graph operations."""

    def __init__(self) -> None:
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
        self.database = os.getenv("NEO4J_DATABASE", "neo4j")

        self.driver = None
        self.available = False
        if GraphDatabase is None:
            return

        self._connect()

    def _connect(self) -> bool:
        """Establish (or re-establish) connection to Neo4j."""
        if GraphDatabase is None:
            self.available = False
            return False

        try:
            if self.driver is not None:
                try:
                    self.driver.close()
                except Exception:
                    pass
                self.driver = None

            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            with self.driver.session(database=self.database) as session:
                session.run("RETURN 1").single()
            self.available = True
            self._ensure_constraints()
            return True
        except Exception:
            self.available = False
            return False

    def close(self) -> None:
        if self.driver is not None:
            self.driver.close()

    def ensure_available(self) -> bool:
        if self.available and self.driver is not None:
            return True
        return self._connect()

    def _run(self, query: str, **params):
        if (not self.available or self.driver is None) and not self._connect():
            raise RuntimeError("Neo4j unavailable")
        with self.driver.session(database=self.database) as session:
            return list(session.run(query, **params))

    def _ensure_constraints(self) -> None:
        self._run(
            "CREATE CONSTRAINT account_id_unique IF NOT EXISTS "
            "FOR (a:Account) REQUIRE a.account_id IS UNIQUE"
        )

    def get_account_status(self, account_id: str) -> Optional[str]:
        rows = self._run(
            "MATCH (a:Account {account_id: $account_id}) RETURN a.status AS status",
            account_id=account_id,
        )
        if not rows:
            return None
        return rows[0]["status"]

    def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        rows = self._run(
            """
            MATCH (a:Account {account_id: $account_id})
            RETURN a.account_id AS account_id,
                   coalesce(a.status, 'ACTIVE') AS status,
                   coalesce(a.risk_score, 0) AS risk_score,
                   a.created_at AS created_at,
                   a.frozen_at AS frozen_at
            """,
            account_id=account_id,
        )
        if not rows:
            return None
        return dict(rows[0])

    def freeze_account(self, account_id: str, risk_score: int = 0) -> Optional[Dict[str, Any]]:
        rows = self._run(
            """
            MERGE (a:Account {account_id: $account_id})
            ON CREATE SET a.created_at = timestamp(),
                          a.risk_score = $risk_score
            ON MATCH SET a.risk_score = coalesce(a.risk_score, $risk_score)
            SET a.status = 'FROZEN',
                a.frozen_at = timestamp()
            RETURN a.account_id AS account_id,
                   a.status AS status,
                   a.frozen_at AS frozen_at,
                   coalesce(a.risk_score, 0) AS risk_score
            """,
            account_id=account_id,
            risk_score=int(risk_score),
        )
        if not rows:
            return None
        return dict(rows[0])

    def unfreeze_account(self, account_id: str, risk_score: int = 0) -> Optional[Dict[str, Any]]:
        rows = self._run(
            """
            MERGE (a:Account {account_id: $account_id})
            ON CREATE SET a.created_at = timestamp(),
                          a.risk_score = $risk_score
            ON MATCH SET a.risk_score = coalesce(a.risk_score, $risk_score)
            SET a.status = 'ACTIVE'
            REMOVE a.frozen_at
            RETURN a.account_id AS account_id,
                   a.status AS status,
                   a.frozen_at AS frozen_at,
                   coalesce(a.risk_score, 0) AS risk_score
            """,
            account_id=account_id,
            risk_score=int(risk_score),
        )
        if not rows:
            return None
        return dict(rows[0])

    def _merge_accounts(self, from_id: str, to_id: str, from_risk: int = 0, to_risk: int = 0) -> None:
        self._run(
            """
            MERGE (from:Account {account_id: $from_id})
            ON CREATE SET from.status = 'ACTIVE', from.created_at = timestamp(), from.risk_score = $from_risk
            ON MATCH SET from.risk_score = coalesce(from.risk_score, $from_risk)

            MERGE (to:Account {account_id: $to_id})
            ON CREATE SET to.status = 'ACTIVE', to.created_at = timestamp(), to.risk_score = $to_risk
            ON MATCH SET to.risk_score = coalesce(to.risk_score, $to_risk)
            """,
            from_id=from_id,
            to_id=to_id,
            from_risk=int(from_risk),
            to_risk=int(to_risk),
        )

    def create_transaction(self, from_id: str, to_id: str, amount: float, txn_id: str, risk_score: int = 0) -> Dict[str, Any]:
        # Ensure nodes exist first so status checks are always valid.
        self._merge_accounts(from_id=from_id, to_id=to_id, from_risk=risk_score, to_risk=0)

        from_status = self.get_account_status(from_id) or "ACTIVE"

        blocked_reason = None
        if from_status == "FROZEN":
            blocked_reason = "Source account is frozen"

        rel_status = "BLOCKED" if blocked_reason else "APPROVED"

        self._run(
            """
            MATCH (from:Account {account_id: $from_id})
            MATCH (to:Account {account_id: $to_id})
            CREATE (from)-[:TRANSFERRED_TO {
                txn_id: $txn_id,
                amount: $amount,
                timestamp: timestamp(),
                status: $status,
                risk_score: $risk_score
            }]->(to)
            """,
            from_id=from_id,
            to_id=to_id,
            txn_id=txn_id,
            amount=float(amount),
            status=rel_status,
            risk_score=int(risk_score),
        )

        tx = {
            "txn_id": txn_id,
            "from_account": from_id,
            "to_account": to_id,
            "amount": float(amount),
            "timestamp": datetime.utcnow().isoformat(),
            "status": rel_status,
            "risk_score": int(risk_score),
        }
        return {
            "blocked": rel_status == "BLOCKED",
            "reason": blocked_reason,
            "transaction": tx,
        }

    def fetch_graph(self) -> Dict[str, List[Dict[str, Any]]]:
        rows = self._run(
            """
            MATCH (a:Account)
            OPTIONAL MATCH (a)-[r:TRANSFERRED_TO]->(b:Account)
            RETURN a.account_id AS a_id,
                   a.status AS a_status,
                   coalesce(a.risk_score, 0) AS a_risk,
                   b.account_id AS b_id,
                   b.status AS b_status,
                   coalesce(b.risk_score, 0) AS b_risk,
                   r.txn_id AS txn_id,
                   r.amount AS amount,
                   r.timestamp AS rel_ts,
                   r.status AS rel_status,
                   r.risk_score AS rel_risk
            """
        )

        nodes: Dict[str, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []

        for row in rows:
            a_id = row["a_id"]
            nodes[a_id] = {
                "id": a_id,
                "status": row.get("a_status") or "ACTIVE",
                "risk_score": int(row.get("a_risk") or 0),
            }

            b_id = row.get("b_id")
            if b_id:
                nodes[b_id] = {
                    "id": b_id,
                    "status": row.get("b_status") or "ACTIVE",
                    "risk_score": int(row.get("b_risk") or 0),
                }

            if row.get("txn_id") and b_id:
                edges.append(
                    {
                        "source": a_id,
                        "target": b_id,
                        "txn_id": row["txn_id"],
                        "amount": float(row.get("amount") or 0.0),
                        "timestamp": row.get("rel_ts"),
                        "status": row.get("rel_status") or "APPROVED",
                        "risk_score": int(row.get("rel_risk") or 0),
                    }
                )

        return {"nodes": list(nodes.values()), "edges": edges}


@lru_cache(maxsize=1)
def get_neo4j_service() -> Neo4jService:
    return Neo4jService()
