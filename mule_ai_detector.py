from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd

try:
    import torch
except Exception:  # pragma: no cover
    torch = None


@dataclass
class MuleAIRunResult:
    rings: List[Dict]
    used_ai: bool
    reason: str


class _CheckpointGNN(torch.nn.Module if torch is not None else object):
    """Minimal GNN-compatible runtime matching the checkpoint key layout."""

    def __init__(self, state_dict: Dict[str, "torch.Tensor"]) -> None:
        if torch is None:  # pragma: no cover
            raise RuntimeError("torch unavailable")
        super().__init__()
        self.state_dict_raw = state_dict

        w1 = state_dict["conv1.linear.weight"]
        b1 = state_dict["conv1.linear.bias"]
        w2 = state_dict["conv2.linear.weight"]
        b2 = state_dict["conv2.linear.bias"]
        w3 = state_dict["fc1.weight"]
        b3 = state_dict["fc1.bias"]
        w4 = state_dict["fc2.weight"]
        b4 = state_dict["fc2.bias"]

        self.in_dim = int(w1.shape[1])
        self.h1 = int(w1.shape[0])
        self.h2 = int(w2.shape[0])
        self.fc1_dim = int(w3.shape[0])
        self.out_dim = int(w4.shape[0])

        self.conv1 = torch.nn.Linear(self.in_dim, self.h1)
        self.conv2 = torch.nn.Linear(self.h1, self.h2)
        self.fc1 = torch.nn.Linear(self.h2, self.fc1_dim)
        self.fc2 = torch.nn.Linear(self.fc1_dim, self.out_dim)

        self.conv1.weight.data.copy_(w1)
        self.conv1.bias.data.copy_(b1)
        self.conv2.weight.data.copy_(w2)
        self.conv2.bias.data.copy_(b2)
        self.fc1.weight.data.copy_(w3)
        self.fc1.bias.data.copy_(b3)
        self.fc2.weight.data.copy_(w4)
        self.fc2.bias.data.copy_(b4)

        self.eval()

    @staticmethod
    def _normalized_adjacency(num_nodes: int, edge_index: "torch.Tensor") -> "torch.Tensor":
        adj = torch.zeros((num_nodes, num_nodes), dtype=torch.float32)
        for src, dst in edge_index.t().tolist():
            adj[src, dst] = 1.0
        adj += torch.eye(num_nodes, dtype=torch.float32)
        deg = adj.sum(dim=1)
        deg_inv_sqrt = torch.pow(deg.clamp(min=1.0), -0.5)
        d_inv = torch.diag(deg_inv_sqrt)
        return d_inv @ adj @ d_inv

    def forward(self, x: "torch.Tensor", edge_index: "torch.Tensor") -> "torch.Tensor":
        norm_adj = self._normalized_adjacency(x.shape[0], edge_index)
        x = norm_adj @ x
        x = torch.relu(self.conv1(x))
        x = norm_adj @ x
        x = torch.relu(self.conv2(x))
        graph_emb = x.mean(dim=0, keepdim=True)
        z = torch.relu(self.fc1(graph_emb))
        return self.fc2(z).squeeze(0)

    def predict_proba(self, feat_a: List[float], feat_b: List[float]) -> float:
        x = torch.tensor([feat_a, feat_b], dtype=torch.float32)
        edge_index = torch.tensor([[0, 1, 0, 1], [1, 0, 0, 1]], dtype=torch.long)
        with torch.no_grad():
            logits = self.forward(x, edge_index)
            if logits.ndim == 0:
                return float(torch.sigmoid(logits).item())
            if logits.shape[0] == 1:
                return float(torch.sigmoid(logits[0]).item())
            probs = torch.softmax(logits, dim=0)
            return float(probs[-1].item())


def _normalize_feature_columns(rows: Dict[str, List[float]]) -> Dict[str, List[float]]:
    if not rows:
        return rows
    cols = len(next(iter(rows.values())))
    mins = [float("inf")] * cols
    maxs = [float("-inf")] * cols
    for vals in rows.values():
        for i, v in enumerate(vals):
            mins[i] = min(mins[i], v)
            maxs[i] = max(maxs[i], v)
    out: Dict[str, List[float]] = {}
    for k, vals in rows.items():
        norm = []
        for i, v in enumerate(vals):
            lo = mins[i]
            hi = maxs[i]
            if hi <= lo:
                norm.append(0.0)
            else:
                norm.append((v - lo) / (hi - lo))
        out[k] = norm
    return out


