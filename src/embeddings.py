# src/embeddings.py
# ─────────────────────────────────────────────────────────────────────────────
# Computes OpenAI text embeddings for each graph node and stores them as
# node properties. These embeddings power the vector search step in the
# Supply Chain & Procurement Intelligence GraphRAG pipeline.
# ─────────────────────────────────────────────────────────────────────────────
import os
import json
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from src.db import Neo4jConnection

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
EMBED_MODEL = "text-embedding-3-small"


# ─────────────────────────────────────────────────────────────────────────────
# Node → Natural Language Description (Retrieval-Friendly)
# ─────────────────────────────────────────────────────────────────────────────
def node_to_text(props: dict, label: str) -> str:
    """
    Convert a graph node into a rich, natural language description optimized
    for semantic retrieval in supply chain & procurement questions.
    """
    name = props.get("name") or props.get("contract_id") or props.get("shipment_id") or str(props)

    if label == "Supplier":
        return (
            f"{name} is a {props.get('tier', '')} supplier based in {props.get('country', '')}. "
            f"Reliability: {props.get('reliability_score')}, ESG: {props.get('esg_rating')}, "
            f"Financial Health: {props.get('financial_health')}, Strategic Importance: {props.get('strategic_importance')}. "
            f"Annual Revenue: ${props.get('annual_revenue_usd_bn')}B, Defect Rate: {props.get('defect_rate_ppm')} ppm."
        )

    if label == "Manufacturer":
        return (
            f"{name} is a {props.get('industry', '')} manufacturer headquartered in {props.get('hq', '')}. "
            f"Employees: {props.get('employees')}, Annual Revenue: ${props.get('annual_revenue_usd_bn')}B. "
            f"Quality System: {props.get('quality_system')}, Tier: {props.get('tier_in_chain')}, "
            f"Inventory Strategy: {props.get('inventory_strategy')}."
        )

    if label == "Component":
        return (
            f"{name} is a {props.get('category', '')} / {props.get('sub_category', '')} component. "
            f"Criticality: {props.get('criticality')}, Avg Price: ${props.get('avg_price_usd')}, "
            f"Lead Time: {props.get('lead_time_weeks_avg')} weeks, Substitutability: {props.get('substitutability')}. "
            f"Hazardous: {props.get('hazardous')}, Compliance: {props.get('compliance_standard')}."
        )

    if label == "Product":
        return (
            f"{name} is a {props.get('category', '')} product manufactured by various OEMs. "
            f"Key features include advanced {props.get('key_technology', 'technology')}."
        )

    if label == "Customer":
        return (
            f"{name} is a {props.get('type', 'major')} customer in the {props.get('industry', '')} sector. "
            f"Located in {props.get('country', '')}, annual spend with suppliers is significant."
        )

    if label == "Location":
        return (
            f"{name} is a {props.get('type', 'key')} location in {props.get('country', '')} / {props.get('region', '')}. "
            f"Strategic importance for supply chain: {props.get('strategic_role', '')}."
        )

    if label == "RiskEvent":
        return (
            f"{name} is a supply chain risk event with impact level {props.get('severity', '')}. "
            f"Category: {props.get('category', '')}, Likelihood: {props.get('likelihood', '')}."
        )

    if label == "Warehouse":
        return (
            f"{name} is a {props.get('type', '')} warehouse located in {props.get('location', '')}. "
            f"Capacity: {props.get('capacity_units', '')} units, Owner: {props.get('owner', '')}."
        )

    if label == "LogisticsCarrier":
        return (
            f"{name} is a logistics carrier specializing in {props.get('mode', '')} transport. "
            f"Reliability: {props.get('reliability_score', '')}, Service Coverage: {props.get('coverage', '')}."
        )

    if label == "ProcurementContract":
        return (
            f"Procurement Contract {name} between {props.get('buyer', '')} and {props.get('supplier', '')}. "
            f"Value: ${props.get('annual_value_usd_mn')}M, Period: {props.get('start_date')} to {props.get('end_date')}."
        )

    if label == "Certification":
        return (
            f"{name} certification issued by {props.get('issuing_body', 'certifying body')}. "
            f"Valid for compliance in supply chain and quality standards."
        )

    if label == "Shipment":
        return (
            f"Shipment {name} of {props.get('product')} to {props.get('customer')} from {props.get('from_loc')} "
            f"to {props.get('to_loc')}. Status: {props.get('status')}, Carrier: {props.get('carrier')}, "
            f"Value: ${props.get('value_usd_k')}K, Delay: {props.get('delay_days')} days."
        )

    # Fallback for other nodes (MitigationAction, Insurer, Auditor, etc.)
    return f"{label}: {name}. " + " ".join(
        f"{k.replace('_', ' ')}: {v}" for k, v in list(props.items())[:8]
    )


