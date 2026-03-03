from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.data import ensure_data_and_load
from src.metrics import evidence_summary, incident_summary, ot_event_summary, readiness_score, readiness_summary, ticketing_kpi_summary, vendor_summary
from src.ui import (
    configure_page,
    format_table,
    render_kpi_cards,
    render_lineage_panel,
    render_page_header,
    render_section_header,
    render_status_badges,
    style_plotly,
)

configure_page("Overview")
render_page_header(
    "Overview",
    "Start here for the executive posture: ORR gates, evidence readiness, operational stability, and guest-entry signal health in one place.",
)

try:
    data = ensure_data_and_load()
except Exception as exc:
    st.error(f"Data load failed: {exc}")
    st.stop()

readiness = readiness_summary(data.readiness)
evidence = evidence_summary(data.evidence)
incidents = incident_summary(data.incidents)
vendors = vendor_summary(data.vendors)
ot = ot_event_summary(data.ot_events)
ticketing = ticketing_kpi_summary(data.ticketing_kpis)

render_status_badges(
    [
        {"label": "Readiness", "status": "CRIT" if readiness["red_gate_count"] else "WARN" if readiness["amber_gate_count"] else "OK"},
        {"label": "Incidents", "status": "CRIT" if incidents["open_sev1_2"] else "WARN" if incidents["open_count"] else "OK"},
        {"label": "OT", "status": "CRIT" if ot["unacked_sev1"] else "WARN" if ot["unacked_sev2"] else "OK"},
        {
            "label": "Ticketing",
            "status": "CRIT" if ticketing["min_success_rate"] is not None and ticketing["min_success_rate"] < 0.94 else "WARN" if ticketing["anomaly_windows"] else "OK",
        },
    ]
)

render_section_header("Executive KPIs", "Use these cards to frame the Go/No-Go conversation in the first 20 seconds.")
render_kpi_cards(
    [
        {
            "title": "RED gates",
            "value": readiness["red_gate_count"],
            "subtitle": f"AMBER gates: {readiness['amber_gate_count']}",
            "status": "CRIT" if readiness["red_gate_count"] else "WARN" if readiness["amber_gate_count"] else "OK",
        },
        {
            "title": "Evidence completion",
            "value": f"{evidence['completion_rate']:.0%}",
            "subtitle": f"Missing items: {evidence['missing_count']}",
            "status": "CRIT" if evidence["missing_count"] >= 12 else "WARN" if evidence["missing_count"] else "OK",
        },
        {
            "title": "Open Sev-1/2 incidents",
            "value": incidents["open_sev1_2"],
            "subtitle": f"MTTA: {incidents['mtta_min']:.0f} min" if incidents["mtta_min"] is not None else "MTTA unavailable",
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

left, right = st.columns(2)
with left:
    render_section_header("Service Risk Ranking", "Services are ranked by RED-gate count and average readiness score.")
    ranking = readiness_score(data.readiness)
    if not ranking.empty:
        chart = px.bar(
            ranking.sort_values(["reds", "score"], ascending=[True, False]),
            x="score",
            y="service",
            orientation="h",
            color="reds",
            color_continuous_scale=["#E8D8C2", "#8C5A37"],
            labels={"score": "Average gate score", "service": "Service"},
            title="Readiness risk by service",
        )
        style_plotly(chart, height=360)
        st.plotly_chart(chart, use_container_width=True)

with right:
    render_section_header("Open Incident Distribution", "Severity mix shows where the control room is carrying unresolved operational risk.")
    open_incidents = data.incidents[data.incidents["status"].isin(["OPEN", "MITIGATED"])].copy()
    if open_incidents.empty:
        st.info("No open incidents in the current snapshot.")
    else:
        chart = px.histogram(
            open_incidents,
            x="service",
            color="severity",
            color_discrete_map={1: "#7F1D1D", 2: "#B43C2F", 3: "#B76A16", 4: "#C68C39"},
            title="Open incidents by service",
        )
        style_plotly(chart, height=360)
        st.plotly_chart(chart, use_container_width=True)

bottom_left, bottom_right = st.columns(2)
with bottom_left:
    render_section_header("OT and Ticketing Watchlist", "These are the signals most likely to turn into visible guest impact.")
    st.markdown(
        "\n".join(
            [
                f"- Unacknowledged Sev-1 OT alarms: {ot['unacked_sev1']}",
                f"- Unacknowledged Sev-2 OT alarms: {ot['unacked_sev2']}",
                f"- Ticketing anomaly windows: {ticketing['anomaly_windows']}",
                f"- Ticketing throughput collapses: {ticketing['throughput_collapses']}",
                f"- Offline fallback activations: {ticketing['total_offline_fallbacks']}",
            ]
        )
    )

with bottom_right:
    render_section_header("Open Blockers", "Keep this table visible while you explain why the overall posture is OK, WARN, or CRIT.")
    blockers = data.readiness[data.readiness["status"].isin(["RED", "AMBER"])][
        ["service", "gate", "status", "blocker", "gate_owner", "source_system"]
    ].head(12)
    st.dataframe(format_table(blockers), use_container_width=True, hide_index=True)

render_lineage_panel(
    data.services,
    title="Data lineage",
    trace_fields=["ci_id", "service_id", "vendor"],
)
