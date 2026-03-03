from __future__ import annotations

import streamlit as st

from src.data import ensure_data_and_load
from src.system_landscape import CORE_BADGE_CATEGORIES, DISCLAIMER
from src.ui import apply_global_styles
try:
    from src.ui import render_kpi_card
except Exception:
    def render_kpi_card(title, value, *_, **__):
        cols = st.columns(1)
        cols[0].metric(title, value)

st.set_page_config(layout="wide")
apply_global_styles()
st.title("📦 Evidence Pack")
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
evidence = data.evidence

col1, col2, col3 = st.columns(3)
with col1:
    service = st.selectbox("Service", ["ALL"] + sorted(evidence["service"].unique().tolist()))
with col2:
    gate = st.selectbox("Gate", ["ALL"] + sorted(evidence["gate"].unique().tolist()))
with col3:
    status = st.selectbox("Status", ["ALL", "COMPLETE", "MISSING"])

filtered = evidence.copy()
if service != "ALL":
    filtered = filtered[filtered["service"] == service]
if gate != "ALL":
    filtered = filtered[filtered["gate"] == gate]
if status != "ALL":
    filtered = filtered[filtered["status"] == status]

total = len(filtered)
missing = int((filtered["status"] == "MISSING").sum()) if total else 0
complete = total - missing

a, b, c = st.columns(3)
render_kpi_card("Evidence items", total, icon="doc", color="#eef6ff")
render_kpi_card("Complete", complete, icon="check", color="#effff4")
render_kpi_card("Missing", missing, icon="alert", color="#fff4f4")

if total:
    st.progress(complete / total)

st.divider()
st.subheader("Action list (missing evidence)")
missing_df = filtered[filtered["status"] == "MISSING"].copy()
cols = ["evidence_id", "service", "gate", "evidence_type", "owner", "updated_at", "note"]
st.dataframe(
    missing_df[cols].sort_values(["service", "gate", "evidence_type"]),
    use_container_width=True,
    hide_index=True,
)

st.download_button(
    "Download filtered evidence CSV",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="evidence_filtered.csv",
    mime="text/csv",
)
