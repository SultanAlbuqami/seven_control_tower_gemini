from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.data import ensure_data_and_load
from src.metrics import vendor_scorecard
from src.system_landscape import CORE_BADGE_CATEGORIES, DISCLAIMER
from src.ui import apply_global_styles, style_plotly

st.set_page_config(layout="wide")
apply_global_styles()
st.title("📊 Vendor Scorecards")
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
vendors = data.vendors.copy()

selected_vendor = st.selectbox("Vendor", ["ALL"] + sorted(vendors["vendor"].unique().tolist()))
if selected_vendor != "ALL":
    vendors = vendors[vendors["vendor"] == selected_vendor]

score = vendor_scorecard(vendors)

st.subheader("Scorecard")
st.dataframe(
    score.sort_values(["breach_count", "vendor"], ascending=[False, True]),
    use_container_width=True,
    hide_index=True,
)

st.divider()
st.subheader("Availability vs SLA")
if not vendors.empty:
    fig = px.scatter(
        vendors,
        x="sla_availability",
        y="availability_actual",
        hover_data=["vendor", "service", "open_critical"],
        title="Actual vs SLA",
    )
    style_plotly(fig)
    st.plotly_chart(fig, use_container_width=True)
