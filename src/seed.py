"""Deterministic synthetic data generator.

Usage:
    python -m src.seed          # generate all CSVs into data/
    python -c "from src.seed import ensure_data_present; ensure_data_present()"

All data is reproducible with seed=42. Fast (<1 s typical).

DISCLAIMER: System names are example labels for large venues;
the demo is source-agnostic. See src/system_landscape.py.
"""
from __future__ import annotations

import logging
from pathlib import Path
from random import Random

import numpy as np
import pandas as pd

from src.domain.constants import GATES, KPI_DEFINITIONS
from src.system_landscape import (
    CMDB_LABELS,
    EDMS_LABELS,
    ITSM_LABELS,
    MONITORING_LABELS,
    OT_LABELS,
    ORR_TRACKER_LABELS,
    TICKETING_LABELS,
    make_ci_id,
    make_dash_ref,
    make_doc_ref,
    make_inc_id,
    make_ot_event_id,
    make_device_id,
    make_pl_id,
)

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"

STATUSES = ["GREEN", "AMBER", "RED"]

_REQUIRED_FILES = [
    "services.csv",
    "readiness.csv",
    "evidence.csv",
    "incidents.csv",
    "vendors.csv",
    "kpis.csv",
    "ot_events.csv",
    "ticketing_kpis.csv",
]


def _now_utc() -> pd.Timestamp:
    return pd.Timestamp.now(tz="UTC").floor("s")


def _choice(rng: Random, items: list, probs: list[float]):
    x = rng.random()
    c = 0.0
    for item, p in zip(items, probs):
        c += p
        if x <= c:
            return item
    return items[-1]


def _rng_choice(rng: Random, items: list):
    return items[rng.randint(0, len(items) - 1)]


def _generate_services(rng: Random) -> pd.DataFrame:
    rows = [
        {"service_id": "SVC-001", "service": "Ticketing", "criticality": 3, "owner_role": "Ops Readiness",
         "source_system": _rng_choice(rng, CMDB_LABELS), "ci_id": make_ci_id(1001), "service_tier": "Tier-1",
         "owner_team": "IT Ops", "primary_system": "Ticketing", "vendor": "Vendor-TIX"},
        {"service_id": "SVC-002", "service": "Entry Gates", "criticality": 3, "owner_role": "Venue Ops",
         "source_system": _rng_choice(rng, CMDB_LABELS), "ci_id": make_ci_id(1002), "service_tier": "Tier-1",
         "owner_team": "Venue Ops", "primary_system": "Access Control", "vendor": "Vendor-GATES"},
        {"service_id": "SVC-003", "service": "POS", "criticality": 3, "owner_role": "Retail Ops",
         "source_system": _rng_choice(rng, CMDB_LABELS), "ci_id": make_ci_id(1003), "service_tier": "Tier-1",
         "owner_team": "IT Ops", "primary_system": "POS", "vendor": "Vendor-POS"},
        {"service_id": "SVC-004", "service": "Wi-Fi", "criticality": 2, "owner_role": "IT Operations",
         "source_system": _rng_choice(rng, CMDB_LABELS), "ci_id": make_ci_id(1004), "service_tier": "Tier-2",
         "owner_team": "IT Ops", "primary_system": "Wi-Fi", "vendor": "Vendor-NET"},
        {"service_id": "SVC-005", "service": "CCTV & Access", "criticality": 2, "owner_role": "Security Ops",
         "source_system": _rng_choice(rng, CMDB_LABELS), "ci_id": make_ci_id(1005), "service_tier": "Tier-2",
         "owner_team": "Security Ops", "primary_system": "CCTV", "vendor": "Vendor-SEC"},
        {"service_id": "SVC-006", "service": "AV & Signage", "criticality": 1, "owner_role": "Guest Experience",
         "source_system": _rng_choice(rng, CMDB_LABELS), "ci_id": make_ci_id(1006), "service_tier": "Tier-3",
         "owner_team": "Guest Experience", "primary_system": "Signage", "vendor": "Vendor-AV"},
    ]
    return pd.DataFrame(rows)


