from __future__ import annotations

from typing import Any

import pandas as pd

from src.system_landscape import THRESHOLDS


STATUS_COLOR_ORDER = {
    "OK": 0,
    "WARN": 1,
    "CRIT": 2,
}


def _minutes_between(start: pd.Series, end: pd.Series) -> pd.Series:
    return (end - start).dt.total_seconds() / 60.0


def compute_mtta_minutes(incidents: pd.DataFrame) -> float | None:
    required = {"opened_at", "ack_at"}
    if not required.issubset(set(incidents.columns)):
        return None
    df = incidents.dropna(subset=["opened_at", "ack_at"]).copy()
    if df.empty:
        return None
    minutes = _minutes_between(df["opened_at"], df["ack_at"]).dropna()
    return float(minutes.mean()) if not minutes.empty else None


def compute_mttr_minutes(incidents: pd.DataFrame) -> float | None:
    required = {"opened_at", "resolved_at"}
    if not required.issubset(set(incidents.columns)):
        return None
    df = incidents.dropna(subset=["opened_at", "resolved_at"]).copy()
    if df.empty:
        return None
    minutes = _minutes_between(df["opened_at"], df["resolved_at"]).dropna()
    return float(minutes.mean()) if not minutes.empty else None


def classify_metric(
    value: float | None,
    warn: float,
    crit: float,
    *,
    higher_is_better: bool = False,
) -> str:
    if value is None:
        return "WARN"
    if higher_is_better:
        if value < crit:
            return "CRIT"
        if value < warn:
            return "WARN"
        return "OK"
    if value > crit:
        return "CRIT"
    if value > warn:
        return "WARN"
    return "OK"


def readiness_score(readiness: pd.DataFrame) -> pd.DataFrame:
    status_map = {"GREEN": 2, "AMBER": 1, "RED": 0}
    df = readiness.copy()
    df["score"] = df["status"].map(status_map).fillna(-1).astype(int)
    return (
        df.groupby("service", as_index=False)
        .agg(score=("score", "mean"), reds=("status", lambda values: int((values == "RED").sum())))
        .sort_values(["reds", "score", "service"], ascending=[False, True, True])
    )


def readiness_summary(readiness: pd.DataFrame) -> dict[str, Any]:
    if readiness.empty:
        return {
            "red_gate_count": 0,
            "amber_gate_count": 0,
            "green_gate_count": 0,
            "hold_count": 0,
            "top_blockers": [],
            "service_ranking": [],
        }
    red = int((readiness["status"] == "RED").sum())
    amber = int((readiness["status"] == "AMBER").sum())
    green = int((readiness["status"] == "GREEN").sum())
    hold_count = int((readiness.get("go_no_go", pd.Series(dtype=str)) == "HOLD").sum())
    blocker_cols = [column for column in ["service", "gate", "gate_name", "blocker", "blocking_dependency", "gate_owner", "source_system"] if column in readiness.columns]
    blockers = (
        readiness[readiness["status"] == "RED"][blocker_cols]
        .head(8)
        .to_dict(orient="records")
    )
    return {
        "red_gate_count": red,
        "amber_gate_count": amber,
        "green_gate_count": green,
        "hold_count": hold_count,
        "top_blockers": blockers,
        "service_ranking": readiness_score(readiness).to_dict(orient="records"),
    }


def evidence_completion(evidence: pd.DataFrame) -> pd.DataFrame:
    df = evidence.copy()
    df["is_complete"] = (df["status"] == "COMPLETE").astype(int)
    out = df.groupby(["service", "gate"], as_index=False).agg(
        items=("evidence_id", "count"),
        complete=("is_complete", "sum"),
    )
    out["completion"] = (out["complete"] / out["items"]).fillna(0.0)
    return out


def evidence_summary(evidence: pd.DataFrame) -> dict[str, Any]:
    if evidence.empty:
        return {
            "missing_count": 0,
            "completion_rate": 0.0,
            "missing_top": [],
            "owners": [],
        }
    missing = evidence[evidence["status"] == "MISSING"].copy()
    completion_rate = float((evidence["status"] == "COMPLETE").mean()) if len(evidence) else 0.0
    owner_backlog = []
    if "owner" in missing.columns and not missing.empty:
        owner_backlog = (
            missing.groupby("owner", as_index=False)
            .agg(missing_items=("evidence_id", "count"))
            .sort_values("missing_items", ascending=False)
            .to_dict(orient="records")
        )
    columns = [
        column
        for column in ["evidence_id", "service", "gate", "evidence_type", "owner", "doc_ref", "approval_status", "source_system"]
        if column in missing.columns
    ]
    return {
        "missing_count": int(len(missing)),
        "completion_rate": completion_rate,
        "missing_top": missing[columns].head(10).to_dict(orient="records") if columns else [],
        "owners": owner_backlog,
    }


