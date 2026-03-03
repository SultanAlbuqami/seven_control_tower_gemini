from __future__ import annotations

from src.recommendations.schema import REQUIRED_KEYS, is_valid, repair_response, validate


def _valid_rec() -> dict:
    return {
        "summary": {
            "headline": "Readiness posture is stable.",
            "status": "OK",
            "go_no_go": "GO",
            "confidence": 0.82,
            "rationale": ["No RED gates", "No open Sev-1/2 incidents"],
        },
        "top_risks": [
            {
                "title": "No material blockers detected",
                "status": "OK",
                "impact": "Maintain discipline.",
                "owner": "Ops Lead",
                "evidence": "All signals are within tolerance.",
                "trace_refs": [],
            }
        ],
        "next_actions": [
            {
                "window": "0-24h",
                "owner": "Ops Lead",
                "action": "Run final readiness review.",
                "expected_outcome": "Shared understanding of launch posture.",
                "trace_refs": [],
            }
        ],
        "incident_improvements": [
            {
                "title": "Sustain response discipline",
                "status": "OK",
                "detail": "No immediate MTTA issue.",
                "metric": "MTTA",
            }
        ],
        "vendor_flags": [
            {
                "vendor": "Portfolio view",
                "status": "OK",
                "detail": "No vendor breaches detected.",
                "trace_refs": [],
            }
        ],
        "ot_signals": [
            {
                "signal": "OT feed stable",
                "status": "OK",
                "detail": "No critical alarms.",
                "trace_refs": [],
            }
        ],
        "ticketing_signals": [
            {
                "signal": "Ticketing stable",
                "status": "OK",
                "detail": "No anomaly windows.",
                "trace_refs": [],
            }
        ],
    }


def test_valid_dict_passes() -> None:
    assert is_valid(_valid_rec())
    assert validate(_valid_rec()) == []


def test_empty_arrays_are_valid() -> None:
    rec = _valid_rec()
    rec["top_risks"] = []
    rec["next_actions"] = []
    assert is_valid(rec)


def test_confidence_boundaries() -> None:
    for value in (0.0, 0.5, 1.0):
        rec = _valid_rec()
        rec["summary"]["confidence"] = value
        assert is_valid(rec)


def test_non_dict_fails() -> None:
    assert validate("not a dict")


def test_missing_required_key() -> None:
    rec = _valid_rec()
    del rec["summary"]
    errors = validate(rec)
    assert any("summary" in error for error in errors)


def test_summary_confidence_out_of_range() -> None:
    rec = _valid_rec()
    rec["summary"]["confidence"] = 1.4
    errors = validate(rec)
    assert any("confidence" in error for error in errors)


def test_top_risks_not_list() -> None:
    rec = _valid_rec()
    rec["top_risks"] = "bad"
    errors = validate(rec)
    assert any("top_risks" in error for error in errors)


def test_top_risk_missing_key() -> None:
    rec = _valid_rec()
    rec["top_risks"] = [{"title": "Risk only"}]
    errors = validate(rec)
    assert any("top_risks[0]" in error for error in errors)


def test_status_must_be_valid() -> None:
    rec = _valid_rec()
    rec["vendor_flags"][0]["status"] = "BAD"
    errors = validate(rec)
    assert any("vendor_flags[0].status" in error for error in errors)


def test_repair_response_handles_legacy_shape() -> None:
    repaired = repair_response(
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
    assert repaired is not None
    assert is_valid(repaired)
    assert repaired["summary"]["headline"] == "Legacy summary"


def test_all_required_keys_covered() -> None:
    rec = _valid_rec()
    assert REQUIRED_KEYS.issubset(rec.keys())
