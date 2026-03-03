from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.data import ensure_data_and_load
from src.metrics import incident_summary
from src.ui import (
    configure_page,
    format_table,
    render_download_buttons,
    render_kpi_cards,
    render_lineage_panel,
    render_page_header,
    render_section_header,
    render_status_badges,
    style_plotly,
)

configure_page("Incidents")
render_page_header(
    "Incidents",
    "Track MTTA, MTTR, severity discipline, and SLA breach exposure without relying on a live ITSM connection.",
)

try:
    data = ensure_data_and_load()
except Exception as exc:
    st.error(f"Data load failed: {exc}")
    st.stop()

incidents = data.incidents.copy()

filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
with filter_col1:
    service = st.selectbox("Service", ["All"] + sorted(incidents["service"].dropna().unique().tolist()))
with filter_col2:
    severity = st.selectbox("Severity", ["All", 1, 2, 3, 4])
with filter_col3:
    status = st.selectbox("Status", ["All"] + sorted(incidents["status"].dropna().unique().tolist()))
with filter_col4:
    assigned_group = st.selectbox("Assigned group", ["All"] + sorted(incidents["assigned_group"].dropna().unique().tolist()))

filtered = incidents.copy()
if service != "All":
    filtered = filtered[filtered["service"] == service]
if severity != "All":
    filtered = filtered[filtered["severity"] == severity]
if status != "All":
    filtered = filtered[filtered["status"] == status]
if assigned_group != "All":
    filtered = filtered[filtered["assigned_group"] == assigned_group]

summary = incident_summary(filtered)
render_status_badges(
    [
        {"label": "Critical incidents", "status": "CRIT" if summary["open_sev1_2"] else "OK"},
        {"label": "SLA discipline", "status": "CRIT" if summary["sla_breaches"] >= 4 else "WARN" if summary["sla_breaches"] else "OK"},
        {"label": "MTTA", "status": "CRIT" if summary["mtta_min"] is not None and summary["mtta_min"] > 20 else "WARN" if summary["mtta_min"] is not None and summary["mtta_min"] > 15 else "OK"},
    ]
)
render_kpi_cards(
    [
        {
            "title": "Open incidents",
            "value": summary["open_count"],
            "subtitle": "OPEN plus MITIGATED incidents in the current filter set.",
            "status": "WARN" if summary["open_count"] else "OK",
        },
        {
            "title": "Open Sev-1/2",
            "value": summary["open_sev1_2"],
            "subtitle": "These are the incidents to highlight in the interview.",
            "status": "CRIT" if summary["open_sev1_2"] else "OK",
        },
        {
            "title": "MTTA",
            "value": f"{summary['mtta_min']:.0f} min" if summary["mtta_min"] is not None else "-",
            "subtitle": "Acknowledgement time should stay inside the 15-minute narrative.",
            "status": "CRIT" if summary["mtta_min"] is not None and summary["mtta_min"] > 20 else "WARN" if summary["mtta_min"] is not None and summary["mtta_min"] > 15 else "OK",
        },
        {
            "title": "MTTR",
            "value": f"{summary['mttr_min']:.0f} min" if summary["mttr_min"] is not None else "-",
            "subtitle": "Extended resolution time usually signals weak runbooks or escalation drift.",
            "status": "CRIT" if summary["mttr_min"] is not None and summary["mttr_min"] > 180 else "WARN" if summary["mttr_min"] is not None and summary["mttr_min"] > 120 else "OK",
        },
    ]
)

left, right = st.columns(2)
with left:
    render_section_header("Incident volume over time", "Show whether the current posture is noise, drift, or a real launch blocker.")
    chart = px.histogram(
        filtered,
        x="opened_at",
        color="severity",
        color_discrete_map={1: "#7F1D1D", 2: "#B43C2F", 3: "#B76A16", 4: "#C68C39"},
        nbins=20,
        title="Incident intake over time",
    )
    style_plotly(chart, height=360)
    st.plotly_chart(chart, use_container_width=True)

with right:
    render_section_header("Severity by service", "This answers where the control room is currently spending operational attention.")
    chart = px.histogram(
        filtered,
        x="service",
        color="severity",
        color_discrete_map={1: "#7F1D1D", 2: "#B43C2F", 3: "#B76A16", 4: "#C68C39"},
        title="Incident severity mix",
    )
    style_plotly(chart, height=360)
    st.plotly_chart(chart, use_container_width=True)

render_section_header("Incident register", "Use source IDs and assigned groups to show traceability back into the example ITSM layer.")
display_columns = [
    "incident_id",
    "source_id",
    "service",
    "vendor",
    "severity",
    "status",
    "category",
    "impact_scope",
    "sla_breached",
    "assigned_group",
    "opened_at",
    "ack_at",
    "resolved_at",
    "source_system",
    "summary",
]
st.dataframe(
    format_table(filtered[display_columns].sort_values("opened_at", ascending=False)),
    use_container_width=True,
    hide_index=True,
)

render_download_buttons(
    [
        {
            "label": "Download incidents CSV",
            "data": filtered.to_csv(index=False).encode("utf-8"),
            "file_name": "incidents_filtered.csv",
            "mime": "text/csv",
        }
    ]
)

render_lineage_panel(
    filtered,
    title="Data lineage",
    trace_fields=["incident_id", "source_id", "assigned_group"],
)
