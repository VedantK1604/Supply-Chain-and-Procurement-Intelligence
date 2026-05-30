# src/loader.py
# ─────────────────────────────────────────────────────────────────────────────
# Sets up the ontology constraints and loads the complete Supply Chain
# & Procurement Intelligence dataset into Neo4j.
# Safe to run multiple times — all writes use MERGE (upsert).
# ─────────────────────────────────────────────────────────────────────────────

from db import Neo4jConnection
from data.supply_chain_data import (
    SUPPLIERS, MANUFACTURERS, COMPONENTS, PRODUCTS, CUSTOMERS,
    LOCATIONS, RISK_EVENTS, WAREHOUSES, LOGISTICS_CARRIERS,
    PROCUREMENT_CONTRACTS, CERTIFICATIONS,
    # Relationships
    SUPPLIES, PRODUCES, USES, LOCATED_IN, HAS_RISK, HAS_ALTERNATIVE,
    SHIPS_VIA, STORED_IN, CERTIFIED_BY, SELLS_TO, MANUFACTURES_FOR,
    SOURCES_FROM, COMPETES_WITH, TRANSITS_THROUGH, MITIGATED_BY,
    AFFECTS, CONTRACTED_WITH, OWNS_WAREHOUSE, CARRIES_FOR,
    ADJACENT_TO, DUAL_SOURCED_WITH, QUALIFIED_BY, SHIPMENTS, INSURED_BY,
    AUDITED_BY
)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: Constraints
# ─────────────────────────────────────────────────────────────────────────────

CONSTRAINTS = [
    "CREATE CONSTRAINT sc_supplier     IF NOT EXISTS FOR (s:Supplier)          REQUIRE s.name IS UNIQUE",
    "CREATE CONSTRAINT sc_manufacturer IF NOT EXISTS FOR (m:Manufacturer)      REQUIRE m.name IS UNIQUE",
    "CREATE CONSTRAINT sc_component    IF NOT EXISTS FOR (c:Component)         REQUIRE c.name IS UNIQUE",
    "CREATE CONSTRAINT sc_product      IF NOT EXISTS FOR (p:Product)           REQUIRE p.name IS UNIQUE",
    "CREATE CONSTRAINT sc_customer     IF NOT EXISTS FOR (c:Customer)          REQUIRE c.name IS UNIQUE",
    "CREATE CONSTRAINT sc_location     IF NOT EXISTS FOR (l:Location)          REQUIRE l.name IS UNIQUE",
    "CREATE CONSTRAINT sc_risk         IF NOT EXISTS FOR (r:RiskEvent)         REQUIRE r.name IS UNIQUE",
    "CREATE CONSTRAINT sc_warehouse    IF NOT EXISTS FOR (w:Warehouse)         REQUIRE w.name IS UNIQUE",
    "CREATE CONSTRAINT sc_carrier      IF NOT EXISTS FOR (c:LogisticsCarrier)  REQUIRE c.name IS UNIQUE",
    "CREATE CONSTRAINT sc_contract     IF NOT EXISTS FOR (c:ProcurementContract) REQUIRE c.contract_id IS UNIQUE",
    "CREATE CONSTRAINT sc_cert         IF NOT EXISTS FOR (c:Certification)     REQUIRE c.name IS UNIQUE",
]


def setup_constraints(db: Neo4jConnection) -> None:
    print("  Setting up ontology constraints...")
    for c in CONSTRAINTS:
        db.write(c)
    print("  ✓ Constraints active")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2: Nodes
# ─────────────────────────────────────────────────────────────────────────────

def load_suppliers(db: Neo4jConnection) -> None:
    for s in SUPPLIERS:
        db.write("""
            MERGE (n:Supplier {name: $name})
            SET n += $props
        """, {"name": s["name"], "props": {k: v for k, v in s.items() if k != "name"}})
    print(f"  ✓ {len(SUPPLIERS)} Supplier nodes")