# ─────────────────────────────────────────────────────────────────────────────
# Batch Embedding
# ─────────────────────────────────────────────────────────────────────────────
def embed_batch(texts: list[str]) -> list[list[float]]:
    """Call the OpenAI Embeddings API for a list of texts in one request."""
    response = client.embeddings.create(input=texts, model=EMBED_MODEL)
    return [item.embedding for item in response.data]


def add_embeddings(db: Neo4jConnection) -> None:
    """
    Embed every node in the graph and store the vector as a JSON string property.
    """
    # Main labels for embedding
    labels = [
        "Supplier", "Manufacturer", "Component", "Product", "Customer",
        "Location", "RiskEvent", "Warehouse", "LogisticsCarrier",
        "ProcurementContract", "Certification", "Shipment"
    ]

    for label in labels:
        rows = db.read(f"MATCH (n:{label}) RETURN n, id(n) AS nid")
        if not rows:
            print(f"  No {label} nodes found, skipping.")
            continue

        texts = [node_to_text(row["n"], label) for row in rows]
        nids = [row["nid"] for row in rows]
        vectors = embed_batch(texts)

        for nid, vec, txt in zip(nids, vectors, texts):
            db.write("""
                MATCH (n) WHERE id(n) = $nid
                SET n.embedding = $vec,
                    n.embedding_text = $txt
            """, {"nid": nid, "vec": json.dumps(vec), "txt": txt})

        print(f"  ✓ {len(rows):>3} {label} nodes embedded")


# ─────────────────────────────────────────────────────────────────────────────
# Hybrid Similarity Search (Keyword + Cosine)
# ─────────────────────────────────────────────────────────────────────────────
def cosine_similarity(a: list[float], b: list[float]) -> float:
    va, vb = np.array(a), np.array(b)
    return float(np.dot(va, vb) / (np.linalg.norm(va) * np.linalg.norm(vb) + 1e-9))


def keyword_score(text: str, query: str) -> float:
    """Simple keyword overlap score (case-insensitive)."""
    text_lower = text.lower()
    query_lower = query.lower()
    query_words = set(query_lower.split())
    if not query_words:
        return 0.0
    matches = sum(1 for word in query_words if word in text_lower)
    return matches / len(query_words)


def find_top_nodes(
    question: str,
    db: Neo4jConnection,
    top_k: int = 5,
    labels: list[str] | None = None,
    alpha: float = 0.7  # weight for vector similarity (0-1)
) -> list[dict]:
    """
    Hybrid search: Combines semantic (cosine) + keyword matching.
    """
    q_vec = client.embeddings.create(input=[question], model=EMBED_MODEL).data[0].embedding

    if labels:
        filter_clause = " OR ".join(f"n:{lbl}" for lbl in labels)
        query = f"MATCH (n) WHERE ({filter_clause}) AND n.embedding IS NOT NULL RETURN n, labels(n)[0] AS lbl"
    else:
        query = "MATCH (n) WHERE n.embedding IS NOT NULL RETURN n, labels(n)[0] AS lbl"

    rows = db.read(query)
    scored = []

    for row in rows:
        props = dict(row["n"])  # convert to dict
        vec_str = props.get("embedding")
        if not vec_str:
            continue
        vec = json.loads(vec_str)

        emb_score = cosine_similarity(q_vec, vec)
        text_for_kw = props.get("embedding_text", "") or " ".join(str(v) for v in props.values())
        kw_score = keyword_score(text_for_kw, question)

        # Hybrid score
        final_score = alpha * emb_score + (1 - alpha) * kw_score

        scored.append({
            "label": row["lbl"],
            "name": props.get("name") or props.get("contract_id") or props.get("shipment_id") or "",
            "score": final_score,
            "emb_score": emb_score,
            "kw_score": kw_score,
            "properties": props,
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


if __name__ == "__main__":
    with Neo4jConnection() as db:
        # print("Computing embeddings for all graph nodes...")
        # add_embeddings(db)
        # print("\n✓ All embeddings stored.")

        # Quick test
        # print("\nTest search: 'risk of Taiwan semiconductor supply disruption'")
        results = find_top_nodes("Show all Tier 1 suppliers in Taiwan", db, top_k=5)
        for r in results:
            print(f" [{r['label']:<20}] {r['name']:<40} hybrid={r['score']:.3f} (emb={r['emb_score']:.3f}, kw={r['kw_score']:.3f})")