def _build_account_features(cyber_df: pd.DataFrame, txn_df: pd.DataFrame) -> Dict[str, List[float]]:
    txn_g = txn_df.groupby("account_id")
    cyber_g = cyber_df.groupby("account_id")

    all_accounts = set(txn_df["account_id"].astype(str).unique()) | set(cyber_df["account_id"].astype(str).unique())
    features: Dict[str, List[float]] = {}

    for acc in sorted(all_accounts):
        tx = txn_g.get_group(acc) if acc in txn_g.groups else pd.DataFrame(columns=txn_df.columns)
        cy = cyber_g.get_group(acc) if acc in cyber_g.groups else pd.DataFrame(columns=cyber_df.columns)
        feats = [
            float(len(tx)),
            float(tx["amount"].sum()) if not tx.empty else 0.0,
            float(tx["beneficiary"].nunique()) if not tx.empty else 0.0,
            float(len(cy)),
            float(cy["device"].nunique()) if not cy.empty else 0.0,
            float(cy["ip"].nunique()) if not cy.empty else 0.0,
            float((cy["event_type"] == "malware_signal").sum()) if not cy.empty else 0.0,
            float((cy["event_type"] == "foreign_ip").sum()) if not cy.empty else 0.0,
            float((cy["event_type"] == "password_reset").sum()) if not cy.empty else 0.0,
            float((cy["event_type"] == "login_fail").sum()) if not cy.empty else 0.0,
        ]
        features[acc] = feats

    return _normalize_feature_columns(features)


def _account_relationship_maps(
    cyber_df: pd.DataFrame, txn_df: pd.DataFrame
) -> Tuple[Dict[str, set], Dict[str, set], Dict[str, set], Dict[str, set], Dict[str, set], Dict[str, set]]:
    account_to_bens = defaultdict(set)
    ben_to_accounts = defaultdict(set)
    for _, row in txn_df.iterrows():
        acc = str(row["account_id"])
        ben = str(row["beneficiary"])
        account_to_bens[acc].add(ben)
        ben_to_accounts[ben].add(acc)

    account_to_devices = defaultdict(set)
    device_to_accounts = defaultdict(set)
    account_to_ips = defaultdict(set)
    ip_to_accounts = defaultdict(set)
    for _, row in cyber_df.iterrows():
        acc = str(row["account_id"])
        dev = f"DEV_{row['device']}"
        ip = f"IP_{row['ip']}"
        account_to_devices[acc].add(dev)
        account_to_ips[acc].add(ip)
        device_to_accounts[dev].add(acc)
        ip_to_accounts[ip].add(acc)

    return (
        account_to_bens,
        ben_to_accounts,
        account_to_devices,
        device_to_accounts,
        account_to_ips,
        ip_to_accounts,
    )


def _pair_candidates(groups: Iterable[set]) -> List[Tuple[str, str]]:
    out = set()
    for accs in groups:
        if len(accs) < 2:
            continue
        for a, b in combinations(sorted(accs), 2):
            out.add((a, b))
    return sorted(out)


def _limited_pair_candidates(
    ben_to_accounts: Dict[str, set],
    device_to_accounts: Dict[str, set],
    ip_to_accounts: Dict[str, set],
    max_pairs: int = 3000,
) -> List[Tuple[str, str]]:
    """Prioritize strongest structural candidates and cap runtime."""
    weighted = defaultdict(float)

    def add_pairs(groups: Dict[str, set], weight: float, max_group_size: int) -> None:
        for accounts in groups.values():
            if len(accounts) < 2:
                continue
            scoped = sorted(accounts)
            if len(scoped) > max_group_size:
                scoped = scoped[:max_group_size]
            for a, b in combinations(scoped, 2):
                weighted[(a, b)] += weight

    # Beneficiary overlap is strongest; device/ip are secondary.
    add_pairs(ben_to_accounts, weight=2.0, max_group_size=120)
    add_pairs(device_to_accounts, weight=1.0, max_group_size=80)
    add_pairs(ip_to_accounts, weight=1.0, max_group_size=80)

    if not weighted:
        return []

    ranked = sorted(weighted.items(), key=lambda x: (-x[1], x[0][0], x[0][1]))
    return [pair for pair, _ in ranked[:max_pairs]]