def _generate_readiness(rng: Random, services: pd.DataFrame, now: pd.Timestamp) -> pd.DataFrame:
    gate_owners = {"G1": "Asset Manager", "G2": "Test Manager", "G3": "Training Lead",
                   "G4": "Monitoring Lead", "G5": "Readiness Lead"}
    block_deps = ["Vendor fix pending", "Authority approval pending", "Integration test required",
                  "Training completion required", "Documentation outstanding"]
    rows: list[dict] = []
    for svc in services["service"].tolist():
        for gate in GATES:
            probs = [0.60, 0.27, 0.13] if gate.code in ("G1", "G2") else [0.45, 0.33, 0.22]
            status = _choice(rng, STATUSES, probs)
            rows.append({
                "service": svc, "gate": gate.code, "gate_name": gate.name, "status": status,
                "last_updated": now - pd.Timedelta(hours=rng.randint(1, 120)),
                "blocker": "" if status != "RED" else "Pending vendor fix / retest evidence",
                "source_system": _rng_choice(rng, ORR_TRACKER_LABELS),
                "gate_owner": gate_owners.get(gate.code, "Ops Lead"),
                "go_no_go": "HOLD" if status == "RED" else "GO",
                "blocking_dependency": _rng_choice(rng, block_deps) if status == "RED" else "",
            })
    return pd.DataFrame(rows)


def _generate_evidence(rng: Random, services: pd.DataFrame, readiness: pd.DataFrame, now: pd.Timestamp) -> pd.DataFrame:
    evidence_types = ["Acceptance Report", "Punch List Snapshot", "Asset Registry Export", "Monitoring Proof",
                      "On-call Roster", "SOP Document", "Training Attendance", "Dry Run Result"]
    ev_class_map = {"Acceptance Report": "SAT", "Punch List Snapshot": "FAT", "Asset Registry Export": "AS_BUILT",
                    "Monitoring Proof": "IST", "On-call Roster": "TRAINING", "SOP Document": "O&M",
                    "Training Attendance": "TRAINING", "Dry Run Result": "DRY_RUN"}
    owners = ["Ops Readiness Lead", "IT Ops Lead", "Vendor Manager", "Security Ops Lead", "Venue Ops Lead"]
    approver_roles = ["Ops Director", "HSE", "Security Lead", "IT Manager", "Facilities Manager"]
    approval_statuses = ["Draft", "Reviewed", "Approved"]
    rows: list[dict] = []
    evid_id = 1
    year = now.year
    for svc in services["service"].tolist():
        n = rng.randint(7, 11)
        for _ in range(n):
            gate = _rng_choice(rng, [g.code for g in GATES])
            et = _rng_choice(rng, evidence_types)
            mask = (readiness["service"] == svc) & (readiness["gate"] == gate)
            svc_gate_status = readiness.loc[mask, "status"].iloc[0] if mask.any() else "GREEN"
            missing_prob = 0.55 if svc_gate_status == "RED" else (0.30 if svc_gate_status == "AMBER" else 0.10)
            status = "MISSING" if rng.random() < missing_prob else "COMPLETE"
            appr_status = _rng_choice(rng, approval_statuses) if status == "COMPLETE" else "Draft"
            rows.append({
                "evidence_id": f"EVD-{evid_id:04d}", "service": svc, "gate": gate, "evidence_type": et,
                "owner": _rng_choice(rng, owners), "status": status,
                "updated_at": now - pd.Timedelta(hours=rng.randint(1, 240)),
                "note": "" if status == "COMPLETE" else "Attach link/screenshot in the Go/No-Go pack",
                "source_system": _rng_choice(rng, EDMS_LABELS),
                "doc_ref": make_doc_ref(evid_id + 86),
                "punch_list_id": make_pl_id(year, evid_id),
                "evidence_class": ev_class_map.get(et, "IST"),
                "approval_status": appr_status,
                "approver_role": _rng_choice(rng, approver_roles),
            })
            evid_id += 1
    return pd.DataFrame(rows)


