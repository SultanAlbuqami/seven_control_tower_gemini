from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Day-One Operations Readiness Control Tower",
    page_icon="🧭",
    layout="wide",
)

st.title("🧭 Day-One Operations Readiness Control Tower")
st.caption("Readiness gates • Evidence packs • Incidents • Vendor scorecards • Live recommendations")

st.info("⚡ Synthetic dataset — evidence-driven readiness demo", icon="🔬")

# ── Check whether data exists; offer generation button ──────────────────────
DATA_DIR = Path(__file__).parent / "data"
_data_files = ["services.csv", "readiness.csv", "evidence.csv", "incidents.csv", "vendors.csv", "kpis.csv"]
data_missing = not all((DATA_DIR / f).exists() for f in _data_files)

if data_missing:
    st.warning(
        "Demo data files not found. Click the button below to generate them now.",
        icon="⚠️",
    )
    if st.button("⚙️ Generate Sample Data", type="primary"):
        with st.spinner("Generating demo data…"):
            result = subprocess.run(
                [sys.executable, "-m", "src.seed"],
                capture_output=True,
                text=True,
            )
        if result.returncode == 0:
            st.success("Demo data generated successfully. Use the sidebar to explore.")
            st.rerun()
        else:
            st.error(f"Seed failed:\n```\n{result.stderr}\n```")
else:
    st.markdown(
        """
Use the pages in the left sidebar:

| Page | What it shows |
|---|---|
| **Overview** | Key KPIs and operational posture at a glance |
| **Readiness** | Services × gates heatmap with blockers |
| **Evidence Pack** | Missing evidence items and ownership |
| **Incidents** | MTTA / MTTR and severity discipline |
| **Vendor Scorecards** | SLA compliance and breach visibility |
| **Recommendations** | Gemini-powered (or heuristic) actions for next 24h / 7d |
"""
    )

with st.sidebar:
    st.subheader("3-min interview demo")
    st.markdown(
        "**Step 1** — Overview: read the 4 KPI cards\n\n"
        "**Step 2** — Readiness: show RED gate heatmap and top blockers\n\n"
        "**Step 3** — Evidence Pack: filter MISSING items; show owner chase list\n\n"
        "**Step 4** — Incidents: MTTA/MTTR; highlight Sev-1/2 escalations\n\n"
        "**Step 5** — Recommendations: click Generate (works offline too)\n\n"
        "**Go/No-Go** answer: 0 RED gates + 0 open Sev-1/2 + evidence ≥ 90%"
    )
