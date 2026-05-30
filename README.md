# Supply Chain & Procurement Intelligence GraphRAG

A GraphRAG system for supply-chain, procurement, supplier-risk, and logistics intelligence. The project builds a Neo4j knowledge graph of suppliers, manufacturers, components, products, customers, locations, risk events, warehouses, carriers, contracts, certifications, and shipments, then answers natural-language questions using hybrid retrieval, graph traversal, and an OpenAI chat model.

Use it to ask questions like:

- What is the supply chain risk exposure for Apple Inc due to Taiwan Strait tensions?
- Which suppliers provide Lithium-Ion Battery and what are their countries?
- Recommend alternative suppliers for A14 Bionic Chip with good qualification status.
- Analyze the impact of Red Sea Shipping Disruption on Tesla's battery supply chain.
- Which suppliers should I prioritize for dual-sourcing OLED Display Panel?

---

## What This Project Demonstrates

| Concept | How it appears in this project |
|---|---|
| Knowledge graph modeling | Neo4j ontology for procurement, suppliers, risks, logistics, and contracts |
| GraphRAG | Hybrid search -> graph traversal -> grounded LLM answer generation |
| Supplier intelligence | Tier, country, reliability, ESG, capacity, audit, financial health, and strategic importance |
| Procurement analysis | Contracts, payment terms, order quantities, cost, sourcing links, and qualification status |
| Supply-chain risk | Risk events, affected entities, mitigation actions, dual sourcing, and alternatives |
| Logistics visibility | Warehouses, routes, carriers, shipments, transit corridors, and delays |
| API + UI | FastAPI backend with a Streamlit chat and graph exploration frontend |
| Docker workflow | Neo4j, API, and Streamlit services in Docker Compose |

---

## Knowledge Graph Ontology

```text
NODES
──────────────────────────────────────────────────────────
Supplier              {name, tier, country, reliability_score, esg_rating, capacity, ...}
Manufacturer          {name, industry, hq, employees, annual_revenue_usd_bn, ...}
Component             {name, category, criticality, avg_price_usd, lead_time_weeks_avg, ...}
Product               {name, category, key_technology, ...}
Customer              {name, type, industry, country, ...}
Location              {name, country, region, type, strategic_role, ...}
RiskEvent             {name, severity, category, likelihood, ...}
Warehouse             {name, type, location, capacity_units, owner, ...}
LogisticsCarrier      {name, mode, reliability_score, coverage, ...}
ProcurementContract   {contract_id, buyer, supplier, annual_value_usd_mn, ...}
Certification         {name, issuing_body, ...}
Shipment              {shipment_id, status, departure_date, eta_date, delay_days, ...}
MitigationAction      {name}
Insurer               {name}
Auditor               {name}

RELATIONSHIPS
──────────────────────────────────────────────────────────
(Supplier)            -[:SUPPLIES]->             (Component)
(Manufacturer)        -[:PRODUCES]->             (Product)
(Product)             -[:USES]->                 (Component)
(Entity)              -[:LOCATED_IN]->           (Location)
(Entity)              -[:HAS_RISK]->             (RiskEvent)
(Component)           -[:HAS_ALTERNATIVE]->      (Supplier)
(Entity)              -[:SHIPS_VIA]->            (LogisticsCarrier)
(Entity)              -[:STORED_IN]->            (Warehouse)
(Entity)              -[:CERTIFIED_BY]->         (Certification)
(Entity)              -[:SELLS_TO]->             (Customer)
(Supplier)            -[:MANUFACTURES_FOR]->     (Manufacturer)
(Manufacturer)        -[:SOURCES_FROM]->         (Supplier)
(Entity)              -[:COMPETES_WITH]->        (Entity)
(Location)            -[:TRANSITS_THROUGH]->     (Location)
(RiskEvent)           -[:MITIGATED_BY]->         (MitigationAction)
(RiskEvent)           -[:AFFECTS]->              (Entity)
(Entity)              -[:CONTRACTED_WITH]->      (Supplier)
(Entity)              -[:OWNS_WAREHOUSE]->       (Warehouse)
(LogisticsCarrier)    -[:CARRIES_FOR]->          (Entity)
(Location)            -[:ADJACENT_TO]->          (Location)
(Supplier)            -[:DUAL_SOURCED_WITH]->    (Supplier)
(Supplier)            -[:QUALIFIED_BY]->         (Manufacturer)
(Shipment)            -[:OF_PRODUCT]->           (Product)
(Shipment)            -[:TO_CUSTOMER]->          (Customer)
(Shipment)            -[:FROM]->                 (Location)
(Shipment)            -[:TO]->                   (Location)
(Entity)              -[:INSURED_BY]->           (Insurer)
(Supplier)            -[:AUDITED_BY]->           (Auditor)
```

