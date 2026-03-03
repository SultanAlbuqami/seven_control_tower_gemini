from __future__ import annotations

import logging
from pathlib import Path
from random import Random

import numpy as np
import pandas as pd

from src.domain.constants import GATES, KPI_DEFINITIONS
from src.system_landscape import (
    BMS_VENDOR_LABELS,
    EDMS_LABELS,
    ITSM_CMDB_LABELS,
    OBSERVABILITY_LABELS,
    ORR_TRACKER_LABELS,
    OT_EVENT_FEED_LABELS,
    TICKETING_LABELS,
    make_ci_id,
    make_dashboard_ref,
    make_device_id,
    make_doc_ref,
    make_incident_id,
    make_ot_event_id,
    make_punch_list_id,
    make_service_id,
    make_source_id,
)

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
FIXED_SEED = 42
ANCHOR_TIME = pd.Timestamp("2026-03-03 08:00:00+00:00")

STATUSES = ("GREEN", "AMBER", "RED")
SERVICE_LEVELS = {3: "Tier-1", 2: "Tier-2", 1: "Tier-3"}

REQUIRED_FILES = (
    "services.csv",
    "readiness.csv",
    "evidence.csv",
    "incidents.csv",
    "vendors.csv",
    "kpis.csv",
    "ot_events.csv",
    "ticketing_kpis.csv",
)


def _pick(rng: Random, items: tuple[str, ...] | list[str]) -> str:
    return items[rng.randint(0, len(items) - 1)]


def _weighted_pick(rng: Random, items: tuple[str, ...] | list[str], weights: tuple[float, ...]) -> str:
    roll = rng.random()
    running = 0.0
    for item, weight in zip(items, weights):
        running += weight
        if roll <= running:
            return item
    return items[-1]


def _generate_services(rng: Random) -> pd.DataFrame:
    services = [
        ("Ticketing and Gate Validation", 3, "Guest Access Lead", "IT Ops", "Ticketing", "Gate Systems Integrator"),
        ("Access Control and Entry Gates", 3, "Security Operations Lead", "Security Ops", "Access Control", "Security Platform Partner"),
        ("POS and Payments", 3, "Retail Operations Lead", "Guest Experience", "POS", "Retail Platform Partner"),
        ("Venue Wi-Fi and NAC", 2, "Network Operations Lead", "IT Ops", "Wi-Fi", "Network Services Partner"),
        ("CCTV and VMS", 2, "Security Systems Manager", "Security Ops", "CCTV", "Video Systems Integrator"),
        ("BMS and Facilities", 2, "Facilities Operations Lead", "Facilities", "BMS", "Facilities Automation Partner"),
        ("Digital Signage", 1, "Guest Experience Manager", "Guest Experience", "Signage", "Media Systems Integrator"),
        ("Guest Communications CRM", 1, "Guest Experience Director", "Guest Experience", "Guest CRM", "Experience Platform Partner"),
    ]

    rows: list[dict[str, object]] = []
    for index, (service, criticality, owner_role, owner_team, primary_system, vendor) in enumerate(services, start=1):
        rows.append(
            {
                "service_id": make_service_id(index),
                "service": service,
                "criticality": criticality,
                "owner_role": owner_role,
                "source_system": _pick(rng, ITSM_CMDB_LABELS),
                "ci_id": make_ci_id(1200 + index),
                "service_tier": SERVICE_LEVELS[criticality],
                "owner_team": owner_team,
                "primary_system": primary_system,
                "vendor": vendor,
            }
        )
    return pd.DataFrame(rows)


