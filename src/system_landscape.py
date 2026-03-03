"""System Landscape Registry.

Defines the TYPICAL destination/venue technology stack as example labels.

DISCLAIMER: These are common example systems for large venues/destinations;
the demo is source-agnostic and connectors can be swapped to match the
actual environment.  All names are trademarks of their respective owners.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SystemCategory:
    category: str
    badge_label: str  # short label shown in UI badges
    examples: list[str] = field(default_factory=list)
    optional: bool = False


# ── Corporate / Enterprise Platforms ────────────────────────────────────────

ITSM = SystemCategory(
    category="ITSM / Service Management",
    badge_label="ITSM",
    examples=[
        "ServiceNow (example)",
        "Jira Service Management (example)",
        "BMC Remedy (example)",
        "Freshservice (example)",
    ],
)

CMDB = SystemCategory(
    category="CMDB / Asset Management",
    badge_label="CMDB",
    examples=[
        "ServiceNow CMDB (example)",
        "Jira Assets (example)",
    ],
)

CMMS = SystemCategory(
    category="CMMS / EAM (Maintenance)",
    badge_label="CMMS",
    examples=[
        "IBM Maximo (example)",
        "SAP PM (example)",
        "Oracle EAM (example)",
    ],
)

EDMS = SystemCategory(
    category="EDMS / Document Control",
    badge_label="EDMS",
    examples=[
        "SharePoint / M365 (example)",
        "EDMS / Document Control (example)",
    ],
)

ERP = SystemCategory(
    category="ERP / Enterprise Apps",
    badge_label="ERP",
    examples=[
        "SAP S/4HANA (example)",
        "Oracle ERP (example)",
    ],
    optional=True,
)

CRM = SystemCategory(
    category="Guest / CRM",
    badge_label="CRM",
    examples=[
        "Microsoft Dynamics 365 (example)",
        "Adobe Experience (example)",
        "Sprinklr (example)",
    ],
    optional=True,
)

MONITORING = SystemCategory(
    category="Observability / Monitoring",
    badge_label="Monitoring",
    examples=[
        "Azure Monitor / Log Analytics (example)",
        "Prometheus / Grafana (example)",
        "Datadog (example)",
        "New Relic (example)",
    ],
)

SIEM = SystemCategory(
    category="Logging / SIEM",
    badge_label="SIEM",
    examples=[
        "Splunk (example)",
        "Elastic / ELK (example)",
        "Microsoft Sentinel (example)",
    ],
    optional=True,
)

# ── Venue / OT & Visitor Systems ─────────────────────────────────────────────

OT_EVENTS = SystemCategory(
    category="OT Events Feed",
    badge_label="OT",
    examples=[
        "BMS / Access Control / CCTV Event Feed (example)",
    ],
)

BMS = SystemCategory(
    category="BMS / Facilities Vendors",
    badge_label="BMS",
    examples=[
        "Honeywell (example)",
        "Siemens (example)",
        "Johnson Controls (example)",
        "Schneider Electric (example)",
    ],
    optional=True,
)

VMS = SystemCategory(
    category="VMS / CCTV Platforms",
    badge_label="VMS",
    examples=[
        "Genetec (example)",
        "Milestone (example)",
    ],
    optional=True,
)

ACCESS_CONTROL = SystemCategory(
    category="Access Control",
    badge_label="Access",
    examples=[
        "HID (example)",
    ],
    optional=True,
)

TICKETING = SystemCategory(
    category="Ticketing & Gate Validation",
    badge_label="Ticketing",
    examples=[
        "accesso Horizon (example)",
        "Ticketing Platform / Gate Validation (generic example)",
    ],
)

POS = SystemCategory(
    category="POS / Payments",
    badge_label="POS",
    examples=[
        "POS System + Payment Gateway Telemetry (example)",
    ],
    optional=True,
)

NETWORK = SystemCategory(
    category="Network / Wi-Fi / NAC",
    badge_label="Network",
    examples=[
        "Network Monitoring (example)",
    ],
    optional=True,
)

FOOTFALL = SystemCategory(
    category="Queue / Footfall Analytics",
    badge_label="Footfall",
    examples=[
        "Crowd / Queue Analytics (example)",
    ],
    optional=True,
)

SIGNAGE = SystemCategory(
    category="Digital Signage CMS",
    badge_label="Signage",
    examples=[
        "Signage CMS (example)",
    ],
    optional=True,
)

# ── Ordered landscape for README / UI display ────────────────────────────────

ALL_CATEGORIES: list[SystemCategory] = [
    ITSM, CMDB, CMMS, EDMS, ERP, CRM, MONITORING, SIEM,
    OT_EVENTS, BMS, VMS, ACCESS_CONTROL, TICKETING, POS,
    NETWORK, FOOTFALL, SIGNAGE,
]

CORE_BADGE_CATEGORIES: list[SystemCategory] = [
    c for c in ALL_CATEGORIES if not c.optional
]

# ── Source-system label pools (used by seed generator) ───────────────────────

ITSM_LABELS = ["ServiceNow", "Jira Service Management"]
CMDB_LABELS = ["ServiceNow CMDB", "Jira Assets"]
EDMS_LABELS = ["SharePoint / M365", "EDMS / Document Control"]
MONITORING_LABELS = ["Azure Monitor / Log Analytics", "Prometheus / Grafana", "Datadog"]
OT_LABELS = ["BMS / Access Control / CCTV Event Feed"]
TICKETING_LABELS = ["accesso Horizon", "Ticketing Platform / Gate Validation"]
ORR_TRACKER_LABELS = ["ORR Tracker / SharePoint"]

# ── ID pattern helpers ───────────────────────────────────────────────────────

def make_inc_id(n: int, source: str = "ServiceNow") -> str:
    """Return a realistic incident source ID."""
    if "Jira" in source:
        return f"OPS-{n:04d}"
    return f"INC{n:07d}"


def make_prb_id(n: int) -> str:
    return f"PRB{n:07d}"


def make_chg_id(n: int) -> str:
    return f"CHG{n:07d}"


def make_doc_ref(n: int) -> str:
    return f"DOC-ORR-{n:05d}"


def make_pl_id(year: int, n: int) -> str:
    return f"PL-{year}-{n:05d}"


def make_dash_ref(n: int) -> str:
    return f"DASH-{n:05d}"


def make_ci_id(n: int) -> str:
    return f"CI{n:07d}"


def make_ot_event_id(n: int) -> str:
    return f"EVT-OT-{n:06d}"


def make_device_id(n: int) -> str:
    return f"DEV-OT-{n:06d}"


# ── Anomaly thresholds ───────────────────────────────────────────────────────

THRESHOLDS = {
    "ticketing_scan_success_rate_warn": 0.97,   # below = warning
    "ticketing_scan_success_rate_crit": 0.94,   # below = critical
    "ticketing_latency_warn_ms": 800,
    "ticketing_latency_crit_ms": 1500,
    "ticketing_throughput_collapse_ppm": 20,    # below peak expected = anomaly
    "ot_unacked_sev1_warn": 0,                  # any unacked sev1 = warn
    "ot_unacked_sev2_warn": 2,
}

DISCLAIMER = (
    "These are common example systems for large venues; the demo is "
    "source-agnostic and connectors can be swapped to match the actual environment."
)
