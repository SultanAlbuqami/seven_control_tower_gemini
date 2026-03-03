from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.data import ensure_data_and_load
from src.system_landscape import CORE_BADGE_CATEGORIES, DISCLAIMER
from src.ui import apply_global_styles, readiness_scale, style_plotly

st.set_page_config(layout="wide")
apply_global_styles()
st.title("🟩🟧🟥 Readiness (Services × Gates)")
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
        color_continuous_scale=readiness_scale(),
        zmin=-1,
        zmax=2,
    )
    style_plotly(fig)
    st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("Blockers and last updates")
cols = ["service", "gate", "gate_name", "status", "last_updated", "blocker"]
st.dataframe(
    readiness_f[cols].sort_values(["status", "service", "gate"]),
    use_container_width=True,
    hide_index=True,
)
