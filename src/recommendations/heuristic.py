"""Deterministic heuristic recommender.

Produces valid schema output from aggregated metrics without any API calls.
Output is intentionally conservative and actionable.
"""
from __future__ import annotations

from typing import Any

from src.recommendations.schema import REQUIRED_KEYS


def build_snapshot_summary(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Extract key scalar metrics from the snapshot dict."""
    red_gates = snapshot.get("readiness", {}).get("red_gate_count", 0)
    missing_evd = snapshot.get("evidence", {}).get("missing_count", 0)
    open_sev12 = snapshot.get("incidents", {}).get("open_sev1_2", 0)
    open_count = snapshot.get("incidents", {}).get("open_count", 0)
    mtta = snapshot.get("incidents", {}).get("mtta_min")
    mttr = snapshot.get("incidents", {}).get("mttr_min")
    breach_vendors = snapshot.get("vendors", {}).get("breach_vendors", [])

    top_blockers = snapshot.get("readiness", {}).get("top_blockers", [])
    missing_top = snapshot.get("evidence", {}).get("missing_top", [])

    return {
        "red_gates": red_gates,
        "missing_evd": missing_evd,
        "open_sev12": open_sev12,
        "open_count": open_count,
        "mtta": mtta,
        "mttr": mttr,
        "breach_vendors": breach_vendors,
        "top_blockers": top_blockers,
        "missing_top": missing_top,
    }


def recommend(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Return a valid recommendation dict derived from heuristic rules."""
    s = build_snapshot_summary(snapshot)

    # ---------- confidence heuristic ----------
    # Lower confidence when many reds/missing items — signals risk
    base_confidence = 0.85
    penalty = min(0.40, (s["red_gates"] * 0.04) + (s["open_sev12"] * 0.05) + (s["missing_evd"] * 0.005))
    confidence = round(max(0.40, base_confidence - penalty), 2)

    # ---------- executive summary ----------
    if s["red_gates"] == 0 and s["open_sev12"] == 0:
        summary = (
            "Readiness posture is GREEN across all gates with no open Sev-1/2 incidents. "
            "Focus on completing remaining evidence items and scheduling the final Go/No-Go review."
        )
    elif s["red_gates"] > 3 or s["open_sev12"] >= 2:
        summary = (
            f"CRITICAL: {s['red_gates']} RED readiness gate(s) and {s['open_sev12']} open Sev-1/2 "
            "incident(s) require immediate executive attention before Day-One opening. "
            "Do NOT proceed to Go/No-Go without resolving the blockers listed below."
        )
    else:
        summary = (
            f"Readiness is AT RISK: {s['red_gates']} RED gate(s) and {s['missing_evd']} missing "
            "evidence items must be resolved. Escalate outstanding vendor fixes and run a final "
            "peak drill before Go/No-Go sign-off."
        )

    # ---------- top risks ----------
    top_risks: list[dict[str, str]] = []

    if s["red_gates"] > 0:
        sample_blockers = s["top_blockers"][:3]
        blocker_str = "; ".join(
            f"{b.get('service','?')}/{b.get('gate','?')}" for b in sample_blockers
        ) if sample_blockers else "see readiness heatmap"
        top_risks.append(
            {
                "risk": f"{s['red_gates']} gate(s) in RED status",
                "impact": "Go/No-Go cannot be signed off with RED gates",
                "evidence": f"Blocked services/gates: {blocker_str}",
                "owner": "Ops Readiness Lead",
                "next_action": "Obtain vendor retest evidence and re-evaluate within 24 h",
            }
        )

    if s["open_sev12"] > 0:
        top_risks.append(
            {
                "risk": f"{s['open_sev12']} open Sev-1/2 incident(s)",
                "impact": "Operational stability risk on Day-One",
                "evidence": "See Incidents page for incident IDs and summaries",
                "owner": "IT Operations Lead",
                "next_action": "Convene war-room, confirm RCA, and apply preventive fix before Day-One",
            }
        )

    if s["missing_evd"] > 0:
        sample_missing = s["missing_top"][:2]
        types_str = ", ".join(m.get("evidence_type", "?") for m in sample_missing) if sample_missing else "see Evidence Pack"
        top_risks.append(
            {
                "risk": f"{s['missing_evd']} missing evidence item(s)",
                "impact": "Cannot demonstrate audit-readiness without complete evidence pack",
                "evidence": f"Missing types include: {types_str}",
                "owner": "Vendor Manager, Ops Readiness Lead",
                "next_action": "Chase owners via Evidence Pack page; upload artefacts to shared drive",
            }
        )

    if s["breach_vendors"]:
        vendor_names = ", ".join(v.get("vendor", "?") for v in s["breach_vendors"][:3])
        top_risks.append(
            {
                "risk": f"Vendor SLA breaches ({len(s['breach_vendors'])} vendor(s))",
                "impact": "Contractual breach; support degradation risk during opening",
                "evidence": f"Breaching vendors: {vendor_names}",
                "owner": "Vendor Manager",
                "next_action": "Raise formal breach notice; agree remediation timeline",
            }
        )

    if not top_risks:
        top_risks.append(
            {
                "risk": "No critical risks detected",
                "impact": "Low — maintain current momentum",
                "evidence": "All gates GREEN, no open Sev-1/2 incidents",
                "owner": "Ops Readiness Lead",
                "next_action": "Schedule final Go/No-Go sign-off meeting",
            }
        )

    # ---------- actions 24h ----------
    actions_24h: list[str] = []
    if s["red_gates"] > 0:
        actions_24h.append("Chase vendors for retest evidence on all RED gates; update readiness tracker")
    if s["open_sev12"] > 0:
        actions_24h.append("Convene Sev-1/2 war-room; confirm RCA complete and preventive action in place")
    if s["missing_evd"] > 0:
        actions_24h.append("Send evidence-chase email to all owners listed in Evidence Pack")
    if s["breach_vendors"]:
        actions_24h.append("Notify vendor SLA breach formally; request remediation commitment by EOD")
    if not actions_24h:
        actions_24h.append("Final readiness review call with all service leads")
    actions_24h.append("Confirm on-call roster and escalation paths for Day-One operations")
    actions_24h.append("Validate monitoring dashboards and alert routing end-to-end")

    # ---------- actions 7d ----------
    actions_7d = [
        "Run full peak-load drill across all criticality-3 services",
        "Complete SOPs review and confirm training attendance sign-off",
        "Conduct tabletop exercise for Sev-1/2 scenarios",
        "Finalise Go/No-Go pack: all evidence, punch list closure, sign-off matrix",
        "Confirm vendor contacts and escalation contacts for Day-One standby",
        "Validate failover + rollback runbooks with live test",
        "Schedule post-Day-One retrospective (T+48h)",
    ]

    # ---------- vendor questions ----------
    vendor_questions = [
        "What is the current status of open critical defects?" ,
        "Can you confirm monitoring probe coverage and alerting channels?",
        "What is your Day-One standby team structure and escalation SLA?",
        "Are retest reports available for all RED/AMBER acceptance-test gates?",
        "Confirm your rollback procedure and maximum rollback time for each service",
    ]

    # ---------- KPIs to watch ----------
    kpis_to_watch = [
        {"kpi": "Entry Queue Time (min)", "reason": "Primary guest-experience metric; directly tied to Gate entry throughput", "threshold": "< 8 min (target)"},
        {"kpi": "Ticket Scan Success (%)", "reason": "Failure causes entry backlog and guest complaints", "threshold": "> 99.0%"},
        {"kpi": "POS Success (%)", "reason": "Revenue impact if below target", "threshold": "> 99.2%"},
        {"kpi": "Wi-Fi Availability (%)", "reason": "Underpins mobile ticketing and staff operations", "threshold": "> 99.5%"},
        {"kpi": "CCTV Coverage (%)", "reason": "Safety obligation; security ops dependency", "threshold": "> 98.0%"},
    ]

    # ---------- assumptions ----------
    assumptions = [
        "Recommendations are generated by the heuristic engine (offline mode — no Gemini API call was made)",
        "Snapshot is based on current synthetic demo data; replace with live data for production use",
        "Go/No-Go criterion: zero RED gates + zero open Sev-1/2 incidents + evidence completion ≥ 90%",
        "Vendor remediation timelines assume 24-hour response SLA from each vendor",
    ]

    result = {
        "executive_summary": summary,
        "top_risks": top_risks,
        "actions_next_24h": actions_24h,
        "actions_next_7d": actions_7d,
        "vendor_questions": vendor_questions,
        "kpis_to_watch": kpis_to_watch,
        "assumptions": assumptions,
        "confidence": confidence,
    }

    # Defensive: ensure all required keys are present
    for k in REQUIRED_KEYS:
        assert k in result, f"Heuristic bug: missing key {k}"

    return result
