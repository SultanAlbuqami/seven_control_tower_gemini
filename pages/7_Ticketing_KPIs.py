from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.data import ensure_data_and_load
from src.metrics import ticketing_kpi_summary
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

configure_page("Ticketing KPIs")
render_page_header(
    "Ticketing KPIs",
    "Track gate scan success, QR latency, throughput, denied entries, and fallback activations using a venue-style time series.",
)

try:
    data = ensure_data_and_load()
except Exception as exc:
    st.error(f"Data load failed: {exc}")
    st.stop()

ticketing = data.ticketing_kpis.copy()

col1, col2 = st.columns(2)
with col1:
    venue_area = st.selectbox("Venue area", ["All"] + sorted(ticketing["venue_area"].dropna().unique().tolist()))
with col2:
    anomaly_only = st.toggle("Show anomaly windows only", value=False)

filtered = ticketing.copy()
if venue_area != "All":
    filtered = filtered[filtered["venue_area"] == venue_area]
if anomaly_only:
    filtered = filtered[
        (filtered["scan_success_rate"] < THRESHOLDS["ticketing_scan_success_rate_warn"])
        | (filtered["qr_validation_latency_ms_p95"] > THRESHOLDS["ticketing_latency_crit_ms"])
    ]

summary = ticketing_kpi_summary(filtered)
render_status_badges(
    [
        {
            "label": "Scan success",
            "status": "CRIT" if summary["min_success_rate"] is not None and summary["min_success_rate"] < THRESHOLDS["ticketing_scan_success_rate_crit"] else "WARN" if summary["anomaly_windows"] else "OK",
        },
        {
            "label": "Latency",
            "status": "CRIT" if summary["max_latency_p95"] is not None and summary["max_latency_p95"] > THRESHOLDS["ticketing_latency_crit_ms"] else "OK",
        },
        {
            "label": "Throughput",
            "status": "WARN" if summary["throughput_collapses"] else "OK",
        },
    ]
)
render_kpi_cards(
    [
        {
            "title": "Anomaly windows",
            "value": summary["anomaly_windows"],
            "subtitle": "Any scan-success drop below 97% or latency above 1500 ms is counted here.",
            "status": "CRIT" if summary["anomaly_windows"] >= 8 else "WARN" if summary["anomaly_windows"] else "OK",
        },
        {
            "title": "Min scan success",
            "value": f"{summary['min_success_rate']:.1%}" if summary["min_success_rate"] is not None else "-",
            "subtitle": "Critical threshold is 94% in this demo.",
            "status": "CRIT" if summary["min_success_rate"] is not None and summary["min_success_rate"] < THRESHOLDS["ticketing_scan_success_rate_crit"] else "WARN" if summary["anomaly_windows"] else "OK",
        },
        {
            "title": "Max latency p95",
            "value": f"{summary['max_latency_p95']:.0f} ms" if summary["max_latency_p95"] is not None else "-",
            "subtitle": "Use this to explain the difference between degradation and collapse.",
            "status": "CRIT" if summary["max_latency_p95"] is not None and summary["max_latency_p95"] > THRESHOLDS["ticketing_latency_crit_ms"] else "OK",
        },
        {
            "title": "Offline fallback",
            "value": summary["total_offline_fallbacks"],
            "subtitle": f"Denied entries: {summary['total_denied']}",
            "status": "WARN" if summary["total_offline_fallbacks"] else "OK",
        },
    ]
)

left, right = st.columns(2)
with left:
    render_section_header("Scan success trend", "This is the chart to use when the panel asks how you would spot guest-entry degradation before queues form.")
    chart = px.line(
        filtered,
        x="ts",
        y="scan_success_rate",
        color="venue_area",
        title="Scan success by venue area",
    )
    chart.add_hline(y=THRESHOLDS["ticketing_scan_success_rate_warn"], line_dash="dot", line_color="#B76A16")
    chart.add_hline(y=THRESHOLDS["ticketing_scan_success_rate_crit"], line_dash="dot", line_color="#B43C2F")
    chart.update_yaxes(tickformat=".0%")
    style_plotly(chart, height=360)
    st.plotly_chart(chart, use_container_width=True)

with right:
    render_section_header("QR latency trend", "Latency spikes usually show up before operators start reporting failed scans.")
    chart = px.line(
        filtered,
        x="ts",
        y="qr_validation_latency_ms_p95",
        color="venue_area",
        title="QR validation latency p95 by venue area",
    )
    chart.add_hline(y=THRESHOLDS["ticketing_latency_warn_ms"], line_dash="dot", line_color="#B76A16")
    chart.add_hline(y=THRESHOLDS["ticketing_latency_crit_ms"], line_dash="dot", line_color="#B43C2F")
    style_plotly(chart, height=360)
    st.plotly_chart(chart, use_container_width=True)

render_section_header("Throughput by venue area", "Use this view to show where guest flow is collapsing even when scan success still looks reasonable.")
throughput = px.line(
    filtered,
    x="ts",
    y="gate_throughput_ppm",
    color="venue_area",
    title="Gate throughput by venue area",
)
style_plotly(throughput, height=360)
st.plotly_chart(throughput, use_container_width=True)

render_section_header("Anomaly register", "Linked incident IDs make ticketing degradation traceable back into the incident register.")
display_columns = [
    "ts",
    "source_system",
    "venue_area",
    "scan_success_rate",
    "qr_validation_latency_ms_p95",
    "gate_throughput_ppm",
    "denied_entries",
    "offline_fallback_activations",
    "payment_dependency_flag",
    "linked_incident_id",
]
st.dataframe(
    format_table(filtered[display_columns].sort_values("ts", ascending=False)),
    use_container_width=True,
    hide_index=True,
)

render_download_buttons(
    [
        {
            "label": "Download ticketing CSV",
            "data": filtered.to_csv(index=False).encode("utf-8"),
            "file_name": "ticketing_kpis_filtered.csv",
            "mime": "text/csv",
        }
    ]
)

render_lineage_panel(
    filtered,
    title="Data lineage",
    trace_fields=["venue_area", "linked_incident_id"],
)