def _resize_features(vec: List[float], dim: int) -> List[float]:
    if len(vec) == dim:
        return vec
    if len(vec) > dim:
        return vec[:dim]
    return vec + [0.0] * (dim - len(vec))


@lru_cache(maxsize=1)
def _load_model(model_path: str) -> Optional[_CheckpointGNN]:
    if torch is None:
        return None
    p = Path(model_path)
    if not p.exists():
        return None
    ckpt = torch.load(str(p), map_location="cpu")
    if not isinstance(ckpt, dict):
        return None
    if "model_state_dict" in ckpt and isinstance(ckpt["model_state_dict"], dict):
        sd = ckpt["model_state_dict"]
    elif "state_dict" in ckpt and isinstance(ckpt["state_dict"], dict):
        sd = ckpt["state_dict"]
    else:
        sd = ckpt
    required = {"conv1.linear.weight", "conv2.linear.weight", "fc1.weight", "fc2.weight"}
    if not required.issubset(set(sd.keys())):
        return None
    return _CheckpointGNN(sd)


def detect_mule_rings_with_ai(
    cyber_df: pd.DataFrame,
    txn_df: pd.DataFrame,
    model_path: str = "best_gnn_a_transactions.pth",
    min_prob: float = 0.60,
) -> MuleAIRunResult:
    model = _load_model(model_path)
    if model is None:
        reason = "torch/model unavailable"
        return MuleAIRunResult(rings=[], used_ai=False, reason=reason)

    (
        account_to_bens,
        ben_to_accounts,
        _account_to_devices,
        device_to_accounts,
        _account_to_ips,
        ip_to_accounts,
    ) = _account_relationship_maps(cyber_df, txn_df)

    features = _build_account_features(cyber_df, txn_df)
    candidates = _limited_pair_candidates(
        ben_to_accounts=ben_to_accounts,
        device_to_accounts=device_to_accounts,
        ip_to_accounts=ip_to_accounts,
        max_pairs=3000,
    )

    if not candidates:
        return MuleAIRunResult(rings=[], used_ai=True, reason="no candidate pairs")

    adj = defaultdict(set)
    scored = []
    for a, b in candidates:
        fa = _resize_features(features.get(a, []), model.in_dim)
        fb = _resize_features(features.get(b, []), model.in_dim)
        p = model.predict_proba(fa, fb)
        scored.append((a, b, p))
        if p >= min_prob:
            adj[a].add(b)
            adj[b].add(a)

    # Ensure at least some edges for sparse outputs from conservative thresholds.
    if not any(adj.values()):
        top = sorted(scored, key=lambda x: x[2], reverse=True)[: min(300, len(scored))]
        for a, b, _ in top:
            adj[a].add(b)
            adj[b].add(a)

    visited = set()
    components = []
    for acc in sorted(features.keys()):
        if acc in visited or acc not in adj:
            continue
        stack = [acc]
        comp = set()
        while stack:
            cur = stack.pop()
            if cur in visited:
                continue
            visited.add(cur)
            comp.add(cur)
            for nbr in adj[cur]:
                if nbr not in visited:
                    stack.append(nbr)
        if len(comp) >= 3:
            components.append(sorted(comp))

    suspicious_rings = []
    for comp_accounts in components:
        ben_count = defaultdict(int)
        for acc in comp_accounts:
            for ben in account_to_bens.get(acc, []):
                ben_count[ben] += 1
        shared_beneficiaries = sorted([ben for ben, c in ben_count.items() if c >= 2])
        if not shared_beneficiaries:
            continue
        suspicious_rings.append(
            {
                "accounts": comp_accounts,
                "shared_beneficiaries": shared_beneficiaries,
                "size": len(comp_accounts),
            }
        )

    suspicious_rings = sorted(suspicious_rings, key=lambda r: (-r["size"], r["accounts"][0]))
    for i, ring in enumerate(suspicious_rings):
        ring["ring_id"] = i

    return MuleAIRunResult(rings=suspicious_rings, used_ai=True, reason="ok")
