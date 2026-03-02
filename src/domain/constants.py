from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Gate:
    code: str
    name: str
    intent: str


GATES: list[Gate] = [
    Gate("G1", "Assets & Scope", "Asset registry, scope closure, and critical path coverage."),
    Gate("G2", "Acceptance Tests", "FAT/SAT evidence, defect triage, and retest outcomes."),
    Gate("G3", "SOPs & Training", "SOP completion, training attendance, and shift readiness."),
    Gate("G4", "Monitoring & On-call", "Observability proof, alert routing, escalation roster."),
    Gate("G5", "Peak Drill / Dry Run", "Peak rehearsal evidence, failover drills, Go/No-Go pack."),
]


KPI_DEFINITIONS = [
    {"kpi": "Entry Queue Time (min)", "service": "Entry Gates", "target": 8},
    {"kpi": "Ticket Scan Success (%)", "service": "Ticketing", "target": 99.0},
    {"kpi": "POS Success (%)", "service": "POS", "target": 99.2},
    {"kpi": "Wi-Fi Availability (%)", "service": "Wi-Fi", "target": 99.5},
    {"kpi": "CCTV Coverage (%)", "service": "CCTV & Access", "target": 98.0},
]
