# src/graphrag.py
# ─────────────────────────────────────────────────────────────────────────────
# The GraphRAG pipeline for the Supply Chain & Procurement Intelligence Graph.
#
# Pipeline stages:
#   1. Vector Search    — find the most relevant graph nodes for the question
#   2. Graph Traversal  — walk the neighbourhood of each relevant node
#   3. Context Assembly — serialise the subgraph into structured text
#   4. LLM Reasoning    — generate a natural language answer from that context
# ─────────────────────────────────────────────────────────────────────────────

import os
from openai import OpenAI
from dotenv import load_dotenv
from src.db import Neo4jConnection
from src.embeddings import find_top_nodes

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 2: Graph Traversal
# ─────────────────────────────────────────────────────────────────────────────

def retrieve_subgraph(node_name: str, node_label: str, db: Neo4jConnection, hops: int = 2) -> dict:
    """
    Collect all nodes and relationships within `hops` of the starting node.
    Improved to handle different identifier properties (name, contract_id, shipment_id).
    """
    query = f"""
        MATCH (start:{node_label})
        WHERE start.name = $name 
           OR start.contract_id = $name 
           OR start.shipment_id = $name

        OPTIONAL MATCH path = (start)-[*1..{hops}]-(neighbor)

        WITH start,
             collect(DISTINCT {{
                 from: COALESCE(
                     startNode(last(relationships(path))).name,
                     startNode(last(relationships(path))).contract_id,
                     startNode(last(relationships(path))).shipment_id
                 ),
                 rel:  type(last(relationships(path))),
                 to:   COALESCE(
                     endNode(last(relationships(path))).name,
                     endNode(last(relationships(path))).contract_id,
                     endNode(last(relationships(path))).shipment_id
                 ),
                 to_label: labels(endNode(last(relationships(path))))[0]
             }}) AS edges

        RETURN start, labels(start)[0] AS start_label, edges
    """
    rows = db.read(query, {"name": node_name})
    if not rows:
        return {}

    row = rows[0]
    return {
        "center":  row["start"],
        "label":   row["start_label"],
        "edges":   [e for e in row["edges"] if e.get("from") and e.get("to")],
    }


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 3: Context Assembly
# ─────────────────────────────────────────────────────────────────────────────

def subgraph_to_context(subgraph: dict) -> str:
    """
    Serialise a subgraph into a clean, LLM-readable text block.
    Optimized for supply chain & procurement data.
    """
    if not subgraph or not subgraph.get("center"):
        return ""

    center = subgraph["center"]
    label = subgraph.get("label", "")

    # Skip internal fields
    skip = {"embedding", "embedding_text"}
    props = ", ".join(
        f"{k.replace('_', ' ')}={v}" 
        for k, v in center.items() 
        if k not in skip and v is not None
    )

    lines = [
        f"ENTITY: {center.get('name') or center.get('contract_id') or center.get('shipment_id') or 'Unknown'} [{label}]",
        f"Properties: {props}",
        "",
        "CONNECTIONS:",
    ]

    seen = set()
    for edge in subgraph.get("edges", []):
        triple = (edge["from"], edge["rel"], edge["to"])
        if triple in seen:
            continue
        seen.add(triple)
        lines.append(f"  • {edge['from']} –[{edge['rel']}]→ {edge['to']}")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 4: LLM Answer Generation
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert Supply Chain & Procurement Intelligence Analyst with deep knowledge of global manufacturing, semiconductor industry, automotive supply chains, risk management, logistics, dual-sourcing strategies, and geopolitical risk analysis.

You answer questions using exclusively the structured knowledge graph data provided in each message. Treat every fact in the graph as ground truth.

Guidelines:
- Answer directly, professionally, and concisely.
- Use bullet points for lists or multiple items.
- Highlight risks, costs, lead times, and mitigation options when relevant.
- If the context is insufficient, clearly state what information is missing.
- Do not speculate or add external knowledge.
- Do not mention the graph, database, or retrieval process."""

def generate_answer(question: str, context: str) -> str:
    """Call the LLM with the assembled context to generate a final answer."""
    user_msg = f"""Based on the following Supply Chain & Procurement knowledge graph data, please answer:

QUESTION: {question}

KNOWLEDGE GRAPH CONTEXT:
{context}

Provide a clear, actionable, and accurate answer based only on the information above."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ],
        temperature=0.1,
    )
    return response.choices[0].message.content.strip()


# ─────────────────────────────────────────────────────────────────────────────
# FULL PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

def graphrag_answer(
    question: str,
    db: Neo4jConnection,
    top_k: int = 5,
    hops: int = 3,
    verbose: bool = False,
) -> dict:
    """
    Answer a question using the full GraphRAG pipeline for Supply Chain Intelligence.
    """

    # ── Stage 1: Hybrid Vector Search ─────────────────────────────────────
    relevant_nodes = find_top_nodes(question, db, top_k=top_k)

    if not relevant_nodes:
        return {
            "answer": "I could not find any relevant entities in the supply chain knowledge graph for this question.",
            "context": "", 
            "retrieved_nodes": [],
        }

    if verbose:
        print(f"\n[Hybrid Search] Top {top_k} nodes:")
        for n in relevant_nodes:
            print(f"  [{n['label']:<20}] {n['name']:<45} score={n['score']:.3f}")

    # ── Stage 2 & 3: Traversal + Context Assembly ────────────────────────
    context_blocks = []
    for node in relevant_nodes:
        sg = retrieve_subgraph(node["name"], node["label"], db, hops=hops)
        block = subgraph_to_context(sg)
        if block:
            context_blocks.append(block)

    context = "\n\n───────────────────────────────────\n\n".join(context_blocks)

    if verbose:
        fact_count = context.count("–[")
        print(f"[Traversal] {fact_count} relationship facts collected from {len(context_blocks)} subgraphs")

    # ── Stage 4: LLM Reasoning ───────────────────────────────────────────
    answer = generate_answer(question, context)

    return {
        "answer":          answer,
        "context":         context,
        "retrieved_nodes": [{"name": n["name"], "label": n["label"], "score": n["score"]}
                            for n in relevant_nodes],
    }


# ─────────────────────────────────────────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    questions = [
        # "Tell me about TSMC",
        # "What are the main risks affecting TSMC?",
        # "Which suppliers provide Lithium-Ion Battery?",
        "List down all the suppliers of tier 2."
        # "What is the supply chain risk exposure for Apple Inc due to Taiwan Strait tensions?",
        # "From the given content, Recommend alternative suppliers for the A14 Bionic Chip",
        # "Analyze the impact of Red Sea Shipping Disruption on Tesla’s battery supply chain",
        # "Which suppliers should I prioritize for dual-sourcing OLED Display Panel?",
    ]

    with Neo4jConnection() as db:
        for q in questions:
            print(f"\n{'='*80}")
            print(f"Q: {q}")
            print("="*80)
            result = graphrag_answer(q, db, verbose=True, top_k=5, hops=3)
            print(f"\nA: {result['answer']}\n")