def _generate_incidents(rng: Random, services: pd.DataFrame, now: pd.Timestamp) -> pd.DataFrame:
    categories = ["Network", "Application", "Hardware", "OT", "Security", "Vendor"]
    impact_scopes = ["Single zone", "Multiple zones", "Whole venue"]
    assigned_groups = ["NOC", "Field Support", "OT Ops", "Vendor", "SOC"]
    statuses_list = ["OPEN", "MITIGATED", "RESOLVED"]
    rows: list[dict] = []
    inc_id = 1
    for _ in range(rng.randint(18, 30)):
        svc = _rng_choice(rng, services["service"].tolist())
        sev = _choice(rng, [1, 2, 3, 4], [0.08, 0.20, 0.42, 0.30])
        opened = now - pd.Timedelta(hours=rng.randint(2, 240))
        ack_delay_min = rng.randint(3, 35) if sev in (1, 2) else rng.randint(10, 120)
        resolve_delay_min = rng.randint(20, 160) if sev in (1, 2) else rng.randint(80, 720)
        ack_at = opened + pd.Timedelta(minutes=ack_delay_min)
        resolved_at = opened + pd.Timedelta(minutes=resolve_delay_min)
        st = _rng_choice(rng, statuses_list)
        if st in ("OPEN", "MITIGATED"):
            resolved_at = pd.NaT
        src_sys = _rng_choice(rng, ITSM_LABELS)
        vendor = services.loc[services["service"] == svc, "vendor"].iloc[0]
        sla_breached = bool(sev in (1, 2) and ack_delay_min > 20)
        rows.append({
            "incident_id": f"INC-{inc_id:04d}", "service": svc, "vendor": vendor, "severity": sev,
            "status": st, "opened_at": opened, "ack_at": ack_at, "resolved_at": resolved_at,
            "summary": f"{svc} degradation during peak-like load",
            "rca_done": bool(rng.random() < 0.55),
            "prevent_action": ("Run peak drill + tighten alert thresholds" if sev in (1, 2)
                               else "Tune monitoring and capacity"),
            "source_system": src_sys,
            "source_id": make_inc_id(inc_id * 43 + 10000, src_sys),
            "category": _rng_choice(rng, categories),
            "impact_scope": _rng_choice(rng, impact_scopes),
            "sla_breached": sla_breached,
            "assigned_group": _rng_choice(rng, assigned_groups),
        })
        inc_id += 1
    return pd.DataFrame(rows)


def _generate_vendors(rng: Random, services: pd.DataFrame, now: pd.Timestamp) -> pd.DataFrame:
    rows: list[dict] = []
    for i, row in services.iterrows():
        sla = 99.5 if row["criticality"] >= 2 else 99.0
        actual = float(np.clip(rng.normalvariate(mu=sla - 0.2, sigma=0.4), 97.5, 99.95))
        mtta_target = 10 if row["criticality"] == 3 else 20
        mttr_target = 60 if row["criticality"] == 3 else 180
        mtta_actual = int(np.clip(rng.normalvariate(mu=mtta_target * 1.1, sigma=6), 3, 120))
        mttr_actual = int(np.clip(rng.normalvariate(mu=mttr_target * 1.15, sigma=30), 10, 720))
        avail_breach = actual < sla
        penalty_risk = "High" if avail_breach and row["criticality"] == 3 else ("Med" if avail_breach else "Low")
        rows.append({
            "vendor": row["vendor"], "service": row["service"],
            "sla_availability": sla, "availability_actual": round(actual, 2),
            "mtta_target_min": mtta_target, "mtta_actual_min": mtta_actual,
            "mttr_target_min": mttr_target, "mttr_actual_min": mttr_actual,
            "open_critical": rng.randint(0, 6),
            "last_review": now - pd.Timedelta(days=rng.randint(1, 14)),
            "source_system": _rng_choice(rng, MONITORING_LABELS),
            "dashboard_ref": make_dash_ref(i + 1),
            "contract_sla": sla,
            "escalation_level": _rng_choice(rng, ["L1", "L2", "L3"]),
            "penalty_risk": penalty_risk,
            "service_credit_applicable": avail_breach,
        })
    return pd.DataFrame(rows)


