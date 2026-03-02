from __future__ import annotations

import streamlit as st

from src.data import load_data

st.set_page_config(layout="wide")
st.title("📦 Evidence Pack")
st.info("⚡ Synthetic dataset — evidence-driven readiness demo", icon="🔬")

try:
    data = load_data()
except FileNotFoundError as e:
    st.error(str(e))
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
a.metric("Evidence items", total)
b.metric("Complete", complete)
c.metric("Missing", missing)

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