def load_manufacturers(db: Neo4jConnection) -> None:
    for m in MANUFACTURERS:
        db.write("""
            MERGE (n:Manufacturer {name: $name})
            SET n += $props
        """, {"name": m["name"], "props": {k: v for k, v in m.items() if k != "name"}})
    print(f"  ✓ {len(MANUFACTURERS)} Manufacturer nodes")


def load_components(db: Neo4jConnection) -> None:
    for c in COMPONENTS:
        db.write("""
            MERGE (n:Component {name: $name})
            SET n += $props
        """, {"name": c["name"], "props": {k: v for k, v in c.items() if k != "name"}})
    print(f"  ✓ {len(COMPONENTS)} Component nodes")


def load_products(db: Neo4jConnection) -> None:
    for p in PRODUCTS:
        db.write("""
            MERGE (n:Product {name: $name})
            SET n += $props
        """, {"name": p["name"], "props": {k: v for k, v in p.items() if k != "name"}})
    print(f"  ✓ {len(PRODUCTS)} Product nodes")


def load_customers(db: Neo4jConnection) -> None:
    for c in CUSTOMERS:
        db.write("""
            MERGE (n:Customer {name: $name})
            SET n += $props
        """, {"name": c["name"], "props": {k: v for k, v in c.items() if k != "name"}})
    print(f"  ✓ {len(CUSTOMERS)} Customer nodes")


def load_locations(db: Neo4jConnection) -> None:
    for loc in LOCATIONS:
        db.write("""
            MERGE (n:Location {name: $name})
            SET n += $props
        """, {"name": loc["name"], "props": {k: v for k, v in loc.items() if k != "name"}})
    print(f"  ✓ {len(LOCATIONS)} Location nodes")


def load_risk_events(db: Neo4jConnection) -> None:
    for r in RISK_EVENTS:
        db.write("""
            MERGE (n:RiskEvent {name: $name})
            SET n += $props
        """, {"name": r["name"], "props": {k: v for k, v in r.items() if k != "name"}})
    print(f"  ✓ {len(RISK_EVENTS)} RiskEvent nodes")


def load_warehouses(db: Neo4jConnection) -> None:
    for w in WAREHOUSES:
        db.write("""
            MERGE (n:Warehouse {name: $name})
            SET n += $props
        """, {"name": w["name"], "props": {k: v for k, v in w.items() if k != "name"}})
    print(f"  ✓ {len(WAREHOUSES)} Warehouse nodes")


def load_logistics_carriers(db: Neo4jConnection) -> None:
    for c in LOGISTICS_CARRIERS:
        db.write("""
            MERGE (n:LogisticsCarrier {name: $name})
            SET n += $props
        """, {"name": c["name"], "props": {k: v for k, v in c.items() if k != "name"}})
    print(f"  ✓ {len(LOGISTICS_CARRIERS)} LogisticsCarrier nodes")


def load_procurement_contracts(db: Neo4jConnection) -> None:
    for c in PROCUREMENT_CONTRACTS:
        db.write("""
            MERGE (n:ProcurementContract {contract_id: $contract_id})
            SET n += $props
        """, {"contract_id": c["contract_id"], "props": {k: v for k, v in c.items() if k != "contract_id"}})
    print(f"  ✓ {len(PROCUREMENT_CONTRACTS)} ProcurementContract nodes")


def load_certifications(db: Neo4jConnection) -> None:
    for c in CERTIFICATIONS:
        db.write("""
            MERGE (n:Certification {name: $name})
            SET n += $props
        """, {"name": c["name"], "props": {k: v for k, v in c.items() if k != "name"}})
    print(f"  ✓ {len(CERTIFICATIONS)} Certification nodes")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3: Relationships
# ─────────────────────────────────────────────────────────────────────────────

