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
        "ot_events": {"unacked_sev1": 0, "unacked_sev2": 0, "total_open": 0, "clusters": []},
        "ticketing": {"anomaly_windows": 0, "min_success_rate": 0.99, "max_latency_p95": 400, "total_offline_fallbacks": 0, "total_denied": 0},
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
    s["ot_events"] = {"unacked_sev1": 2, "unacked_sev2": 4, "total_open": 10, "clusters": [{"zone": "Zone-A", "subsystem": "BMS", "size": 6}]}
    s["ticketing"] = {"anomaly_windows": 5, "min_success_rate": 0.91, "max_latency_p95": 1800, "total_offline_fallbacks": 3, "total_denied": 12}
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


# ── OT + Ticketing signal sections ───────────────────────────────────────────

def test_ot_signals_always_present():
    for snap in (_empty_snapshot(), _critical_snapshot()):
        result = heuristic.recommend(snap)
        assert isinstance(result.get("ot_signals"), list)
        assert len(result["ot_signals"]) >= 1


def test_ticketing_signals_always_present():
    for snap in (_empty_snapshot(), _critical_snapshot()):
        result = heuristic.recommend(snap)
        assert isinstance(result.get("ticketing_signals"), list)
        assert len(result["ticketing_signals"]) >= 1


def test_ot_sev1_triggers_critical_signal():
    s = _empty_snapshot()
    s["ot_events"] = {"unacked_sev1": 3, "unacked_sev2": 0, "total_open": 3, "clusters": []}
    result = heuristic.recommend(s)
    ot_text = " ".join(result["ot_signals"]).lower()
    assert "sev-1" in ot_text or "sev1" in ot_text or "unacked" in ot_text


def test_ticketing_anomaly_lowers_confidence():
    clean = _empty_snapshot()
    anomalous = _empty_snapshot()
    anomalous["ticketing"] = {"anomaly_windows": 8, "min_success_rate": 0.90, "max_latency_p95": 2000, "total_offline_fallbacks": 5, "total_denied": 20}
    clean_conf = heuristic.recommend(clean)["confidence"]
    anomalous_conf = heuristic.recommend(anomalous)["confidence"]
    assert anomalous_conf <= clean_conf, "Anomalous ticketing should lower or equal confidence"


def test_incident_improvements_always_present():
    for snap in (_empty_snapshot(), _critical_snapshot()):
        result = heuristic.recommend(snap)
        assert isinstance(result.get("incident_improvements"), list)
        assert len(result["incident_improvements"]) >= 1


def test_vendor_flags_always_present():
    for snap in (_empty_snapshot(), _critical_snapshot()):
        result = heuristic.recommend(snap)
        assert isinstance(result.get("vendor_flags"), list)
        assert len(result["vendor_flags"]) >= 1
