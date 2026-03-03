"""Page 5 — Live Recommendations (Groq + heuristic fallback).

Key design decisions:
- service.recommend() never raises; fallback is always available.
- Streaming is attempted when key is available; falls back to one-shot on error.
- JSON output is validated before rendering structured panels.
- API key is NEVER echoed to the UI or logs.
"""
from __future__ import annotations

import os
from typing import Any

import streamlit as st

from src.data import ensure_data_and_load
from src.metrics import (
    compute_mtta_minutes,
    compute_mttr_minutes,
    ot_event_summary,
    readiness_score,
    ticketing_kpi_summary,
    vendor_scorecard,
)
from src.recommendations import schema as rec_schema
from src.recommendations import service as rec_service
from src.recommendations.groq_adapter import call_groq_stream, parse_and_validate
from src.system_landscape import CORE_BADGE_CATEGORIES, DISCLAIMER
from src.ui import apply_global_styles

st.set_page_config(layout="wide")
apply_global_styles()
st.title("🧠 Recommendations")
st.caption("Groq-powered (falls back to heuristic if key is unavailable)")

# ── Demo mode banner ──────────────────────────────────────────────────────────
st.info(
    "⚡ Synthetic dataset — evidence-driven readiness model — example system landscape labels. "
    + DISCLAIMER,
    icon="🔬",
)

# ── Landscape badges ───────────────────────────────────────────────────────────
badge_cols = st.columns(len(CORE_BADGE_CATEGORIES))
for col, cat in zip(badge_cols, CORE_BADGE_CATEGORIES):
    col.caption(f"**{cat.badge_label}**")

st.divider()

# ── Secret / key handling ─────────────────────────────────────────────────────
def _resolve_api_key() -> str | None:
    """Resolve GROQ_API_KEY without ever echoing the value to the UI."""
    try:
        if "GROQ_API_KEY" in st.secrets:
            return str(st.secrets["GROQ_API_KEY"]).strip() or None
    except Exception:
        pass
    return os.environ.get("GROQ_API_KEY", "").strip() or None


api_key = _resolve_api_key()

with st.sidebar:
    st.subheader("API Key")
    if api_key:
        st.success("Key loaded from environment / secrets.", icon="🔑")
    else:
        st.info(
            "No key found. Paste below for this session (not saved to disk).",
            icon="🔑",
        )
        session_key = st.text_input("GROQ_API_KEY (session only)", type="password", key="groq_session_key")
        if session_key:
            os.environ["GROQ_API_KEY"] = session_key.strip()
            api_key = session_key.strip()

    st.subheader("Model settings")
    model = st.selectbox(
        "Model",
        ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"],
        index=0,
    )
    temperature = st.slider("Temperature", 0.0, 1.0, 0.2, 0.05)
    max_tokens = st.selectbox("Max output tokens", [512, 1024, 1536, 2048], index=2)
    use_stream = st.toggle("Streaming (when key available)", value=True)

# ── Load data (auto-generate if missing) ──────────────────────────────────────
try:
    data = ensure_data_and_load()
except Exception as e:
    st.error(f"Data load error: {e}")
    st.stop()

# ── Build snapshot (aggregated metrics only — no raw secrets) ─────────────────
rs = readiness_score(data.readiness)
vs = vendor_scorecard(data.vendors)
open_inc = data.incidents[data.incidents["status"].isin(["OPEN", "MITIGATED"])].copy()
sev12 = open_inc[open_inc["severity"].isin([1, 2])]

ot_sig = ot_event_summary(data.ot_events)
tkt_sig = ticketing_kpi_summary(data.ticketing_kpis)

snapshot: dict[str, Any] = {
    "readiness": {
        "red_gate_count": int((data.readiness["status"] == "RED").sum()),
        "top_blockers": (
            data.readiness[data.readiness["status"] == "RED"][["service", "gate", "blocker"]]
            .head(8)
            .to_dict(orient="records")
        ),
        "service_ranking": rs.head(6).to_dict(orient="records"),
    },
    "evidence": {
        "missing_count": int((data.evidence["status"] == "MISSING").sum()),
        "missing_top": (
            data.evidence[data.evidence["status"] == "MISSING"][
                ["service", "gate", "evidence_type", "owner"]
            ]
            .head(10)
            .to_dict(orient="records")
        ),
    },
    "incidents": {
        "open_count": int(len(open_inc)),
        "open_sev1_2": int(len(sev12)),
        "mtta_min": compute_mtta_minutes(data.incidents),
        "mttr_min": compute_mttr_minutes(data.incidents),
        "open_top": (
            open_inc.sort_values("opened_at", ascending=False)[
                ["incident_id", "service", "severity", "status", "summary"]
            ]
            .head(10)
            .to_dict(orient="records")
        ),
    },
    "vendors": {
        "breach_vendors": (
            vs[vs["breach_count"] > 0][["vendor", "service", "breach_count"]]
            .head(10)
            .to_dict(orient="records")
        ),
    },
    "ot_events": ot_sig,
    "ticketing": tkt_sig,
}

