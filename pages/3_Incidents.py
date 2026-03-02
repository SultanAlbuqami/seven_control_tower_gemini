from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.data import load_data
from src.metrics import compute_mtta_minutes, compute_mttr_minutes

st.set_page_config(layout="wide")
st.title("🚨 Incidents")
st.info("⚡ Synthetic dataset — evidence-driven readiness demo", icon="🔬")

try:
    data = load_data()
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()
inc = data.incidents.copy()

c1, c2, c3 = st.columns(3)
with c1:
    service = st.selectbox("Service", ["ALL"] + sorted(inc["service"].unique().tolist()))
with c2:
    severity = st.selectbox("Severity", ["ALL", 1, 2, 3, 4])
with c3:
    status = st.selectbox("Status", ["ALL"] + sorted(inc["status"].unique().tolist()))

if service != "ALL":
    inc = inc[inc["service"] == service]
if severity != "ALL":
    inc = inc[inc["severity"] == severity]
if status != "ALL":
    inc = inc[inc["status"] == status]

mtta = compute_mtta_minutes(inc)
mttr = compute_mttr_minutes(inc)

k1, k2, k3 = st.columns(3)
k1.metric("Incidents", len(inc))
k2.metric("MTTA (min)", "-" if mtta is None else f"{mtta:.1f}")
k3.metric("MTTR (min)", "-" if mttr is None else f"{mttr:.1f}")

st.divider()
st.subheader("Opened incidents distribution")
if not inc.empty:
    fig = px.histogram(inc, x="opened_at", color="severity", nbins=24)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No incidents match the current filters.")

st.subheader("Incident list")
cols = [
    "incident_id",
    "service",
    "vendor",
    "severity",
    "status",
    "opened_at",
    "ack_at",
    "resolved_at",
    "summary",
    "rca_done",
    "prevent_action",
]
st.dataframe(
    inc[cols].sort_values("opened_at", ascending=False),
    use_container_width=True,
    hide_index=True,
)