def _generate_readiness(rng: Random, services: pd.DataFrame, now: pd.Timestamp) -> pd.DataFrame:
    blockers = (
        "Vendor fix pending",
        "Authority approval pending",
        "Integration test rerun required",
        "Training completion pending",
        "Dry run evidence not uploaded",
        "Monitoring dashboard sign-off pending",
    )
    gate_owners = {
        "G1": "Asset Manager",
        "G2": "Test Manager",
        "G3": "Training Lead",
        "G4": "Observability Lead",
        "G5": "Readiness Director",
    }
    rows: list[dict[str, object]] = []
    for service_row in services.itertuples(index=False):
        for gate in GATES:
            criticality = int(service_row.criticality)
            if criticality == 3:
                weights = (0.52, 0.28, 0.20)
            elif criticality == 2:
                weights = (0.60, 0.28, 0.12)
            else:
                weights = (0.68, 0.24, 0.08)
            if gate.code in {"G2", "G5"}:
                weights = tuple(max(0.05, value - 0.04) for value in weights[:2]) + (min(0.30, weights[2] + 0.08),)
                total = sum(weights)
                weights = tuple(value / total for value in weights)
            status = _weighted_pick(rng, list(STATUSES), weights)
            blocker = ""
            dependency = ""
            if status in {"AMBER", "RED"}:
                dependency = _pick(rng, blockers)
                blocker = dependency if status == "RED" else f"Watch item: {dependency}"
            rows.append(
                {
                    "service": service_row.service,
                    "gate": gate.code,
                    "gate_name": gate.name,
                    "status": status,
                    "last_updated": now - pd.Timedelta(hours=rng.randint(2, 96)),
                    "blocker": blocker,
                    "source_system": _pick(rng, ORR_TRACKER_LABELS),
                    "gate_owner": gate_owners[gate.code],
                    "go_no_go": "HOLD" if status == "RED" else "GO",
                    "blocking_dependency": dependency,
                }
            )
    return pd.DataFrame(rows)


def _generate_evidence(
    rng: Random,
    services: pd.DataFrame,
    readiness: pd.DataFrame,
    now: pd.Timestamp,
) -> pd.DataFrame:
    evidence_types = {
        "FAT report": "FAT",
        "SAT report": "SAT",
        "Integrated systems test": "IST",
        "Dry run rehearsal": "DRY_RUN",
        "Training attendance": "TRAINING",
        "Operations manual": "O&M",
        "As-built package": "AS_BUILT",
    }
    owners = (
        "Ops Readiness Lead",
        "IT Ops Lead",
        "Security Ops Lead",
        "Facilities Lead",
        "Guest Experience Lead",
    )
    approver_roles = ("Ops Director", "HSE", "Security", "IT", "Facilities")
    rows: list[dict[str, object]] = []
    evidence_counter = 1
    for readiness_row in readiness.itertuples(index=False):
        items_per_gate = 2 if readiness_row.status == "GREEN" else 3
        for _ in range(items_per_gate):
            evidence_type = _pick(rng, tuple(evidence_types.keys()))
            if readiness_row.status == "RED":
                status = _weighted_pick(rng, ["MISSING", "COMPLETE"], (0.58, 0.42))
            elif readiness_row.status == "AMBER":
                status = _weighted_pick(rng, ["MISSING", "COMPLETE"], (0.28, 0.72))
            else:
                status = _weighted_pick(rng, ["MISSING", "COMPLETE"], (0.08, 0.92))
            approval_status = "Draft"
            if status == "COMPLETE":
                approval_status = _weighted_pick(rng, ["Reviewed", "Approved"], (0.42, 0.58))
            note = ""
            if status == "MISSING":
                note = f"Owner to upload {evidence_type.lower()} before the next ORR review."
            rows.append(
                {
                    "evidence_id": f"EVD-{evidence_counter:04d}",
                    "service": readiness_row.service,
                    "gate": readiness_row.gate,
                    "evidence_type": evidence_type,
                    "owner": _pick(rng, owners),
                    "status": status,
                    "updated_at": now - pd.Timedelta(hours=rng.randint(6, 144)),
                    "note": note,
                    "source_system": _pick(rng, EDMS_LABELS),
                    "doc_ref": make_doc_ref(86 + evidence_counter),
                    "punch_list_id": make_punch_list_id(now.year, evidence_counter),
                    "evidence_class": evidence_types[evidence_type],
                    "approval_status": approval_status,
                    "approver_role": _pick(rng, approver_roles),
                }
            )
            evidence_counter += 1
    return pd.DataFrame(rows)


