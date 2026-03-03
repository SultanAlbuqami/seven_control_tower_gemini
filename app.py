from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import streamlit as st

from src.seed import ensure_data_present
from src.system_landscape import CORE_BADGE_CATEGORIES, DISCLAIMER
from src.ui import apply_global_styles, render_color_legend, render_theme_settings
from src.ui import apply_global_styles
try:
    from src.ui import render_theme_settings, render_color_legend
except Exception:
    def render_theme_settings():
        return None
    def render_color_legend():
        return None

st.set_page_config(
    page_title="Day-One Operations Readiness Control Tower",
    page_icon="🧭",
    layout="wide",
)

apply_global_styles()

st.title("🧭 Day-One Operations Readiness Control Tower")
st.caption("Readiness gates • Evidence packs • Incidents • Vendor scorecards • OT Events • Ticketing KPIs • Live recommendations")

st.info(
    "⚡ Synthetic dataset — evidence-driven readiness model — example system landscape labels. " + DISCLAIMER,
    icon="🔬",
)

# ── Landscape badges ─────────────────────────────────────────────────────────
badge_cols = st.columns(len(CORE_BADGE_CATEGORIES))
for col, cat in zip(badge_cols, CORE_BADGE_CATEGORIES):
    col.caption(f"**{cat.badge_label}**")

# Theme settings (sidebar) and Legend for color meanings
render_theme_settings()
render_color_legend()

st.divider()

# ── Auto-seed on startup (silent) ────────────────────────────────────────────
_DATA_DIR = Path(__file__).parent / "data"
_REQUIRED_FILES = [
    "services.csv", "readiness.csv", "evidence.csv",
    "incidents.csv", "vendors.csv", "kpis.csv",
    "ot_events.csv", "ticketing_kpis.csv",
]

with st.spinner("Checking demo data…"):
    try:
        ensure_data_present()
    except Exception as _seed_err:
        st.error(f"Auto-seed failed: {_seed_err}")

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
| **OT Events** | BMS / Access Control / CCTV alarm monitor |
| **Ticketing KPIs** | Gate scan success, QR latency, throughput |
| **Recommendations** | Gemini-powered (or heuristic) actions for next 24 h / 7 d |
"""
)

# ── Optional manual regeneration ─────────────────────────────────────────────
with st.expander("⚙️ Advanced — regenerate demo data"):
    if st.button("Regenerate Sample Data", type="secondary"):
        with st.spinner("Regenerating…"):
            result = subprocess.run(
                [sys.executable, "-m", "src.seed"],
                capture_output=True,
                text=True,
            )
        if result.returncode == 0:
            st.success("Demo data regenerated. Refresh any open page.")
        else:
            st.error(f"Seed failed:\n```\n{result.stderr}\n```")

with st.sidebar:
    st.subheader("3-min interview demo")
    st.markdown(
        "**Step 1** — Overview: read the 4 KPI cards\n\n"
        "**Step 2** — Readiness: show RED gate heatmap and top blockers\n\n"
        "**Step 3** — Evidence Pack: filter MISSING items; show owner chase list\n\n"
        "**Step 4** — Incidents: MTTA/MTTR; highlight Sev-1/2 escalations\n\n"
        "**Step 5** — OT Events: unacked Sev-1/2 alarms, mean ack time\n\n"
        "**Step 6** — Ticketing KPIs: scan success rate, QR latency anomalies\n\n"
        "**Step 7** — Recommendations: click Generate (works offline too)\n\n"
        "**Go/No-Go** answer: 0 RED gates + 0 open Sev-1/2 + evidence ≥ 90%"
    )
