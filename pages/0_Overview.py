from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.data import load_data
from src.metrics import compute_mtta_minutes, compute_mttr_minutes, readiness_score, vendor_scorecard

st.set_page_config(layout="wide")
st.title("📍 Overview")
st.info("⚡ Synthetic dataset — evidence-driven readiness demo", icon="🔬")

try:
    data = load_data()
except FileNotFoundError as e:
    st.error(str(e))
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
        fig = px.histogram(open_inc, x="service", color="severity", title="Open incidents")
        st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("KPIs (last 48 hours)")
kpis = data.kpis.copy()
if not kpis.empty:
    recent = kpis.sort_values("ts").groupby(["kpi", "service"], as_index=False).tail(48)
    fig = px.line(recent, x="ts", y="value", color="kpi", line_group="service", title="Recent KPI trend")
    st.plotly_chart(fig, use_container_width=True)

with st.expander("Notes"):
    st.write(
        "This view provides the operational posture at a glance. "
        "Use it to frame a Go/No-Go conversation and focus the team on the top blockers."
    )