def _generate_incidents(rng: Random, services: pd.DataFrame, now: pd.Timestamp) -> pd.DataFrame:
    categories = ("Network", "Application", "Hardware", "OT", "Security", "Vendor")
    impact_scopes = ("Single zone", "Multiple zones", "Whole venue")
    assigned_groups = ("NOC", "Field Support", "OT Ops", "Vendor", "SOC")
    statuses = ("OPEN", "MITIGATED", "RESOLVED")
    summaries = (
        "Peak-window degradation detected on guest-facing workflow",
        "Controller heartbeat intermittent after maintenance window",
        "External dependency latency elevated during synthetic rehearsal",
        "Alarm storm required manual validation and triage",
        "Capacity threshold breach triggered degraded-mode response",
    )
    rows: list[dict[str, object]] = []
    for number in range(1, 27):
        service_row = services.iloc[(number - 1) % len(services)]
        severity = int(_weighted_pick(rng, ["1", "2", "3", "4"], (0.08, 0.22, 0.40, 0.30)))
        opened_at = now - pd.Timedelta(hours=rng.randint(4, 192), minutes=rng.randint(0, 59))
        ack_delay = rng.randint(3, 18) if severity in {1, 2} else rng.randint(10, 75)
        resolve_delay = rng.randint(25, 140) if severity in {1, 2} else rng.randint(90, 600)
        ack_at = opened_at + pd.Timedelta(minutes=ack_delay)
        resolved_at = opened_at + pd.Timedelta(minutes=resolve_delay)
        status = _pick(rng, statuses)
        if status in {"OPEN", "MITIGATED"}:
            resolved_at = pd.NaT
        source_system = _pick(rng, ITSM_CMDB_LABELS)
        sla_breached = bool(severity in {1, 2} and ack_delay > 12)
        prefix = "PRB" if number % 9 == 0 else ("CHG" if number % 7 == 0 else "INC")
        rows.append(
            {
                "incident_id": make_incident_id(number),
                "service": service_row["service"],
                "vendor": service_row["vendor"],
                "severity": severity,
                "status": status,
                "opened_at": opened_at,
                "ack_at": ack_at,
                "resolved_at": resolved_at,
                "summary": _pick(rng, summaries),
                "rca_done": bool(rng.random() < 0.62 if severity in {1, 2} else rng.random() < 0.38),
                "prevent_action": "Validate runbook, tune alert routing, and repeat targeted rehearsal",
                "source_system": source_system,
                "source_id": make_source_id(10000 + number * 17, source_system, prefix=prefix),
                "category": _pick(rng, categories),
                "impact_scope": _pick(rng, impact_scopes),
                "sla_breached": sla_breached,
                "assigned_group": _pick(rng, assigned_groups),
            }
        )
    return pd.DataFrame(rows)


def _generate_vendors(rng: Random, services: pd.DataFrame, now: pd.Timestamp) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for number, service_row in enumerate(services.itertuples(index=False), start=1):
        contract_sla = 99.7 if int(service_row.criticality) == 3 else (99.5 if int(service_row.criticality) == 2 else 99.2)
        availability_actual = round(float(np.clip(rng.normalvariate(contract_sla - 0.18, 0.35), 97.8, 99.95)), 2)
        mtta_target = 10 if int(service_row.criticality) == 3 else 20
        mttr_target = 60 if int(service_row.criticality) == 3 else 180
        mtta_actual = int(np.clip(rng.normalvariate(mtta_target * 1.08, 5), 4, 120))
        mttr_actual = int(np.clip(rng.normalvariate(mttr_target * 1.12, 25), 20, 720))
        availability_breach = availability_actual < contract_sla
        breach_count = sum(
            [
                availability_breach,
                mtta_actual > mtta_target,
                mttr_actual > mttr_target,
            ]
        )
        if breach_count >= 2:
            penalty_risk = "High"
        elif breach_count == 1:
            penalty_risk = "Med"
        else:
            penalty_risk = "Low"
        rows.append(
            {
                "vendor": service_row.vendor,
                "service": service_row.service,
                "sla_availability": contract_sla,
                "availability_actual": availability_actual,
                "mtta_target_min": mtta_target,
                "mtta_actual_min": mtta_actual,
                "mttr_target_min": mttr_target,
                "mttr_actual_min": mttr_actual,
                "open_critical": rng.randint(0, 4 if int(service_row.criticality) == 3 else 2),
                "last_review": now - pd.Timedelta(days=rng.randint(2, 14)),
                "source_system": _pick(rng, OBSERVABILITY_LABELS),
                "dashboard_ref": make_dashboard_ref(number),
                "contract_sla": contract_sla,
                "escalation_level": _pick(rng, ("L1", "L2", "L3")),
                "penalty_risk": penalty_risk,
                "service_credit_applicable": bool(availability_breach),
            }
        )
    return pd.DataFrame(rows)