def load_supplies(db: Neo4jConnection) -> None:
    for rel in SUPPLIES:
        supplier, component, *props = rel
        db.write("""
            MATCH (s:Supplier {name: $supplier})
            MATCH (c:Component {name: $component})
            MERGE (s)-[r:SUPPLIES]->(c)
            SET r.lead_time_days = $lead_time_days,
                r.cost_per_unit_usd = $cost_per_unit_usd,
                r.min_order_qty = $min_order_qty,
                r.payment_terms_days = $payment_terms_days,
                r.defect_rate_ppm = $defect_rate_ppm,
                r.contract_id = $contract_id,
                r.incoterms = $incoterms,
                r.active = $active
        """, {
            "supplier": supplier, "component": component,
            "lead_time_days": props[0], "cost_per_unit_usd": props[1],
            "min_order_qty": props[2], "payment_terms_days": props[3],
            "defect_rate_ppm": props[4], "contract_id": props[5],
            "incoterms": props[6], "active": props[7]
        })
    print(f"  ✓ {len(SUPPLIES)} SUPPLIES relationships")


def load_produces(db: Neo4jConnection) -> None:
    for rel in PRODUCES:
        manufacturer, product, *props = rel
        db.write("""
            MATCH (m:Manufacturer {name: $manufacturer})
            MATCH (p:Product {name: $product})
            MERGE (m)-[r:PRODUCES]->(p)
            SET r.annual_capacity_k_units = $cap,
                r.yield_rate_pct = $yield,
                r.assembly_location = $loc
        """, {
            "manufacturer": manufacturer, "product": product,
            "cap": props[0], "yield": props[1], "loc": props[2]
        })
    print(f"  ✓ {len(PRODUCES)} PRODUCES relationships")

# ─────────────────────────────────────────────────────────────────────────────
# Additional Relationship Loaders
# ─────────────────────────────────────────────────────────────────────────────

def load_located_in(db: Neo4jConnection) -> None:
    for entity, location, since in LOCATED_IN:
        db.write("""
            MATCH (e) WHERE e.name = $entity
            MATCH (l:Location {name: $location})
            MERGE (e)-[r:LOCATED_IN]->(l)
            SET r.since = $since
        """, {"entity": entity, "location": location, "since": since})
    print(f"  ✓ {len(LOCATED_IN)} LOCATED_IN relationships")


def load_has_risk(db: Neo4jConnection) -> None:
    for entity, risk, direct, exposure in HAS_RISK:
        db.write("""
            MATCH (e) WHERE e.name = $entity
            MATCH (r:RiskEvent {name: $risk})
            MERGE (e)-[rel:HAS_RISK]->(r)
            SET rel.direct_impact = $direct, rel.exposure_level = $exposure
        """, {"entity": entity, "risk": risk, "direct": direct, "exposure": exposure})
    print(f"  ✓ {len(HAS_RISK)} HAS_RISK relationships")


def load_has_alternative(db: Neo4jConnection) -> None:
    for comp, alt_supplier, status, premium, delta in HAS_ALTERNATIVE:
        db.write("""
            MATCH (c:Component {name: $comp})
            MATCH (s:Supplier {name: $supplier})
            MERGE (c)-[r:HAS_ALTERNATIVE]->(s)
            SET r.qualification_status = $status,
                r.cost_premium_pct = $premium,
                r.lead_time_delta_days = $delta
        """, {
            "comp": comp, "supplier": alt_supplier, "status": status,
            "premium": premium, "delta": delta
        })
    print(f"  ✓ {len(HAS_ALTERNATIVE)} HAS_ALTERNATIVE relationships")


def load_ships_via(db: Neo4jConnection) -> None:
    for item, carrier, route, days, mode, cost in SHIPS_VIA:
        db.write("""
            MATCH (i) WHERE i.name = $item
            MATCH (c:LogisticsCarrier {name: $carrier})
            MERGE (i)-[r:SHIPS_VIA]->(c)
            SET r.route = $route,
                r.typical_transit_days = $days,
                r.mode = $mode,
                r.cost_usd_per_unit = $cost
        """, {
            "item": item, "carrier": carrier, "route": route,
            "days": days, "mode": mode, "cost": cost
        })
    print(f"  ✓ {len(SHIPS_VIA)} SHIPS_VIA relationships")


