from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data import ensure_data_and_load
from src.metrics import (
    access_governance_summary,
    operations_dependency_matrix,
    parking_mobility_summary,
    wfm_roster_summary,
)
from src.system_landscape import THRESHOLDS
from src.ui import (
    configure_page,
    format_percent,
    format_table,
    render_download_buttons,
    render_kpi_cards,
    render_lineage_panel,
    render_page_header,
    render_section_header,
    render_status_badges,
    style_plotly,
)

configure_page("Operations Dependencies", icon=":material/hub:")
render_page_header(
    "Operations Dependencies",
    "Connect readiness blockers with staffing coverage, arrival pressure, and access governance before a Day-One launch call.",
)

try:
    data = ensure_data_and_load()
except Exception as exc:
    st.error(f"Data load failed: {exc}")
    st.stop()

matrix = operations_dependency_matrix(
    data.services,
    data.readiness,
    data.wfm_roster,
    data.parking_mobility,
    data.access_governance,
)
wfm = wfm_roster_summary(data.wfm_roster)
parking = parking_mobility_summary(data.parking_mobility)
access = access_governance_summary(data.access_governance)

owner_team_options = ["All"] + sorted(matrix["owner_team"].dropna().unique().tolist())
status_options = ["All", "CRIT", "WARN", "OK"]
col1, col2 = st.columns(2)
with col1:
    owner_team = st.selectbox("Owner team", owner_team_options)
with col2:
    status_filter = st.selectbox("Dependency status", status_options)

filtered_matrix = matrix.copy()
if owner_team != "All":
    filtered_matrix = filtered_matrix[filtered_matrix["owner_team"] == owner_team]
if status_filter != "All":
    filtered_matrix = filtered_matrix[filtered_matrix["overall_status"] == status_filter]

if filtered_matrix.empty:
    st.info("No services match the current filter combination.")
    st.stop()

filtered_services = filtered_matrix["service"].dropna().tolist()
filtered_wfm = data.wfm_roster[data.wfm_roster["service"].isin(filtered_services)].copy()
filtered_access = data.access_governance[data.access_governance["service"].isin(filtered_services)].copy()
filtered_parking = data.parking_mobility.copy()

staffing_status = (
    "CRIT"
    if wfm["critical_shift_gaps"] > 0 or (wfm["overall_fill_rate"] is not None and wfm["overall_fill_rate"] < THRESHOLDS["wfm_fill_rate_crit"])
    else "WARN"
    if wfm["backfill_required"] > 0 or (wfm["overall_fill_rate"] is not None and wfm["overall_fill_rate"] < THRESHOLDS["wfm_fill_rate_warn"])
    else "OK"
)
arrival_status = (
    "CRIT"
    if (
        parking["max_occupancy_pct"] is not None
        and parking["max_occupancy_pct"] >= THRESHOLDS["parking_occupancy_crit"]
    )
    or (
        parking["max_queue_minutes"] is not None
        and parking["max_queue_minutes"] >= THRESHOLDS["parking_queue_crit_min"]
    )
    else "WARN"
    if parking["congestion_windows"] > 0
    else "OK"
)
access_status = (
    "CRIT"
    if access["pending_privileged_approvals"] >= THRESHOLDS["iam_pending_privileged_crit"] or access["privileged_exceptions"] > 0
    else "WARN"
    if access["pending_approvals_total"] > 0 or access["low_mfa_roles"] > 0
    else "OK"
)

render_status_badges(
    [
        {
            "label": "Readiness-linked services",
            "status": "CRIT" if int(filtered_matrix["red_gates"].sum()) else "WARN" if int(filtered_matrix["amber_gates"].sum()) else "OK",
        },
        {"label": "Staffing coverage", "status": staffing_status},
        {"label": "Arrival pressure", "status": arrival_status},
        {"label": "Access governance", "status": access_status},
    ]
)

render_section_header("Executive dependency posture", "Use this page to explain why launch readiness depends on more than ORR gate color alone.")
render_kpi_cards(
    [
        {
            "title": "Services on HOLD",
            "value": int(filtered_matrix["hold_flag"].astype(bool).sum()),
            "subtitle": f"RED gates across selection: {int(filtered_matrix['red_gates'].sum())}",
            "status": "CRIT" if int(filtered_matrix["hold_flag"].astype(bool).sum()) else "OK",
        },
        {
            "title": "Critical shift gaps",
            "value": int(filtered_matrix["critical_shift_gaps"].sum()),
            "subtitle": f"Staffing fill rate: {format_percent(filtered_matrix['staffing_fill_rate'].mean(), digits=1, assume_ratio=True)}",
            "status": staffing_status,
        },
        {
            "title": "Arrival congestion windows",
            "value": parking["congestion_windows"],
            "subtitle": f"Peak queue: {parking['max_queue_minutes']:.0f} min" if parking["max_queue_minutes"] is not None else "Peak queue unavailable",
            "status": arrival_status,
        },
        {
            "title": "Privileged access exceptions",
            "value": access["privileged_exceptions"],
            "subtitle": f"Pending privileged approvals: {access['pending_privileged_approvals']}",
            "status": access_status,
        },
    ]
)

