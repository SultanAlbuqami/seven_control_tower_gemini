from __future__ import annotations

from dataclasses import dataclass
from typing import Final


DISCLAIMER: Final[str] = (
    "These are common example systems for large venues; the demo is source-agnostic "
    "and connectors can be swapped to match the actual environment."
)

DEFAULT_STACK_NAME: Final[str] = "Typical Destination / Venue Stack"


@dataclass(frozen=True)
class LandscapeCategory:
    slug: str
    family: str
    badge_label: str
    badge_tooltip: str
    category: str
    examples: tuple[str, ...]
    contributions: tuple[str, ...]
    trace_fields: tuple[str, ...]
    id_rule: str
    optional: bool = False


ITSM_CMDB_LABELS: Final[tuple[str, ...]] = (
    "ServiceNow (example)",
    "Jira Service Management (example)",
    "BMC Remedy (example)",
    "Freshservice (example)",
)

CMMS_EAM_LABELS: Final[tuple[str, ...]] = (
    "IBM Maximo (example)",
    "SAP PM (example)",
    "Oracle EAM (example)",
)

EDMS_LABELS: Final[tuple[str, ...]] = (
    "SharePoint/M365 (example)",
    "Generic EDMS (example)",
)

ERP_LABELS: Final[tuple[str, ...]] = (
    "SAP S/4HANA (example)",
    "Oracle ERP (example)",
)

CRM_LABELS: Final[tuple[str, ...]] = (
    "Microsoft Dynamics 365 (example)",
    "Adobe Experience (example)",
    "Sprinklr (example)",
)

OBSERVABILITY_LABELS: Final[tuple[str, ...]] = (
    "Azure Monitor/Log Analytics (example)",
    "Prometheus/Grafana (example)",
    "Datadog (example)",
    "New Relic (example)",
)

SIEM_LABELS: Final[tuple[str, ...]] = (
    "Splunk (example)",
    "Elastic/ELK (example)",
    "Microsoft Sentinel (example)",
)

OT_EVENT_FEED_LABELS: Final[tuple[str, ...]] = (
    "BMS / Access Control / CCTV Event Feed (example)",
)

BMS_VENDOR_LABELS: Final[tuple[str, ...]] = (
    "Honeywell (example)",
    "Siemens (example)",
    "Johnson Controls (example)",
    "Schneider Electric (example)",
)

VMS_CCTV_LABELS: Final[tuple[str, ...]] = (
    "Genetec (example)",
    "Milestone (example)",
)

ACCESS_CONTROL_LABELS: Final[tuple[str, ...]] = (
    "HID (example)",
)

TICKETING_LABELS: Final[tuple[str, ...]] = (
    "accesso Horizon (example)",
    "Generic Ticketing/Gate Validation Platform (example)",
)

POS_PAYMENTS_LABELS: Final[tuple[str, ...]] = (
    "POS System + Payment Gateway Telemetry (example)",
)

NETWORK_LABELS: Final[tuple[str, ...]] = (
    "Network Monitoring Platform (example)",
)

QUEUE_ANALYTICS_LABELS: Final[tuple[str, ...]] = (
    "Crowd/Queue Analytics (example)",
)

SIGNAGE_LABELS: Final[tuple[str, ...]] = (
    "Signage CMS (example)",
)

PMIS_LABELS: Final[tuple[str, ...]] = (
    "Oracle Primavera Unifier (example)",
    "PMWeb (example)",
    "Procore (example)",
)

WFM_LABELS: Final[tuple[str, ...]] = (
    "UKG/Kronos Workforce Central (example)",
    "Oracle Workforce Management (example)",
    "SAP SuccessFactors Time Tracking (example)",
)

CDE_BIM_LABELS: Final[tuple[str, ...]] = (
    "Autodesk Construction Cloud / BIM 360 (example)",
    "Bentley ProjectWise (example)",
    "Procore Documents / Handover (example)",
)

PARKING_MOBILITY_LABELS: Final[tuple[str, ...]] = (
    "Parking Guidance Platform (example)",
    "Traffic Operations Platform (example)",
    "Mobility Aggregator (example)",
)