The bundled dataset currently includes suppliers, manufacturers, components, products, customers, locations, risk events, warehouses, carriers, contracts, certifications, and shipments for a procurement intelligence demo.

---

## Architecture

```text
User question
     |
     v
Hybrid retrieval
OpenAI embedding + keyword overlap over graph node descriptions
     |
     v
Graph traversal
Collect 1-4 hop neighborhoods around the most relevant entities
     |
     v
Context assembly
Convert graph facts into structured text triples
     |
     v
LLM answer generation
Answer using only retrieved supply-chain graph context
```

Core implementation files:

- `src/loader.py` loads the graph into Neo4j.
- `src/embeddings.py` builds retrieval text, stores embeddings, and performs hybrid search.
- `src/graphrag.py` retrieves subgraphs and generates grounded answers.
- `api.py` exposes FastAPI endpoints.
- `app.py` provides the Streamlit UI.
- `data/supply_chain_data.py` contains the demo graph data.

---

## Setup

### Prerequisites

| Tool | Notes |
|---|---|
| Docker Desktop / Docker Engine | Required for Neo4j and the full Compose workflow |
| Python 3.11+ | Required for local API, Streamlit, loader, and embedding scripts |
| OpenAI API key | Required for embeddings and answer generation |

### 1. Configure environment

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-...
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=supplychain!
API_URL=http://localhost:8000
```

### 2. Start Neo4j

```bash
docker compose up neo4j -d
```

Open Neo4j Browser at:

```text
http://localhost:7474
```

Login:

```text
Username: neo4j
Password: supplychain!
```

### 3. Install Python dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

On Windows, activate the environment with:

```bash
venv\Scripts\activate
```

### 4. Load the knowledge graph

Run this from the project root:

```bash
PYTHONPATH="$PWD:$PWD/src" python3 src/loader.py
```

The loader clears and reloads the demo graph. It creates uniqueness constraints, loads all node types, creates relationships, and prints a graph summary.

### 5. Add vector embeddings

Run this once after loading the graph:

```bash
PYTHONPATH="$PWD:$PWD/src" python3 -c "from src.db import Neo4jConnection; from src.embeddings import add_embeddings; db = Neo4jConnection(); add_embeddings(db); db.close()"
```

Embeddings are stored directly on Neo4j nodes as `embedding` and `embedding_text` properties. Re-running the command refreshes existing embeddings.

### 6. Start the API

```bash
uvicorn api:app --reload --port 8000
```

FastAPI docs:

```text
http://localhost:8000/docs
```

### 7. Start Streamlit

In a second terminal:

```bash
source venv/bin/activate
streamlit run app.py
```

Streamlit app:

```text
http://localhost:8501
```

---

## Docker Compose Workflow

You can also start the complete stack:

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| Neo4j Browser | http://localhost:7474 |
| FastAPI docs | http://localhost:8000/docs |
| Streamlit app | http://localhost:8501 |

After the services are up, load data and embeddings from your local terminal using the commands above, or run equivalent commands inside the API container.

---

## Streamlit App

The UI has four main pages:

| Page | Purpose |
|---|---|
| Chat | Ask natural-language supply-chain and procurement questions |
| Explore | Look up an entity and inspect its graph neighborhood |
| Suppliers | Browse suppliers by tier and open full supplier context |
| Stats | View node and relationship counts, and run read-only Cypher queries |

Suggested questions are included in the Chat page to help test supplier risk, alternatives, dual sourcing, and disruption analysis.

---

## FastAPI Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Ask a GraphRAG question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Which suppliers provide Lithium-Ion Battery and what are their countries?", "top_k": 5, "hops": 2}'

# Hybrid search over embedded graph nodes
curl "http://localhost:8000/search?q=Taiwan+risk&top_k=8"

# Entity neighborhood
curl "http://localhost:8000/graph/TSMC?label=Supplier&hops=2"

# Suppliers, optionally filtered by tier
curl "http://localhost:8000/suppliers?tier=Tier1"

# Risk events
curl "http://localhost:8000/risks"

# Graph statistics
curl "http://localhost:8000/stats"

# Read-only Cypher query
curl -X POST http://localhost:8000/cypher \
  -H "Content-Type: application/json" \
  -d '{"query": "MATCH (s:Supplier) RETURN s.name, s.country, s.tier, s.reliability_score LIMIT 10"}'
```

