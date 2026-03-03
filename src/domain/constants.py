from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Gate:
    code: str
    name: str
    intent: str


GATES: list[Gate] = [
    Gate("G1", "Assets and Scope", "Asset registry, scope closure, and critical-path coverage."),
    Gate("G2", "Acceptance Tests", "FAT/SAT evidence, defect triage, and retest outcomes."),
    Gate("G3", "SOPs and Training", "SOP completion, training attendance, and shift readiness."),
    Gate("G4", "Monitoring and On-call", "Observability proof, alert routing, and escalation coverage."),
    Gate("G5", "Peak Drill and Dry Run", "Peak rehearsal evidence, failover drills, and Go/No-Go pack quality."),
]


KPI_DEFINITIONS = [
    {"kpi": "Entry Queue Time (min)", "service": "Access Control and Entry Gates", "target": 8.0},
    {"kpi": "Ticket Scan Success (%)", "service": "Ticketing and Gate Validation", "target": 99.0},
    {"kpi": "POS Success (%)", "service": "POS and Payments", "target": 99.2},
    {"kpi": "Wi-Fi Availability (%)", "service": "Venue Wi-Fi and NAC", "target": 99.5},
    {"kpi": "CCTV Coverage (%)", "service": "CCTV and VMS", "target": 98.0},
    {"kpi": "Signage Uptime (%)", "service": "Digital Signage", "target": 99.0},
]
