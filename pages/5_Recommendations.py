from __future__ import annotations

import json
import os
from typing import Any

import streamlit as st

from src.data import ensure_data_and_load
from src.recommendations.service import recommend, stream_draft_preview
from src.recommendations.snapshot import build_snapshot
from src.ui import (
    configure_page,
    render_download_buttons,
    render_kpi_cards,
    render_page_header,
    render_section_header,
    render_status_badges,
)


def _resolve_api_key() -> str | None:
    try:
        if "OPENAI_API_KEY" in st.secrets:
            secret_value = str(st.secrets["OPENAI_API_KEY"]).strip()
            if secret_value:
                return secret_value
    except Exception:
        pass

    env_value = os.environ.get("OPENAI_API_KEY", "").strip()
    if env_value:
        return env_value

    session_value = str(st.session_state.get("openai_session_key", "")).strip()
    return session_value or None


def _render_signal_list(items: list[dict[str, Any]], primary_key: str) -> None:
    if not items:
        st.caption("No items.")
        return
    for item in items:
        label = item.get(primary_key, "")
        status = str(item.get("status", "OK")).upper()
        detail = item.get("detail", item.get("impact", ""))
        owner = item.get("owner")
        trace_refs = item.get("trace_refs", [])
        st.markdown(f"**{label}**")
        st.caption(f"{status} | {detail}")
        if owner:
            st.caption(f"Owner: {owner}")
        if trace_refs:
            st.code(", ".join(str(value) for value in trace_refs), language="text")


configure_page("Recommendations")
render_page_header(
    "Recommendations",
    "Generate a Draft preview from a fast OpenAI model and then a Final authoritative recommendation set in strict JSON. The final JSON is the only structured output used by the page and exports.",
)

try:
    data = ensure_data_and_load()
except Exception as exc:
    st.error(f"Data load failed: {exc}")
    st.stop()

snapshot = build_snapshot(data)
api_key = _resolve_api_key()

with st.sidebar:
    st.markdown("#### Recommendation settings")
    st.caption("Key lookup order: Streamlit secrets, then environment variable, then the session-only field below.")
    st.text_input(
        "Session-only OPENAI_API_KEY",
        key="openai_session_key",
        type="password",
        help="Stored in this browser session only and never written to disk.",
    )
    preview_model = st.selectbox(
        "Draft preview model",
        ["gpt-4.1-mini", "gpt-4.1"],
        index=0,
    )
    final_model = st.selectbox(
        "Final authoritative model",
        ["gpt-4.1", "gpt-4.1-mini"],
        index=0,
    )

render_status_badges(
    [
        {"label": "Draft preview", "status": "OK" if api_key else "WARN"},
        {"label": "Final JSON", "status": "OK" if api_key else "WARN"},
        {"label": "Offline fallback", "status": "OK"},
    ]
)
render_kpi_cards(
    [
        {
            "title": "RED gates",
            "value": snapshot["readiness"]["red_gate_count"],
            "subtitle": "Primary launch gating signal in the final recommendation set.",
            "status": "CRIT" if snapshot["readiness"]["red_gate_count"] else "OK",
        },
        {
            "title": "Missing evidence",
            "value": snapshot["evidence"]["missing_count"],
            "subtitle": "Document-control debt included in the recommendation snapshot.",
            "status": "WARN" if snapshot["evidence"]["missing_count"] else "OK",
        },
        {
            "title": "Open Sev-1/2 incidents",
            "value": snapshot["incidents"]["open_sev1_2"],
            "subtitle": "Critical incident volume feeding the recommendation engine.",
            "status": "CRIT" if snapshot["incidents"]["open_sev1_2"] else "OK",
        },
        {
            "title": "Ticketing anomaly windows",
            "value": snapshot["ticketing_signals"]["anomaly_windows"],
            "subtitle": "Guest-entry performance signal feeding the recommendation engine.",
            "status": "WARN" if snapshot["ticketing_signals"]["anomaly_windows"] else "OK",
        },
    ]
)

if "recommendation_payload" not in st.session_state:
    st.session_state["recommendation_payload"] = None
    st.session_state["recommendation_source"] = None
    st.session_state["recommendation_warning"] = None
    st.session_state["draft_preview"] = ""
    st.session_state["draft_notice"] = None

