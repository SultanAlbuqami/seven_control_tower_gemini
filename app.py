from __future__ import annotations

import streamlit as st

from src.data import ensure_data_and_load
from src.metrics import evidence_summary, incident_summary, ot_event_summary, readiness_summary, ticketing_kpi_summary, vendor_summary
from src.seed import generate
from src.ui import (
    configure_page,
    render_kpi_cards,
    render_page_header,
    render_section_header,
    render_status_badges,
)

configure_page("Control Tower Home", icon=":material/apartment:")
render_page_header(
    "Control Tower Home",
    "Launch the demo with meaningful data immediately, inspect the operating posture, and move into the deeper pages from the sidebar.",
)

try:
    data = ensure_data_and_load()
except Exception as exc:
    st.error(f"Auto-seed failed and the demo data could not be loaded: {exc}")
    st.stop()

readiness = readiness_summary(data.readiness)
evidence = evidence_summary(data.evidence)
incidents = incident_summary(data.incidents)
vendors = vendor_summary(data.vendors)
ot = ot_event_summary(data.ot_events)
ticketing = ticketing_kpi_summary(data.ticketing_kpis)

render_status_badges(
    [
        {"label": "Demo Mode", "status": "OK"},
        {"label": "Offline-safe fallback", "status": "OK"},
        {"label": "Readiness posture", "status": "CRIT" if readiness["red_gate_count"] else "WARN" if readiness["amber_gate_count"] else "OK"},
        {"label": "Go/No-Go", "status": "CRIT" if readiness["hold_count"] or incidents["open_sev1_2"] else "OK"},
    ]
)

render_section_header("Executive Snapshot", "The home screen summarizes the full control tower before you move into the supporting views.")
render_kpi_cards(
    [
        {
            "title": "RED gates",
            "value": readiness["red_gate_count"],
            "subtitle": f"AMBER gates: {readiness['amber_gate_count']}",
            "status": "CRIT" if readiness["red_gate_count"] else "WARN" if readiness["amber_gate_count"] else "OK",
        },
        {
            "title": "Missing evidence",
            "value": evidence["missing_count"],
            "subtitle": f"Completion rate: {evidence['completion_rate']:.0%}",
            "status": "CRIT" if evidence["missing_count"] >= 12 else "WARN" if evidence["missing_count"] else "OK",
        },
        {
            "title": "Open Sev-1/2 incidents",
            "value": incidents["open_sev1_2"],
            "subtitle": f"Open incidents total: {incidents['open_count']}",
            "status": "CRIT" if incidents["open_sev1_2"] else "WARN" if incidents["open_count"] else "OK",
        },
        {
            "title": "Vendor breach signals",
            "value": vendors["breach_count"],
            "subtitle": f"High penalty risk: {vendors['high_penalty_risk']}",
            "status": "CRIT" if vendors["high_penalty_risk"] else "WARN" if vendors["breach_count"] else "OK",
        },
    ]
)

left, right = st.columns([1.2, 1.0])
with left:
    render_section_header("Interview Flow", "Use the sidebar pages in this order during the three-minute walkthrough.")
    st.markdown(
        "\n".join(
            [
                "1. Overview: establish the operating posture and threshold for launch.",
                "2. Readiness heatmap: isolate blocked services and gate owners.",
                "3. Evidence pack: call out missing approvals and trace refs.",
                "4. Incidents: review MTTA, MTTR, and SLA discipline.",
                "5. Vendor scorecards: show partner accountability and penalty risk.",
                "6. OT Events and Ticketing KPIs: prove live operational signal coverage.",
                "7. Recommendations: compare the Draft preview with the Final authoritative output.",
            ]
        )
    )

with right:
    render_section_header("Data Coverage", "All pages load immediately from deterministic synthetic data.")
    st.markdown(
        "\n".join(
            [
                f"- Services catalog rows: {len(data.services)}",
                f"- Readiness records: {len(data.readiness)}",
                f"- Evidence records: {len(data.evidence)}",
                f"- Incident records: {len(data.incidents)}",
                f"- OT event records: {len(data.ot_events)}",
                f"- Ticketing KPI rows: {len(data.ticketing_kpis)}",
                f"- Vendor scorecards: {len(data.vendors)}",
            ]
        )
    )

render_section_header("Control Actions", "Regeneration is optional. The app will auto-seed again if any required CSV disappears.")
if st.button("Regenerate data", type="primary"):
    try:
        generate()
        st.success("Deterministic demo data regenerated.")
        st.rerun()
    except Exception as exc:
        st.error(f"Data regeneration failed: {exc}")

render_section_header("Signal Watch", "Use these pages when the panel asks for operational detail.")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Unacknowledged Sev-1 OT alarms", ot["unacked_sev1"])
    st.metric("Ticketing anomaly windows", ticketing["anomaly_windows"])
with col2:
    st.metric("Open OT events", ot["total_open"])
    st.metric("Ticketing min scan success", f"{ticketing['min_success_rate']:.1%}" if ticketing["min_success_rate"] is not None else "-")
with col3:
    st.metric("Incident MTTA", f"{incidents['mtta_min']:.0f} min" if incidents["mtta_min"] is not None else "-")
    st.metric("Incident MTTR", f"{incidents['mttr_min']:.0f} min" if incidents["mttr_min"] is not None else "-")
