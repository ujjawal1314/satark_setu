from __future__ import annotations

from datetime import datetime
import json
import time
from typing import List

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import networkx as nx
import pandas as pd

from api_models import BorrowerActionRequest, InterventionSimulationRequest
from detection_engine import SatarkSetuDetector
from repositories import BorrowerRepository


try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


app = FastAPI(title="SatarkSetu - Borrower Health Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

active_connections: List[WebSocket] = []
repo = BorrowerRepository()

borrower_df = pd.read_csv("borrowers.csv")
txn_df = pd.read_csv("loan_transactions.csv", parse_dates=["timestamp"])
regional_df = pd.read_csv("regional_context.csv")

detector = SatarkSetuDetector(borrower_df, txn_df, regional_df)
graph_stats = detector.build_graph()
graph = detector.get_networkx_graph()


def sync_borrower(borrower_id: str, default_status: str = "ACTIVE") -> dict:
    analysis = detector.analyze_borrower(borrower_id).as_dict()
    row = borrower_df[borrower_df["borrower_id"] == borrower_id]
    if row.empty:
        raise HTTPException(status_code=404, detail="Borrower not found")
    repo.upsert_borrower_risk(
        borrower_id,
        risk_score=analysis["risk_score"],
        health_score=analysis["health_score"],
        name=str(row.iloc[0]["name"]),
        default_status=default_status,
    )
    return analysis


def merged_borrower_record(borrower_id: str) -> dict:
    analysis = sync_borrower(borrower_id)
    repo_row = repo.get_borrower(borrower_id) or repo.ensure_borrower(borrower_id, name=analysis["name"])
    profile = borrower_df[borrower_df["borrower_id"] == borrower_id].iloc[0].to_dict()
    profile.update(analysis)
    profile["status"] = repo_row.get("status", "ACTIVE")
    return profile


def stream_events():
    top_borrowers = detector.get_flagged_borrowers(threshold=50)[:80]
    for item in top_borrowers:
        event = {
            "type": "borrower_alert",
            "timestamp": datetime.utcnow().isoformat(),
            "borrower_id": item["borrower_id"],
            "name": item["name"],
            "risk_score": item["risk_score"],
            "health_score": item["health_score"],
            "risk_level": item["risk_level"],
            "region": item["region"],
            "loan_scheme": item["loan_scheme"],
            "behavioral_flags": item["behavioral_flags"],
            "contextual_flags": item["contextual_flags"],
        }
        time.sleep(0.02)
        yield f"data: {json.dumps(event)}\n\n"


@app.get("/")
def root():
    return {
        "service": "SatarkSetu Borrower Health Backend",
        "status": "active",
        "version": "2.0",
        "endpoints": {
            "stats": "/stats",
            "borrowers": "/borrowers",
            "borrower_analysis": "/borrowers/{borrower_id}",
            "stress_clusters": "/clusters",
            "graph_stats": "/graph/stats",
            "support_action": "POST /borrowers/{borrower_id}/support",
            "resolve_action": "POST /borrowers/{borrower_id}/resolve",
            "simulate_intervention": "POST /interventions/simulate",
            "stream": "/stream",
        },
    }


@app.get("/stats")
def stats():
    summary = detector.portfolio_summary()
    return {
        "timestamp": datetime.utcnow().isoformat(),
        **summary,
        "regional_hotspots": len(detector.detect_stress_clusters()),
        "watchlist_borrowers": repo.status_count("WATCHLIST"),
        "support_required_borrowers": repo.status_count("SUPPORT_REQUIRED"),
        "recovering_borrowers": repo.status_count("RECOVERING"),
        "graph": {"nodes": graph.number_of_nodes(), "edges": graph.number_of_edges()},
    }


@app.get("/graph/stats")
def graph_stats_endpoint():
    return {
        "graph": {
            "nodes": graph.number_of_nodes(),
            "edges": graph.number_of_edges(),
            "density": nx.density(graph) if graph.number_of_nodes() > 1 else 0.0,
        },
        "node_types": graph_stats["node_types"],
    }


@app.get("/clusters")
def stress_clusters():
    clusters = detector.detect_stress_clusters()
    return {"count": len(clusters), "clusters": clusters}


@app.get("/borrowers")
def borrowers(min_risk: int = 0, limit: int = 100):
    records = []
    for borrower_id in borrower_df["borrower_id"]:
        analysis = sync_borrower(borrower_id)
        if analysis["risk_score"] < min_risk:
            continue
        repo_row = repo.get_borrower(borrower_id) or {}
        records.append({**analysis, "status": repo_row.get("status", "ACTIVE")})
    records.sort(key=lambda row: row["risk_score"], reverse=True)
    return {"count": len(records), "borrowers": records[:limit]}


@app.get("/borrowers/{borrower_id}")
def borrower_analysis(borrower_id: str):
    if borrower_id not in set(borrower_df["borrower_id"]):
        raise HTTPException(status_code=404, detail="Borrower not found")

    record = merged_borrower_record(borrower_id)
    txns = txn_df[txn_df["borrower_id"] == borrower_id].sort_values("timestamp")
    record["recent_transactions"] = txns.tail(12).to_dict("records")
    record["graph_degree"] = graph.degree(borrower_id) if borrower_id in graph else 0
    return record


@app.get("/borrowers/{borrower_id}/status")
def borrower_status(borrower_id: str):
    borrower = repo.get_borrower(borrower_id)
    if not borrower:
        sync_borrower(borrower_id)
        borrower = repo.get_borrower(borrower_id)
    if not borrower:
        raise HTTPException(status_code=404, detail="Borrower not found")
    return borrower


@app.post("/borrowers/{borrower_id}/support")
def mark_support_required(borrower_id: str, req: BorrowerActionRequest | None = None):
    analysis = sync_borrower(borrower_id, default_status="SUPPORT_REQUIRED")
    request = req or BorrowerActionRequest()
    borrower = repo.set_status(
        borrower_id,
        status="SUPPORT_REQUIRED",
        reason=request.reason,
        performed_by=request.performed_by,
    )
    return {"borrower": borrower, "analysis": analysis, "message": "Borrower marked for support review"}


@app.post("/borrowers/{borrower_id}/resolve")
def mark_recovering(borrower_id: str, req: BorrowerActionRequest | None = None):
    analysis = sync_borrower(borrower_id, default_status="RECOVERING")
    request = req or BorrowerActionRequest(reason="Borrower moved to recovery monitoring")
    borrower = repo.set_status(
        borrower_id,
        status="RECOVERING",
        reason=request.reason,
        performed_by=request.performed_by,
    )
    return {"borrower": borrower, "analysis": analysis, "message": "Borrower moved to recovery monitoring"}


@app.post("/interventions/simulate")
def simulate_intervention(req: InterventionSimulationRequest):
    if req.borrower_id not in set(borrower_df["borrower_id"]):
        raise HTTPException(status_code=404, detail="Borrower not found")
    current = detector.analyze_borrower(req.borrower_id).as_dict()
    improved_risk = max(0, current["risk_score"] - int(round(req.expected_impact)))
    improved_health = min(100, current["health_score"] + int(round(req.expected_impact)))
    return {
        "borrower_id": req.borrower_id,
        "support_type": req.support_type,
        "current_risk_score": current["risk_score"],
        "projected_risk_score": improved_risk,
        "current_health_score": current["health_score"],
        "projected_health_score": improved_health,
    }


@app.get("/stream")
def stream():
    return StreamingResponse(
        stream_events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@app.get("/stream/test")
def stream_test():
    events = []
    for item in detector.get_flagged_borrowers(threshold=60)[:5]:
        events.append(
            {
                "borrower_id": item["borrower_id"],
                "risk_score": item["risk_score"],
                "risk_level": item["risk_level"],
                "region": item["region"],
            }
        )
    return {"message": "Borrower alert stream test", "count": len(events), "events": events}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        await websocket.send_json(
            {
                "type": "connection",
                "message": "Connected to SatarkSetu borrower health backend",
                "stats": detector.portfolio_summary(),
            }
        )
        for item in detector.get_flagged_borrowers(threshold=60)[:25]:
            await websocket.send_json({"type": "borrower_alert", **item})
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)


if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting SatarkSetu Borrower Health Backend...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