def vendor_scorecard(vendors: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "vendor",
        "service",
        "sla_availability",
        "availability_actual",
        "mtta_target_min",
        "mtta_actual_min",
        "mttr_target_min",
        "mttr_actual_min",
        "open_critical",
        "last_review",
        "source_system",
        "dashboard_ref",
        "contract_sla",
        "escalation_level",
        "penalty_risk",
        "service_credit_applicable",
    ]
    out = vendors.copy()
    for column in columns:
        if column not in out.columns:
            out[column] = pd.NA

    out["availability_breach"] = (
        pd.to_numeric(out["availability_actual"], errors="coerce")
        < pd.to_numeric(out["sla_availability"], errors="coerce")
    )
    out["mtta_breach"] = (
        pd.to_numeric(out["mtta_actual_min"], errors="coerce")
        > pd.to_numeric(out["mtta_target_min"], errors="coerce")
    )
    out["mttr_breach"] = (
        pd.to_numeric(out["mttr_actual_min"], errors="coerce")
        > pd.to_numeric(out["mttr_target_min"], errors="coerce")
    )
    out["breach_count"] = out[["availability_breach", "mtta_breach", "mttr_breach"]].fillna(False).sum(axis=1)
    return out[columns + ["availability_breach", "mtta_breach", "mttr_breach", "breach_count"]]


def vendor_summary(vendors: pd.DataFrame) -> dict[str, Any]:
    scorecard = vendor_scorecard(vendors)
    breach_vendors = scorecard[scorecard["breach_count"] > 0].sort_values(
        ["breach_count", "penalty_risk"],
        ascending=[False, False],
    )
    columns = [
        column
        for column in ["vendor", "service", "breach_count", "penalty_risk", "dashboard_ref", "source_system"]
        if column in breach_vendors.columns
    ]
    return {
        "breach_count": int((scorecard["breach_count"] > 0).sum()) if not scorecard.empty else 0,
        "high_penalty_risk": int((scorecard.get("penalty_risk", pd.Series(dtype=str)) == "High").sum()),
        "service_credits": int(scorecard.get("service_credit_applicable", pd.Series(dtype=bool)).fillna(False).sum()) if not scorecard.empty else 0,
        "breach_vendors": breach_vendors[columns].head(10).to_dict(orient="records") if columns else [],
    }


def incident_summary(incidents: pd.DataFrame) -> dict[str, Any]:
    if incidents.empty:
        return {
            "open_count": 0,
            "open_sev1_2": 0,
            "mtta_min": None,
            "mttr_min": None,
            "sla_breaches": 0,
            "open_top": [],
        }
    open_incidents = incidents[incidents["status"].isin(["OPEN", "MITIGATED"])].copy()
    sev12 = open_incidents[open_incidents["severity"].isin([1, 2])]
    columns = [
        column
        for column in ["incident_id", "source_id", "service", "severity", "status", "summary", "assigned_group", "source_system"]
        if column in open_incidents.columns
    ]
    return {
        "open_count": int(len(open_incidents)),
        "open_sev1_2": int(len(sev12)),
        "mtta_min": compute_mtta_minutes(incidents),
        "mttr_min": compute_mttr_minutes(incidents),
        "sla_breaches": int(incidents.get("sla_breached", pd.Series(dtype=bool)).fillna(False).sum()),
        "open_top": open_incidents.sort_values("opened_at", ascending=False)[columns].head(10).to_dict(orient="records"),
    }


