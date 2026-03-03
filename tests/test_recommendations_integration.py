from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from src.recommendations import service as rec_service
from src.recommendations.schema import is_valid


def _minimal_snapshot() -> dict:
    return {
        "readiness": {"red_gate_count": 2, "amber_gate_count": 1, "green_gate_count": 3, "hold_count": 2, "top_blockers": [], "service_ranking": []},
        "evidence": {"missing_count": 5, "completion_rate": 0.82, "missing_top": [], "owners": []},
        "incidents": {"open_count": 1, "open_sev1_2": 1, "mtta_min": 12.0, "mttr_min": 80.0, "sla_breaches": 1, "open_top": []},
        "vendors": {"breach_count": 1, "high_penalty_risk": 0, "service_credits": 0, "breach_vendors": []},
        "ot_signals": {"unacked_sev1": 0, "unacked_sev2": 1, "total_open": 2, "mean_ack_min": 7.0, "clusters": [], "top_open_events": []},
        "ticketing_signals": {"anomaly_windows": 1, "min_success_rate": 0.96, "max_latency_p95": 750.0, "total_offline_fallbacks": 0, "total_denied": 3, "throughput_collapses": 0, "payment_dependency_windows": 0, "worst_areas": []},
    }


def _valid_openai_json() -> str:
    return json.dumps(
        {
            "summary": {
                "headline": "Mocked final summary",
                "status": "WARN",
                "go_no_go": "HOLD",
                "confidence": 0.78,
                "rationale": ["Mocked rationale"],
            },
            "top_risks": [
                {
                    "title": "Mock risk",
                    "status": "WARN",
                    "impact": "High",
                    "owner": "Ops Lead",
                    "evidence": "Mock evidence",
                    "trace_refs": ["incident_id:INC-0001"],
                }
            ],
            "next_actions": [
                {
                    "window": "0-24h",
                    "owner": "Ops Lead",
                    "action": "Mock action",
                    "expected_outcome": "Mock outcome",
                    "trace_refs": [],
                }
            ],
            "incident_improvements": [
                {
                    "title": "Improve MTTA",
                    "status": "WARN",
                    "detail": "Mock detail",
                    "metric": "MTTA",
                }
            ],
            "vendor_flags": [
                {
                    "vendor": "Mock vendor",
                    "status": "WARN",
                    "detail": "Mock detail",
                    "trace_refs": [],
                }
            ],
            "ot_signals": [
                {
                    "signal": "Mock OT signal",
                    "status": "WARN",
                    "detail": "Mock detail",
                    "trace_refs": [],
                }
            ],
            "ticketing_signals": [
                {
                    "signal": "Mock ticketing signal",
                    "status": "WARN",
                    "detail": "Mock detail",
                    "trace_refs": [],
                }
            ],
        }
    )


def test_no_key_returns_heuristic() -> None:
    with patch.dict("os.environ", {}, clear=False):
        import os

        os.environ.pop("OPENAI_API_KEY", None)
        result, warning, source = rec_service.recommend(_minimal_snapshot(), api_key=None)

    assert is_valid(result)
    assert warning is not None
    assert source == "heuristic"


def test_valid_openai_response_returned() -> None:
    with patch("src.recommendations.service.openai_adapter.request_final_json", return_value=_valid_openai_json()):
        result, warning, source = rec_service.recommend(_minimal_snapshot(), api_key="fake-api-key")

    assert is_valid(result)
    assert warning is None
    assert source == "openai_final"
    assert result["summary"]["headline"] == "Mocked final summary"


def test_invalid_openai_json_triggers_fallback() -> None:
    with patch("src.recommendations.service.openai_adapter.request_final_json", return_value="not valid json"):
        result, warning, source = rec_service.recommend(_minimal_snapshot(), api_key="fake-api-key")

    assert is_valid(result)
    assert warning is not None
    assert source == "heuristic"


def test_schema_invalid_openai_json_can_be_repaired() -> None:
    legacy = json.dumps(
        {
            "executive_summary": "Legacy summary",
            "top_risks": [{"risk": "Risk", "impact": "High", "owner": "Ops", "evidence": "Proof", "next_action": "Act"}],
            "actions_next_24h": ["Do the thing"],
            "incident_improvements": ["Improve MTTA"],
            "vendor_flags": ["Vendor issue"],
            "ot_signals": ["OT issue"],
            "ticketing_signals": ["Ticketing issue"],
        }
    )
    with patch("src.recommendations.service.openai_adapter.request_final_json", return_value=legacy):
        result, warning, source = rec_service.recommend(_minimal_snapshot(), api_key="fake-api-key")

    assert is_valid(result)
    assert warning is None
    assert source == "openai_final"


def test_openai_api_exception_triggers_fallback() -> None:
    with patch(
        "src.recommendations.service.openai_adapter.request_final_json",
        side_effect=RuntimeError("Simulated network error"),
    ):
        result, warning, source = rec_service.recommend(_minimal_snapshot(), api_key="fake-api-key")

    assert is_valid(result)
    assert warning is not None
    assert source == "heuristic"


def test_service_never_raises_on_bad_key() -> None:
    with patch(
        "src.recommendations.service.openai_adapter.request_final_json",
        side_effect=Exception("Auth failed"),
    ):
        try:
            result, warning, source = rec_service.recommend(_minimal_snapshot(), api_key="garbage-key")
            assert is_valid(result)
            assert source == "heuristic"
        except Exception as exc:  # pragma: no cover
            pytest.fail(f"service.recommend raised unexpectedly: {exc}")


def test_stream_draft_preview_requires_key() -> None:
    with patch.dict("os.environ", {}, clear=False):
        import os

        os.environ.pop("OPENAI_API_KEY", None)
        with pytest.raises(RuntimeError):
            list(rec_service.stream_draft_preview(_minimal_snapshot(), api_key=None))
