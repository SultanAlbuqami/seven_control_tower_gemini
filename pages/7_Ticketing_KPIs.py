"""Page 7 — Ticketing KPIs (gate scan / QR validation / throughput time series).

DISCLAIMER: Source system names are example labels; demo is source-agnostic.
"""
from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.data import ensure_data_and_load
from src.system_landscape import CORE_BADGE_CATEGORIES, DISCLAIMER, THRESHOLDS

st.set_page_config(layout="wide")
st.title("🎫 Ticketing KPIs")
st.caption("Gate scan success / QR validation latency / throughput — 48-hour rolling view")

# ── Demo mode banner & landscape badges ──────────────────────────────────────
st.info(
    "⚡ Synthetic dataset — evidence-driven readiness model — example system landscape labels. "
    + DISCLAIMER,
    icon="🔬",
)
badge_cols = st.columns(len(CORE_BADGE_CATEGORIES))
for col, cat in zip(badge_cols, CORE_BADGE_CATEGORIES):
    col.caption(f"**{cat.badge_label}**")

st.divider()

# ── Load data ─────────────────────────────────────────────────────────────────
try:
    data = ensure_data_and_load()
except Exception as e:
    st.error(f"Data load error: {e}")
    st.stop()

tkt = data.ticketing_kpis.copy()

if tkt.empty:
    st.warning("No ticketing KPI data available.")
    st.stop()

# ── Filters ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.subheader("Filters")
    area_opts = sorted(tkt["venue_area"].dropna().unique().tolist()) if "venue_area" in tkt.columns else []
    sel_area = st.multiselect("Venue area", area_opts, default=area_opts, key="tkt_area")
    anomaly_only = st.checkbox("Show anomaly windows only", value=False)

df = tkt.copy()
if sel_area and "venue_area" in df.columns:
    df = df[df["venue_area"].isin(sel_area)]

# ── Anomaly flag columns ───────────────────────────────────────────────────────
warn_sr = THRESHOLDS["ticketing_scan_success_rate_warn"]
crit_sr = THRESHOLDS["ticketing_scan_success_rate_crit"]
crit_lat = THRESHOLDS["ticketing_latency_crit_ms"]

if "scan_success_rate" in df.columns:
    import pandas as pd
    df["sr_status"] = "OK"
    df.loc[df["scan_success_rate"] < warn_sr, "sr_status"] = "WARN"
    df.loc[df["scan_success_rate"] < crit_sr, "sr_status"] = "CRIT"

if anomaly_only and "scan_success_rate" in df.columns and "qr_validation_latency_ms_p95" in df.columns:
    import pandas as pd
    anom_mask = (
        (df["scan_success_rate"] < warn_sr)
        | (df["qr_validation_latency_ms_p95"] > crit_lat)
    )
    df = df[anom_mask]

# ── KPI cards ─────────────────────────────────────────────────────────────────
total_anomalies = 0
total_offline = 0
min_sr = None
max_lat = None

if "scan_success_rate" in tkt.columns:
    sr_series = tkt["scan_success_rate"].dropna()
    min_sr = float(sr_series.min()) if not sr_series.empty else None
    total_anomalies += int((sr_series < warn_sr).sum())

if "qr_validation_latency_ms_p95" in tkt.columns:
    lat_series = tkt["qr_validation_latency_ms_p95"].dropna()
    max_lat = float(lat_series.max()) if not lat_series.empty else None
    total_anomalies += int((lat_series > crit_lat).sum())

if "offline_fallback_activations" in tkt.columns:
    total_offline = int(tkt["offline_fallback_activations"].fillna(0).sum())

total_denied = int(tkt["denied_entries"].fillna(0).sum()) if "denied_entries" in tkt.columns else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric(
    "Anomaly Windows",
    total_anomalies,
    delta="⚠️ Review" if total_anomalies > 0 else "OK",
    delta_color="inverse" if total_anomalies > 0 else "normal",
)
c2.metric(
    "Min Scan Success Rate",
    f"{min_sr:.1%}" if min_sr is not None else "N/A",
    delta="⚠️ CRIT" if min_sr is not None and min_sr < crit_sr else ("WARN" if min_sr is not None and min_sr < warn_sr else "OK"),
    delta_color="inverse" if min_sr is not None and min_sr < warn_sr else "normal",
)
c3.metric("Offline Fallback Activations", total_offline)
c4.metric("Total Denied Entries", total_denied)

st.divider()

# ── Charts ─────────────────────────────────────────────────────────────────────
left, right = st.columns(2)

