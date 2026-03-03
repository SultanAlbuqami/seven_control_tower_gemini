"""Tests for OT event metric aggregators in src/metrics.py"""
from __future__ import annotations

import pandas as pd
import numpy as np
import pytest

from src.metrics import ot_event_summary, compute_ot_mean_ack_minutes


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_ot_events(**overrides) -> pd.DataFrame:
    """Return a minimal OT events DataFrame."""
    now = pd.Timestamp("2025-01-10 10:00:00")
    base = pd.DataFrame(
        [
            {
                "event_id": "EVT-OT-000001",
                "subsystem": "BMS",
                "alarm_type": "HighTemp",
                "zone": "Zone-A",
                "device_id": "DEV-001",
                "severity": 1,
                "event_time": now - pd.Timedelta(hours=3),
                "ack_time": pd.NaT,
                "cleared_time": pd.NaT,
                "status": "OPEN",
                "source_system": "Siemens-BMS",
                "linked_incident_id": "",
            },
            {
                "event_id": "EVT-OT-000002",
                "subsystem": "AccessControl",
                "alarm_type": "ForcedEntry",
                "zone": "Zone-B",
                "device_id": "DEV-002",
                "severity": 2,
                "event_time": now - pd.Timedelta(hours=2),
                "ack_time": pd.NaT,
                "cleared_time": pd.NaT,
                "status": "OPEN",
                "source_system": "CCURE-9000",
                "linked_incident_id": "",
            },
            {
                "event_id": "EVT-OT-000003",
                "subsystem": "CCTV",
                "alarm_type": "CameraOffline",
                "zone": "Zone-A",
                "device_id": "DEV-003",
                "severity": 3,
                "event_time": now - pd.Timedelta(hours=1),
                "ack_time": now - pd.Timedelta(minutes=50),
                "cleared_time": now - pd.Timedelta(minutes=30),
                "status": "CLEARED",
                "source_system": "Milestone-XProtect",
                "linked_incident_id": "",
            },
        ]
    )
    for k, v in overrides.items():
        base[k] = v
    return base


# ── ot_event_summary ──────────────────────────────────────────────────────────

def test_ot_event_summary_empty():
    df = pd.DataFrame(
        columns=["event_id", "severity", "ack_time", "status", "zone", "subsystem"]
    )
    result = ot_event_summary(df)
    assert result["unacked_sev1"] == 0
    assert result["unacked_sev2"] == 0
    assert result["total_open"] == 0
    assert result["clusters"] == []


def test_ot_event_summary_counts_unacked_sev1():
    df = _make_ot_events()
    result = ot_event_summary(df)
    # EVT-OT-000001 is Sev-1 OPEN with NaT ack_time → unacked
    assert result["unacked_sev1"] == 1


def test_ot_event_summary_counts_unacked_sev2():
    df = _make_ot_events()
    result = ot_event_summary(df)
    # EVT-OT-000002 is Sev-2 OPEN with NaT ack_time → unacked
    assert result["unacked_sev2"] == 1


def test_ot_event_summary_total_open():
    df = _make_ot_events()
    result = ot_event_summary(df)
    # EVT-OT-000001 and 000002 are OPEN; 000003 is CLEARED
    assert result["total_open"] == 2


def test_ot_event_summary_cleared_not_counted_unacked():
    df = _make_ot_events()
    result = ot_event_summary(df)
    # Event 3 is cleared sev-3 — should NOT be in unacked_sev1 or sev2
    assert result["unacked_sev1"] == 1
    assert result["unacked_sev2"] == 1


def test_ot_event_summary_clusters_non_empty_when_open():
    df = _make_ot_events()
    result = ot_event_summary(df)
    assert isinstance(result["clusters"], list)
    # We have 2 open events across 2 zones/subsystems
    assert len(result["clusters"]) >= 1


def test_ot_event_summary_all_acked():
    """When all events have ack_time, unacked counts should be 0."""
    now = pd.Timestamp("2025-01-10 10:00:00")
    df = _make_ot_events()
    df["ack_time"] = now - pd.Timedelta(minutes=10)
    result = ot_event_summary(df)
    assert result["unacked_sev1"] == 0
    assert result["unacked_sev2"] == 0


# ── compute_ot_mean_ack_minutes ───────────────────────────────────────────────

def test_mean_ack_minutes_none_when_empty():
    df = pd.DataFrame(columns=["event_time", "ack_time"])
    result = compute_ot_mean_ack_minutes(df)
    assert result is None


def test_mean_ack_minutes_none_when_no_acked():
    now = pd.Timestamp("2025-01-10 10:00:00")
    df = pd.DataFrame(
        [
            {"event_time": now - pd.Timedelta(hours=1), "ack_time": pd.NaT},
        ]
    )
    result = compute_ot_mean_ack_minutes(df)
    assert result is None


def test_mean_ack_minutes_correct_value():
    now = pd.Timestamp("2025-01-10 10:00:00")
    df = pd.DataFrame(
        [
            {
                "event_time": now - pd.Timedelta(minutes=60),
                "ack_time": now - pd.Timedelta(minutes=30),  # 30 min ack time
            },
            {
                "event_time": now - pd.Timedelta(minutes=50),
                "ack_time": now - pd.Timedelta(minutes=40),  # 10 min ack time
            },
        ]
    )
    result = compute_ot_mean_ack_minutes(df)
    assert result is not None
    assert abs(result - 20.0) < 1.0, f"Expected ~20, got {result}"


def test_mean_ack_minutes_positive():
    now = pd.Timestamp("2025-01-10 10:00:00")
    df = pd.DataFrame(
        [{"event_time": now - pd.Timedelta(minutes=5), "ack_time": now}]
    )
    result = compute_ot_mean_ack_minutes(df)
    assert result is not None
    assert result > 0