CAD_DISPATCH_RADIO_LABELS: Final[tuple[str, ...]] = (
    "Motorola Solutions CommandCentral (example)",
    "Hexagon CAD (example)",
    "Radio Dispatch Platform (example)",
)

IAM_SSO_LABELS: Final[tuple[str, ...]] = (
    "Microsoft Entra ID (example)",
    "Okta (example)",
    "Ping Identity (example)",
)

ORR_TRACKER_LABELS: Final[tuple[str, ...]] = (
    "ORR Tracker / SharePoint (example)",
    "ORR Tracker / Project Controls (example)",
    "PMIS / Project Controls (example)",
)

ACRONYM_GLOSSARY: Final[dict[str, str]] = {
    "BMS": "Building Management System",
    "CMDB": "Configuration Management Database",
    "CMMS": "Computerized Maintenance Management System",
    "CRM": "Customer Relationship Management",
    "CCTV": "Closed-Circuit Television",
    "CDE": "Common Data Environment",
    "EAM": "Enterprise Asset Management",
    "EDMS": "Electronic Document Management System",
    "ERP": "Enterprise Resource Planning",
    "BIM": "Building Information Modeling",
    "CAD": "Computer-Aided Dispatch",
    "IAM": "Identity and Access Management",
    "ITSM": "IT Service Management",
    "NAC": "Network Access Control",
    "OT": "Operational Technology",
    "PMIS": "Project Management Information System",
    "POS": "Point of Sale",
    "SIEM": "Security Information and Event Management",
    "SSO": "Single Sign-On",
    "VMS": "Video Management System",
    "WFM": "Workforce Management",
}