def _generate_kpis(rng: Random, now: pd.Timestamp) -> pd.DataFrame:
    start = (now - pd.Timedelta(days=7)).floor("h")
    timestamps = pd.date_range(start=start, end=now.floor("h"), freq="h", tz="UTC")
    queue_sources = ("Crowd/Queue Analytics (example)", "Network Monitoring Platform (example)")
    rows: list[dict[str, object]] = []
    for index, definition in enumerate(KPI_DEFINITIONS, start=1):
        target = float(definition["target"])
        source_system = _pick(rng, queue_sources if "Queue" in definition["kpi"] else OBSERVABILITY_LABELS)
        dashboard_ref = make_dashboard_ref(40 + index)
        for timestamp in timestamps:
            peak_factor = 1.0 if timestamp.hour in {10, 11, 12, 17, 18, 19, 20} else 0.45
            if "Queue" in definition["kpi"]:
                value = float(np.clip(rng.normalvariate(target * (0.8 + peak_factor), 1.8), 2.0, 40.0))
                direction = "LOWER_IS_BETTER"
            else:
                value = float(np.clip(rng.normalvariate(target - peak_factor * 0.25, 0.18), target - 3.5, 100.0))
                direction = "HIGHER_IS_BETTER"
            rows.append(
                {
                    "ts": timestamp,
                    "kpi": definition["kpi"],
                    "service": definition["service"],
                    "value": round(value, 3),
                    "target": target,
                    "direction": direction,
                    "source_system": source_system,
                    "dashboard_ref": dashboard_ref,
                }
            )
    return pd.DataFrame(rows)


def _generate_ot_events(rng: Random, incidents: pd.DataFrame, now: pd.Timestamp) -> pd.DataFrame:
    subsystem_alarm_map = {
        "BMS": ("HVACFault", "FirePanelTrouble", "PowerAnomaly", "ChillerFault"),
        "AccessControl": ("DoorForcedOpen", "GateControllerFault", "BadgeReaderOffline"),
        "CCTV": ("CameraOffline", "VideoRecorderAlert", "AnalyticsFeedDown"),
        "Fire": ("FirePanelTrouble", "DetectorLoopFault", "PowerAnomaly"),
    }
    zones = ("Main Gate", "Zone-A", "Zone-B", "Zone-C", "Zone-D", "Back of House")
    roles = ("Security Ops", "Facilities", "IT Ops")
    critical_incidents = incidents[incidents["severity"].isin([1, 2])]["incident_id"].tolist()
    rows: list[dict[str, object]] = []
    for number in range(1, 85):
        subsystem = _pick(rng, tuple(subsystem_alarm_map.keys()))
        severity = int(_weighted_pick(rng, ["1", "2", "3", "4"], (0.08, 0.22, 0.40, 0.30)))
        event_time = now - pd.Timedelta(minutes=rng.randint(45, 7 * 24 * 60))
        ack_time = pd.NaT
        cleared_time = pd.NaT
        acked_by_role = ""
        ack_probability = 0.58 if severity == 1 else (0.72 if severity == 2 else 0.88)
        if rng.random() <= ack_probability:
            ack_time = event_time + pd.Timedelta(minutes=rng.randint(2, 12 if severity in {1, 2} else 55))
            acked_by_role = _pick(rng, roles)
        if pd.notna(ack_time) and rng.random() < 0.82:
            cleared_time = ack_time + pd.Timedelta(minutes=rng.randint(8, 90 if severity in {1, 2} else 360))
        linked_incident_id = ""
        if critical_incidents and severity in {1, 2} and rng.random() < 0.38:
            linked_incident_id = _pick(rng, critical_incidents)
        rows.append(
            {
                "ot_event_id": make_ot_event_id(number),
                "source_system": _pick(rng, OT_EVENT_FEED_LABELS),
                "subsystem": subsystem,
                "alarm_type": _pick(rng, subsystem_alarm_map[subsystem]),
                "zone": _pick(rng, zones),
                "device_id": make_device_id(1000 + number),
                "severity": severity,
                "event_time": event_time,
                "ack_time": ack_time,
                "cleared_time": cleared_time,
                "acked_by_role": acked_by_role,
                "linked_incident_id": linked_incident_id,
            }
        )
    return pd.DataFrame(rows)


