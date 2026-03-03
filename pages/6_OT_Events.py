"""Page 6 — OT Events (BMS / Access Control / CCTV alarm feed).

DISCLAIMER: Source system names are example labels; demo is source-agnostic.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data import ensure_data_and_load
from src.metrics import compute_ot_mean_ack_minutes
from src.system_landscape import CORE_BADGE_CATEGORIES, DISCLAIMER, THRESHOLDS

st.set_page_config(layout="wide")
st.title("🏗️ OT Events")
st.caption("BMS / Access Control / CCTV alarm feed — example system landscape labels")

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

ot = data.ot_events.copy()

if ot.empty:
    st.warning("No OT event data available.")
    st.stop()

# ── Filters ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.subheader("Filters")
    sev_opts = sorted(ot["severity"].dropna().unique().tolist())
    sel_sev = st.multiselect("Severity", sev_opts, default=sev_opts, key="ot_sev")

    sub_opts = sorted(ot["subsystem"].dropna().unique().tolist()) if "subsystem" in ot.columns else []
    sel_sub = st.multiselect("Subsystem", sub_opts, default=sub_opts, key="ot_sub")

    zone_opts = sorted(ot["zone"].dropna().unique().tolist()) if "zone" in ot.columns else []
    sel_zone = st.multiselect("Zone", zone_opts, default=zone_opts, key="ot_zone")

    unacked_only = st.checkbox("Unacknowledged only", value=False)

df = ot.copy()
if sel_sev:
    df = df[df["severity"].isin(sel_sev)]
if sel_sub and "subsystem" in df.columns:
    df = df[df["subsystem"].isin(sel_sub)]
if sel_zone and "zone" in df.columns:
    df = df[df["zone"].isin(sel_zone)]
if unacked_only and "ack_time" in df.columns:
    df = df[df["ack_time"].isna()]

# ── KPI cards ─────────────────────────────────────────────────────────────────
unacked_mask = ot["ack_time"].isna() if "ack_time" in ot.columns else pd.Series(False, index=ot.index)
unacked_sev1 = int((unacked_mask & (ot["severity"] == 1)).sum()) if "severity" in ot.columns else 0
unacked_sev2 = int((unacked_mask & (ot["severity"] == 2)).sum()) if "severity" in ot.columns else 0
cleared_mask = ot["cleared_time"].notna() if "cleared_time" in ot.columns else pd.Series(False, index=ot.index)
open_events = int((~cleared_mask).sum())
mean_ack = compute_ot_mean_ack_minutes(ot)

c1, c2, c3, c4 = st.columns(4)
c1.metric(
    "Unacked Sev-1",
    unacked_sev1,
    delta=f"{'⚠️ ACTION' if unacked_sev1 > THRESHOLDS['ot_unacked_sev1_warn'] else 'OK'}",
    delta_color="inverse",
)
c2.metric(
    "Unacked Sev-2",
    unacked_sev2,
    delta=f"{'⚠️ WARN' if unacked_sev2 > THRESHOLDS['ot_unacked_sev2_warn'] else 'OK'}",
    delta_color="inverse",
)
c3.metric("Open (not cleared)", open_events)
c4.metric(
    "Mean Ack Time (min)",
    f"{mean_ack:.1f}" if mean_ack is not None else "N/A",
    help="Mean time from event to acknowledgement, across all acked events",
)

st.divider()

# ── Charts ─────────────────────────────────────────────────────────────────────
left, right = st.columns(2)

with left:
    st.subheader("Events by Subsystem & Severity")
    if not df.empty and "subsystem" in df.columns:
        fig = px.histogram(
            df, x="subsystem", color="severity",
            color_discrete_sequence=px.colors.sequential.Reds_r,
            title="OT Event Count by Subsystem",
            labels={"subsystem": "Subsystem", "count": "Events"},
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data for chart.")

with right:
    st.subheader("Events by Zone & Severity")
    if not df.empty and "zone" in df.columns:
        fig2 = px.histogram(
            df, x="zone", color="severity",
            color_discrete_sequence=px.colors.sequential.Oranges_r,
            title="OT Event Count by Zone",
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No data for chart.")

# ── Timeline chart ─────────────────────────────────────────────────────────────
st.subheader("Event Timeline")
if not df.empty and "event_time" in df.columns:
    timeline_df = df.dropna(subset=["event_time"]).copy()
    if not timeline_df.empty:
        fig3 = px.scatter(
            timeline_df,
            x="event_time",
            y="zone" if "zone" in timeline_df.columns else timeline_df.index,
            color="severity",
            symbol="subsystem" if "subsystem" in timeline_df.columns else None,
            hover_data=["ot_event_id", "alarm_type", "device_id"] if "ot_event_id" in timeline_df.columns else None,
            title="OT Alarm Timeline",
            color_continuous_scale="Reds_r",
        )
        st.plotly_chart(fig3, use_container_width=True)

# ── Alarm type breakdown ────────────────────────────────────────────────────────
st.subheader("Alarm Type Breakdown")
if not df.empty and "alarm_type" in df.columns:
    at_counts = df["alarm_type"].value_counts().reset_index()
    at_counts.columns = ["alarm_type", "count"]
    fig4 = px.bar(at_counts, x="alarm_type", y="count", color="count",
                  color_continuous_scale="Reds", title="Alarm Types (filtered)")
    st.plotly_chart(fig4, use_container_width=True)

# ── Table & download ───────────────────────────────────────────────────────────
st.subheader(f"Event table ({len(df)} rows filtered)")

display_cols = [c for c in ["ot_event_id", "source_system", "subsystem", "alarm_type", "zone",
                             "device_id", "severity", "event_time", "ack_time", "cleared_time",
                             "acked_by_role", "linked_incident_id"] if c in df.columns]
st.dataframe(df[display_cols].sort_values("event_time", ascending=False) if "event_time" in df.columns
             else df[display_cols], use_container_width=True)

csv_bytes = df[display_cols].to_csv(index=False).encode()
st.download_button("⬇ Download OT Events CSV", csv_bytes, "ot_events_filtered.csv", "text/csv")

# ── Source system note ────────────────────────────────────────────────────────
with st.expander("Source system note"):
    st.markdown(
        "Data labelled with source system: **BMS / Access Control / CCTV Event Feed (example)**. "
        "In a real deployment, this feed would be ingested via the venue's OT event broker or API gateway. "
        + DISCLAIMER
    )