with left:
    st.subheader("Scan Success Rate over Time")
    if not df.empty and "ts" in df.columns and "scan_success_rate" in df.columns:
        avg_df = df.groupby("ts", as_index=False)["scan_success_rate"].mean()
        fig = px.line(
            avg_df, x="ts", y="scan_success_rate",
            title="Avg Scan Success Rate (all areas)",
            labels={"scan_success_rate": "Success Rate", "ts": "Time"},
        )
        fig.add_hline(y=warn_sr, line_dash="dash", line_color="orange", annotation_text=f"Warn {warn_sr:.0%}")
        fig.add_hline(y=crit_sr, line_dash="dash", line_color="red", annotation_text=f"Crit {crit_sr:.0%}")
        fig.update_yaxes(tickformat=".1%")
        st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("QR Validation Latency p95")
    if not df.empty and "ts" in df.columns and "qr_validation_latency_ms_p95" in df.columns:
        avg_lat = df.groupby("ts", as_index=False)["qr_validation_latency_ms_p95"].mean()
        fig2 = px.line(
            avg_lat, x="ts", y="qr_validation_latency_ms_p95",
            title="Avg QR Latency p95 (ms)",
            labels={"qr_validation_latency_ms_p95": "Latency p95 (ms)", "ts": "Time"},
        )
        fig2.add_hline(y=THRESHOLDS["ticketing_latency_warn_ms"], line_dash="dash",
                       line_color="orange", annotation_text=f"Warn {THRESHOLDS['ticketing_latency_warn_ms']} ms")
        fig2.add_hline(y=crit_lat, line_dash="dash",
                       line_color="red", annotation_text=f"Crit {crit_lat} ms")
        st.plotly_chart(fig2, use_container_width=True)

# ── Per-area throughput ────────────────────────────────────────────────────────
st.subheader("Gate Throughput per Area")
if not df.empty and "ts" in df.columns and "gate_throughput_ppm" in df.columns and "venue_area" in df.columns:
    fig3 = px.line(
        df, x="ts", y="gate_throughput_ppm", color="venue_area",
        title="Gate Throughput (persons/min) by Area",
        labels={"gate_throughput_ppm": "Throughput (ppm)", "ts": "Time"},
    )
    st.plotly_chart(fig3, use_container_width=True)

# ── Per-area scan success heatmap-style ───────────────────────────────────────
st.subheader("Scan Success Rate by Area")
if not df.empty and "venue_area" in df.columns and "scan_success_rate" in df.columns:
    area_agg = df.groupby("venue_area", as_index=False)["scan_success_rate"].mean()
    area_agg["status"] = area_agg["scan_success_rate"].apply(
        lambda v: "CRIT" if v < crit_sr else ("WARN" if v < warn_sr else "OK")
    )
    color_map = {"OK": "green", "WARN": "orange", "CRIT": "red"}
    fig4 = px.bar(
        area_agg, x="venue_area", y="scan_success_rate", color="status",
        color_discrete_map=color_map,
        title="Mean Scan Success Rate by Area (filtered period)",
    )
    fig4.update_yaxes(tickformat=".1%", range=[0.85, 1.0])
    st.plotly_chart(fig4, use_container_width=True)

# ── Anomaly rows highlight ─────────────────────────────────────────────────────
st.subheader("Anomaly window details")
anom_df = tkt.copy()
if "scan_success_rate" in anom_df.columns and "qr_validation_latency_ms_p95" in anom_df.columns:
    anom_df = anom_df[
        (anom_df["scan_success_rate"] < warn_sr)
        | (anom_df["qr_validation_latency_ms_p95"] > crit_lat)
    ]

if anom_df.empty:
    st.success("No anomaly windows detected in the current dataset. ✓")
else:
    st.warning(f"{len(anom_df)} anomaly window(s) detected below threshold or above latency ceiling.")
    show_cols = [c for c in ["ts", "source_system", "venue_area", "scan_success_rate",
                              "qr_validation_latency_ms_p95", "gate_throughput_ppm",
                              "denied_entries", "offline_fallback_activations",
                              "payment_dependency_flag", "linked_incident_id"] if c in anom_df.columns]
    st.dataframe(anom_df[show_cols].sort_values("ts", ascending=False) if "ts" in anom_df.columns
                 else anom_df[show_cols], use_container_width=True)

# ── Full table & download ──────────────────────────────────────────────────────
with st.expander(f"Full filtered data ({len(df)} rows)"):
    all_cols = [c for c in ["ts", "source_system", "venue_area", "scan_success_rate",
                              "qr_validation_latency_ms_p95", "gate_throughput_ppm",
                              "denied_entries", "offline_fallback_activations",
                              "payment_dependency_flag", "linked_incident_id"] if c in df.columns]
    st.dataframe(df[all_cols], use_container_width=True)

    csv_bytes = df[all_cols].to_csv(index=False).encode()
    st.download_button("⬇ Download Ticketing KPIs CSV", csv_bytes, "ticketing_kpis_filtered.csv", "text/csv")

# ── Source system note ────────────────────────────────────────────────────────
with st.expander("Source system note"):
    st.markdown(
        "Data labelled with source system: **accesso Horizon / Ticketing Platform — Gate Validation (examples)**. "
        "In a real deployment, this time series would be ingested from the venue's ticketing platform via API or data lake export. "
        + DISCLAIMER
    )
