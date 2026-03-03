from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

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
scorecard["availability_gap"] = scorecard["availability_actual"] - scorecard["contract_sla"]
scorecard["mtta_gap_min"] = scorecard["mtta_actual_min"] - scorecard["mtta_target_min"]
scorecard["mttr_gap_min"] = scorecard["mttr_actual_min"] - scorecard["mttr_target_min"]
scorecard["partner_label"] = scorecard["vendor"] + " | " + scorecard["service"]
color_map = {"Low": "#1F7A4D", "Med": "#B76A16", "High": "#B43C2F"}
scorecard["risk_color"] = scorecard["penalty_risk"].map(color_map).fillna("#2F6F6C")

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

ranked_availability = scorecard.sort_values(
    ["availability_gap", "breach_count", "vendor"],
    ascending=[True, False, True],
)
ranked_response = scorecard.sort_values(
    ["breach_count", "mtta_gap_min", "mttr_gap_min", "vendor"],
    ascending=[False, False, False, True],
)

left, right = st.columns(2)
with left:
    render_section_header(
        "Availability vs contract",
        "This is the executive view: each bar is actual availability and the marker shows the contract target.",
    )
    availability_chart = go.Figure()
    availability_chart.add_bar(
        x=ranked_availability["availability_actual"],
        y=ranked_availability["partner_label"],
        orientation="h",
        name="Actual availability",
        marker_color=ranked_availability["risk_color"],
        customdata=ranked_availability[["vendor", "service", "contract_sla", "availability_gap", "dashboard_ref", "source_system"]],
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Service: %{customdata[1]}<br>"
            "Actual: %{x:.2f}%<br>"
            "Contract: %{customdata[2]:.2f}%<br>"
            "Gap: %{customdata[3]:+.2f} pts<br>"
            "Dashboard: %{customdata[4]}<br>"
            "Source: %{customdata[5]}<extra></extra>"
        ),
    )
    availability_chart.add_scatter(
        x=ranked_availability["contract_sla"],
        y=ranked_availability["partner_label"],
        mode="markers",
        name="Contract target",
        marker=dict(color="#1E252F", size=13, symbol="line-ns-open"),
        hovertemplate="Contract target: %{x:.2f}%<extra></extra>",
    )
    style_plotly(availability_chart, height=430)
    availability_chart.update_layout(title="Availability target versus actual", barmode="overlay")
    availability_chart.update_xaxes(title="Availability %", ticksuffix="%")
    availability_chart.update_yaxes(title=None, categoryorder="array", categoryarray=ranked_availability["partner_label"].tolist())
    st.plotly_chart(availability_chart, use_container_width=True)

with right:
    render_section_header(
        "MTTA and MTTR vs targets",
        "Target markers show the contract discipline. Bars show the actual response and restoration load carried today.",
    )
    response_chart = make_subplots(
        rows=1,
        cols=2,
        shared_yaxes=True,
        horizontal_spacing=0.16,
        subplot_titles=("MTTA", "MTTR"),
    )
    for column_index, actual_col, target_col, title in [
        (1, "mtta_actual_min", "mtta_target_min", "MTTA"),
        (2, "mttr_actual_min", "mttr_target_min", "MTTR"),
    ]:
        response_chart.add_bar(
            x=ranked_response[actual_col],
            y=ranked_response["partner_label"],
            orientation="h",
            marker_color=ranked_response["risk_color"],
            name="Actual",
            legendgroup="actual",
            showlegend=column_index == 1,
            customdata=ranked_response[["vendor", "service", target_col, "dashboard_ref"]],
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Service: %{customdata[1]}<br>"
                f"{title} actual: %{{x:.0f}} min<br>"
                f"{title} target: %{{customdata[2]:.0f}} min<br>"
                "Dashboard: %{customdata[3]}<extra></extra>"
            ),
            row=1,
            col=column_index,
        )
        response_chart.add_scatter(
            x=ranked_response[target_col],
            y=ranked_response["partner_label"],
            mode="markers",
            marker=dict(color="#1E252F", size=12, symbol="line-ns-open"),
            name="Target",
            legendgroup="target",
            showlegend=column_index == 1,
            hovertemplate=f"{title} target: %{{x:.0f}} min<extra></extra>",
            row=1,
            col=column_index,
        )
    style_plotly(response_chart, height=430)
    response_chart.update_layout(title="Response discipline against contract targets")
    response_chart.update_xaxes(title="Minutes", row=1, col=1)
    response_chart.update_xaxes(title="Minutes", row=1, col=2)
    response_chart.update_yaxes(title=None, categoryorder="array", categoryarray=ranked_response["partner_label"].tolist(), row=1, col=1)
    response_chart.update_yaxes(title=None, categoryorder="array", categoryarray=ranked_response["partner_label"].tolist(), row=1, col=2)
    st.plotly_chart(response_chart, use_container_width=True)

with st.expander("Analytic view", expanded=False):
    st.caption("Scatter plots remain available when you want to discuss relationships rather than exceptions.")
    tab1, tab2 = st.tabs(["Availability relationship", "Response relationship"])
    with tab1:
        chart = px.scatter(
            filtered,
            x="contract_sla",
            y="availability_actual",
            color="penalty_risk",
            hover_data=["vendor", "service", "dashboard_ref", "source_system"],
            color_discrete_map=color_map,
            title="Actual availability versus contract",
        )
        style_plotly(chart, height=360)
        st.plotly_chart(chart, use_container_width=True)
    with tab2:
        chart = px.scatter(
            filtered,
            x="mtta_actual_min",
            y="mttr_actual_min",
            color="penalty_risk",
            hover_data=["vendor", "service", "dashboard_ref"],
            color_discrete_map=color_map,
            title="Response and restoration relationship",
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
    "availability_gap",
    "mtta_gap_min",
    "mttr_gap_min",
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