---

## Example Questions

Try these in Streamlit or through `POST /ask`:

- What is the supply chain risk exposure for Apple Inc due to Taiwan Strait tensions?
- Tell me about TSMC including risks and alternatives.
- Show all Tier 1 suppliers in Taiwan.
- Which suppliers provide Lithium-Ion Battery?
- Recommend alternative suppliers for A14 Bionic Chip with good qualification status.
- Analyze the impact of Red Sea Shipping Disruption on Tesla's battery supply chain.
- Which suppliers should I prioritize for dual-sourcing OLED Display Panel?
- Which suppliers have high reliability and strong ESG ratings?
- What shipments are delayed and which customers are affected?

---

## Project Structure

```text
Supply-Chain-&-Procurement-Intelligence/
├── README.md
├── requirements.txt
├── docker-compose.yml
├── Dockerfile.api
├── Dockerfile.streamlit
├── api.py                         # FastAPI backend
├── app.py                         # Streamlit frontend
├── data/
│   ├── supply_chain_data.py        # Graph nodes and relationships
│   └── logo/
│       └── supply_chain_logo.png
└── src/
    ├── db.py                       # Neo4j connection wrapper
    ├── loader.py                   # Load ontology and data into Neo4j
    ├── embeddings.py               # Node text, embeddings, hybrid retrieval
    └── graphrag.py                 # Subgraph retrieval and LLM answering
```

---

## Interesting Cypher Queries

Run these in Neo4j Browser or through `POST /cypher`.

```cypher
-- Highest reliability suppliers
MATCH (s:Supplier)
RETURN s.name, s.tier, s.country, s.reliability_score, s.esg_rating
ORDER BY s.reliability_score DESC
LIMIT 10;
```

```cypher
-- Components supplied by Tier 1 suppliers in Taiwan
MATCH (s:Supplier)-[:SUPPLIES]->(c:Component)
WHERE s.tier = 'Tier1' AND s.country = 'Taiwan'
RETURN s.name AS supplier, c.name AS component, c.criticality AS criticality
ORDER BY supplier, component;
```

```cypher
-- Risk events affecting suppliers or products
MATCH (r:RiskEvent)-[a:AFFECTS]->(e)
RETURN r.name AS risk, r.severity AS risk_severity, labels(e)[0] AS entity_type,
       e.name AS entity, a.impact_type AS impact_type, a.revenue_impact_usd_mn AS revenue_impact
ORDER BY revenue_impact DESC;
```

```cypher
-- Alternative suppliers for a critical component
MATCH (c:Component {name: 'A14 Bionic Chip'})-[a:HAS_ALTERNATIVE]->(s:Supplier)
RETURN c.name AS component, s.name AS alternative_supplier, s.country AS country,
       a.qualification_status AS qualification_status,
       a.cost_premium_pct AS cost_premium_pct,
       a.lead_time_delta_days AS lead_time_delta_days;
```

```cypher
-- Dual-sourcing relationships
MATCH (a:Supplier)-[r:DUAL_SOURCED_WITH]->(b:Supplier)
RETURN a.name AS primary_supplier, b.name AS secondary_supplier,
       r.component AS component, r.split_pct_primary AS primary_split, r.reason AS reason;
```

```cypher
-- Delayed shipments and affected customers
MATCH (sh:Shipment)-[:OF_PRODUCT]->(p:Product),
      (sh)-[:TO_CUSTOMER]->(c:Customer)
WHERE sh.delay_days > 0
RETURN sh.shipment_id AS shipment, p.name AS product, c.name AS customer,
       sh.status AS status, sh.eta_date AS eta, sh.delay_days AS delay_days
ORDER BY sh.delay_days DESC;
```

---