def _generate_kpis(rng: Random, now: pd.Timestamp) -> pd.DataFrame:
    start = (now - pd.Timedelta(days=7)).floor("h")
    ts = pd.date_range(start=start, end=now.floor("h"), freq="h", tz="UTC")
    rows: list[dict] = []
    for k in KPI_DEFINITIONS:
        base_target = float(k["target"])
        for t in ts:
            hour = int(t.hour)
            peak = 1.0 if hour in (18, 19, 20, 21) else (0.6 if hour in (16, 17, 22) else 0.35)
            if "Queue" in k["kpi"]:
                value = float(np.clip(rng.normalvariate(mu=base_target * (1.0 + peak), sigma=2.0), 2, 45))
                direction = "LOWER_IS_BETTER"
            else:
                value = float(np.clip(rng.normalvariate(mu=base_target - (peak * 0.35), sigma=0.25), base_target - 3.0, 100.0))
                direction = "HIGHER_IS_BETTER"
            rows.append({"ts": t, "kpi": k["kpi"], "service": k["service"],
                         "value": round(value, 3), "target": base_target, "direction": direction})
    return pd.DataFrame(rows)


def _generate_ot_events(rng: Random, incidents: pd.DataFrame, now: pd.Timestamp) -> pd.DataFrame:
    subsystem_alarm_map = {
        "BMS": ["HVACFault", "FirePanelTrouble", "PowerAnomaly", "SmokeAlarm", "ElevatorFault"],
        "AccessControl": ["DoorForcedOpen", "GateControllerFault", "AccessPointDown"],
        "CCTV": ["CameraOffline", "NetworkSwitchDown"],
    }
    subsystems = list(subsystem_alarm_map.keys())
    zones = ["Zone-A", "Zone-B", "Zone-C", "Zone-D", "Zone-E", "Main-Gate", "Back-of-House"]
    acked_by_roles = ["Security Ops", "Facilities", "IT Ops"]
    incident_ids = incidents["incident_id"].tolist() if not incidents.empty else []
    rows: list[dict] = []
    for i in range(1, 81):
        subsystem = _rng_choice(rng, subsystems)
        alarm_type = _rng_choice(rng, subsystem_alarm_map[subsystem])
        sev = _choice(rng, [1, 2, 3, 4], [0.06, 0.18, 0.46, 0.30])
        event_time = now - pd.Timedelta(minutes=rng.randint(30, 10080))
        ack_time: object = pd.NaT
        cleared_time: object = pd.NaT
        acked_by = ""
        if rng.random() > (0.30 if sev in (1, 2) else 0.10):
            ack_delay_min = rng.randint(1, 20 if sev in (1, 2) else 60)
            ack_time = event_time + pd.Timedelta(minutes=ack_delay_min)
            acked_by = _rng_choice(rng, acked_by_roles)
        if pd.notna(ack_time) and rng.random() > (0.25 if sev in (1, 2) else 0.10):
            clear_delay_min = rng.randint(5, 120 if sev in (1, 2) else 480)
            cleared_time = ack_time + pd.Timedelta(minutes=clear_delay_min)
        linked_inc = ""
        if incident_ids and sev in (1, 2) and rng.random() < 0.30:
            linked_inc = _rng_choice(rng, incident_ids)
        rows.append({
            "ot_event_id": make_ot_event_id(i),
            "source_system": _rng_choice(rng, OT_LABELS),
            "subsystem": subsystem, "alarm_type": alarm_type,
            "zone": _rng_choice(rng, zones), "device_id": make_device_id(100 + i),
            "severity": sev, "event_time": event_time, "ack_time": ack_time,
            "cleared_time": cleared_time, "acked_by_role": acked_by,
            "linked_incident_id": linked_inc,
        })
    return pd.DataFrame(rows)


