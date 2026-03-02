from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.data import load_data

st.set_page_config(layout="wide")
st.title("🟩🟧🟥 Readiness (Services × Gates)")
st.info("⚡ Synthetic dataset — evidence-driven readiness demo", icon="🔬")

try:
    data = load_data()
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()
services = data.services
readiness = data.readiness

left, right = st.columns([1, 2])

with left:
    crit_min = st.selectbox("Minimum criticality", [1, 2, 3], index=1)
    selected_vendors = st.multiselect(
        "Vendors", sorted(services["vendor"].unique().tolist()), default=[]
    )

svc_filter = services[services["criticality"] >= crit_min].copy()
if selected_vendors:
    svc_filter = svc_filter[svc_filter["vendor"].isin(selected_vendors)]

readiness_f = readiness[readiness["service"].isin(svc_filter["service"])].copy()

status_map = {"GREEN": 2, "AMBER": 1, "RED": 0}
readiness_f["score"] = readiness_f["status"].map(status_map).fillna(-1).astype(int)

pivot = readiness_f.pivot(index="service", columns="gate", values="score").fillna(-1)

with right:
    st.subheader("Heatmap")
    fig = px.imshow(
        pivot,
        aspect="auto",
        labels=dict(x="Gate", y="Service", color="Status"),
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("Blockers and last updates")
cols = ["service", "gate", "gate_name", "status", "last_updated", "blocker"]
st.dataframe(
    readiness_f[cols].sort_values(["status", "service", "gate"]),
    use_container_width=True,
    hide_index=True,
)
