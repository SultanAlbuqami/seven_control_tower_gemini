"""Tests for src/recommendations/schema.py"""
from __future__ import annotations

import pytest

from src.recommendations.schema import validate, is_valid, REQUIRED_KEYS


# ── helpers ───────────────────────────────────────────────────────────────────

def _valid_rec() -> dict:
    """Minimal valid recommendation dict."""
    return {
        "executive_summary": "All systems nominal.",
        "top_risks": [
            {
                "risk": "Test risk",
                "impact": "Low",
                "evidence": "None",
                "owner": "Ops Lead",
                "next_action": "Monitor",
            }
        ],
        "actions_next_24h": ["Action A"],
        "actions_next_7d": ["Action B"],
        "vendor_questions": ["Question 1"],
        "kpis_to_watch": [
            {"kpi": "Entry Queue", "reason": "Bottleneck", "threshold": "< 8 min"}
        ],
        "assumptions": ["Dataset is synthetic"],
        "confidence": 0.75,
        "ot_signals": ["All OT systems nominal"],
        "ticketing_signals": ["Scan success rate within bounds"],
        "incident_improvements": ["Reduce Sev-1 target to 15 min"],
        "vendor_flags": ["No vendor breaches"],
    }


# ── passing cases ─────────────────────────────────────────────────────────────

def test_valid_dict_passes():
    assert is_valid(_valid_rec())
    assert validate(_valid_rec()) == []


def test_empty_arrays_are_valid():
    rec = _valid_rec()
    rec["top_risks"] = []
    rec["actions_next_24h"] = []
    assert is_valid(rec)


def test_confidence_boundaries():
    for val in (0.0, 0.5, 1.0):
        rec = _valid_rec()
        rec["confidence"] = val
        assert is_valid(rec), f"Expected valid for confidence={val}"


# ── failing cases ─────────────────────────────────────────────────────────────

def test_non_dict_fails():
    errors = validate("not a dict")
    assert errors


def test_missing_required_key():
    rec = _valid_rec()
    del rec["executive_summary"]
    errors = validate(rec)
    assert any("executive_summary" in e for e in errors)


def test_confidence_out_of_range():
    rec = _valid_rec()
    rec["confidence"] = 1.5
    errors = validate(rec)
    assert any("confidence" in e for e in errors)


def test_top_risks_not_list():
    rec = _valid_rec()
    rec["top_risks"] = "should be a list"
    errors = validate(rec)
    assert any("top_risks" in e for e in errors)


def test_top_risk_missing_key():
    rec = _valid_rec()
    rec["top_risks"] = [{"risk": "X"}]  # missing impact, evidence, owner, next_action
    errors = validate(rec)
    assert any("top_risks[0]" in e for e in errors)


def test_kpis_to_watch_missing_key():
    rec = _valid_rec()
    rec["kpis_to_watch"] = [{"kpi": "X"}]  # missing reason, threshold
    errors = validate(rec)
    assert any("kpis_to_watch[0]" in e for e in errors)


def test_actions_must_be_list():
    for key in ("actions_next_24h", "actions_next_7d", "vendor_questions", "assumptions"):
        rec = _valid_rec()
        rec[key] = "not a list"
        errors = validate(rec)
        assert any(key in e for e in errors), f"Expected error for {key}=str"


def test_all_required_keys_covered():
    """Ensure REQUIRED_KEYS matches the valid schema dict."""
    rec = _valid_rec()
    assert REQUIRED_KEYS.issubset(rec.keys())
