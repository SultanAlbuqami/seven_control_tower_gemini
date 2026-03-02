from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.data import load_data
from src.metrics import vendor_scorecard

st.set_page_config(layout="wide")
st.title("📊 Vendor Scorecards")
st.info("⚡ Synthetic dataset — evidence-driven readiness demo", icon="🔬")

try:
    data = load_data()
except FileNotFoundError as e:
    st.error(str(e))
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
    st.plotly_chart(fig, use_container_width=True)