LANDSCAPE_CATEGORIES: Final[tuple[LandscapeCategory, ...]] = (
    LandscapeCategory(
        slug="itsm_cmdb",
        family="Enterprise / Corporate",
        badge_label="ITSM / CMDB",
        badge_tooltip="IT Service Management / Configuration Management Database",
        category="ITSM/CMDB",
        examples=ITSM_CMDB_LABELS,
        contributions=("Incidents", "Change references", "Service ownership", "CI metadata"),
        trace_fields=("source_system", "source_id", "ci_id"),
        id_rule="INC0012345, PRB0012345, CHG0012345, or OPS-1234",
    ),
    LandscapeCategory(
        slug="cmms_eam",
        family="Enterprise / Corporate",
        badge_label="CMMS / EAM",
        badge_tooltip="Computerized Maintenance Management System / Enterprise Asset Management",
        category="CMMS/EAM",
        examples=CMMS_EAM_LABELS,
        contributions=("Punch lists", "Maintenance backlog", "Asset readiness"),
        trace_fields=("source_system", "punch_list_id", "service_id"),
        id_rule="PL-YYYY-xxxxx",
    ),
    LandscapeCategory(
        slug="edms_document_control",
        family="Enterprise / Corporate",
        badge_label="EDMS",
        badge_tooltip="Electronic Document Management System",
        category="EDMS/Document Control",
        examples=EDMS_LABELS,
        contributions=("Evidence packs", "Approvals", "Document control"),
        trace_fields=("source_system", "doc_ref", "approval_status"),
        id_rule="DOC-ORR-00087",
    ),
    LandscapeCategory(
        slug="erp_enterprise_apps",
        family="Enterprise / Corporate",
        badge_label="ERP",
        badge_tooltip="Enterprise Resource Planning",
        category="ERP/Enterprise Apps",
        examples=ERP_LABELS,
        contributions=("Commercial context", "Contract metadata", "Cost ownership"),
        trace_fields=("source_system", "dashboard_ref", "owner_team"),
        id_rule="DASH-00012",
        optional=True,
    ),
    LandscapeCategory(
        slug="guest_crm",
        family="Enterprise / Corporate",
        badge_label="Guest / CRM",
        badge_tooltip="Guest systems / Customer Relationship Management",
        category="Guest/CRM",
        examples=CRM_LABELS,
        contributions=("Guest communications", "Campaign coordination", "Case context"),
        trace_fields=("source_system", "service_id", "owner_team"),
        id_rule="SVC-001",
        optional=True,
    ),
    LandscapeCategory(
        slug="observability_monitoring",
        family="Enterprise / Corporate",
        badge_label="Observability",
        badge_tooltip="Monitoring, telemetry, logs, traces, and alerting",
        category="Observability/Monitoring",
        examples=OBSERVABILITY_LABELS,
        contributions=("Availability KPIs", "Latency", "Vendor dashboards"),
        trace_fields=("source_system", "dashboard_ref", "service_credit_applicable"),
        id_rule="DASH-00012",
    ),
    LandscapeCategory(
        slug="logging_siem",
        family="Enterprise / Corporate",
        badge_label="Logging / SIEM",
        badge_tooltip="Logging / Security Information and Event Management",
        category="Logging/SIEM",
        examples=SIEM_LABELS,
        contributions=("Security event context", "Correlation support"),
        trace_fields=("source_system", "source_id", "assigned_group"),
        id_rule="INC0012345 or OPS-1234",
        optional=True,
    ),
    LandscapeCategory(
        slug="pmis_project_controls",
        family="Enterprise / Corporate",
        badge_label="PMIS",
        badge_tooltip="Project Management Information System",
        category="Project Controls / PMIS",
        examples=PMIS_LABELS,
        contributions=("Milestones", "Handover packages", "Authority approvals", "Action tracking"),
        trace_fields=("source_system", "doc_ref", "service_id"),
        id_rule="ACT-000123 or PKG-ORR-001",
        optional=True,
    ),
    LandscapeCategory(
        slug="wfm_rostering",
        family="Enterprise / Corporate",
        badge_label="WFM",
        badge_tooltip="Workforce Management and rostering",
        category="Workforce Management / Rostering",
        examples=WFM_LABELS,
        contributions=("Shift coverage", "Role readiness", "Training roster assurance"),
        trace_fields=("source_system", "owner_team", "service_id"),
        id_rule="SHIFT-000123 or ROSTER-OPS-01",
        optional=True,
    ),
    LandscapeCategory(
        slug="cde_bim_handover",
        family="Enterprise / Corporate",
        badge_label="CDE / BIM",
        badge_tooltip="Common Data Environment / Building Information Modeling / Handover",
        category="CDE / BIM / Handover",
        examples=CDE_BIM_LABELS,
        contributions=("As-built packages", "Handover completeness", "Model and document traceability"),
        trace_fields=("source_system", "doc_ref", "service_id"),
        id_rule="HB-000123 or BIM-MDL-001",
        optional=True,
    ),
    LandscapeCategory(
        slug="iam_sso",
        family="Enterprise / Corporate",
        badge_label="IAM / SSO",
        badge_tooltip="Identity and Access Management / Single Sign-On",
        category="IAM / SSO",
        examples=IAM_SSO_LABELS,
        contributions=("Operator access readiness", "Role and privilege assurance", "Authentication traceability"),
        trace_fields=("source_system", "owner_team", "service_id"),
        id_rule="ROLE-SEC-01 or APP-ACCESS-001",
        optional=True,
    ),
    LandscapeCategory(
        slug="ot_events_feed",
        family="Venue / OT and Visitor Systems",
        badge_label="OT Events",
        badge_tooltip="Operational Technology events and alarms",
        category="OT Events Feed",
        examples=OT_EVENT_FEED_LABELS,
        contributions=("Live alarms", "Subsystem health", "Device-level traces"),
        trace_fields=("source_system", "ot_event_id", "device_id"),
        id_rule="EVT-OT-000123 and DEV-OT-000123",
    ),
    LandscapeCategory(
        slug="bms_facilities",
        family="Venue / OT and Visitor Systems",
        badge_label="BMS",
        badge_tooltip="Building Management System",
        category="BMS/Facilities vendors",
        examples=BMS_VENDOR_LABELS,
        contributions=("Building automation context", "Facilities ownership"),
        trace_fields=("source_system", "device_id", "zone"),
        id_rule="DEV-OT-000123",
        optional=True,
    ),
    LandscapeCategory(
        slug="vms_cctv",
        family="Venue / OT and Visitor Systems",
        badge_label="VMS / CCTV",
        badge_tooltip="Video Management System / Closed-Circuit Television",
        category="VMS/CCTV",
        examples=VMS_CCTV_LABELS,
        contributions=("Camera health", "Security visibility", "Alarm context"),
        trace_fields=("source_system", "device_id", "linked_incident_id"),
        id_rule="DEV-OT-000123",
        optional=True,
    ),
    LandscapeCategory(
        slug="access_control",
        family="Venue / OT and Visitor Systems",
        badge_label="Access",
        badge_tooltip="Physical access control systems",
        category="Access Control",
        examples=ACCESS_CONTROL_LABELS,
        contributions=("Door and gate controller state", "Entry-device alarms"),
        trace_fields=("source_system", "device_id", "linked_incident_id"),
        id_rule="DEV-OT-000123",
        optional=True,
    ),
    LandscapeCategory(
        slug="ticketing_gate_validation",
        family="Venue / OT and Visitor Systems",
        badge_label="Ticketing",
        badge_tooltip="Ticketing and gate validation telemetry",
        category="Ticketing and Gate Validation",
        examples=TICKETING_LABELS,
        contributions=("Scan success", "QR latency", "Throughput", "Offline fallback events"),
        trace_fields=("source_system", "linked_incident_id", "venue_area"),
        id_rule="INC-0001 linkage plus venue-area timestamps",
    ),
    LandscapeCategory(
        slug="pos_payments",
        family="Venue / OT and Visitor Systems",
        badge_label="POS / Payments",
        badge_tooltip="Point of Sale and payment telemetry",
        category="POS/Payments",
        examples=POS_PAYMENTS_LABELS,
        contributions=("Payment dependency signals", "Revenue protection"),
        trace_fields=("source_system", "service_id", "dashboard_ref"),
        id_rule="SVC-003 and DASH-00012",
        optional=True,
    ),
    LandscapeCategory(
        slug="network_wifi_nac",
        family="Venue / OT and Visitor Systems",
        badge_label="Network",
        badge_tooltip="Network, Wi-Fi, and network access control visibility",
        category="Network/Wi-Fi/NAC",
        examples=NETWORK_LABELS,
        contributions=("Connectivity health", "Wi-Fi readiness", "Dependency visibility"),
        trace_fields=("source_system", "dashboard_ref", "assigned_group"),
        id_rule="DASH-00012",
        optional=True,
    ),
    LandscapeCategory(
        slug="parking_traffic_mobility",
        family="Venue / OT and Visitor Systems",
        badge_label="Parking / Mobility",
        badge_tooltip="Parking, traffic, and mobility operations",
        category="Parking / Traffic / Mobility",
        examples=PARKING_MOBILITY_LABELS,
        contributions=("Arrival flow", "Occupancy pressure", "Ingress and egress coordination"),
        trace_fields=("source_system", "dashboard_ref", "venue_area"),
        id_rule="PARK-AREA-01 or DASH-00077",
        optional=True,
    ),
    LandscapeCategory(
        slug="cad_dispatch_radio",
        family="Venue / OT and Visitor Systems",
        badge_label="CAD / Radio",
        badge_tooltip="Computer-Aided Dispatch, dispatch, and radio operations",
        category="CAD / Dispatch / Radio",
        examples=CAD_DISPATCH_RADIO_LABELS,
        contributions=("Dispatch events", "Field response coordination", "Radio resilience"),
        trace_fields=("source_system", "source_id", "assigned_group"),
        id_rule="CAD-000123 or TG-OPS-01",
        optional=True,
    ),
    LandscapeCategory(
        slug="queue_footfall_analytics",
        family="Venue / OT and Visitor Systems",
        badge_label="Queue / Footfall",
        badge_tooltip="Crowd, queue, and footfall analytics",
        category="Queue/Footfall Analytics",
        examples=QUEUE_ANALYTICS_LABELS,
        contributions=("Guest flow context", "Demand signals", "Congestion patterns"),
        trace_fields=("source_system", "venue_area", "ts"),
        id_rule="Timestamp plus venue area",
        optional=True,
    ),
    LandscapeCategory(
        slug="digital_signage",
        family="Venue / OT and Visitor Systems",
        badge_label="Signage",
        badge_tooltip="Digital signage and wayfinding content management",
        category="Digital Signage",
        examples=SIGNAGE_LABELS,
        contributions=("Wayfinding readiness", "Guest comms coverage"),
        trace_fields=("source_system", "service_id", "dashboard_ref"),
        id_rule="SVC-007 and DASH-00012",
        optional=True,
    ),
)

