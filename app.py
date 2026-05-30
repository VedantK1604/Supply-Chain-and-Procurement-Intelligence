# src/app.py
# ─────────────────────────────────────────────────────────────────────────────
# Streamlit frontend for the Supply Chain & Procurement Intelligence GraphRAG.
#
# Pages:
#   💬 Chat     — Conversational GraphRAG question answering
#   🔍 Explore  — Browse the graph by entity name
#   📦 Suppliers — Browse suppliers and components
#   📊 Stats    — Database and graph statistics
# ─────────────────────────────────────────────────────────────────────────────

import os
import httpx
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")


# ─────────────────────────────────────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Supply Chain & Procurement Intelligence",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .stChatMessage { border-radius: 12px; }
    .entity-chip {
        display: inline-block;
        background: #1E88E5;
        color: white;
        border-radius: 20px;
        padding: 2px 12px;
        margin: 3px;
        font-size: 0.85em;
    }
    .score-bar {
        height: 8px;
        background: linear-gradient(90deg, #1E88E5, #42A5F5);
        border-radius: 4px;
    }
    .risk-high { color: #D32F2F; font-weight: bold; }
    .risk-medium { color: #F57C00; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# API Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

def api_post(endpoint: str, payload: dict) -> dict | None:
    try:
        r = httpx.post(f"{API_URL}{endpoint}", json=payload, timeout=90)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        st.error(f"API error {e.response.status_code}: {e.response.text}")
    except Exception as e:
        st.error(f"Connection error: {e}")
    return None


def api_get(endpoint: str, params: dict = None) -> dict | None:
    try:
        r = httpx.get(f"{API_URL}{endpoint}", params=params or {}, timeout=45)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        st.error(f"API error {e.response.status_code}: {e.response.text}")
    except Exception as e:
        st.error(f"Connection error: {e}")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/supply-chain.png", width=70)
    st.title("📦 Supply Chain & Procurement Intelligence")
    st.caption("GraphRAG × Neo4j × GPT-4o")
    st.divider()

    page = st.radio(
        "Navigate",
        ["💬 Chat", "🔍 Explore", "📦 Suppliers", "📊 Stats"],
        label_visibility="collapsed",
    )

    st.divider()
    st.subheader("Query Settings")
    top_k = st.slider("Starting nodes (top_k)", 1, 8, 5,
                      help="Number of relevant nodes to retrieve")
    hops = st.slider("Traversal depth (hops)", 1, 4, 2,
                     help="How deep to explore relationships (2 is recommended)")

    st.divider()
    # Health check
    health = api_get("/health")
    if health:
        st.success(f"✓ Connected • {health['node_count']} nodes")
    else:
        st.error("✗ API unreachable")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: Chat
# ─────────────────────────────────────────────────────────────────────────────

if page == "💬 Chat":
    st.header("💬 Supply Chain & Procurement Assistant")
    st.caption("Ask complex questions • Powered by Knowledge Graph + LLM")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Suggested questions
    with st.expander("✨ Suggested Questions", expanded=True):
        suggestions = [
            "What is the supply chain risk exposure for Apple Inc due to Taiwan Strait tensions?",
            "Recommend alternative suppliers for A14 Bionic Chip with good qualification status",
            "Which suppliers provide Lithium-Ion Battery and what are their countries?",
            "Analyze the impact of Red Sea Shipping Disruption on Tesla’s battery supply chain",
            "Tell me about TSMC including risks and alternatives",
            "Which suppliers should I prioritize for dual-sourcing OLED Display Panel?",
            "Show all Tier 1 suppliers in Taiwan",
        ]
        cols = st.columns(2)
        for i, s in enumerate(suggestions):
            if cols[i % 2].button(s, use_container_width=True, key=f"sug_{i}"):
                st.session_state.pending_question = s

    st.divider()

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and "nodes" in msg:
                with st.expander("📍 Retrieved Graph Nodes", expanded=False):
                    for node in msg["nodes"]:
                        score_pct = int(node["score"] * 100)
                        st.markdown(
                            f'<span class="entity-chip">{node["label"]}</span> '
                            f'**{node["name"]}** — {score_pct}% match',
                            unsafe_allow_html=True,
                        )

    # Handle pending question from suggestion
    pending = st.session_state.pop("pending_question", None)

    # Chat input
    user_input = st.chat_input("Ask about suppliers, risks, components, logistics...")
    question = pending or user_input

    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing knowledge graph..."):
                result = api_post("/ask", {
                    "question": question,
                    "top_k": top_k,
                    "hops": hops,
                })

            if result:
                st.markdown(result["answer"])

                with st.expander("📍 Graph nodes used as context", expanded=False):
                    for node in result["retrieved_nodes"]:
                        score_pct = int(node["score"] * 100)
                        st.markdown(
                            f'<span class="entity-chip">{node["label"]}</span> '
                            f'**{node["name"]}** — {score_pct}% match',
                            unsafe_allow_html=True,
                        )

                with st.expander("🕸️ Raw Graph Context", expanded=False):
                    st.code(result.get("context_preview", "") + "\n...", language="text")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result["answer"],
                    "nodes": result["retrieved_nodes"],
                })
            else:
                st.error("Failed to get response from the API.")

    if st.session_state.messages:
        if st.button("🗑️ Clear Conversation", type="secondary"):
            st.session_state.messages = []
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: Explore
# ─────────────────────────────────────────────────────────────────────────────

elif page == "🔍 Explore":
    st.header("🔍 Explore the Supply Chain Graph")

    col1, col2 = st.columns([2, 1])
    with col1:
        entity_name = st.text_input("Entity name", placeholder="e.g. TSMC, Apple Inc, Lithium-Ion Battery")
    with col2:
        entity_label = st.selectbox(
            "Node Type",
            ["Supplier", "Manufacturer", "Component", "Product", "RiskEvent", "Shipment"]
        )

    explore_hops = st.slider("Traversal depth", 1, 4, 2)

    if st.button("🔍 Explore Entity", type="primary") and entity_name:
        with st.spinner("Traversing graph..."):
            result = api_get(
                f"/graph/{entity_name}",
                {"label": entity_label, "hops": explore_hops}
            )

        if result:
            st.subheader(f"Neighbourhood of: **{entity_name}**")
            st.code(result["context"], language="text")

    st.divider()
    st.subheader("🔎 Hybrid Similarity Search")
    search_q = st.text_input("Search term", placeholder="e.g. Taiwan risk, battery suppliers, red sea disruption")
    search_label = st.selectbox("Filter by type", ["(all)", "Supplier", "Manufacturer", "Component", "RiskEvent"])

    if st.button("Search") and search_q:
        params = {"q": search_q, "top_k": 10}
        if search_label != "(all)":
            params["label"] = search_label

        results = api_get("/search", params)
        if results:
            st.subheader(f"Top matches for: **{search_q}**")
            for r in results["results"]:
                score_pct = int(r["score"] * 100)
                col_a, col_b, col_c = st.columns([3, 1.2, 2])
                col_a.write(f"**{r['name']}**")
                col_b.write(f"`{r['label']}`")
                col_c.progress(r["score"], text=f"{score_pct}%")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: Suppliers
# ─────────────────────────────────────────────────────────────────────────────

elif page == "📦 Suppliers":
    st.header("📦 Suppliers & Components")

    tier = st.selectbox("Filter by Tier", ["All", "Tier1", "Tier2", "Tier3"])
    data = api_get("/suppliers", {"tier": tier if tier != "All" else None})

    if data and data.get("suppliers"):
        suppliers = data["suppliers"]
        st.caption(f"Showing {len(suppliers)} suppliers")

        for s in suppliers:
            with st.expander(f"**{s['name']}** — {s['tier']} | {s['country']}"):
                st.write(f"**Reliability:** {s['reliability']} | **ESG:** {s['esg']}")
                if st.button("Show Full Graph Context", key=f"sup_{s['name']}"):
                    result = api_get(f"/graph/{s['name']}", {"label": "Supplier", "hops": 2})
                    if result:
                        st.code(result["context"], language="text")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: Stats
# ─────────────────────────────────────────────────────────────────────────────

elif page == "📊 Stats":
    st.header("📊 Supply Chain Graph Statistics")

    data = api_get("/stats")
    if data:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Node Counts")
            total_nodes = sum(r["count"] for r in data["nodes"])
            st.metric("Total Nodes", total_nodes)
            for row in data["nodes"]:
                st.progress(row["count"] / max(total_nodes, 1),
                            text=f"{row['label']}: {row['count']}")

        with col2:
            st.subheader("Relationship Counts")
            total_rels = sum(r["count"] for r in data["relationships"])
            st.metric("Total Relationships", total_rels)
            for row in data["relationships"]:
                st.progress(row["count"] / max(total_rels, 1),
                            text=f"{row['rel_type']}: {row['count']}")

    st.divider()
    st.subheader("🔬 Run Raw Cypher Query")
    st.caption("Read-only queries only")

    default_q = "MATCH (s:Supplier) RETURN s.name, s.country, s.tier, s.reliability_score LIMIT 10"
    cypher_input = st.text_area("Cypher query", value=default_q, height=100)

    if st.button("▶ Run Query", type="primary"):
        result = api_post("/cypher", {"query": cypher_input})
        if result:
            st.caption(f"{result['count']} rows returned")
            st.dataframe(result["results"], use_container_width=True)


# Footer
st.sidebar.caption("Supply Chain GraphRAG • Built with Neo4j + FastAPI + Streamlit")