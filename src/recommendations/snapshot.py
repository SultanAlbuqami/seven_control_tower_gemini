from __future__ import annotations

from typing import Any

from src.data import DataBundle
from src.metrics import (
    evidence_summary,
    incident_summary,
    ot_event_summary,
    readiness_summary,
    ticketing_kpi_summary,
    vendor_summary,
)


def build_snapshot(data: DataBundle) -> dict[str, Any]:
    return {
        "readiness": readiness_summary(data.readiness),
        "evidence": evidence_summary(data.evidence),
        "incidents": incident_summary(data.incidents),
        "vendors": vendor_summary(data.vendors),
        "ot_signals": ot_event_summary(data.ot_events),
        "ticketing_signals": ticketing_kpi_summary(data.ticketing_kpis),
    }
