from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.data import ensure_data_and_load
from src.metrics import ot_event_summary
from src.system_landscape import THRESHOLDS
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

configure_page("OT Events")
render_page_header(
    "OT Events",
    "Monitor BMS, access-control, CCTV, and fire-alarm events with severity, zone, acknowledgement discipline, and incident linkage.",
)

try:
    data = ensure_data_and_load()
except Exception as exc:
    st.error(f"Data load failed: {exc}")
    st.stop()

events = data.ot_events.copy()

col1, col2, col3, col4 = st.columns(4)
with col1:
    subsystem = st.selectbox("Subsystem", ["All"] + sorted(events["subsystem"].dropna().unique().tolist()))
with col2:
    zone = st.selectbox("Zone", ["All"] + sorted(events["zone"].dropna().unique().tolist()))
with col3:
    severity = st.selectbox("Severity", ["All", 1, 2, 3, 4])
with col4:
    unacked_only = st.toggle("Unacknowledged only", value=False)

filtered = events.copy()
if subsystem != "All":
    filtered = filtered[filtered["subsystem"] == subsystem]
if zone != "All":
    filtered = filtered[filtered["zone"] == zone]
if severity != "All":
    filtered = filtered[filtered["severity"] == severity]
if unacked_only:
    filtered = filtered[filtered["ack_time"].isna()]

summary = ot_event_summary(filtered)
render_status_badges(
    [
        {"label": "Sev-1 backlog", "status": "CRIT" if summary["unacked_sev1"] > THRESHOLDS["ot_unacked_sev1_warn"] else "OK"},
        {"label": "Sev-2 backlog", "status": "WARN" if summary["unacked_sev2"] > THRESHOLDS["ot_unacked_sev2_warn"] else "OK"},
        {"label": "Open OT load", "status": "WARN" if summary["total_open"] >= 14 else "OK"},
    ]
)
render_kpi_cards(
    [
        {
            "title": "Unacknowledged Sev-1",
            "value": summary["unacked_sev1"],
            "subtitle": "Any non-zero value should be treated as an interview talking point.",
            "status": "CRIT" if summary["unacked_sev1"] else "OK",
        },
        {
            "title": "Unacknowledged Sev-2",
            "value": summary["unacked_sev2"],
            "subtitle": "Sev-2 backlog indicates response discipline drift.",
            "status": "WARN" if summary["unacked_sev2"] else "OK",
        },
        {
            "title": "Open OT events",
            "value": summary["total_open"],
            "subtitle": "Open means not yet cleared in the synthetic alarm feed.",
            "status": "WARN" if summary["total_open"] >= 14 else "OK",
        },
        {
            "title": "Mean ack time",
            "value": f"{summary['mean_ack_min']:.0f} min" if summary["mean_ack_min"] is not None else "-",
            "subtitle": "This is the control-room response discipline metric.",
            "status": "WARN" if summary["mean_ack_min"] is not None and summary["mean_ack_min"] > 15 else "OK",
        },
    ]
)

left, right = st.columns(2)
with left:
    render_section_header("Event volume by subsystem", "Use this to show whether the issue is facilities, access, security, or fire-related.")
    chart = px.histogram(
        filtered,
        x="subsystem",
        color="severity",
        color_discrete_map={1: "#7F1D1D", 2: "#B43C2F", 3: "#B76A16", 4: "#C68C39"},
        title="OT events by subsystem",
    )
    style_plotly(chart, height=360)
    st.plotly_chart(chart, use_container_width=True)

with right:
    render_section_header("Zone heat", "Alarm clustering is more compelling than a flat list when you present the OT story.")
    chart = px.histogram(
        filtered,
        x="zone",
        color="severity",
        color_discrete_map={1: "#7F1D1D", 2: "#B43C2F", 3: "#B76A16", 4: "#C68C39"},
        title="OT events by zone",
    )
    style_plotly(chart, height=360)
    st.plotly_chart(chart, use_container_width=True)

render_section_header("Alarm timeline", "Linked incident IDs make it clear when OT alarms have already crossed into formal incident handling.")
timeline = px.scatter(
    filtered.sort_values("event_time"),
    x="event_time",
    y="zone",
    color="severity",
    symbol="subsystem",
    hover_data=["ot_event_id", "alarm_type", "device_id", "linked_incident_id"],
    color_discrete_map={1: "#7F1D1D", 2: "#B43C2F", 3: "#B76A16", 4: "#C68C39"},
    title="OT event timeline",
)
style_plotly(timeline, height=380)
st.plotly_chart(timeline, use_container_width=True)

render_section_header("OT alarm register", "Use this table when the panel asks how you would chase one of the alarms down to a device or incident.")
display_columns = [
    "ot_event_id",
    "source_system",
    "subsystem",
    "alarm_type",
    "zone",
    "device_id",
    "severity",
    "event_time",
    "ack_time",
    "cleared_time",
    "acked_by_role",
    "linked_incident_id",
]
st.dataframe(
    format_table(filtered[display_columns].sort_values("event_time", ascending=False)),
    use_container_width=True,
    hide_index=True,
)

render_download_buttons(
    [
        {
            "label": "Download OT events CSV",
            "data": filtered.to_csv(index=False).encode("utf-8"),
            "file_name": "ot_events_filtered.csv",
            "mime": "text/csv",
        }
    ]
)

render_lineage_panel(
    filtered,
    title="Data lineage",
    trace_fields=["ot_event_id", "device_id", "linked_incident_id"],
)
