from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.data import ensure_data_and_load
from src.metrics import compute_mtta_minutes, compute_mttr_minutes
from src.system_landscape import CORE_BADGE_CATEGORIES, DISCLAIMER
from src.ui import SEVERITY_COLORS, apply_global_styles, style_plotly
try:
    from src.ui import render_kpi_card
except Exception:
    def render_kpi_card(title, value, *_, **__):
        cols = st.columns(1)
        cols[0].metric(title, value)

st.set_page_config(layout="wide")
apply_global_styles()
st.title("🚨 Incidents")
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
render_kpi_card("Incidents", len(inc), icon="alert", color="#fff4f4")
render_kpi_card("MTTA (min)", "-" if mtta is None else f"{mtta:.1f}", icon=None, color="#eef6ff")
render_kpi_card("MTTR (min)", "-" if mttr is None else f"{mttr:.1f}", icon=None, color="#eef6ff")

st.divider()
st.subheader("Opened incidents distribution")
if not inc.empty:
    fig = px.histogram(
        inc,
        x="opened_at",
        color="severity",
        color_discrete_map=SEVERITY_COLORS,
        nbins=24,
    )
    style_plotly(fig)
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