left, right = st.columns(2)
with left:
    render_section_header("Service dependency ranking", "This is the fastest way to show which services need coordinated action across readiness, staffing, arrival, and access.")
    chart = px.bar(
        filtered_matrix.head(8),
        x="dependency_score",
        y="service",
        orientation="h",
        color="overall_status",
        color_discrete_map={"OK": "#1F7A4D", "WARN": "#B76A16", "CRIT": "#B43C2F"},
        hover_data=["owner_team", "red_gates", "critical_shift_gaps", "pending_access_approvals", "arrival_hotspot"],
        title="Dependency score by service",
    )
    style_plotly(chart, height=380)
    st.plotly_chart(chart, use_container_width=True)

with right:
    render_section_header("Arrival pressure trend", "Arrival stress is shown independently because it can break guest experience even when IT signals still look green.")
    recent_parking = filtered_parking[filtered_parking["ts"] >= filtered_parking["ts"].max() - pd.Timedelta(hours=12)] if "ts" in filtered_parking.columns else filtered_parking
    chart = px.line(
        recent_parking,
        x="ts",
        y="queue_minutes",
        color="venue_area",
        title="Arrival queue minutes by venue area",
    )
    chart.add_hline(y=THRESHOLDS["parking_queue_warn_min"], line_dash="dot", line_color="#B76A16")
    chart.add_hline(y=THRESHOLDS["parking_queue_crit_min"], line_dash="dot", line_color="#B43C2F")
    style_plotly(chart, height=380)
    st.plotly_chart(chart, use_container_width=True)

bottom_left, bottom_right = st.columns(2)
with bottom_left:
    render_section_header("Staffing gap register", "Critical-role undercoverage and training gaps should be treated as Go/No-Go dependencies.")
    staffing_watch = filtered_wfm[
        (filtered_wfm["critical_role_flag"].fillna(False))
        & (
            (filtered_wfm["checked_in_headcount"] < filtered_wfm["required_headcount"])
            | (filtered_wfm["training_compliance_rate"] < THRESHOLDS["wfm_training_warn"])
        )
    ][
        [
            "shift_id",
            "roster_ref",
            "service",
            "role_name",
            "zone",
            "shift_start",
            "required_headcount",
            "checked_in_headcount",
            "training_compliance_rate",
            "source_system",
        ]
    ].sort_values("shift_start")
    st.dataframe(format_table(staffing_watch), use_container_width=True, hide_index=True)

with bottom_right:
    render_section_header("Access exception register", "This view ties launch risk to privileged access readiness, overdue certifications, and MFA coverage.")
    access_watch = filtered_access[
        (
            filtered_access["pending_approvals"] > 0
        )
        | (
            filtered_access["stale_accounts"] > 0
        )
        | (
            filtered_access["mfa_coverage_rate"] < THRESHOLDS["iam_mfa_warn"]
        )
        | filtered_access["segregation_of_duties_flag"].fillna(False)
    ][
        [
            "access_review_id",
            "application_ref",
            "service",
            "application_name",
            "role_name",
            "pending_approvals",
            "stale_accounts",
            "mfa_coverage_rate",
            "next_review_due",
            "source_system",
        ]
    ].sort_values(["pending_approvals", "stale_accounts"], ascending=False)
    st.dataframe(format_table(access_watch), use_container_width=True, hide_index=True)

render_section_header("Cross-domain watchlist", "Each row blends readiness posture with staffing, arrival exposure, and access-governance readiness.")
watch_columns = [
    "service",
    "owner_team",
    "primary_system",
    "red_gates",
    "hold_flag",
    "critical_shift_gaps",
    "staffing_fill_rate",
    "pending_access_approvals",
    "low_mfa_roles",
    "arrival_dependency_status",
    "arrival_hotspot",
    "overall_status",
]
watchlist = filtered_matrix[watch_columns].copy()
watchlist["staffing_fill_rate"] = watchlist["staffing_fill_rate"].map(lambda value: format_percent(value, digits=1, assume_ratio=True))
st.dataframe(watchlist, use_container_width=True, hide_index=True)

render_download_buttons(
    [
        {
            "label": "Download dependency matrix",
            "data": filtered_matrix.to_csv(index=False).encode("utf-8"),
            "file_name": "operations_dependency_matrix.csv",
            "mime": "text/csv",
        }
    ]
)

render_lineage_panel(
    filtered_wfm,
    title="Staffing lineage",
    trace_fields=["shift_id", "roster_ref"],
)
render_lineage_panel(
    filtered_parking,
    title="Arrival lineage",
    trace_fields=["arrival_ref", "dashboard_ref", "linked_incident_id"],
)
render_lineage_panel(
    filtered_access,
    title="Access governance lineage",
    trace_fields=["access_review_id", "application_ref"],
)