def load_stored_in(db: Neo4jConnection) -> None:
    for item, warehouse, avg_inv, safety, days in STORED_IN:
        db.write("""
            MATCH (i) WHERE i.name = $item
            MATCH (w:Warehouse {name: $warehouse})
            MERGE (i)-[r:STORED_IN]->(w)
            SET r.avg_inventory_units = $avg,
                r.safety_stock_units = $safety,
                r.days_of_supply = $days
        """, {
            "item": item, "warehouse": warehouse,
            "avg": avg_inv, "safety": safety, "days": days
        })
    print(f"  ✓ {len(STORED_IN)} STORED_IN relationships")


def load_certified_by(db: Neo4jConnection) -> None:
    for entity, cert, issue, expiry in CERTIFIED_BY:
        db.write("""
            MATCH (e) WHERE e.name = $entity
            MATCH (c:Certification {name: $cert})
            MERGE (e)-[r:CERTIFIED_BY]->(c)
            SET r.issue_date = $issue, r.expiry_date = $expiry
        """, {"entity": entity, "cert": cert, "issue": issue, "expiry": expiry})
    print(f"  ✓ {len(CERTIFIED_BY)} CERTIFIED_BY relationships")


def load_sells_to(db: Neo4jConnection) -> None:
    for seller, customer, channel, order_val, terms, revenue in SELLS_TO:
        db.write("""
            MATCH (s) WHERE s.name = $seller
            MATCH (c:Customer {name: $customer})
            MERGE (s)-[r:SELLS_TO]->(c)
            SET r.channel = $channel,
                r.avg_order_value_usd_k = $order_val,
                r.payment_terms_days = $terms,
                r.ytd_revenue_usd_mn = $revenue
        """, {
            "seller": seller, "customer": customer, "channel": channel,
            "order_val": order_val, "terms": terms, "revenue": revenue
        })
    print(f"  ✓ {len(SELLS_TO)} SELLS_TO relationships")


def load_manufactures_for(db: Neo4jConnection) -> None:
    for supplier, manufacturer, volume, sla, dedicated in MANUFACTURES_FOR:
        db.write("""
            MATCH (s:Supplier {name: $supplier})
            MATCH (m:Manufacturer {name: $manufacturer})
            MERGE (s)-[r:MANUFACTURES_FOR]->(m)
            SET r.annual_volume_units_k = $volume,
                r.sla_uptime_pct = $sla,
                r.dedicated_line = $dedicated
        """, {
            "supplier": supplier, "manufacturer": manufacturer,
            "volume": volume, "sla": sla, "dedicated": dedicated
        })
    print(f"  ✓ {len(MANUFACTURES_FOR)} MANUFACTURES_FOR relationships")


def load_sources_from(db: Neo4jConnection) -> None:
    for manufacturer, supplier, spend, single, strategic in SOURCES_FROM:
        db.write("""
            MATCH (m:Manufacturer {name: $manufacturer})
            MATCH (s:Supplier {name: $supplier})
            MERGE (m)-[r:SOURCES_FROM]->(s)
            SET r.spend_usd_mn_annual = $spend,
                r.single_source = $single,
                r.strategic_partner = $strategic
        """, {
            "manufacturer": manufacturer, "supplier": supplier,
            "spend": spend, "single": single, "strategic": strategic
        })
    print(f"  ✓ {len(SOURCES_FROM)} SOURCES_FROM relationships")


