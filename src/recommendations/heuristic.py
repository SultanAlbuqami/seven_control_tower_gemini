from __future__ import annotations

from typing import Any

from src.recommendations.schema import empty_response
from src.system_landscape import THRESHOLDS


def _trace_refs(records: list[dict[str, Any]], *fields: str) -> list[str]:
    refs: list[str] = []
    for record in records:
        for field in fields:
            value = record.get(field)
            if value is not None and str(value).strip():
                refs.append(f"{field}:{value}")
    return refs[:4]


def _overall_status(snapshot: dict[str, Any]) -> str:
    readiness = snapshot.get("readiness", {})
    incidents = snapshot.get("incidents", {})
    ot = snapshot.get("ot_signals", snapshot.get("ot_events", {}))
    ticketing = snapshot.get("ticketing_signals", snapshot.get("ticketing", {}))
    vendors = snapshot.get("vendors", {})
    if (
        readiness.get("red_gate_count", 0) > 0
        or incidents.get("open_sev1_2", 0) > 0
        or ot.get("unacked_sev1", 0) > 0
        or (ticketing.get("min_success_rate") is not None and ticketing.get("min_success_rate", 1.0) < THRESHOLDS["ticketing_scan_success_rate_crit"])
        or vendors.get("high_penalty_risk", 0) > 0
    ):
        return "CRIT"
    if (
        readiness.get("amber_gate_count", 0) > 0
        or snapshot.get("evidence", {}).get("missing_count", 0) > 0
        or ticketing.get("anomaly_windows", 0) > 0
        or ot.get("unacked_sev2", 0) > 0
    ):
        return "WARN"
    return "OK"


def _confidence(snapshot: dict[str, Any], status: str) -> float:
    base = {"OK": 0.92, "WARN": 0.76, "CRIT": 0.58}[status]
    penalty = (
        snapshot.get("readiness", {}).get("red_gate_count", 0) * 0.03
        + snapshot.get("incidents", {}).get("open_sev1_2", 0) * 0.04
        + snapshot.get("evidence", {}).get("missing_count", 0) * 0.002
        + snapshot.get("ticketing_signals", {}).get("anomaly_windows", 0) * 0.001
    )
    return round(max(0.35, base - min(0.30, penalty)), 2)


