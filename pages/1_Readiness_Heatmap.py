from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.data import ensure_data_and_load
from src.metrics import readiness_summary
from src.ui import (
    configure_page,
    format_table,
    readiness_scale,
    render_download_buttons,
    render_kpi_cards,
    render_lineage_panel,
    render_page_header,
    render_section_header,
    render_status_badges,
    style_plotly,
)

configure_page("Readiness heatmap")
render_page_header(
    "Readiness heatmap",
    "Review service-by-gate status, isolate blockers, and show exactly who needs to move each gate back toward sign-off.",
)

try:
    data = ensure_data_and_load()
except Exception as exc:
    st.error(f"Data load failed: {exc}")
    st.stop()

services = data.services.copy()
readiness = data.readiness.copy()

filter_col1, filter_col2, filter_col3 = st.columns(3)
with filter_col1:
    min_criticality = st.selectbox("Minimum criticality", [1, 2, 3], index=1)
with filter_col2:
    owner_team = st.selectbox("Owner team", ["All"] + sorted(services["owner_team"].dropna().unique().tolist()))
with filter_col3:
    vendor = st.selectbox("Vendor", ["All"] + sorted(services["vendor"].dropna().unique().tolist()))

filtered_services = services[services["criticality"] >= min_criticality].copy()
if owner_team != "All":
    filtered_services = filtered_services[filtered_services["owner_team"] == owner_team]
if vendor != "All":
    filtered_services = filtered_services[filtered_services["vendor"] == vendor]

filtered_readiness = readiness[readiness["service"].isin(filtered_services["service"])].copy()
summary = readiness_summary(filtered_readiness)

render_status_badges(
    [
        {"label": "RED gates", "status": "CRIT" if summary["red_gate_count"] else "OK"},
        {"label": "AMBER gates", "status": "WARN" if summary["amber_gate_count"] else "OK"},
        {"label": "Go/No-Go holds", "status": "CRIT" if summary["hold_count"] else "OK"},
    ]
)
render_kpi_cards(
    [
        {
            "title": "Filtered services",
            "value": len(filtered_services),
            "subtitle": "Scope after owner-team and vendor filters.",
            "status": "OK",
        },
        {
            "title": "RED gates",
            "value": summary["red_gate_count"],
            "subtitle": "Any RED gate keeps Go/No-Go on HOLD.",
            "status": "CRIT" if summary["red_gate_count"] else "OK",
        },
        {
            "title": "AMBER gates",
            "value": summary["amber_gate_count"],
            "subtitle": "Watch items that still need proof or closure.",
            "status": "WARN" if summary["amber_gate_count"] else "OK",
        },
        {
            "title": "Go/No-Go holds",
            "value": summary["hold_count"],
            "subtitle": "HOLD count pulled directly from the ORR tracker feed.",
            "status": "CRIT" if summary["hold_count"] else "OK",
        },
    ]
)

render_section_header("Service-by-gate heatmap", "This is the fastest way to explain where launch readiness is blocked.")
status_map = {"RED": 0, "AMBER": 1, "GREEN": 2}
heatmap = filtered_readiness.copy()
heatmap["score"] = heatmap["status"].map(status_map).fillna(1)
pivot = heatmap.pivot(index="service", columns="gate", values="score").fillna(1)

figure = px.imshow(
    pivot,
    aspect="auto",
    labels={"x": "Gate", "y": "Service", "color": "Readiness"},
    color_continuous_scale=readiness_scale(),
    zmin=0,
    zmax=2,
    title="Readiness heatmap",
)
style_plotly(figure, height=420)
st.plotly_chart(figure, use_container_width=True)

render_section_header("Blocker register", "Use this table to name owners, dependencies, and exact source-system lineage.")
display_columns = [
    "service",
    "gate",
    "gate_name",
    "status",
    "blocker",
    "blocking_dependency",
    "gate_owner",
    "go_no_go",
    "last_updated",
    "source_system",
]
st.dataframe(
    format_table(filtered_readiness[display_columns].sort_values(["status", "service", "gate"])),
    use_container_width=True,
    hide_index=True,
)

render_download_buttons(
    [
        {
            "label": "Download readiness CSV",
            "data": filtered_readiness.to_csv(index=False).encode("utf-8"),
            "file_name": "readiness_filtered.csv",
            "mime": "text/csv",
        }
    ]
)

render_lineage_panel(
    filtered_readiness,
    title="Data lineage",
    trace_fields=["gate", "gate_owner", "blocking_dependency"],
)
