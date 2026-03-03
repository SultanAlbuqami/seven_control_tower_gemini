"""Integration tests for src/recommendations/service.py with mocked Groq.

Groq SDK is fully mocked — no network calls are made.
"""
from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import pytest

from src.recommendations import service as rec_service
from src.recommendations.schema import is_valid


# ── fixture ───────────────────────────────────────────────────────────────────

def _minimal_snapshot() -> dict:
    return {
        "readiness": {"red_gate_count": 2, "top_blockers": [], "service_ranking": []},
        "evidence": {"missing_count": 5, "missing_top": []},
        "incidents": {"open_count": 1, "open_sev1_2": 1, "mtta_min": 12.0, "mttr_min": 80.0, "open_top": []},
        "vendors": {"breach_vendors": []},
        "ot_events": {"unacked_sev1": 0, "unacked_sev2": 1, "total_open": 2, "clusters": []},
        "ticketing": {"anomaly_windows": 1, "min_success_rate": 0.96, "max_latency_p95": 750, "total_offline_fallbacks": 0, "total_denied": 3},
    }


def _valid_groq_json() -> str:
    return json.dumps({
        "executive_summary": "Mocked executive summary",
        "top_risks": [
            {
                "risk": "Mock risk",
                "impact": "High",
                "evidence": "Mock evidence",
                "owner": "Test Lead",
                "next_action": "Mock action",
            }
        ],
        "actions_next_24h": ["Action 1"],
        "actions_next_7d": ["Action 7d"],
        "vendor_questions": ["Q1"],
        "kpis_to_watch": [
            {"kpi": "Entry Queue", "reason": "Bottleneck", "threshold": "< 8 min"}
        ],
        "assumptions": ["This is mocked"],
        "confidence": 0.9,
        "ot_signals": ["All OT systems nominal"],
        "ticketing_signals": ["Scan success rate within bounds"],
        "incident_improvements": ["Improve Sev-1 ack time target to < 15 min"],
        "vendor_flags": ["No vendor breaches detected"],
    })


# ── no-key fallback ───────────────────────────────────────────────────────────

def test_no_key_returns_heuristic():
    """When no API key is available, fallback is immediately used."""
    with patch.dict("os.environ", {}, clear=False):
        # Ensure env var is absent for this test
        import os
        os.environ.pop("GROQ_API_KEY", None)
        result, warning = rec_service.recommend(_minimal_snapshot(), api_key=None)

    assert is_valid(result), "Heuristic fallback must produce schema-valid output"
    assert warning is not None, "Warning must be set when using fallback"
    assert "offline" in warning.lower() or "heuristic" in warning.lower()


# ── valid Groq response ──────────────────────────────────────────────────────

def test_valid_groq_response_returned():
    """Mock Groq returning valid JSON → use it directly."""
    valid_json = _valid_groq_json()

    with patch("src.recommendations.service._groq.call_groq_once", return_value=valid_json):
        result, warning = rec_service.recommend(
            _minimal_snapshot(),
            api_key="fake-api-key",
        )

    assert is_valid(result), f"Expected valid schema, got: {result}"
    assert warning is None, "No warning expected when Groq succeeds"
    assert result["executive_summary"] == "Mocked executive summary"


# ── invalid Groq JSON → fallback ─────────────────────────────────────────────

def test_invalid_groq_json_triggers_fallback():
    """Mock Groq returning unparseable garbage → heuristic fallback."""
    with patch("src.recommendations.service._groq.call_groq_once", return_value="not valid json at all {{{{"):
        result, warning = rec_service.recommend(
            _minimal_snapshot(),
            api_key="fake-api-key",
        )

    assert is_valid(result), "Fallback must produce schema-valid output"
    assert warning is not None, "Warning must be set when fallback is used"


# ── schema-invalid Groq JSON → repair attempt → fallback ────────────────────

def test_schema_invalid_groq_json_triggers_fallback():
    """Mock Groq returning valid JSON but wrong schema → parse_and_validate returns None → fallback."""
    bad_schema = json.dumps({"executive_summary": "Missing all other required fields"})

    with patch("src.recommendations.service._groq.call_groq_once", return_value=bad_schema):
        result, warning = rec_service.recommend(
            _minimal_snapshot(),
            api_key="fake-api-key",
        )

    assert is_valid(result), "Fallback must produce schema-valid output"
    assert warning is not None


# ── Groq API exception → fallback ────────────────────────────────────────────

def test_groq_api_exception_triggers_fallback():
    """Mock Groq raising an exception → graceful fallback."""
    with patch(
        "src.recommendations.service._groq.call_groq_once",
        side_effect=RuntimeError("Simulated network error"),
    ):
        result, warning = rec_service.recommend(
            _minimal_snapshot(),
            api_key="fake-api-key",
        )

    assert is_valid(result), "Fallback must produce schema-valid output"
    assert warning is not None


# ── service never raises ──────────────────────────────────────────────────────

def test_service_never_raises_on_bad_key():
    """Even with garbage key + mocked exception, service must not raise."""
    with patch(
        "src.recommendations.service._groq.call_groq_once",
        side_effect=Exception("Auth failed"),
    ):
        try:
            result, warning = rec_service.recommend(
                _minimal_snapshot(),
                api_key="garbage-key",
            )
            assert is_valid(result)
        except Exception as e:
            pytest.fail(f"service.recommend raised unexpectedly: {e}")