ALL_CATEGORIES: Final[list[LandscapeCategory]] = list(LANDSCAPE_CATEGORIES)
CORE_BADGE_CATEGORIES: Final[list[LandscapeCategory]] = [
    category for category in ALL_CATEGORIES if not category.optional
]
CATEGORY_BY_SLUG: Final[dict[str, LandscapeCategory]] = {
    category.slug: category for category in ALL_CATEGORIES
}
LABEL_POOLS: Final[dict[str, tuple[str, ...]]] = {
    category.slug: category.examples for category in ALL_CATEGORIES
}
ID_RULES: Final[dict[str, str]] = {
    category.slug: category.id_rule for category in ALL_CATEGORIES
}

THRESHOLDS: Final[dict[str, float | int]] = {
    "ticketing_scan_success_rate_warn": 0.97,
    "ticketing_scan_success_rate_crit": 0.94,
    "ticketing_latency_warn_ms": 800,
    "ticketing_latency_crit_ms": 1500,
    "ticketing_throughput_collapse_ppm": 20,
    "ot_unacked_sev1_warn": 0,
    "ot_unacked_sev2_warn": 2,
    "wfm_fill_rate_warn": 0.95,
    "wfm_fill_rate_crit": 0.90,
    "wfm_training_warn": 0.95,
    "wfm_training_crit": 0.90,
    "parking_occupancy_warn": 0.90,
    "parking_occupancy_crit": 0.97,
    "parking_queue_warn_min": 10,
    "parking_queue_crit_min": 18,
    "parking_ingress_warn_min": 12,
    "parking_ingress_crit_min": 20,
    "iam_mfa_warn": 0.95,
    "iam_mfa_crit": 0.90,
    "iam_pending_privileged_warn": 3,
    "iam_pending_privileged_crit": 8,
}