def load_competes_with(db: Neo4jConnection) -> None:
    for a, b, segment, overlap in COMPETES_WITH:
        db.write("""
            MATCH (x) WHERE x.name = $a
            MATCH (y) WHERE y.name = $b
            MERGE (x)-[r:COMPETES_WITH]->(y)
            SET r.market_segment = $segment, r.overlap_pct = $overlap
        """, {"a": a, "b": b, "segment": segment, "overlap": overlap})
    print(f"  ✓ {len(COMPETES_WITH)} COMPETES_WITH relationships")


def load_transits_through(db: Neo4jConnection) -> None:
    for start, end, via, carrier, days in TRANSITS_THROUGH:
        db.write("""
            MATCH (s:Location {name: $start})
            MATCH (e:Location {name: $end})
            MERGE (s)-[r:TRANSITS_THROUGH]->(e)
            SET r.via = $via, r.carrier = $carrier, r.avg_days = $days
        """, {"start": start, "end": end, "via": via, "carrier": carrier, "days": days})
    print(f"  ✓ {len(TRANSITS_THROUGH)} TRANSITS_THROUGH relationships")


def load_mitigated_by(db: Neo4jConnection) -> None:
    for risk, action, mtype, effectiveness, cost, owner in MITIGATED_BY:
        db.write("""
            MATCH (r:RiskEvent {name: $risk})
            MERGE (r)-[m:MITIGATED_BY]->(a:MitigationAction {name: $action})
            SET m.mitigation_type = $mtype,
                m.effectiveness = $effectiveness,
                m.cost_usd_mn = $cost,
                m.owner = $owner
        """, {
            "risk": risk, "action": action, "mtype": mtype,
            "effectiveness": effectiveness, "cost": cost, "owner": owner
        })
    print(f"  ✓ {len(MITIGATED_BY)} MITIGATED_BY relationships")


def load_affects(db: Neo4jConnection) -> None:
    for risk, entity, impact_type, severity, revenue_impact in AFFECTS:
        db.write("""
            MATCH (r:RiskEvent {name: $risk})
            MATCH (e) WHERE e.name = $entity
            MERGE (r)-[a:AFFECTS]->(e)
            SET a.impact_type = $impact_type,
                a.severity_on_entity = $severity,
                a.revenue_impact_usd_mn = $revenue
        """, {
            "risk": risk, "entity": entity, "impact_type": impact_type,
            "severity": severity, "revenue": revenue_impact
        })
    print(f"  ✓ {len(AFFECTS)} AFFECTS relationships")


def load_contracted_with(db: Neo4jConnection) -> None:
    for buyer, supplier, cid, start, end, value in CONTRACTED_WITH:
        db.write("""
            MATCH (b) WHERE b.name = $buyer
            MATCH (s:Supplier {name: $supplier})
            MATCH (c:ProcurementContract {contract_id: $cid})
            MERGE (b)-[r:CONTRACTED_WITH]->(s)
            SET r.contract_id = $cid,
                r.start_date = $start,
                r.end_date = $end,
                r.annual_value_usd_mn = $value
        """, {
            "buyer": buyer, "supplier": supplier, "cid": cid,
            "start": start, "end": end, "value": value
        })
    print(f"  ✓ {len(CONTRACTED_WITH)} CONTRACTED_WITH relationships")


def load_owns_warehouse(db: Neo4jConnection) -> None:
    for owner, warehouse, otype, cost in OWNS_WAREHOUSE:
        db.write("""
            MATCH (o) WHERE o.name = $owner
            MATCH (w:Warehouse {name: $warehouse})
            MERGE (o)-[r:OWNS_WAREHOUSE]->(w)
            SET r.ownership_type = $otype, r.annual_cost_usd_mn = $cost
        """, {"owner": owner, "warehouse": warehouse, "otype": otype, "cost": cost})
    print(f"  ✓ {len(OWNS_WAREHOUSE)} OWNS_WAREHOUSE relationships")