run = st.button("Generate recommendations", type="primary")
if run:
    st.session_state["draft_preview"] = ""
    st.session_state["draft_notice"] = None
    preview_placeholder = st.empty()

    if api_key:
        preview_text = ""
        try:
            with st.spinner("Streaming Draft / Preview..."):
                for chunk in stream_draft_preview(
                    snapshot,
                    api_key=api_key,
                    preview_model=preview_model,
                ):
                    preview_text += chunk
                    preview_placeholder.markdown(f"#### Draft / Preview\n\n{preview_text}")
            st.session_state["draft_preview"] = preview_text
        except Exception as exc:
            st.session_state["draft_notice"] = (
                f"Draft / Preview was unavailable ({type(exc).__name__}). Proceeding directly to the final authoritative result."
            )
    else:
        st.session_state["draft_notice"] = (
            "No API key is available, so Draft / Preview streaming is skipped and the page will use deterministic heuristic logic."
        )

    with st.spinner("Generating Final authoritative recommendations..."):
        payload, warning, source = recommend(snapshot, api_key=api_key, final_model=final_model)
    st.session_state["recommendation_payload"] = payload
    st.session_state["recommendation_warning"] = warning
    st.session_state["recommendation_source"] = source

if st.session_state["draft_preview"]:
    render_section_header("Draft / Preview", "Fast, non-authoritative text streamed from the preview model.")
    st.markdown(st.session_state["draft_preview"])
if st.session_state["draft_notice"]:
    st.info(st.session_state["draft_notice"])

payload = st.session_state["recommendation_payload"]
if payload is None:
    st.info("Click Generate recommendations to produce the Draft preview and the Final authoritative recommendation set.")
    st.stop()

render_section_header("Final authoritative recommendations", "This structured JSON is the only output used for panels and export.")
render_status_badges(
    [
        {"label": "Result source", "status": "OK" if st.session_state["recommendation_source"] == "openai_final" else "WARN"},
        {"label": "Overall posture", "status": payload["summary"]["status"]},
    ]
)
if st.session_state["recommendation_warning"]:
    st.warning(st.session_state["recommendation_warning"])

summary = payload["summary"]
st.markdown(f"### {summary['headline']}")
st.caption(
    f"Status: {summary['status']} | Go/No-Go: {summary['go_no_go']} | Confidence: {summary['confidence']:.0%}"
)
st.markdown("\n".join(f"- {line}" for line in summary["rationale"]))

top_left, top_right = st.columns(2)
with top_left:
    render_section_header("Top risks", "These are the talking points to keep in the interview script.")
    _render_signal_list(payload["top_risks"], "title")
with top_right:
    render_section_header("Next actions", "The final JSON is structured so the actions can be exported cleanly.")
    _render_signal_list(payload["next_actions"], "action")

mid_left, mid_right = st.columns(2)
with mid_left:
    render_section_header("Incident improvements", "Operational discipline improvements grounded in the current snapshot.")
    _render_signal_list(payload["incident_improvements"], "title")
with mid_right:
    render_section_header("Vendor flags", "Supplier accountability and penalty exposure.")
    _render_signal_list(payload["vendor_flags"], "vendor")

bottom_left, bottom_right = st.columns(2)
with bottom_left:
    render_section_header("OT signals", "Live alarm conditions and control-room follow-up.")
    _render_signal_list(payload["ot_signals"], "signal")
with bottom_right:
    render_section_header("Ticketing signals", "Guest-entry performance conditions included in the final result.")
    _render_signal_list(payload["ticketing_signals"], "signal")

render_download_buttons(
    [
        {
            "label": "Download final JSON",
            "data": json.dumps(payload, indent=2).encode("utf-8"),
            "file_name": "recommendations_final.json",
            "mime": "application/json",
        },
        {
            "label": "Download snapshot JSON",
            "data": json.dumps(snapshot, indent=2).encode("utf-8"),
            "file_name": "recommendations_snapshot.json",
            "mime": "application/json",
        },
    ]
)

with st.expander("Final authoritative JSON"):
    st.json(payload)
