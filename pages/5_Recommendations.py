from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Any

import streamlit as st

from src.data import ensure_data_and_load
from src.recommendations import heuristic
from src.recommendations.service import (
    FINAL_CALL_FAILED_WARNING,
    NO_KEY_WARNING,
    recommend,
    stream_draft_preview,
)
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


def _snapshot_signature(snapshot: dict[str, Any]) -> str:
    serialized = json.dumps(snapshot, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:12]


def _live_signature(snapshot_sig: str, preview_model: str, final_model: str, api_key: str | None) -> str:
    key_sig = hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:12] if api_key else "no-key"
    return f"{snapshot_sig}|{preview_model}|{final_model}|{key_sig}"


def _engine_tone(engine_state: str) -> str:
    return {
        "Live LLM": "OK",
        "Fallback": "WARN",
        "Pending": "WARN",
        "Error": "CRIT",
    }.get(engine_state, "WARN")


def _apply_heuristic_baseline(snapshot: dict[str, Any], *, api_key_available: bool) -> None:
    st.session_state["recommendation_payload"] = heuristic.recommend(snapshot)
    st.session_state["recommendation_source"] = "heuristic_baseline" if api_key_available else "fallback_no_key"
    st.session_state["recommendation_warning"] = None if api_key_available else NO_KEY_WARNING
    st.session_state["recommendation_engine_state"] = "Pending" if api_key_available else "Fallback"
    st.session_state["recommendation_live_refresh_state"] = "queued" if api_key_available else "idle"
    st.session_state["recommendation_requested_at"] = time.time() if api_key_available else None
    st.session_state["draft_preview"] = ""
    st.session_state["draft_notice"] = None


def _queue_live_refresh() -> None:
    st.session_state["recommendation_engine_state"] = "Pending"
    st.session_state["recommendation_live_refresh_state"] = "queued"
    st.session_state["recommendation_requested_at"] = time.time()
    st.session_state["draft_preview"] = ""
    st.session_state["draft_notice"] = None


def _render_engine_banner(engine_state: str, warning: str | None) -> None:
    if engine_state == "Pending":
        st.info(
            "The page is already showing the instant deterministic authoritative baseline. "
            "A live OpenAI refresh is queued in the background."
        )
    elif engine_state == "Live LLM":
        st.success("The final authoritative panels and exports are currently backed by a live OpenAI result.")
    elif engine_state == "Error":
        st.error(warning or "The live recommendation pipeline failed before a new authoritative result could be applied.")
    elif warning:
        st.warning(warning)


configure_page("Recommendations")
render_page_header(
    "Recommendations",
    "Show the authoritative recommendation set immediately from the deterministic baseline, then refresh it from OpenAI when a key is available.",
)

try:
    data = ensure_data_and_load()
except Exception as exc:
    st.error(f"Data load failed: {exc}")
    st.stop()

snapshot = build_snapshot(data)
snapshot_sig = _snapshot_signature(snapshot)

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

api_key = _resolve_api_key()
current_live_sig = _live_signature(snapshot_sig, preview_model, final_model, api_key)

if "recommendation_payload" not in st.session_state:
    _apply_heuristic_baseline(snapshot, api_key_available=bool(api_key))
    st.session_state["recommendation_snapshot_sig"] = snapshot_sig
    st.session_state["recommendation_live_sig"] = current_live_sig
elif st.session_state.get("recommendation_snapshot_sig") != snapshot_sig:
    _apply_heuristic_baseline(snapshot, api_key_available=bool(api_key))
    st.session_state["recommendation_snapshot_sig"] = snapshot_sig
    st.session_state["recommendation_live_sig"] = current_live_sig
elif st.session_state.get("recommendation_live_sig") != current_live_sig:
    st.session_state["recommendation_live_sig"] = current_live_sig
    if api_key:
        _queue_live_refresh()
    else:
        _apply_heuristic_baseline(snapshot, api_key_available=False)

payload = st.session_state["recommendation_payload"]
engine_state = str(st.session_state.get("recommendation_engine_state", "Fallback"))

render_status_badges(
    [
        {
            "label": "Recommendation engine",
            "value": engine_state,
            "status": _engine_tone(engine_state),
        }
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

refresh_label = "Refresh live recommendations" if api_key else "Refresh heuristic recommendations"
if st.button(refresh_label, type="primary"):
    if api_key:
        _queue_live_refresh()
    else:
        _apply_heuristic_baseline(snapshot, api_key_available=False)
    st.rerun()


@st.fragment(run_every=2)
def _live_refresh_worker() -> None:
    if not api_key:
        return

    if st.session_state.get("recommendation_live_refresh_state") != "queued":
        return

    requested_at = float(st.session_state.get("recommendation_requested_at") or 0.0)
    if time.time() - requested_at < 1.0:
        st.caption("Live OpenAI refresh is queued.")
        return

    st.session_state["recommendation_live_refresh_state"] = "running"

    try:
        with st.status("Live OpenAI refresh", expanded=True) as status:
            status.write("Streaming Draft / Preview from the fast model.")
            preview_text = ""
            preview_placeholder = st.empty()
            try:
                for chunk in stream_draft_preview(
                    snapshot,
                    api_key=api_key,
                    preview_model=preview_model,
                ):
                    preview_text += chunk
                    preview_placeholder.markdown(f"#### Draft / Preview\n\n{preview_text}")
                if preview_text.strip():
                    st.session_state["draft_preview"] = preview_text
                    st.session_state["draft_notice"] = None
            except Exception as exc:
                st.session_state["draft_preview"] = ""
                st.session_state["draft_notice"] = (
                    f"Draft / Preview was unavailable ({type(exc).__name__}). The final authoritative refresh continued."
                )

            status.write("Validating the final authoritative JSON.")
            payload, warning, source = recommend(snapshot, api_key=api_key, final_model=final_model)

            st.session_state["recommendation_payload"] = payload
            st.session_state["recommendation_warning"] = warning
            st.session_state["recommendation_source"] = source
            st.session_state["recommendation_live_refresh_state"] = "done"

            if source == "openai_final":
                st.session_state["recommendation_engine_state"] = "Live LLM"
                status.update(label="Live OpenAI refresh complete", state="complete", expanded=False)
            else:
                st.session_state["recommendation_engine_state"] = "Fallback"
                status.update(label="Live OpenAI refresh fell back to the deterministic baseline", state="error", expanded=True)
    except Exception as exc:  # pragma: no cover - defensive UI safeguard
        st.session_state["recommendation_engine_state"] = "Error"
        st.session_state["recommendation_warning"] = (
            f"Live OpenAI refresh failed before a new authoritative result could be applied ({type(exc).__name__}). "
            f"The page is still showing the deterministic baseline. {FINAL_CALL_FAILED_WARNING}"
        )
        st.session_state["recommendation_source"] = "fallback_error"
        st.session_state["recommendation_live_refresh_state"] = "failed"

    st.rerun()


_live_refresh_worker()

payload = st.session_state["recommendation_payload"]
engine_state = str(st.session_state.get("recommendation_engine_state", "Fallback"))
warning = st.session_state.get("recommendation_warning")
_render_engine_banner(engine_state, warning)

if st.session_state.get("draft_preview"):
    render_section_header("Draft / Preview", "Fast, non-authoritative text streamed from the preview model.")
    st.markdown(st.session_state["draft_preview"])
if st.session_state.get("draft_notice"):
    st.info(st.session_state["draft_notice"])

render_section_header(
    "Final authoritative recommendations",
    "This structured JSON is the only output used for panels and export.",
)
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
