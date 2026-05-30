# src/api.py
# ─────────────────────────────────────────────────────────────────────────────
# FastAPI backend for the Supply Chain & Procurement Intelligence GraphRAG system.
#
# Endpoints:
#   POST /ask           — GraphRAG question answering
#   GET  /search        — Hybrid similarity search over nodes
#   GET  /graph/{name}  — Return the neighbourhood subgraph of an entity
#   GET  /stats         — Database statistics
#   GET  /health        — Health check
#   POST /cypher        — Run a raw read-only Cypher query (dev mode)
# ─────────────────────────────────────────────────────────────────────────────

import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from dotenv import load_dotenv

from src.db import Neo4jConnection
from src.graphrag import graphrag_answer, retrieve_subgraph, subgraph_to_context
from src.embeddings import find_top_nodes

load_dotenv()

app = FastAPI(
    title="Supply Chain & Procurement Intelligence GraphRAG API",
    description="Knowledge graph-powered question answering and analytics for global supply chain, procurement, risk, and logistics",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single shared connection (FastAPI runs in one process)
db = Neo4jConnection()


# ─────────────────────────────────────────────────────────────────────────────
# Request / Response Models
# ─────────────────────────────────────────────────────────────────────────────

class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=5, example="What is the supply chain risk exposure for Apple Inc due to Taiwan Strait tensions?")
    top_k:    int = Field(default=5, ge=1, le=10, description="Number of starting nodes for graph traversal")
    hops:     int = Field(default=2, ge=1, le=4,  description="Traversal depth from each starting node (1=direct, 2=recommended)")


class QuestionResponse(BaseModel):
    question:        str
    answer:          str
    retrieved_nodes: list[dict]
    context_preview: str          # First 600 chars of context, for transparency


class CypherRequest(BaseModel):
    query: str = Field(..., example="MATCH (s:Supplier) RETURN s.name, s.country LIMIT 5")


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Confirm the API and database are reachable."""
    try:
        count = db.read("MATCH (n) RETURN count(n) AS total")[0]["total"]
        return {"status": "ok", "node_count": count}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/ask", response_model=QuestionResponse)
def ask(req: QuestionRequest):
    """
    Answer a natural language question about supply chain & procurement using GraphRAG.

    The pipeline:
    1. Hybrid (Keyword + Vector) search to find most relevant nodes
    2. Traverse each node's neighbourhood up to `hops` relationship steps
    3. Assemble structured context from subgraph
    4. Use GPT-4o to generate accurate, actionable answer
    """
    try:
        result = graphrag_answer(
            question=req.question,
            db=db,
            top_k=req.top_k,
            hops=req.hops,
        )
        return QuestionResponse(
            question=req.question,
            answer=result["answer"],
            retrieved_nodes=result["retrieved_nodes"],
            context_preview=result["context"][:600] + "..." if len(result["context"]) > 600 else result["context"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search")
def search(
    q: str = Query(..., description="Search term"),
    top_k: int = Query(default=8, ge=1, le=30),
    label: Optional[str] = Query(default=None, description="Filter by node label (Supplier, Manufacturer, Component, RiskEvent, etc.)"),
):
    """
    Hybrid similarity search over graph nodes.

    Useful for exploring entities in the supply chain graph.
    """
    try:
        labels = [label] if label else None
        results = find_top_nodes(q, db, top_k=top_k, labels=labels)
        return {
            "query":   q,
            "results": [
                {
                    "label": r["label"], 
                    "name": r["name"], 
                    "score": round(r["score"], 4),
                    "emb_score": round(r.get("emb_score", 0), 4),
                    "kw_score": round(r.get("kw_score", 0), 4)
                }
                for r in results
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph/{entity_name}")
def get_subgraph(
    entity_name: str,
    label: str = Query(default="Supplier", description="Node label (Supplier, Manufacturer, Component, RiskEvent, ...)"),
    hops: int   = Query(default=2, ge=1, le=4),
):
    """
    Return the neighbourhood subgraph of a named entity as structured text.
    """
    try:
        sg      = retrieve_subgraph(entity_name, label, db, hops=hops)
        context = subgraph_to_context(sg)
        if not context:
            raise HTTPException(status_code=404, detail=f"Entity '{entity_name}' not found as {label}")
        return {"entity": entity_name, "label": label, "context": context}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
def stats():
    """Return counts of nodes and relationship types in the graph."""
    node_counts = db.read("""
        MATCH (n)
        RETURN labels(n)[0] AS label, count(n) AS count
        ORDER BY count DESC
    """)
    rel_counts = db.read("""
        MATCH ()-[r]->()
        RETURN type(r) AS rel_type, count(r) AS count
        ORDER BY count DESC
    """)
    return {
        "nodes":         node_counts,
        "relationships": rel_counts,
    }


@app.post("/cypher")
def run_cypher(req: CypherRequest):
    """
    Execute a raw read-only Cypher query (development & exploration only).
    """
    query_upper = req.query.strip().upper()
    forbidden = ["CREATE", "MERGE", "DELETE", "SET", "REMOVE", "DROP", "CALL", "UNWIND"]
    for word in forbidden:
        if word in query_upper:
            raise HTTPException(
                status_code=400,
                detail=f"Write or unsafe operation '{word}' not permitted on this endpoint."
            )
    try:
        rows = db.read(req.query)
        return {"results": rows, "count": len(rows)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Supply Chain Specific Helper Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/suppliers")
def list_suppliers(tier: Optional[str] = Query(None, description="Filter by tier: Tier1, Tier2, Tier3")):
    """List suppliers with optional tier filter."""
    query = """
        MATCH (s:Supplier)
        WHERE $tier IS NULL OR s.tier = $tier
        RETURN s.name AS name, s.tier AS tier, s.country AS country, 
               s.reliability_score AS reliability, s.esg_rating AS esg
        ORDER BY s.reliability_score DESC
    """
    rows = db.read(query, {"tier": tier})
    return {"suppliers": rows}


@app.get("/risks")
def list_risks(severity: Optional[str] = None):
    """List active risk events."""
    query = """
        MATCH (r:RiskEvent)
        WHERE $severity IS NULL OR r.severity = $severity
        RETURN r.name AS risk, r.severity AS severity, r.category AS category
        ORDER BY r.severity DESC
    """
    rows = db.read(query, {"severity": severity})
    return {"risk_events": rows}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)