def acronym_guide_rows() -> list[dict[str, str]]:
    return [
        {"abbreviation": acronym, "full_name": full_name}
        for acronym, full_name in sorted(ACRONYM_GLOSSARY.items())
    ]


def make_ci_id(number: int) -> str:
    return f"CI{number:07d}"


def make_doc_ref(number: int) -> str:
    return f"DOC-ORR-{number:05d}"


def make_punch_list_id(year: int, number: int) -> str:
    return f"PL-{year}-{number:05d}"


def make_dashboard_ref(number: int) -> str:
    return f"DASH-{number:05d}"


def make_service_id(number: int) -> str:
    return f"SVC-{number:03d}"


def make_incident_id(number: int) -> str:
    return f"INC-{number:04d}"


def make_shift_id(number: int) -> str:
    return f"SHIFT-{number:06d}"


def make_roster_ref(number: int) -> str:
    return f"ROSTER-OPS-{number:05d}"


def make_arrival_ref(number: int) -> str:
    return f"ARR-{number:05d}"


def make_access_review_id(number: int) -> str:
    return f"ACC-REV-{number:05d}"


def make_source_id(number: int, source_system: str, prefix: str = "INC") -> str:
    if "Jira Service Management" in source_system:
        return f"OPS-{number:04d}"
    token = prefix.upper()
    if token not in {"INC", "PRB", "CHG"}:
        token = "INC"
    return f"{token}{number:07d}"


def make_ot_event_id(number: int) -> str:
    return f"EVT-OT-{number:06d}"


def make_device_id(number: int) -> str:
    return f"DEV-OT-{number:06d}"
