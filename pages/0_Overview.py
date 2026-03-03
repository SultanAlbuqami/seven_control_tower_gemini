from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.data import ensure_data_and_load
from src.metrics import compute_mtta_minutes, compute_mttr_minutes, readiness_score, vendor_scorecard
from src.system_landscape import CORE_BADGE_CATEGORIES, DISCLAIMER
from src.ui import SEVERITY_COLORS, apply_global_styles, style_plotly

st.set_page_config(layout="wide")
apply_global_styles()
st.title("📍 Overview")
st.info(
    "⚡ Synthetic dataset — evidence-driven readiness model — example system landscape labels. " + DISCLAIMER,
    icon="🔬",
)

badge_cols = st.columns(len(CORE_BADGE_CATEGORIES))
for col, cat in zip(badge_cols, CORE_BADGE_CATEGORIES):
    col.caption(f"**{cat.badge_label}**")

st.divider()

try:
    data = ensure_data_and_load()
except Exception as e:
    st.error(f"Data load error: {e}")
    st.stop()

rs = readiness_score(data.readiness)
vs = vendor_scorecard(data.vendors)

open_inc = data.incidents[data.incidents["status"].isin(["OPEN", "MITIGATED"])].copy()
sev12 = open_inc[open_inc["severity"].isin([1, 2])]
missing_evd = data.evidence[data.evidence["status"] == "MISSING"]

mtta = compute_mtta_minutes(data.incidents)
mttr = compute_mttr_minutes(data.incidents)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Services with RED gates", int((data.readiness["status"] == "RED").sum()))
c2.metric("Missing evidence items", int(len(missing_evd)))
c3.metric("Open Sev-1/2 incidents", int(len(sev12)))
c4.metric("Vendor breach signals", int((vs["breach_count"] > 0).sum()))

st.divider()

left, right = st.columns([1, 1])

with left:
    st.subheader("Readiness ranking")
    st.dataframe(rs, use_container_width=True, hide_index=True)

with right:
    st.subheader("Open incidents (by service)")
    if open_inc.empty:
        st.info("No open incidents in current dataset.")
    else:
        fig = px.histogram(
            open_inc,
            x="service",
            color="severity",
            color_discrete_map=SEVERITY_COLORS,
            title="Open incidents",
        )
        style_plotly(fig)
        st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("KPIs (last 48 hours)")
kpis = data.kpis.copy()
if not kpis.empty:
    recent = kpis.sort_values("ts").groupby(["kpi", "service"], as_index=False).tail(48)
    fig = px.line(recent, x="ts", y="value", color="kpi", line_group="service", title="Recent KPI trend")
    style_plotly(fig)
    st.plotly_chart(fig, use_container_width=True)

with st.expander("Notes"):
    st.write(
        "This view provides the operational posture at a glance. "
        "Use it to frame a Go/No-Go conversation and focus the team on the top blockers."
    )