# ── Action ────────────────────────────────────────────────────────────────────
run = st.button("🚀 Generate Recommendations", type="primary")

if not run:
    st.info("Click **Generate Recommendations** to produce an AI-powered action plan.")
    st.stop()

rec_dict: dict[str, Any] | None = None
warning_msg: str | None = None

# --- Attempt Groq if key present and streaming requested ---
if api_key and use_stream:
    st.subheader("Raw output (streaming…)")
    placeholder = st.empty()
    raw_text = ""
    groq_ok = False

    try:
        for chunk in call_groq_stream(
            snapshot=snapshot,
            api_key=api_key,
            model=model,
            temperature=float(temperature),
            max_output_tokens=int(max_tokens),
        ):
            raw_text += chunk
            placeholder.markdown(raw_text)
        groq_ok = True
    except Exception as exc:
        st.warning(
            f"Groq streaming unavailable ({type(exc).__name__}). "
            "Switching to heuristic recommendations.",
            icon="⚠️",
        )

    if groq_ok:
        rec_dict = parse_and_validate(raw_text)
        if rec_dict is None:
            st.warning(
                "Groq returned output that could not be parsed. "
                "Showing heuristic recommendations instead.",
                icon="⚠️",
            )

elif api_key and not use_stream:
    with st.spinner("Calling Groq…"):
        rec_dict, warning_msg = rec_service.recommend(
            snapshot=snapshot,
            api_key=api_key,
            model=model,
            temperature=float(temperature),
            max_output_tokens=int(max_tokens),
            stream=False,
        )

# --- Fallback ---
if rec_dict is None:
    rec_dict, warning_msg = rec_service.recommend(snapshot, api_key=None)

if warning_msg:
    st.warning(warning_msg, icon="ℹ️")

# ── Render structured panels ──────────────────────────────────────────────────
st.divider()
st.subheader("Executive Summary")
st.markdown(f"> {rec_dict.get('executive_summary', '—')}")

confidence = rec_dict.get("confidence", 0.0)
st.caption(f"Confidence: {float(confidence):.0%}")

col_l, col_r = st.columns(2)

with col_l:
    st.subheader("🔴 Top Risks")
    for risk in rec_dict.get("top_risks", []):
        with st.expander(f"**{risk.get('risk', '?')}**"):
            st.markdown(f"**Impact**: {risk.get('impact', '—')}")
            st.markdown(f"**Evidence**: {risk.get('evidence', '—')}")
            st.markdown(f"**Owner**: {risk.get('owner', '—')}")
            st.markdown(f"**Next Action**: {risk.get('next_action', '—')}")

    st.subheader("📅 Actions — Next 24 h")
    for a in rec_dict.get("actions_next_24h", []):
        st.markdown(f"- {a}")

with col_r:
    st.subheader("📅 Actions — Next 7 Days")
    for a in rec_dict.get("actions_next_7d", []):
        st.markdown(f"- {a}")

    st.subheader("❓ Vendor Questions")
    for q in rec_dict.get("vendor_questions", []):
        st.markdown(f"- {q}")

st.divider()
col3, col4 = st.columns(2)

with col3:
    st.subheader("🏗️ OT Signals")
    for sig in rec_dict.get("ot_signals", []):
        st.markdown(f"- {sig}")

    st.subheader("🎫 Ticketing Signals")
    for sig in rec_dict.get("ticketing_signals", []):
        st.markdown(f"- {sig}")

with col4:
    st.subheader("🔧 Incident Improvements")
    for imp in rec_dict.get("incident_improvements", []):
        st.markdown(f"- {imp}")

    st.subheader("🤝 Vendor Flags")
    for flag in rec_dict.get("vendor_flags", []):
        st.markdown(f"- {flag}")

st.divider()
col_kpi, col_assume = st.columns(2)

with col_kpi:
    st.subheader("📈 KPIs to Watch")
    for k in rec_dict.get("kpis_to_watch", []):
        st.markdown(f"**{k.get('kpi','?')}** — {k.get('reason','—')} *(threshold: {k.get('threshold','—')})*")

with col_assume:
    st.subheader("⚙️ Assumptions")
    for a in rec_dict.get("assumptions", []):
        st.markdown(f"- {a}")

st.divider()
with st.expander("Raw JSON output"):
    st.json(rec_dict)

# Validation badge
errors = rec_schema.validate(rec_dict)
if errors:
    st.error(f"Schema validation errors: {errors}")
else:
    st.success("Output passes schema validation ✓", icon="✅")
