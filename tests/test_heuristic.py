from __future__ import annotations

from src.recommendations import heuristic
from src.recommendations.schema import is_valid, validate


def _empty_snapshot() -> dict:
    return {
        "readiness": {"red_gate_count": 0, "amber_gate_count": 0, "green_gate_count": 5, "hold_count": 0, "top_blockers": [], "service_ranking": []},
        "evidence": {"missing_count": 0, "completion_rate": 1.0, "missing_top": [], "owners": []},
        "incidents": {"open_count": 0, "open_sev1_2": 0, "mtta_min": 8.0, "mttr_min": 60.0, "sla_breaches": 0, "open_top": []},
        "vendors": {"breach_count": 0, "high_penalty_risk": 0, "service_credits": 0, "breach_vendors": []},
        "ot_signals": {"unacked_sev1": 0, "unacked_sev2": 0, "total_open": 0, "mean_ack_min": 4.0, "clusters": [], "top_open_events": []},
        "ticketing_signals": {"anomaly_windows": 0, "min_success_rate": 0.99, "max_latency_p95": 400.0, "total_offline_fallbacks": 0, "total_denied": 0, "throughput_collapses": 0, "payment_dependency_windows": 0, "worst_areas": []},
    }


def _critical_snapshot() -> dict:
    snapshot = _empty_snapshot()
    snapshot["readiness"]["red_gate_count"] = 6
    snapshot["readiness"]["amber_gate_count"] = 4
    snapshot["readiness"]["hold_count"] = 6
    snapshot["readiness"]["top_blockers"] = [
        {"service": "Ticketing", "gate": "G2", "source_system": "ORR Tracker (example)"},
    ]
    snapshot["evidence"]["missing_count"] = 18
    snapshot["evidence"]["missing_top"] = [{"evidence_id": "EVD-0012", "doc_ref": "DOC-ORR-00012", "service": "Ticketing"}]
    snapshot["incidents"]["open_sev1_2"] = 2
    snapshot["incidents"]["open_count"] = 4
    snapshot["incidents"]["open_top"] = [{"incident_id": "INC-0001", "source_id": "INC0012345", "service": "Ticketing"}]
    snapshot["vendors"]["breach_count"] = 2
    snapshot["vendors"]["high_penalty_risk"] = 1
    snapshot["vendors"]["breach_vendors"] = [{"vendor": "Vendor-TIX", "service": "Ticketing", "breach_count": 2, "dashboard_ref": "DASH-00012"}]
    snapshot["ot_signals"] = {
        "unacked_sev1": 1,
        "unacked_sev2": 3,
        "total_open": 11,
        "mean_ack_min": 18.0,
        "clusters": [{"zone": "Zone-A", "subsystem": "BMS", "size": 4}],
        "top_open_events": [{"ot_event_id": "EVT-OT-000101", "device_id": "DEV-OT-000111", "linked_incident_id": "INC-0001"}],
    }
    snapshot["ticketing_signals"] = {
        "anomaly_windows": 9,
        "min_success_rate": 0.91,
        "max_latency_p95": 1800.0,
        "total_offline_fallbacks": 4,
        "total_denied": 15,
        "throughput_collapses": 5,
        "payment_dependency_windows": 2,
        "worst_areas": [{"venue_area": "Main Gate"}],
    }
    return snapshot


def test_heuristic_empty_snapshot_valid_schema() -> None:
    result = heuristic.recommend(_empty_snapshot())
    assert validate(result) == []


def test_heuristic_critical_snapshot_valid_schema() -> None:
    result = heuristic.recommend(_critical_snapshot())
    assert validate(result) == []


def test_heuristic_is_valid_shortcut() -> None:
    assert is_valid(heuristic.recommend(_empty_snapshot()))
    assert is_valid(heuristic.recommend(_critical_snapshot()))


def test_confidence_lower_when_critical() -> None:
    clean_confidence = heuristic.recommend(_empty_snapshot())["summary"]["confidence"]
    critical_confidence = heuristic.recommend(_critical_snapshot())["summary"]["confidence"]
    assert critical_confidence < clean_confidence


def test_confidence_within_bounds() -> None:
    for snapshot in (_empty_snapshot(), _critical_snapshot()):
        confidence = heuristic.recommend(snapshot)["summary"]["confidence"]
        assert 0.0 <= confidence <= 1.0


def test_empty_snapshot_summary_is_positive() -> None:
    headline = heuristic.recommend(_empty_snapshot())["summary"]["headline"].lower()
    assert "track" in headline or "stable" in headline or "no immediate" in headline


def test_critical_snapshot_summary_mentions_critical() -> None:
    headline = heuristic.recommend(_critical_snapshot())["summary"]["headline"].upper()
    assert "INTERVENTION" in headline or "HOLD" in headline or "BELOW LAUNCH TOLERANCE" in headline


def test_top_risks_non_empty_when_critical() -> None:
    assert len(heuristic.recommend(_critical_snapshot())["top_risks"]) >= 1


def test_next_actions_non_empty() -> None:
    for snapshot in (_empty_snapshot(), _critical_snapshot()):
        assert len(heuristic.recommend(snapshot)["next_actions"]) >= 1


def test_missing_evidence_mentioned_in_risks() -> None:
    snapshot = _empty_snapshot()
    snapshot["evidence"]["missing_count"] = 9
    titles = " ".join(item["title"] for item in heuristic.recommend(snapshot)["top_risks"]).lower()
    assert "evidence" in titles or "missing" in titles


def test_vendor_breach_mentioned_in_risks() -> None:
    snapshot = _empty_snapshot()
    snapshot["vendors"]["breach_count"] = 1
    snapshot["vendors"]["breach_vendors"] = [{"vendor": "V1", "service": "S1", "breach_count": 1, "dashboard_ref": "DASH-1"}]
    titles = " ".join(item["title"] for item in heuristic.recommend(snapshot)["top_risks"]).lower()
    assert "vendor" in titles or "breach" in titles or "sla" in titles


def test_ot_signals_always_present() -> None:
    for snapshot in (_empty_snapshot(), _critical_snapshot()):
        assert len(heuristic.recommend(snapshot)["ot_signals"]) >= 1


def test_ticketing_signals_always_present() -> None:
    for snapshot in (_empty_snapshot(), _critical_snapshot()):
        assert len(heuristic.recommend(snapshot)["ticketing_signals"]) >= 1


def test_ot_sev1_triggers_critical_signal() -> None:
    snapshot = _empty_snapshot()
    snapshot["ot_signals"]["unacked_sev1"] = 3
    signals = " ".join(item["signal"] for item in heuristic.recommend(snapshot)["ot_signals"]).lower()
    assert "critical" in signals or "sev-1" in signals


def test_ticketing_anomaly_lowers_confidence() -> None:
    clean_conf = heuristic.recommend(_empty_snapshot())["summary"]["confidence"]
    noisy = _empty_snapshot()
    noisy["ticketing_signals"]["anomaly_windows"] = 8
    noisy["ticketing_signals"]["min_success_rate"] = 0.90
    noisy_conf = heuristic.recommend(noisy)["summary"]["confidence"]
    assert noisy_conf <= clean_conf


def test_incident_improvements_always_present() -> None:
    for snapshot in (_empty_snapshot(), _critical_snapshot()):
        assert len(heuristic.recommend(snapshot)["incident_improvements"]) >= 1


def test_vendor_flags_always_present() -> None:
    for snapshot in (_empty_snapshot(), _critical_snapshot()):
        assert len(heuristic.recommend(snapshot)["vendor_flags"]) >= 1