def load_carries_for(db: Neo4jConnection) -> None:
    for carrier, entity, ctype, value in CARRIES_FOR:
        db.write("""
            MATCH (c:LogisticsCarrier {name: $carrier})
            MATCH (e) WHERE e.name = $entity
            MERGE (c)-[r:CARRIES_FOR]->(e)
            SET r.contract_type = $ctype, r.annual_value_usd_mn = $value
        """, {"carrier": carrier, "entity": entity, "ctype": ctype, "value": value})
    print(f"  ✓ {len(CARRIES_FOR)} CARRIES_FOR relationships")


def load_adjacent_to(db: Neo4jConnection) -> None:
    for loc1, loc2, dist, corridor, border in ADJACENT_TO:
        db.write("""
            MATCH (a:Location {name: $loc1})
            MATCH (b:Location {name: $loc2})
            MERGE (a)-[r:ADJACENT_TO]->(b)
            SET r.distance_km = $dist,
                r.trade_corridor = $corridor,
                r.border_crossing = $border
        """, {
            "loc1": loc1, "loc2": loc2, "dist": dist,
            "corridor": corridor, "border": border
        })
    print(f"  ✓ {len(ADJACENT_TO)} ADJACENT_TO relationships")


def load_dual_sourced_with(db: Neo4jConnection) -> None:
    for s1, s2, component, split, reason in DUAL_SOURCED_WITH:
        db.write("""
            MATCH (a:Supplier {name: $s1})
            MATCH (b:Supplier {name: $s2})
            MERGE (a)-[r:DUAL_SOURCED_WITH]->(b)
            SET r.component = $component,
                r.split_pct_primary = $split,
                r.reason = $reason
        """, {
            "s1": s1, "s2": s2, "component": component,
            "split": split, "reason": reason
        })
    print(f"  ✓ {len(DUAL_SOURCED_WITH)} DUAL_SOURCED_WITH relationships")


def load_qualified_by(db: Neo4jConnection) -> None:
    for supplier, manufacturer, approval, requal, components in QUALIFIED_BY:
        db.write("""
            MATCH (s:Supplier {name: $supplier})
            MATCH (m:Manufacturer {name: $manufacturer})
            MERGE (s)-[r:QUALIFIED_BY]->(m)
            SET r.approval_date = $approval,
                r.re_qualification_due = $requal,
                r.approved_components = $components
        """, {
            "supplier": supplier, "manufacturer": manufacturer,
            "approval": approval, "requal": requal, "components": components
        })
    print(f"  ✓ {len(QUALIFIED_BY)} QUALIFIED_BY relationships")


def load_shipments(db: Neo4jConnection) -> None:
    for sid, product, customer, fr, to, status, carrier, dep, eta, value, insured, delay in SHIPMENTS:
        db.write("""
            MATCH (p:Product {name: $product})
            MATCH (c:Customer {name: $customer})
            MATCH (from:Location {name: $from_loc})
            MATCH (to:Location {name: $to_loc})
            MERGE (sh:Shipment {shipment_id: $sid})
            SET sh.status = $status,
                sh.departure_date = $dep,
                sh.eta_date = $eta,
                sh.value_usd_k = $value,
                sh.insured = $insured,
                sh.delay_days = $delay
            MERGE (sh)-[:OF_PRODUCT]->(p)
            MERGE (sh)-[:TO_CUSTOMER]->(c)
            MERGE (sh)-[:FROM]->(from)
            MERGE (sh)-[:TO]->(to)
        """, {
            "sid": sid, "product": product, "customer": customer,
            "from_loc": fr, "to_loc": to, "status": status,
            "carrier": carrier, "dep": dep, "eta": eta,
            "value": value, "insured": insured, "delay": delay
        })
    print(f"  ✓ {len(SHIPMENTS)} Shipment nodes + relationships")


