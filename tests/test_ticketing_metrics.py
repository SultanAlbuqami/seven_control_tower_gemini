"""Tests for ticketing KPI metric aggregators in src/metrics.py"""
from __future__ import annotations

import pandas as pd
import pytest

from src.metrics import ticketing_kpi_summary
from src.system_landscape import THRESHOLDS


# ── helpers ───────────────────────────────────────────────────────────────────

_WARN = THRESHOLDS["ticketing_scan_success_rate_warn"]   # 0.97
_CRIT = THRESHOLDS["ticketing_scan_success_rate_crit"]   # 0.94
_LAT_WARN = THRESHOLDS["ticketing_latency_warn_ms"]       # 800
_LAT_CRIT = THRESHOLDS["ticketing_latency_crit_ms"]       # 1500


def _make_ticketing_kpis(
    scan_success_rates: list[float] | None = None,
    latencies: list[float] | None = None,
    offline_fallbacks: list[int] | None = None,
    denied: list[int] | None = None,
) -> pd.DataFrame:
    n = max(
        len(scan_success_rates or []),
        len(latencies or []),
        len(offline_fallbacks or []),
        len(denied or []),
        3,
    )
    base_time = pd.Timestamp("2025-01-10 08:00:00")
    times = [base_time + pd.Timedelta(minutes=15 * i) for i in range(n)]

    return pd.DataFrame(
        {
            "window_start": times,
            "venue_area": ["Main Entrance"] * n,
            "scan_success_rate": (scan_success_rates or [0.99] * n)[:n],
            "qr_validation_latency_ms_p95": (latencies or [400.0] * n)[:n],
            "gate_throughput_ppm": [120.0] * n,
            "offline_fallback_activations": (offline_fallbacks or [0] * n)[:n],
            "denied_entries": (denied or [1] * n)[:n],
        }
    )


# ── empty DataFrame ───────────────────────────────────────────────────────────

def test_ticketing_summary_empty():
    df = pd.DataFrame(
        columns=[
            "scan_success_rate", "qr_validation_latency_ms_p95",
            "offline_fallback_activations", "denied_entries",
        ]
    )
    result = ticketing_kpi_summary(df)
    assert result["anomaly_windows"] == 0
    assert result["total_offline_fallbacks"] == 0
    assert result["total_denied"] == 0


# ── anomaly detection: scan success ──────────────────────────────────────────

def test_no_anomaly_when_all_good():
    df = _make_ticketing_kpis(
        scan_success_rates=[0.99, 0.98, 0.99],
        latencies=[300.0, 350.0, 320.0],
    )
    result = ticketing_kpi_summary(df)
    assert result["anomaly_windows"] == 0


def test_anomaly_when_scan_below_warn():
    """Values below warning threshold should be counted as anomalies."""
    df = _make_ticketing_kpis(
        scan_success_rates=[0.99, _WARN - 0.01, 0.99],
        latencies=[300.0, 300.0, 300.0],
    )
    result = ticketing_kpi_summary(df)
    assert result["anomaly_windows"] >= 1


def test_anomaly_when_scan_below_crit():
    """Critical scan success rate should be counted."""
    df = _make_ticketing_kpis(
        scan_success_rates=[_CRIT - 0.01, 0.99, 0.99],
        latencies=[300.0, 300.0, 300.0],
    )
    result = ticketing_kpi_summary(df)
    assert result["anomaly_windows"] >= 1


# ── anomaly detection: latency ────────────────────────────────────────────────

def test_anomaly_when_latency_above_warn():
    """Latency anomaly is triggered at lat_crit threshold (implementation uses lat_crit)."""
    df = _make_ticketing_kpis(
        scan_success_rates=[0.99, 0.99, 0.99],
        latencies=[300.0, _LAT_CRIT + 100, 300.0],
    )
    result = ticketing_kpi_summary(df)
    assert result["anomaly_windows"] >= 1


def test_anomaly_when_latency_above_crit():
    df = _make_ticketing_kpis(
        scan_success_rates=[0.99, 0.99, 0.99],
        latencies=[300.0, _LAT_CRIT + 200, 300.0],
    )
    result = ticketing_kpi_summary(df)
    assert result["anomaly_windows"] >= 1


# ── aggregated fields ─────────────────────────────────────────────────────────

def test_total_offline_fallbacks():
    df = _make_ticketing_kpis(offline_fallbacks=[0, 3, 2])
    result = ticketing_kpi_summary(df)
    assert result["total_offline_fallbacks"] == 5


def test_total_denied():
    df = _make_ticketing_kpis(denied=[4, 0, 6])
    result = ticketing_kpi_summary(df)
    assert result["total_denied"] == 10


def test_min_success_rate():
    df = _make_ticketing_kpis(scan_success_rates=[0.99, 0.92, 0.97])
    result = ticketing_kpi_summary(df)
    assert abs(result["min_success_rate"] - 0.92) < 1e-6


def test_max_latency_p95():
    df = _make_ticketing_kpis(latencies=[400.0, 1800.0, 600.0])
    result = ticketing_kpi_summary(df)
    assert abs(result["max_latency_p95"] - 1800.0) < 1.0


def test_anomaly_count_matches_bad_windows():
    """Implementation uses lat_crit (1500ms) for latency anomaly, not lat_warn.
    Windows 0 and 2 fail scan_success_rate; window 1 latency (850ms) is below
    lat_crit so NOT anomalous. Expected anomaly count = 2.
    """
    df = _make_ticketing_kpis(
        scan_success_rates=[0.96, 0.99, 0.95],  # windows 0 and 2 are bad
        latencies=[300.0, _LAT_WARN + 50, 300.0],  # 850ms < 1500ms crit → not anomalous
    )
    result = ticketing_kpi_summary(df)
    assert result["anomaly_windows"] == 2