def _generate_ticketing_kpis(rng: Random, incidents: pd.DataFrame, now: pd.Timestamp) -> pd.DataFrame:
    venue_areas = ("Main Gate", "Zone-1", "Zone-2", "Zone-3", "VIP Gate", "Staff Entry")
    incident_links = incidents[incidents["service"].isin(["Ticketing and Gate Validation", "Access Control and Entry Gates", "POS and Payments"])]["incident_id"].tolist()
    timestamps = pd.date_range(
        start=(now - pd.Timedelta(hours=48)).floor("15min"),
        end=now.floor("15min"),
        freq="15min",
        tz="UTC",
    )
    rows: list[dict[str, object]] = []
    for timestamp in timestamps:
        is_peak = timestamp.hour in {10, 11, 12, 17, 18, 19, 20}
        for area in venue_areas:
            anomaly = bool(is_peak and rng.random() < 0.06)
            base_success = 0.989 if not anomaly else rng.uniform(0.89, 0.965)
            base_latency = 320.0 if not anomaly else float(rng.randint(900, 2200))
            base_throughput = 78.0 if is_peak else 24.0
            if anomaly:
                base_throughput = max(8.0, base_throughput - rng.randint(20, 55))
            scan_success_rate = float(np.clip(rng.normalvariate(base_success, 0.004), 0.82, 1.0))
            latency = float(np.clip(rng.normalvariate(base_latency, 45.0), 90.0, 5000.0))
            throughput = float(np.clip(rng.normalvariate(base_throughput, 4.5), 0.0, 140.0))
            denied_entries = max(0, int(rng.normalvariate(1 if is_peak else 0, 0.8)))
            offline_fallback = 1 if anomaly and rng.random() < 0.35 else 0
            payment_dependency_flag = bool(anomaly and rng.random() < 0.28)
            linked_incident_id = _pick(rng, incident_links) if incident_links and anomaly and rng.random() < 0.52 else ""
            rows.append(
                {
                    "ts": timestamp,
                    "source_system": _pick(rng, TICKETING_LABELS),
                    "venue_area": area,
                    "scan_success_rate": round(scan_success_rate, 4),
                    "qr_validation_latency_ms_p95": round(latency, 1),
                    "gate_throughput_ppm": round(throughput, 1),
                    "denied_entries": denied_entries,
                    "offline_fallback_activations": offline_fallback,
                    "payment_dependency_flag": payment_dependency_flag,
                    "linked_incident_id": linked_incident_id,
                }
            )
    return pd.DataFrame(rows)


def generate(seed: int = FIXED_SEED) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    rng = Random(seed)
    np.random.seed(seed)
    now = ANCHOR_TIME

    services = _generate_services(rng)
    readiness = _generate_readiness(rng, services, now)
    evidence = _generate_evidence(rng, services, readiness, now)
    incidents = _generate_incidents(rng, services, now)
    vendors = _generate_vendors(rng, services, now)
    kpis = _generate_kpis(rng, now)
    ot_events = _generate_ot_events(rng, incidents, now)
    ticketing_kpis = _generate_ticketing_kpis(rng, incidents, now)

    services.to_csv(DATA_DIR / "services.csv", index=False)
    readiness.to_csv(DATA_DIR / "readiness.csv", index=False)
    evidence.to_csv(DATA_DIR / "evidence.csv", index=False)
    incidents.to_csv(DATA_DIR / "incidents.csv", index=False)
    vendors.to_csv(DATA_DIR / "vendors.csv", index=False)
    kpis.to_csv(DATA_DIR / "kpis.csv", index=False)
    ot_events.to_csv(DATA_DIR / "ot_events.csv", index=False)
    ticketing_kpis.to_csv(DATA_DIR / "ticketing_kpis.csv", index=False)
    logger.info("Generated deterministic demo datasets in %s", DATA_DIR)


def ensure_data_present(seed: int = FIXED_SEED) -> None:
    missing = [filename for filename in REQUIRED_FILES if not (DATA_DIR / filename).exists()]
    if missing:
        logger.info("Missing data files %s. Regenerating the full deterministic dataset.", missing)
        generate(seed=seed)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    generate()
    print("Deterministic demo data generated.")