def load_insured_by(db: Neo4jConnection) -> None:
    for entity, insurer, policy, coverage, premium, deductible in INSURED_BY:
        db.write("""
            MATCH (e) WHERE e.name = $entity
            MERGE (i:Insurer {name: $insurer})
            MERGE (e)-[r:INSURED_BY]->(i)
            SET r.policy_type = $policy,
                r.coverage_usd_mn = $coverage,
                r.premium_pct_revenue = $premium,
                r.deductible_usd_k = $deductible
        """, {
            "entity": entity, "insurer": insurer, "policy": policy,
            "coverage": coverage, "premium": premium, "deductible": deductible
        })
    print(f"  ✓ {len(INSURED_BY)} INSURED_BY relationships")


def load_audited_by(db: Neo4jConnection) -> None:
    for supplier, auditor, date, atype, score, findings, follow_up in AUDITED_BY:
        db.write("""
            MATCH (s:Supplier {name: $supplier})
            MERGE (a:Auditor {name: $auditor})
            MERGE (s)-[r:AUDITED_BY]->(a)
            SET r.audit_date = $date,
                r.audit_type = $atype,
                r.score = $score,
                r.findings_count = $findings,
                r.follow_up_due = $follow_up
        """, {
            "supplier": supplier, "auditor": auditor, "date": date,
            "atype": atype, "score": score, "findings": findings, "follow_up": follow_up
        })
    print(f"  ✓ {len(AUDITED_BY)} AUDITED_BY relationships")

def load_uses(db: Neo4jConnection) -> None:
    for rel in USES:
        product, component, *props = rel
        db.write("""
            MATCH (p:Product {name: $product})
            MATCH (c:Component {name: $component})
            MERGE (p)-[r:USES]->(c)
            SET r.quantity_per_unit = $qty,
                r.bom_level = $level,
                r.optional = $opt,
                r.procurement_type = $proc
        """, {
            "product": product, "component": component,
            "qty": props[0], "level": props[1], "opt": props[2], "proc": props[3]
        })
    print(f"  ✓ {len(USES)} USES relationships")

def load_all(db: Neo4jConnection, clear_first: bool = False) -> None:
    if clear_first:
        print("  Clearing existing data...")
        db.write("MATCH (n) DETACH DELETE n")

    print("\n[1/2] Loading nodes...")
    setup_constraints(db)
    load_suppliers(db)
    load_manufacturers(db)
    load_components(db)
    load_products(db)
    load_customers(db)
    load_locations(db)
    load_risk_events(db)
    load_warehouses(db)
    load_logistics_carriers(db)
    load_procurement_contracts(db)
    load_certifications(db)

    print("\n[2/2] Loading relationships...")
    
    load_supplies(db)
    load_produces(db)
    load_uses(db)
    load_located_in(db)
    load_has_risk(db)
    load_has_alternative(db)
    load_ships_via(db)
    load_stored_in(db)
    load_certified_by(db)
    load_sells_to(db)
    load_manufactures_for(db)
    load_sources_from(db)
    load_competes_with(db)
    load_transits_through(db)
    load_mitigated_by(db)
    load_affects(db)
    load_contracted_with(db)
    load_owns_warehouse(db)
    load_carries_for(db)
    load_adjacent_to(db)
    load_dual_sourced_with(db)
    load_qualified_by(db)
    load_shipments(db)
    load_insured_by(db)
    load_audited_by(db)

    # Summary
    summary = db.read("""
        MATCH (n) RETURN labels(n)[0] AS Label, count(n) AS Count
        ORDER BY Count DESC
    """)
    rel_count = db.read("MATCH ()-[r]->() RETURN count(r) AS total")[0]["total"]

    print("\n─── Supply Chain Graph Summary ─────────────────────")
    for row in summary:
        print(f"  {row['Label']:<25} {row['Count']} nodes")
    print(f"  {'Relationships':<25} {rel_count}")
    print("─────────────────────────────────────────────────────")


if __name__ == "__main__":
    with Neo4jConnection() as db:
        load_all(db, clear_first=True)
        print("\n✓ Supply Chain & Procurement Intelligence Graph loaded.")
        print("  Open http://localhost:7474 to explore visually.")