def _generate_ticketing_kpis(rng: Random, incidents: pd.DataFrame, now: pd.Timestamp) -> pd.DataFrame:
    venue_areas = ["Main Gate", "Zone-1 North", "Zone-2 East", "Zone-3 South", "VIP Gate", "Staff Entry"]
    ticket_src = _rng_choice(rng, TICKETING_LABELS)
    incident_ids = incidents["incident_id"].tolist() if not incidents.empty else []
    start = (now - pd.Timedelta(hours=48)).floor("15min")
    ts_index = pd.date_range(start=start, end=now.floor("15min"), freq="15min", tz="UTC")
    rows: list[dict] = []
    for t in ts_index:
        hour = t.hour
        is_peak = hour in (10, 11, 12, 17, 18, 19, 20)
        for area in venue_areas:
            base_success = 0.985
            base_latency_p95 = 350.0
            base_throughput = 80.0 if is_peak else 25.0
            base_denied = 1 if is_peak else 0
            anomaly = rng.random() < 0.05 and is_peak
            if anomaly:
                base_success = rng.uniform(0.88, 0.96)
                base_latency_p95 = float(rng.randint(900, 2200))
                base_throughput = max(5.0, base_throughput - rng.randint(20, 60))
                base_denied = rng.randint(3, 12)
            success_rate = float(np.clip(rng.normalvariate(base_success, 0.005), 0.70, 1.0))
            latency = float(np.clip(rng.normalvariate(base_latency_p95, 50), 100, 5000))
            throughput = float(max(0, rng.normalvariate(base_throughput, 5)))
            denied = max(0, int(rng.normalvariate(base_denied, 0.5)))
            offline_fb = 1 if anomaly and rng.random() < 0.4 else 0
            payment_dep = bool(anomaly and rng.random() < 0.3)
            linked_inc = ""
            if incident_ids and anomaly and rng.random() < 0.5:
                linked_inc = _rng_choice(rng, incident_ids)
            rows.append({
                "ts": t, "source_system": ticket_src, "venue_area": area,
                "scan_success_rate": round(success_rate, 4),
                "qr_validation_latency_ms_p95": round(latency, 1),
                "gate_throughput_ppm": round(throughput, 1),
                "denied_entries": denied, "offline_fallback_activations": offline_fb,
                "payment_dependency_flag": payment_dep, "linked_incident_id": linked_inc,
            })
    return pd.DataFrame(rows)


def generate(seed: int = 42) -> None:
    """Generate all CSV datasets and write to data/."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    rng = Random(seed)
    np.random.seed(seed)
    now = _now_utc()

    logger.info("Generating services…")
    services = _generate_services(rng)
    services.to_csv(DATA_DIR / "services.csv", index=False)

    logger.info("Generating readiness…")
    readiness = _generate_readiness(rng, services, now)
    readiness.to_csv(DATA_DIR / "readiness.csv", index=False)

    logger.info("Generating evidence…")
    evidence = _generate_evidence(rng, services, readiness, now)
    evidence.to_csv(DATA_DIR / "evidence.csv", index=False)

    logger.info("Generating incidents…")
    incidents = _generate_incidents(rng, services, now)
    incidents.to_csv(DATA_DIR / "incidents.csv", index=False)

    logger.info("Generating vendors…")
    vendors = _generate_vendors(rng, services, now)
    vendors.to_csv(DATA_DIR / "vendors.csv", index=False)

    logger.info("Generating KPIs…")
    kpis = _generate_kpis(rng, now)
    kpis.to_csv(DATA_DIR / "kpis.csv", index=False)

    logger.info("Generating OT events…")
    ot_events = _generate_ot_events(rng, incidents, now)
    ot_events.to_csv(DATA_DIR / "ot_events.csv", index=False)

    logger.info("Generating ticketing KPIs…")
    ticketing_kpis = _generate_ticketing_kpis(rng, incidents, now)
    ticketing_kpis.to_csv(DATA_DIR / "ticketing_kpis.csv", index=False)

    logger.info("All datasets written to %s", DATA_DIR)


def ensure_data_present(seed: int = 42) -> None:
    """Generate all datasets if any required CSV is missing."""
    missing = [f for f in _REQUIRED_FILES if not (DATA_DIR / f).exists()]
    if missing:
        logger.info("Missing data files %s — generating deterministic dataset…", missing)
        generate(seed=seed)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    generate()
    print("Demo data generated successfully.")