def recommend(snapshot: dict[str, Any]) -> dict[str, Any]:
    response = empty_response()
    readiness = snapshot.get("readiness", {})
    evidence = snapshot.get("evidence", {})
    incidents = snapshot.get("incidents", {})
    vendors = snapshot.get("vendors", {})
    ot = snapshot.get("ot_signals", snapshot.get("ot_events", {}))
    ticketing = snapshot.get("ticketing_signals", snapshot.get("ticketing", {}))

    status = _overall_status(snapshot)
    go_no_go = "HOLD" if status == "CRIT" else "GO"
    confidence = _confidence(snapshot, status)

    headline = {
        "OK": "Readiness posture is on track with no immediate Day-One blockers.",
        "WARN": "Readiness posture is workable but needs focused closure before the next executive review.",
        "CRIT": "Readiness posture is below launch tolerance and requires executive intervention before Go/No-Go.",
    }[status]
    rationale = [
        f"RED gates: {readiness.get('red_gate_count', 0)}",
        f"Missing evidence items: {evidence.get('missing_count', 0)}",
        f"Open Sev-1/2 incidents: {incidents.get('open_sev1_2', 0)}",
        f"Unacknowledged Sev-1 OT alarms: {ot.get('unacked_sev1', 0)}",
        f"Ticketing anomaly windows: {ticketing.get('anomaly_windows', 0)}",
    ]
    response["summary"] = {
        "headline": headline,
        "status": status,
        "go_no_go": go_no_go,
        "confidence": confidence,
        "rationale": rationale,
    }

    top_risks: list[dict[str, Any]] = []
    if readiness.get("red_gate_count", 0) > 0:
        blockers = readiness.get("top_blockers", [])
        top_risks.append(
            {
                "title": f"{readiness.get('red_gate_count', 0)} readiness gate(s) remain RED",
                "status": "CRIT",
                "impact": "Go/No-Go should remain on HOLD until blocked gates are re-tested and re-scored.",
                "owner": "Readiness Director",
                "evidence": "Blocked services still show unresolved dependencies in the ORR tracker.",
                "trace_refs": _trace_refs(blockers, "service", "gate", "source_system"),
            }
        )
    if incidents.get("open_sev1_2", 0) > 0:
        open_incidents = incidents.get("open_top", [])
        top_risks.append(
            {
                "title": f"{incidents.get('open_sev1_2', 0)} open Sev-1/2 incident(s)",
                "status": "CRIT",
                "impact": "Guest-entry resilience and control-room confidence remain at risk.",
                "owner": "IT Operations Lead",
                "evidence": "Critical incidents are still open or mitigated rather than resolved.",
                "trace_refs": _trace_refs(open_incidents, "incident_id", "source_id", "service"),
            }
        )
    if evidence.get("missing_count", 0) > 0:
        missing = evidence.get("missing_top", [])
        top_risks.append(
            {
                "title": f"{evidence.get('missing_count', 0)} evidence item(s) still missing",
                "status": "WARN" if status != "CRIT" else "CRIT",
                "impact": "Audit readiness and formal sign-off are exposed until document refs are complete.",
                "owner": "Evidence Pack Coordinator",
                "evidence": "Open evidence actions remain across multiple services and gates.",
                "trace_refs": _trace_refs(missing, "evidence_id", "doc_ref", "service"),
            }
        )
    if vendors.get("breach_count", 0) > 0:
        breach_vendors = vendors.get("breach_vendors", [])
        top_risks.append(
            {
                "title": f"{vendors.get('breach_count', 0)} vendor scorecard breach signal(s)",
                "status": "WARN" if vendors.get("high_penalty_risk", 0) == 0 else "CRIT",
                "impact": "Service stability and commercial recovery exposure are both elevated.",
                "owner": "Vendor Manager",
                "evidence": "Availability, MTTA, or MTTR is out of contract for one or more partners.",
                "trace_refs": _trace_refs(breach_vendors, "vendor", "dashboard_ref", "source_system"),
            }
        )
    if ot.get("unacked_sev1", 0) > 0:
        top_risks.append(
            {
                "title": f"{ot.get('unacked_sev1', 0)} unacknowledged Sev-1 OT alarm(s)",
                "status": "CRIT",
                "impact": "Critical alarms must be acknowledged before Day-One operating mode is credible.",
                "owner": "Security Ops / Facilities",
                "evidence": "OT event feed still shows critical alarms without acknowledgement.",
                "trace_refs": _trace_refs(ot.get("top_open_events", []), "ot_event_id", "device_id", "linked_incident_id"),
            }
        )
    if ticketing.get("anomaly_windows", 0) > 0:
        worst_area = ticketing.get("worst_areas", [])
        top_risks.append(
            {
                "title": f"{ticketing.get('anomaly_windows', 0)} ticketing anomaly window(s)",
                "status": "WARN" if ticketing.get("min_success_rate", 1.0) >= THRESHOLDS["ticketing_scan_success_rate_crit"] else "CRIT",
                "impact": "Queue growth and degraded guest-entry flow are likely during peak arrivals.",
                "owner": "Guest Access Lead",
                "evidence": "Scan success or QR latency thresholds are breached in the ticketing feed.",
                "trace_refs": _trace_refs(worst_area, "venue_area"),
            }
        )
    if not top_risks:
        top_risks.append(
            {
                "title": "No material blockers detected",
                "status": "OK",
                "impact": "The next executive review can focus on maintaining operating discipline.",
                "owner": "Readiness Director",
                "evidence": "Current snapshot shows no RED gates, critical incidents, or critical OT alarms.",
                "trace_refs": [],
            }
        )
    response["top_risks"] = top_risks

    next_actions: list[dict[str, Any]] = []
    if readiness.get("red_gate_count", 0) > 0:
        next_actions.append(
            {
                "window": "0-24h",
                "owner": "Readiness Director",
                "action": "Run a red-gate closure review with each service lead and vendor owner.",
                "expected_outcome": "Blocked gates move to AMBER or GREEN with updated evidence refs.",
                "trace_refs": _trace_refs(readiness.get("top_blockers", []), "service", "gate"),
            }
        )
    if incidents.get("open_sev1_2", 0) > 0:
        next_actions.append(
            {
                "window": "0-24h",
                "owner": "IT Operations Lead",
                "action": "Hold a focused incident war-room and confirm RCA plus prevention actions for all open Sev-1/2 incidents.",
                "expected_outcome": "Critical incidents are resolved or backed by an accepted mitigation plan.",
                "trace_refs": _trace_refs(incidents.get("open_top", []), "incident_id", "source_id"),
            }
        )
    if evidence.get("missing_count", 0) > 0:
        next_actions.append(
            {
                "window": "0-24h",
                "owner": "Evidence Pack Coordinator",
                "action": "Issue a same-day document chase list and escalate overdue approvals.",
                "expected_outcome": "Missing document refs and approvals are reduced before the next ORR checkpoint.",
                "trace_refs": _trace_refs(evidence.get("missing_top", []), "evidence_id", "doc_ref"),
            }
        )
    next_actions.extend(
        [
            {
                "window": "2-7d",
                "owner": "Operations Director",
                "action": "Re-run a peak rehearsal covering ticketing, access control, OT alarms, and fallback procedures.",
                "expected_outcome": "Cross-domain dependencies are validated under realistic load.",
                "trace_refs": [],
            },
            {
                "window": "2-7d",
                "owner": "Vendor Manager",
                "action": "Review vendor scorecards with partners and lock remediation dates for any SLA drift.",
                "expected_outcome": "Penalty-risk vendors have a dated recovery plan and standby model.",
                "trace_refs": _trace_refs(vendors.get("breach_vendors", []), "vendor", "dashboard_ref"),
            },
        ]
    )
    response["next_actions"] = next_actions

    incident_improvements = [
        {
            "title": "Tighten incident acknowledgement discipline",
            "status": "WARN" if incidents.get("mtta_min") and incidents.get("mtta_min", 0) > 15 else "OK",
            "detail": (
                f"Current MTTA is {incidents.get('mtta_min', 0):.0f} min. "
                "Use alert-routing checks and shift handover validation."
                if incidents.get("mtta_min") is not None
                else "MTTA is unavailable; validate incident timestamp quality."
            ),
            "metric": "MTTA",
        },
        {
            "title": "Stabilize closure quality",
            "status": "WARN" if incidents.get("mttr_min") and incidents.get("mttr_min", 0) > 120 else "OK",
            "detail": (
                f"Current MTTR is {incidents.get('mttr_min', 0):.0f} min. "
                "Confirm runbooks, escalation paths, and supplier standby coverage."
                if incidents.get("mttr_min") is not None
                else "MTTR is unavailable; resolve missing resolution timestamps."
            ),
            "metric": "MTTR",
        },
    ]
    response["incident_improvements"] = incident_improvements

    vendor_flags = []
    for record in vendors.get("breach_vendors", [])[:4]:
        vendor_flags.append(
            {
                "vendor": str(record.get("vendor", "Vendor")),
                "status": "CRIT" if str(record.get("penalty_risk", "")).lower() == "high" else "WARN",
                "detail": f"{record.get('service', 'Service')} shows {record.get('breach_count', 0)} breach signal(s).",
                "trace_refs": _trace_refs([record], "dashboard_ref", "source_system"),
            }
        )
    if not vendor_flags:
        vendor_flags.append(
            {
                "vendor": "Portfolio view",
                "status": "OK",
                "detail": "No vendor scorecard breaches are currently above tolerance.",
                "trace_refs": [],
            }
        )
    response["vendor_flags"] = vendor_flags

    ot_signals = []
    if ot.get("unacked_sev1", 0) > 0:
        ot_signals.append(
            {
                "signal": "Critical OT alarms remain unacknowledged",
                "status": "CRIT",
                "detail": f"{ot.get('unacked_sev1', 0)} Sev-1 alarm(s) require immediate control-room action.",
                "trace_refs": _trace_refs(ot.get("top_open_events", []), "ot_event_id", "device_id"),
            }
        )
    if ot.get("unacked_sev2", 0) > 0:
        ot_signals.append(
            {
                "signal": "Elevated Sev-2 OT backlog",
                "status": "WARN",
                "detail": f"{ot.get('unacked_sev2', 0)} Sev-2 alarm(s) are still unacknowledged.",
                "trace_refs": _trace_refs(ot.get("top_open_events", []), "ot_event_id", "linked_incident_id"),
            }
        )
    if ot.get("clusters"):
        top_cluster = ot["clusters"][0]
        ot_signals.append(
            {
                "signal": "OT alarm clustering detected",
                "status": "WARN",
                "detail": f"{top_cluster.get('zone', 'Zone')} / {top_cluster.get('subsystem', 'Subsystem')} is the current hotspot.",
                "trace_refs": [f"cluster:{top_cluster.get('zone', 'Zone')}/{top_cluster.get('subsystem', 'Subsystem')}"],
            }
        )
    if not ot_signals:
        ot_signals.append(
            {
                "signal": "OT feed is stable",
                "status": "OK",
                "detail": "No critical OT alarm condition is currently above threshold.",
                "trace_refs": [],
            }
        )
    response["ot_signals"] = ot_signals

    ticketing_signals = []
    if ticketing.get("anomaly_windows", 0) > 0:
        ticketing_signals.append(
            {
                "signal": "Ticketing anomaly windows detected",
                "status": "CRIT" if ticketing.get("min_success_rate", 1.0) < THRESHOLDS["ticketing_scan_success_rate_crit"] else "WARN",
                "detail": (
                    f"Minimum scan success is {ticketing.get('min_success_rate', 1.0):.1%}; "
                    f"peak latency reached {ticketing.get('max_latency_p95', 0):.0f} ms."
                ),
                "trace_refs": _trace_refs(ticketing.get("worst_areas", []), "venue_area"),
            }
        )
    if ticketing.get("throughput_collapses", 0) > 0:
        ticketing_signals.append(
            {
                "signal": "Throughput collapse windows recorded",
                "status": "WARN",
                "detail": f"{ticketing.get('throughput_collapses', 0)} time window(s) dropped below throughput tolerance.",
                "trace_refs": [],
            }
        )
    if ticketing.get("payment_dependency_windows", 0) > 0:
        ticketing_signals.append(
            {
                "signal": "Payment dependency flagged in guest-entry flow",
                "status": "WARN",
                "detail": f"{ticketing.get('payment_dependency_windows', 0)} time window(s) show payment-side dependency risk.",
                "trace_refs": [],
            }
        )
    if not ticketing_signals:
        ticketing_signals.append(
            {
                "signal": "Ticketing feed is within tolerance",
                "status": "OK",
                "detail": "Scan success, latency, and throughput remain inside the configured bounds.",
                "trace_refs": [],
            }
        )
    response["ticketing_signals"] = ticketing_signals

    return response
