from __future__ import annotations

from pathlib import Path
from random import Random

import numpy as np
import pandas as pd

from src.domain.constants import GATES, KPI_DEFINITIONS

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"

STATUSES = ["GREEN", "AMBER", "RED"]


def _now_utc() -> pd.Timestamp:
    return pd.Timestamp.now(tz="UTC").floor("s")


def _choice(rng: Random, items: list[str], probs: list[float]) -> str:
    x = rng.random()
    c = 0.0
    for item, p in zip(items, probs):
        c += p
        if x <= c:
            return item
    return items[-1]


def generate(seed: int = 42) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    rng = Random(seed)
    now = _now_utc()

    services = pd.DataFrame(
        [
            {"service_id": "SVC-001", "service": "Ticketing", "criticality": 3, "owner_role": "Ops Readiness", "vendor": "Vendor-TIX"},
            {"service_id": "SVC-002", "service": "Entry Gates", "criticality": 3, "owner_role": "Venue Ops", "vendor": "Vendor-GATES"},
            {"service_id": "SVC-003", "service": "POS", "criticality": 3, "owner_role": "Retail Ops", "vendor": "Vendor-POS"},
            {"service_id": "SVC-004", "service": "Wi-Fi", "criticality": 2, "owner_role": "IT Operations", "vendor": "Vendor-NET"},
            {"service_id": "SVC-005", "service": "CCTV & Access", "criticality": 2, "owner_role": "Security Ops", "vendor": "Vendor-SEC"},
            {"service_id": "SVC-006", "service": "AV & Signage", "criticality": 1, "owner_role": "Guest Experience", "vendor": "Vendor-AV"},
        ]
    )
    services.to_csv(DATA_DIR / "services.csv", index=False)

    readiness_rows: list[dict] = []
    for svc in services["service"].tolist():
        for gate in GATES:
            probs = [0.60, 0.27, 0.13] if gate.code in ("G1", "G2") else [0.45, 0.33, 0.22]
            status = _choice(rng, STATUSES, probs)
            readiness_rows.append(
                {
                    "service": svc,
                    "gate": gate.code,
                    "gate_name": gate.name,
                    "status": status,
                    "last_updated": now - pd.Timedelta(hours=rng.randint(1, 120)),
                    "blocker": "" if status != "RED" else "Pending vendor fix / retest evidence",
                }
            )
    readiness = pd.DataFrame(readiness_rows)
    readiness.to_csv(DATA_DIR / "readiness.csv", index=False)

    evidence_types = [
        "Acceptance Report",
        "Punch List Snapshot",
        "Asset Registry Export",
        "Monitoring Proof",
        "On-call Roster",
        "SOP Document",
        "Training Attendance",
        "Dry Run Result",
    ]
    owners = ["Ops Readiness Lead", "IT Ops Lead", "Vendor Manager", "Security Ops Lead", "Venue Ops Lead"]

    evidence_rows: list[dict] = []
    evid_id = 1
    for svc in services["service"].tolist():
        n = rng.randint(7, 11)
        for _ in range(n):
            gate = rng.choice([g.code for g in GATES])
            et = rng.choice(evidence_types)

            svc_gate_status = readiness.loc[(readiness["service"] == svc) & (readiness["gate"] == gate), "status"].iloc[0]
            missing_prob = 0.55 if svc_gate_status == "RED" else (0.30 if svc_gate_status == "AMBER" else 0.10)
            status = "MISSING" if rng.random() < missing_prob else "COMPLETE"

            evidence_rows.append(
                {
                    "evidence_id": f"EVD-{evid_id:04d}",
                    "service": svc,
                    "gate": gate,
                    "evidence_type": et,
                    "owner": rng.choice(owners),
                    "status": status,
                    "updated_at": now - pd.Timedelta(hours=rng.randint(1, 240)),
                    "note": "" if status == "COMPLETE" else "Attach link/screenshot in the Go/No-Go pack",
                }
            )
            evid_id += 1
    evidence = pd.DataFrame(evidence_rows)
    evidence.to_csv(DATA_DIR / "evidence.csv", index=False)

    incident_rows: list[dict] = []
    inc_id = 1
    severities = [1, 2, 3, 4]  # 1 highest
    statuses = ["OPEN", "MITIGATED", "RESOLVED"]

    for _ in range(rng.randint(18, 30)):
        svc = rng.choice(services["service"].tolist())
        sev = rng.choice(severities)
        opened = now - pd.Timedelta(hours=rng.randint(2, 240))
        ack_delay_min = rng.randint(3, 35) if sev in (1, 2) else rng.randint(10, 120)
        resolve_delay_min = rng.randint(20, 160) if sev in (1, 2) else rng.randint(80, 720)

        ack_at = opened + pd.Timedelta(minutes=ack_delay_min)
        resolved_at = opened + pd.Timedelta(minutes=resolve_delay_min)

        st = rng.choice(statuses)
        if st in ("OPEN", "MITIGATED"):
            resolved_at = pd.NaT

        vendor = services.loc[services["service"] == svc, "vendor"].iloc[0]
        incident_rows.append(
            {
                "incident_id": f"INC-{inc_id:04d}",
                "service": svc,
                "vendor": vendor,
                "severity": sev,
                "status": st,
                "opened_at": opened,
                "ack_at": ack_at,
                "resolved_at": resolved_at,
                "summary": f"{svc} degradation during peak-like load",
                "rca_done": bool(rng.random() < 0.55),
                "prevent_action": "Run peak drill + tighten alert thresholds" if sev in (1, 2) else "Tune monitoring and capacity",
            }
        )
        inc_id += 1

    incidents = pd.DataFrame(incident_rows)
    incidents.to_csv(DATA_DIR / "incidents.csv", index=False)

    vendor_rows: list[dict] = []
    for _, row in services.iterrows():
        sla = 99.5 if row["criticality"] >= 2 else 99.0
        actual = float(np.clip(rng.normalvariate(mu=sla - 0.2, sigma=0.4), 97.5, 99.95))

        mtta_target = 10 if row["criticality"] == 3 else 20
        mttr_target = 60 if row["criticality"] == 3 else 180

        mtta_actual = int(np.clip(rng.normalvariate(mu=mtta_target * 1.1, sigma=6), 3, 120))
        mttr_actual = int(np.clip(rng.normalvariate(mu=mttr_target * 1.15, sigma=30), 10, 720))

        vendor_rows.append(
            {
                "vendor": row["vendor"],
                "service": row["service"],
                "sla_availability": sla,
                "availability_actual": round(actual, 2),
                "mtta_target_min": mtta_target,
                "mtta_actual_min": mtta_actual,
                "mttr_target_min": mttr_target,
                "mttr_actual_min": mttr_actual,
                "open_critical": rng.randint(0, 6),
                "last_review": now - pd.Timedelta(days=rng.randint(1, 14)),
            }
        )
    vendors = pd.DataFrame(vendor_rows)
    vendors.to_csv(DATA_DIR / "vendors.csv", index=False)

    # KPI time-series (hourly, last 7 days)
    start = (now - pd.Timedelta(days=7)).floor("h")
    ts = pd.date_range(start=start, end=now.floor("h"), freq="h", tz="UTC")
    kpi_rows: list[dict] = []

    for k in KPI_DEFINITIONS:
        base_target = float(k["target"])
        for t in ts:
            # Simulate peak periods
            hour = int(t.hour)
            peak = 1.0 if hour in (18, 19, 20, 21) else (0.6 if hour in (16, 17, 22) else 0.35)

            if "Queue" in k["kpi"]:
                # queue time higher in peak
                value = float(np.clip(rng.normalvariate(mu=base_target * (1.0 + peak), sigma=2.0), 2, 45))
                target = base_target
                direction = "LOWER_IS_BETTER"
            else:
                # success/availability slightly degrades at peak
                value = float(np.clip(rng.normalvariate(mu=base_target - (peak * 0.35), sigma=0.25), base_target - 3.0, 100.0))
                target = base_target
                direction = "HIGHER_IS_BETTER"

            kpi_rows.append(
                {
                    "ts": t,
                    "kpi": k["kpi"],
                    "service": k["service"],
                    "value": round(value, 3),
                    "target": target,
                    "direction": direction,
                }
            )
    kpis = pd.DataFrame(kpi_rows)
    kpis.to_csv(DATA_DIR / "kpis.csv", index=False)


if __name__ == "__main__":
    generate()
    print(f"Generated demo data in: {DATA_DIR}")
