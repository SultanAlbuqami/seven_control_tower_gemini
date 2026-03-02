"""Tests for src/recommendations/heuristic.py"""
from __future__ import annotations

import pytest

from src.recommendations import heuristic
from src.recommendations.schema import is_valid, validate


# ── snapshot fixtures ─────────────────────────────────────────────────────────

def _empty_snapshot() -> dict:
    return {
        "readiness": {"red_gate_count": 0, "top_blockers": [], "service_ranking": []},
        "evidence": {"missing_count": 0, "missing_top": []},
        "incidents": {"open_count": 0, "open_sev1_2": 0, "mtta_min": None, "mttr_min": None, "open_top": []},
        "vendors": {"breach_vendors": []},
    }


def _critical_snapshot() -> dict:
    s = _empty_snapshot()
    s["readiness"]["red_gate_count"] = 8
    s["readiness"]["top_blockers"] = [
        {"service": "Ticketing", "gate": "G1", "blocker": "Vendor fix pending"},
        {"service": "Entry Gates", "gate": "G2", "blocker": "Retest required"},
    ]
    s["evidence"]["missing_count"] = 25
    s["incidents"]["open_sev1_2"] = 3
    s["vendors"]["breach_vendors"] = [
        {"vendor": "Vendor-TIX", "service": "Ticketing", "breach_count": 2}
    ]
    return s


# ── output schema compliance ──────────────────────────────────────────────────

def test_heuristic_empty_snapshot_valid_schema():
    result = heuristic.recommend(_empty_snapshot())
    errors = validate(result)
    assert errors == [], f"Schema errors: {errors}"


def test_heuristic_critical_snapshot_valid_schema():
    result = heuristic.recommend(_critical_snapshot())
    errors = validate(result)
    assert errors == [], f"Schema errors: {errors}"


def test_heuristic_is_valid_shortcut():
    for snap in (_empty_snapshot(), _critical_snapshot()):
        assert is_valid(heuristic.recommend(snap))


# ── confidence heuristic ──────────────────────────────────────────────────────

def test_confidence_lower_when_critical():
    low = heuristic.recommend(_empty_snapshot())
    high_risk = heuristic.recommend(_critical_snapshot())
    assert high_risk["confidence"] < low["confidence"], (
        "Critical snapshot should produce lower confidence"
    )


def test_confidence_within_bounds():
    for snap in (_empty_snapshot(), _critical_snapshot()):
        conf = heuristic.recommend(snap)["confidence"]
        assert 0.0 <= conf <= 1.0, f"confidence {conf} out of [0,1]"


# ── content checks ────────────────────────────────────────────────────────────

def test_empty_snapshot_summary_is_positive():
    result = heuristic.recommend(_empty_snapshot())
    assert "GREEN" in result["executive_summary"] or "nominal" in result["executive_summary"].lower() or "sign" in result["executive_summary"].lower()


def test_critical_snapshot_summary_mentions_critical():
    result = heuristic.recommend(_critical_snapshot())
    summary = result["executive_summary"].upper()
    assert "CRITICAL" in summary or "RISK" in summary or "RED" in summary


def test_top_risks_non_empty_when_critical():
    result = heuristic.recommend(_critical_snapshot())
    assert len(result["top_risks"]) >= 1


def test_actions_24h_non_empty():
    for snap in (_empty_snapshot(), _critical_snapshot()):
        result = heuristic.recommend(snap)
        assert len(result["actions_next_24h"]) >= 1, "actions_next_24h should not be empty"


def test_kpis_to_watch_all_have_threshold():
    result = heuristic.recommend(_empty_snapshot())
    for k in result["kpis_to_watch"]:
        assert k.get("threshold"), f"KPI {k.get('kpi')} missing threshold"


def test_missing_evidence_mentioned_in_risks():
    s = _empty_snapshot()
    s["evidence"]["missing_count"] = 15
    result = heuristic.recommend(s)
    risk_texts = " ".join(r["risk"] for r in result["top_risks"])
    assert "evidence" in risk_texts.lower() or "missing" in risk_texts.lower()


def test_vendor_breach_mentioned_in_risks():
    s = _empty_snapshot()
    s["vendors"]["breach_vendors"] = [{"vendor": "V1", "service": "S1", "breach_count": 1}]
    result = heuristic.recommend(s)
    risk_texts = " ".join(r["risk"] for r in result["top_risks"])
    assert "vendor" in risk_texts.lower() or "breach" in risk_texts.lower() or "sla" in risk_texts.lower()
