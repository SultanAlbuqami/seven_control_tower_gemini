from __future__ import annotations

import streamlit as st

from src.data import ensure_data_and_load
from src.metrics import evidence_summary
from src.ui import (
    configure_page,
    format_table,
    render_download_buttons,
    render_kpi_cards,
    render_lineage_panel,
    render_page_header,
    render_section_header,
    render_status_badges,
)

configure_page("Evidence pack")
render_page_header(
    "Evidence pack",
    "Track document readiness, approval status, and traceable proof for every ORR gate before the final Go/No-Go forum.",
)

try:
    data = ensure_data_and_load()
except Exception as exc:
    st.error(f"Data load failed: {exc}")
    st.stop()

evidence = data.evidence.copy()
summary = evidence_summary(evidence)

col1, col2, col3, col4 = st.columns(4)
with col1:
    service = st.selectbox("Service", ["All"] + sorted(evidence["service"].dropna().unique().tolist()))
with col2:
    gate = st.selectbox("Gate", ["All"] + sorted(evidence["gate"].dropna().unique().tolist()))
with col3:
    status = st.selectbox("Status", ["All"] + sorted(evidence["status"].dropna().unique().tolist()))
with col4:
    approval = st.selectbox("Approval status", ["All"] + sorted(evidence["approval_status"].dropna().unique().tolist()))

filtered = evidence.copy()
if service != "All":
    filtered = filtered[filtered["service"] == service]
if gate != "All":
    filtered = filtered[filtered["gate"] == gate]
if status != "All":
    filtered = filtered[filtered["status"] == status]
if approval != "All":
    filtered = filtered[filtered["approval_status"] == approval]

filtered_summary = evidence_summary(filtered)
render_status_badges(
    [
        {"label": "Completion", "status": "CRIT" if filtered_summary["completion_rate"] < 0.80 else "WARN" if filtered_summary["completion_rate"] < 0.92 else "OK"},
        {"label": "Missing items", "status": "CRIT" if filtered_summary["missing_count"] >= 12 else "WARN" if filtered_summary["missing_count"] else "OK"},
    ]
)
render_kpi_cards(
    [
        {
            "title": "Filtered items",
            "value": len(filtered),
            "subtitle": "Evidence records after the current filters.",
            "status": "OK",
        },
        {
            "title": "Completion rate",
            "value": f"{filtered_summary['completion_rate']:.0%}",
            "subtitle": "The pack should be 90%+ before the final executive review.",
            "status": "CRIT" if filtered_summary["completion_rate"] < 0.80 else "WARN" if filtered_summary["completion_rate"] < 0.92 else "OK",
        },
        {
            "title": "Missing items",
            "value": filtered_summary["missing_count"],
            "subtitle": "Missing records are the fastest way to lose confidence in sign-off.",
            "status": "CRIT" if filtered_summary["missing_count"] >= 12 else "WARN" if filtered_summary["missing_count"] else "OK",
        },
        {
            "title": "Total portfolio missing",
            "value": summary["missing_count"],
            "subtitle": "Use this as the cross-check when asked for the overall chase list.",
            "status": "WARN" if summary["missing_count"] else "OK",
        },
    ]
)

render_section_header("Missing-evidence chase list", "Filter to MISSING when you need a clean action register with owners and document refs.")
display_columns = [
    "evidence_id",
    "service",
    "gate",
    "evidence_type",
    "evidence_class",
    "owner",
    "approval_status",
    "approver_role",
    "doc_ref",
    "punch_list_id",
    "updated_at",
    "source_system",
    "note",
]
st.dataframe(
    format_table(
        filtered.sort_values(["status", "service", "gate", "updated_at"], ascending=[True, True, True, False])[display_columns]
    ),
    use_container_width=True,
    hide_index=True,
)

render_download_buttons(
    [
        {
            "label": "Download evidence CSV",
            "data": filtered.to_csv(index=False).encode("utf-8"),
            "file_name": "evidence_filtered.csv",
            "mime": "text/csv",
        }
    ]
)

render_lineage_panel(
    filtered,
    title="Data lineage",
    trace_fields=["evidence_id", "doc_ref", "punch_list_id"],
)
