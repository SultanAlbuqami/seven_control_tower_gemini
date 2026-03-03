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

    # OT signals
    ot = snapshot.get("ot_events", {})
    unacked_sev1 = ot.get("unacked_sev1", 0)
    unacked_sev2 = ot.get("unacked_sev2", 0)
    ot_total_open = ot.get("total_open", 0)
    ot_clusters = ot.get("clusters", [])

    # Ticketing signals
    tkt = snapshot.get("ticketing", {})
    tkt_anomaly_windows = tkt.get("anomaly_windows", 0)
    tkt_min_sr = tkt.get("min_success_rate")
    tkt_max_lat = tkt.get("max_latency_p95")
    tkt_offline_fb = tkt.get("total_offline_fallbacks", 0)

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
        "unacked_sev1": unacked_sev1,
        "unacked_sev2": unacked_sev2,
        "ot_total_open": ot_total_open,
        "ot_clusters": ot_clusters,
        "tkt_anomaly_windows": tkt_anomaly_windows,
        "tkt_min_sr": tkt_min_sr,
        "tkt_max_lat": tkt_max_lat,
        "tkt_offline_fb": tkt_offline_fb,
    }


def recommend(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Return a valid recommendation dict derived from heuristic rules."""
    s = build_snapshot_summary(snapshot)

    # ---------- confidence heuristic ----------
    base_confidence = 0.85
    penalty = min(
        0.45,
        (s["red_gates"] * 0.04)
        + (s["open_sev12"] * 0.05)
        + (s["missing_evd"] * 0.005)
        + (s["unacked_sev1"] * 0.07)
        + (s["tkt_anomaly_windows"] * 0.003),
    )
    confidence = round(max(0.40, base_confidence - penalty), 2)

    # ---------- executive summary ----------
    if s["red_gates"] == 0 and s["open_sev12"] == 0 and s["unacked_sev1"] == 0:
        summary = (
            "Readiness posture is GREEN across all gates with no open Sev-1/2 incidents. "
            "Focus on completing remaining evidence items and scheduling the final Go/No-Go review."
        )
    elif s["red_gates"] > 3 or s["open_sev12"] >= 2 or s["unacked_sev1"] >= 1:
        summary = (
            f"CRITICAL: {s['red_gates']} RED readiness gate(s), {s['open_sev12']} open Sev-1/2 "
            f"incident(s), and {s['unacked_sev1']} unacknowledged Sev-1 OT alarm(s) require "
            "immediate executive attention before Day-One opening. "
            "Do NOT proceed to Go/No-Go without resolving the blockers listed below."
        )
    else:
        summary = (
            f"Readiness is AT RISK: {s['red_gates']} RED gate(s), {s['missing_evd']} missing "
            "evidence items, and active OT/ticketing signals must be resolved. "
            "Escalate outstanding vendor fixes and run a final peak drill before Go/No-Go sign-off."
        )

    # ---------- top risks ----------
    top_risks: list[dict[str, str]] = []

    if s["red_gates"] > 0:
        sample_blockers = s["top_blockers"][:3]
        blocker_str = "; ".join(
            f"{b.get('service','?')}/{b.get('gate','?')}" for b in sample_blockers
        ) if sample_blockers else "see readiness heatmap"
        top_risks.append({
            "risk": f"{s['red_gates']} gate(s) in RED status",
            "impact": "Go/No-Go cannot be signed off with RED gates",
            "evidence": f"Blocked services/gates: {blocker_str}",
            "owner": "Ops Readiness Lead",
            "next_action": "Obtain vendor retest evidence and re-evaluate within 24 h",
        })

    if s["open_sev12"] > 0:
        top_risks.append({
            "risk": f"{s['open_sev12']} open Sev-1/2 incident(s)",
            "impact": "Operational stability risk on Day-One",
            "evidence": "See Incidents page for incident IDs and summaries",
            "owner": "IT Operations Lead",
            "next_action": "Convene war-room, confirm RCA, and apply preventive fix before Day-One",
        })

    if s["missing_evd"] > 0:
        sample_missing = s["missing_top"][:2]
        types_str = ", ".join(m.get("evidence_type", "?") for m in sample_missing) if sample_missing else "see Evidence Pack"
        top_risks.append({
            "risk": f"{s['missing_evd']} missing evidence item(s)",
            "impact": "Cannot demonstrate audit-readiness without complete evidence pack",
            "evidence": f"Missing types include: {types_str}",
            "owner": "Vendor Manager, Ops Readiness Lead",
            "next_action": "Chase owners via Evidence Pack page; upload artefacts to shared drive",
        })

    if s["breach_vendors"]:
        vendor_names = ", ".join(v.get("vendor", "?") for v in s["breach_vendors"][:3])
        top_risks.append({
            "risk": f"Vendor SLA breaches ({len(s['breach_vendors'])} vendor(s))",
            "impact": "Contractual breach; support degradation risk during opening",
            "evidence": f"Breaching vendors: {vendor_names}",
            "owner": "Vendor Manager",
            "next_action": "Raise formal breach notice; agree remediation timeline",
        })

    if s["unacked_sev1"] > 0:
        top_risks.append({
            "risk": f"{s['unacked_sev1']} unacknowledged Sev-1 OT alarm(s)",
            "impact": "Safety and facility risk if BMS/Access/CCTV alarms go unactioned",
            "evidence": "See OT Events page — filter Sev-1 unacknowledged",
            "owner": "Security Ops / Facilities",
            "next_action": "Acknowledge and dispatch field response within 15 minutes",
        })

    if s["tkt_anomaly_windows"] > 5:
        top_risks.append({
            "risk": f"Ticketing scan anomalies detected ({s['tkt_anomaly_windows']} windows below threshold)",
            "impact": "Entry queue buildup/gate failure risk at peak",
            "evidence": f"Min scan success rate: {s['tkt_min_sr']:.1%}" if s["tkt_min_sr"] else "See Ticketing KPIs page",
            "owner": "IT Ops / Venue Ops",
            "next_action": "Review gate controller logs; test offline fallback mode activation",
        })

    if not top_risks:
        top_risks.append({
            "risk": "No critical risks detected",
            "impact": "Low — maintain current momentum",
            "evidence": "All gates GREEN, no open Sev-1/2 incidents, no critical OT alarms",
            "owner": "Ops Readiness Lead",
            "next_action": "Schedule final Go/No-Go sign-off meeting",
        })

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
    if s["unacked_sev1"] > 0 or s["unacked_sev2"] > 2:
        actions_24h.append("Dispatch field team to acknowledge and clear all Sev-1/2 OT alarms immediately")
    if s["tkt_anomaly_windows"] > 0:
        actions_24h.append("Test ticketing gate offline-fallback procedure; confirm QR scanner firmware versions")
    if not actions_24h:
        actions_24h.append("Final readiness review call with all service leads")
    actions_24h.append("Confirm on-call roster and escalation paths for Day-One operations")
    actions_24h.append("Validate monitoring dashboards and alert routing end-to-end")

    # ---------- actions 7d ----------
    actions_7d = [
        "Run full peak-load drill across all criticality-3 services",
        "Complete SOPs review and confirm training attendance sign-off",
        "Conduct tabletop exercise for Sev-1/2 scenarios including OT alarm storms",
        "Finalise Go/No-Go pack: all evidence, punch list closure, sign-off matrix",
        "Confirm vendor contacts and escalation contacts for Day-One standby",
        "Validate failover + rollback runbooks with live test",
        "Run BMS/Access/CCTV OT alarm drill — confirm ack times meet SLA",
        "Stress-test ticketing gate throughput at 110% peak load; validate offline fallback",
        "Schedule post-Day-One retrospective (T+48h)",
    ]

    # ---------- vendor questions ----------
    vendor_questions = [
        "What is the current status of open critical defects?",
        "Can you confirm monitoring probe coverage and alerting channels?",
        "What is your Day-One standby team structure and escalation SLA?",
        "Are retest reports available for all RED/AMBER acceptance-test gates?",
        "Confirm your rollback procedure and maximum rollback time for each service",
        "What is the OT/BMS vendor on-call contact and escalation path for Day-One?",
    ]

    # ---------- OT signals ----------
    ot_signals: list[str] = []
    if s["unacked_sev1"] > 0:
        ot_signals.append(f"{s['unacked_sev1']} Sev-1 OT alarm(s) unacknowledged — immediate action required")
    if s["unacked_sev2"] > 0:
        ot_signals.append(f"{s['unacked_sev2']} Sev-2 OT alarm(s) unacknowledged — assign within 30 min")
    if s["ot_total_open"] > 10:
        ot_signals.append(f"{s['ot_total_open']} total open OT events — review BMS/CCTV/Access dashboards")
    if s["ot_clusters"]:
        cluster_str = "; ".join(
            f"{c.get('zone','?')}/{c.get('subsystem','?')} ({c.get('size',0)})"
            for c in s["ot_clusters"][:3]
        )
        ot_signals.append(f"OT alarm clusters detected: {cluster_str}")
    if not ot_signals:
        ot_signals.append("No critical OT alarms detected — continue routine monitoring")

    # ---------- ticketing signals ----------
    ticketing_signals: list[str] = []
    if s["tkt_anomaly_windows"] > 0:
        ticketing_signals.append(
            f"{s['tkt_anomaly_windows']} ticketing time windows below scan-success or latency threshold"
        )
    if s["tkt_min_sr"] is not None and s["tkt_min_sr"] < 0.94:
        ticketing_signals.append(f"Minimum scan success rate dropped to {s['tkt_min_sr']:.1%} — below critical threshold")
    if s["tkt_max_lat"] is not None and s["tkt_max_lat"] > 1500:
        ticketing_signals.append(f"Peak QR validation latency: {s['tkt_max_lat']:.0f} ms p95 — exceeds 1500 ms critical threshold")
    if s["tkt_offline_fb"] > 0:
        ticketing_signals.append(f"Offline fallback activated {s['tkt_offline_fb']} time(s) — review payment gateway connectivity")
    if not ticketing_signals:
        ticketing_signals.append("Ticketing scan success and latency within normal bounds")

    # ---------- incident improvements ----------
    incident_improvements: list[str] = []
    if s["mtta"] and s["mtta"] > 20:
        incident_improvements.append(f"Mean MTTA {s['mtta']:.0f} min exceeds 20 min target — review alert routing and on-call roster")
    if s["mttr"] and s["mttr"] > 120:
        incident_improvements.append(f"Mean MTTR {s['mttr']:.0f} min is high — verify runbooks and escalation paths")
    incident_improvements.append("Ensure all Sev-1/2 incidents have RCA documented before Day-One")
    incident_improvements.append("Configure automated escalation if MTTA > 15 min for Sev-1 incidents")

    # ---------- vendor flags ----------
    vendor_flags: list[str] = []
    for v in s["breach_vendors"][:4]:
        vname = v.get("vendor", "?")
        bc = v.get("breach_count", 0)
        vendor_flags.append(f"{vname}: {bc} SLA metric(s) in breach — escalate and request remediation plan")
    if not vendor_flags:
        vendor_flags.append("All vendors within SLA thresholds at time of snapshot")

    # ---------- KPIs to watch ----------
    kpis_to_watch = [
        {"kpi": "Entry Queue Time (min)", "reason": "Primary guest-experience metric; directly tied to gate throughput", "threshold": "< 8 min"},
        {"kpi": "Ticket Scan Success (%)", "reason": "Failure causes entry backlog and guest complaints", "threshold": "> 99.0%"},
        {"kpi": "Gate QR Validation Latency p95 (ms)", "reason": "Latency spikes indicate backend/network issues before queue forms", "threshold": "< 800 ms"},
        {"kpi": "POS Success (%)", "reason": "Revenue impact if below target", "threshold": "> 99.2%"},
        {"kpi": "Wi-Fi Availability (%)", "reason": "Underpins mobile ticketing and staff operations", "threshold": "> 99.5%"},
        {"kpi": "CCTV Coverage (%)", "reason": "Safety obligation; security ops dependency", "threshold": "> 98.0%"},
        {"kpi": "OT Sev-1 Alarm Ack Time (min)", "reason": "Unacked critical alarms represent unmitigated safety risk", "threshold": "< 5 min"},
    ]

    # ---------- assumptions ----------
    assumptions = [
        "Recommendations are generated by the heuristic engine (offline mode — no Groq API call was made)",
        "Snapshot is based on current synthetic demo data; replace with live data for production use",
        "Go/No-Go criterion: zero RED gates + zero open Sev-1/2 incidents + evidence completion ≥ 90%",
        "Vendor remediation timelines assume 24-hour response SLA from each vendor",
        "OT alarm thresholds: Sev-1 ack within 5 min, Sev-2 ack within 30 min",
        "Ticketing anomaly threshold: scan success < 97% or p95 latency > 800 ms",
    ]

    result = {
        "executive_summary": summary,
        "top_risks": top_risks,
        "actions_next_24h": actions_24h,
        "actions_next_7d": actions_7d,
        "vendor_questions": vendor_questions,
        "kpis_to_watch": kpis_to_watch,
        "ot_signals": ot_signals,
        "ticketing_signals": ticketing_signals,
        "incident_improvements": incident_improvements,
        "vendor_flags": vendor_flags,
        "assumptions": assumptions,
        "confidence": confidence,
    }

    # Defensive: ensure all required keys are present
    for k in REQUIRED_KEYS:
        assert k in result, f"Heuristic bug: missing key {k}"

    return result
