from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.data import ensure_data_and_load
from src.metrics import vendor_scorecard, vendor_summary
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

configure_page("Vendor scorecards")
render_page_header(
    "Vendor scorecards",
    "Compare contracted availability, response metrics, and penalty exposure so the panel can see partner accountability clearly.",
)

try:
    data = ensure_data_and_load()
except Exception as exc:
    st.error(f"Data load failed: {exc}")
    st.stop()

vendors = data.vendors.copy()

col1, col2, col3 = st.columns(3)
with col1:
    vendor = st.selectbox("Vendor", ["All"] + sorted(vendors["vendor"].dropna().unique().tolist()))
with col2:
    service = st.selectbox("Service", ["All"] + sorted(vendors["service"].dropna().unique().tolist()))
with col3:
    penalty_risk = st.selectbox("Penalty risk", ["All"] + sorted(vendors["penalty_risk"].dropna().unique().tolist()))

filtered = vendors.copy()
if vendor != "All":
    filtered = filtered[filtered["vendor"] == vendor]
if service != "All":
    filtered = filtered[filtered["service"] == service]
if penalty_risk != "All":
    filtered = filtered[filtered["penalty_risk"] == penalty_risk]

summary = vendor_summary(filtered)
scorecard = vendor_scorecard(filtered)
render_status_badges(
    [
        {"label": "Breach signals", "status": "CRIT" if summary["high_penalty_risk"] else "WARN" if summary["breach_count"] else "OK"},
        {"label": "Service credits", "status": "WARN" if summary["service_credits"] else "OK"},
    ]
)
render_kpi_cards(
    [
        {
            "title": "Filtered vendors",
            "value": len(filtered),
            "subtitle": "Partner rows currently in scope.",
            "status": "OK",
        },
        {
            "title": "Breach signals",
            "value": summary["breach_count"],
            "subtitle": "Availability, MTTA, or MTTR out of threshold.",
            "status": "CRIT" if summary["high_penalty_risk"] else "WARN" if summary["breach_count"] else "OK",
        },
        {
            "title": "High penalty risk",
            "value": summary["high_penalty_risk"],
            "subtitle": "High-risk partners should be named explicitly in the walkthrough.",
            "status": "CRIT" if summary["high_penalty_risk"] else "OK",
        },
        {
            "title": "Service credits",
            "value": summary["service_credits"],
            "subtitle": "Commercial recovery indicator from the synthetic scorecard.",
            "status": "WARN" if summary["service_credits"] else "OK",
        },
    ]
)

left, right = st.columns(2)
with left:
    render_section_header("Availability vs contract", "Keep this chart visible while you explain the strongest and weakest partner positions.")
    chart = px.scatter(
        filtered,
        x="contract_sla",
        y="availability_actual",
        color="penalty_risk",
        hover_data=["vendor", "service", "dashboard_ref", "source_system"],
        color_discrete_map={"Low": "#1F7A4D", "Med": "#B76A16", "High": "#B43C2F"},
        title="Actual availability versus contract",
    )
    style_plotly(chart, height=360)
    st.plotly_chart(chart, use_container_width=True)

with right:
    render_section_header("MTTA vs MTTR", "This gives the panel a fast sense of response discipline and restoration discipline.")
    chart = px.scatter(
        filtered,
        x="mtta_actual_min",
        y="mttr_actual_min",
        color="penalty_risk",
        hover_data=["vendor", "service", "dashboard_ref"],
        color_discrete_map={"Low": "#1F7A4D", "Med": "#B76A16", "High": "#B43C2F"},
        title="Response and restoration performance",
    )
    style_plotly(chart, height=360)
    st.plotly_chart(chart, use_container_width=True)

render_section_header("Vendor register", "Dashboard references and source labels show exactly where each scorecard is coming from.")
display_columns = [
    "vendor",
    "service",
    "availability_actual",
    "contract_sla",
    "mtta_target_min",
    "mtta_actual_min",
    "mttr_target_min",
    "mttr_actual_min",
    "open_critical",
    "penalty_risk",
    "service_credit_applicable",
    "dashboard_ref",
    "source_system",
]
st.dataframe(
    format_table(scorecard[display_columns + ["breach_count"]].sort_values(["breach_count", "penalty_risk"], ascending=[False, False])),
    use_container_width=True,
    hide_index=True,
)

render_download_buttons(
    [
        {
            "label": "Download vendor CSV",
            "data": filtered.to_csv(index=False).encode("utf-8"),
            "file_name": "vendors_filtered.csv",
            "mime": "text/csv",
        }
    ]
)

render_lineage_panel(
    filtered,
    title="Data lineage",
    trace_fields=["dashboard_ref", "vendor", "service"],
)