def ot_event_summary(ot_events: pd.DataFrame) -> dict[str, Any]:
    if ot_events is None or ot_events.empty:
        return {
            "unacked_sev1": 0,
            "unacked_sev2": 0,
            "total_open": 0,
            "mean_ack_min": None,
            "clusters": [],
            "top_open_events": [],
        }

    df = ot_events.copy()
    unacked = df[df["ack_time"].isna()] if "ack_time" in df.columns else df
    open_events = df[df["cleared_time"].isna()] if "cleared_time" in df.columns else df
    severity_column = "severity" if "severity" in df.columns else None

    unacked_sev1 = int((unacked[severity_column] == 1).sum()) if severity_column else 0
    unacked_sev2 = int((unacked[severity_column] == 2).sum()) if severity_column else 0

    clusters: list[dict[str, Any]] = []
    if severity_column and {"zone", "subsystem"}.issubset(df.columns):
        critical = unacked[unacked[severity_column].isin([1, 2])]
        if not critical.empty:
            grouped = (
                critical.groupby(["zone", "subsystem"], as_index=False)
                .size()
                .sort_values("size", ascending=False)
                .head(5)
            )
            clusters = grouped.to_dict(orient="records")

    columns = [
        column
        for column in ["ot_event_id", "subsystem", "alarm_type", "zone", "device_id", "severity", "linked_incident_id", "source_system"]
        if column in open_events.columns
    ]
    return {
        "unacked_sev1": unacked_sev1,
        "unacked_sev2": unacked_sev2,
        "total_open": int(len(open_events)),
        "mean_ack_min": compute_ot_mean_ack_minutes(df),
        "clusters": clusters,
        "top_open_events": open_events.sort_values("event_time", ascending=False)[columns].head(8).to_dict(orient="records"),
    }


def compute_ot_mean_ack_minutes(ot_events: pd.DataFrame) -> float | None:
    if ot_events is None or ot_events.empty:
        return None
    required = {"event_time", "ack_time"}
    if not required.issubset(set(ot_events.columns)):
        return None
    df = ot_events.dropna(subset=["event_time", "ack_time"]).copy()
    if df.empty:
        return None
    minutes = _minutes_between(df["event_time"], df["ack_time"]).dropna()
    return float(minutes.mean()) if not minutes.empty else None


def ticketing_kpi_summary(ticketing_kpis: pd.DataFrame) -> dict[str, Any]:
    if ticketing_kpis is None or ticketing_kpis.empty:
        return {
            "anomaly_windows": 0,
            "min_success_rate": None,
            "max_latency_p95": None,
            "total_offline_fallbacks": 0,
            "total_denied": 0,
            "throughput_collapses": 0,
            "payment_dependency_windows": 0,
            "worst_areas": [],
        }

    df = ticketing_kpis.copy()
    warn_threshold = THRESHOLDS["ticketing_scan_success_rate_warn"]
    crit_latency = THRESHOLDS["ticketing_latency_crit_ms"]
    throughput_floor = THRESHOLDS["ticketing_throughput_collapse_ppm"]

    scan_series = pd.to_numeric(df.get("scan_success_rate", pd.Series(dtype=float)), errors="coerce")
    latency_series = pd.to_numeric(df.get("qr_validation_latency_ms_p95", pd.Series(dtype=float)), errors="coerce")
    throughput_series = pd.to_numeric(df.get("gate_throughput_ppm", pd.Series(dtype=float)), errors="coerce")

    anomaly_mask = (scan_series < warn_threshold) | (latency_series > crit_latency)
    anomaly_windows = int(anomaly_mask.fillna(False).sum())
    throughput_collapses = int((throughput_series < throughput_floor).fillna(False).sum())
    payment_dependency_windows = int(df.get("payment_dependency_flag", pd.Series(dtype=bool)).fillna(False).sum())

    worst_areas: list[dict[str, Any]] = []
    if {"venue_area", "scan_success_rate"}.issubset(df.columns):
        worst_areas = (
            df.groupby("venue_area", as_index=False)
            .agg(
                min_success_rate=("scan_success_rate", "min"),
                max_latency_p95=("qr_validation_latency_ms_p95", "max"),
                anomaly_windows=("scan_success_rate", lambda values: int((pd.to_numeric(values, errors="coerce") < warn_threshold).sum())),
            )
            .sort_values(["min_success_rate", "max_latency_p95"], ascending=[True, False])
            .head(6)
            .to_dict(orient="records")
        )

    min_success_rate = float(scan_series.min()) if not scan_series.dropna().empty else None
    max_latency = float(latency_series.max()) if not latency_series.dropna().empty else None
    total_offline = int(df.get("offline_fallback_activations", pd.Series([0])).fillna(0).sum())
    total_denied = int(df.get("denied_entries", pd.Series([0])).fillna(0).sum())

    return {
        "anomaly_windows": anomaly_windows,
        "min_success_rate": min_success_rate,
        "max_latency_p95": max_latency,
        "total_offline_fallbacks": total_offline,
        "total_denied": total_denied,
        "throughput_collapses": throughput_collapses,
        "payment_dependency_windows": payment_dependency_windows,
        "worst_areas": worst_areas,
    }
