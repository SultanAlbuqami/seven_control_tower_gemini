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


def wfm_roster_summary(wfm_roster: pd.DataFrame) -> dict[str, Any]:
    if wfm_roster is None or wfm_roster.empty:
        return {
            "total_shifts": 0,
            "critical_shift_gaps": 0,
            "overall_fill_rate": None,
            "undertrained_shifts": 0,
            "backfill_required": 0,
            "top_service_gaps": [],
        }

    df = wfm_roster.copy()
    required = pd.to_numeric(df.get("required_headcount", pd.Series(dtype=float)), errors="coerce")
    checked_in = pd.to_numeric(df.get("checked_in_headcount", pd.Series(dtype=float)), errors="coerce")
    training = pd.to_numeric(df.get("training_compliance_rate", pd.Series(dtype=float)), errors="coerce")
    critical = df.get("critical_role_flag", pd.Series(dtype=bool)).fillna(False).astype(bool)
    backfill = df.get("backfill_required_flag", pd.Series(dtype=bool)).fillna(False).astype(bool)

    critical_gap_mask = critical & (checked_in < required)
    undertrained_mask = training < THRESHOLDS["wfm_training_warn"]
    total_required = float(required.fillna(0).sum())
    overall_fill_rate = float(checked_in.fillna(0).sum() / total_required) if total_required > 0 else None

    top_service_gaps: list[dict[str, Any]] = []
    if "service" in df.columns:
        service_view = df.assign(
            critical_gap=critical_gap_mask.astype(int),
            undertrained=undertrained_mask.astype(int),
        )
        grouped = (
            service_view.groupby("service", as_index=False)
            .agg(
                required_headcount=("required_headcount", "sum"),
                checked_in_headcount=("checked_in_headcount", "sum"),
                critical_shift_gaps=("critical_gap", "sum"),
                undertrained_shifts=("undertrained", "sum"),
            )
        )
        grouped["fill_rate"] = (
            pd.to_numeric(grouped["checked_in_headcount"], errors="coerce")
            / pd.to_numeric(grouped["required_headcount"], errors="coerce").replace(0, pd.NA)
        ).fillna(0.0)
        top_service_gaps = (
            grouped.sort_values(["critical_shift_gaps", "fill_rate", "undertrained_shifts"], ascending=[False, True, False])
            .head(8)
            .to_dict(orient="records")
        )

    return {
        "total_shifts": int(len(df)),
        "critical_shift_gaps": int(critical_gap_mask.fillna(False).sum()),
        "overall_fill_rate": overall_fill_rate,
        "undertrained_shifts": int(undertrained_mask.fillna(False).sum()),
        "backfill_required": int(backfill.sum()),
        "top_service_gaps": top_service_gaps,
    }


def parking_mobility_summary(parking_mobility: pd.DataFrame) -> dict[str, Any]:
    if parking_mobility is None or parking_mobility.empty:
        return {
            "congestion_windows": 0,
            "max_occupancy_pct": None,
            "max_queue_minutes": None,
            "max_ingress_time_min_p95": None,
            "staffing_dependency_windows": 0,
            "incident_windows": 0,
            "worst_areas": [],
        }

    df = parking_mobility.copy()
    occupancy = pd.to_numeric(df.get("occupancy_pct", pd.Series(dtype=float)), errors="coerce")
    queue = pd.to_numeric(df.get("queue_minutes", pd.Series(dtype=float)), errors="coerce")
    ingress = pd.to_numeric(df.get("ingress_time_min_p95", pd.Series(dtype=float)), errors="coerce")
    congestion_mask = (
        (occupancy > THRESHOLDS["parking_occupancy_warn"])
        | (queue > THRESHOLDS["parking_queue_warn_min"])
        | (ingress > THRESHOLDS["parking_ingress_warn_min"])
    )

    worst_areas: list[dict[str, Any]] = []
    if "venue_area" in df.columns:
        area_view = df.assign(congestion=congestion_mask.fillna(False).astype(int))
        worst_areas = (
            area_view.groupby("venue_area", as_index=False)
            .agg(
                max_occupancy_pct=("occupancy_pct", "max"),
                max_queue_minutes=("queue_minutes", "max"),
                max_ingress_time_min_p95=("ingress_time_min_p95", "max"),
                congestion_windows=("congestion", "sum"),
            )
            .sort_values(
                ["congestion_windows", "max_queue_minutes", "max_occupancy_pct"],
                ascending=[False, False, False],
            )
            .head(6)
            .to_dict(orient="records")
        )

    return {
        "congestion_windows": int(congestion_mask.fillna(False).sum()),
        "max_occupancy_pct": float(occupancy.max()) if not occupancy.dropna().empty else None,
        "max_queue_minutes": float(queue.max()) if not queue.dropna().empty else None,
        "max_ingress_time_min_p95": float(ingress.max()) if not ingress.dropna().empty else None,
        "staffing_dependency_windows": int(df.get("staffing_dependency_flag", pd.Series(dtype=bool)).fillna(False).sum()),
        "incident_windows": int(df.get("incident_flag", pd.Series(dtype=bool)).fillna(False).sum()),
        "worst_areas": worst_areas,
    }


def access_governance_summary(access_governance: pd.DataFrame) -> dict[str, Any]:
    if access_governance is None or access_governance.empty:
        return {
            "pending_approvals_total": 0,
            "pending_privileged_approvals": 0,
            "stale_accounts_total": 0,
            "low_mfa_roles": 0,
            "overdue_certifications": 0,
            "privileged_exceptions": 0,
            "top_service_gaps": [],
        }

    df = access_governance.copy()
    privileged = df.get("privileged_access_flag", pd.Series(dtype=bool)).fillna(False).astype(bool)
    pending = pd.to_numeric(df.get("pending_approvals", pd.Series(dtype=float)), errors="coerce").fillna(0)
    stale = pd.to_numeric(df.get("stale_accounts", pd.Series(dtype=float)), errors="coerce").fillna(0)
    mfa = pd.to_numeric(df.get("mfa_coverage_rate", pd.Series(dtype=float)), errors="coerce")
    next_review_due = df.get("next_review_due", pd.Series(dtype="datetime64[ns, UTC]"))
    overdue = next_review_due.notna() & (next_review_due < pd.Timestamp.now(tz="UTC"))
    privileged_exception_mask = privileged & (
        (pending > 0)
        | (stale > 0)
        | (mfa < THRESHOLDS["iam_mfa_warn"])
        | df.get("segregation_of_duties_flag", pd.Series(dtype=bool)).fillna(False).astype(bool)
    )

    top_service_gaps: list[dict[str, Any]] = []
    if "service" in df.columns:
        service_view = df.assign(
            low_mfa=(mfa < THRESHOLDS["iam_mfa_warn"]).fillna(False).astype(int),
            privileged_exception=privileged_exception_mask.fillna(False).astype(int),
        )
        top_service_gaps = (
            service_view.groupby("service", as_index=False)
            .agg(
                pending_approvals=("pending_approvals", "sum"),
                stale_accounts=("stale_accounts", "sum"),
                low_mfa_roles=("low_mfa", "sum"),
                privileged_exceptions=("privileged_exception", "sum"),
            )
            .sort_values(
                ["privileged_exceptions", "pending_approvals", "stale_accounts"],
                ascending=[False, False, False],
            )
            .head(8)
            .to_dict(orient="records")
        )

    return {
        "pending_approvals_total": int(pending.sum()),
        "pending_privileged_approvals": int(pending[privileged].sum()),
        "stale_accounts_total": int(stale.sum()),
        "low_mfa_roles": int((mfa < THRESHOLDS["iam_mfa_warn"]).fillna(False).sum()),
        "overdue_certifications": int(overdue.sum()),
        "privileged_exceptions": int(privileged_exception_mask.fillna(False).sum()),
        "top_service_gaps": top_service_gaps,
    }


def operations_dependency_matrix(
    services: pd.DataFrame,
    readiness: pd.DataFrame,
    wfm_roster: pd.DataFrame,
    parking_mobility: pd.DataFrame,
    access_governance: pd.DataFrame,
) -> pd.DataFrame:
    if services is None or services.empty:
        return pd.DataFrame()

    base = services[
        [column for column in ["service", "owner_team", "service_tier", "primary_system", "criticality"] if column in services.columns]
    ].drop_duplicates("service").copy()

    readiness_agg = readiness.groupby("service", as_index=False).agg(
        red_gates=("status", lambda values: int((values == "RED").sum())),
        amber_gates=("status", lambda values: int((values == "AMBER").sum())),
        hold_flag=("go_no_go", lambda values: bool((values == "HOLD").any())),
    )

    wfm_view = wfm_roster.copy()
    wfm_view["critical_gap"] = (
        wfm_view.get("critical_role_flag", pd.Series(dtype=bool)).fillna(False).astype(bool)
        & (pd.to_numeric(wfm_view.get("checked_in_headcount", pd.Series(dtype=float)), errors="coerce")
           < pd.to_numeric(wfm_view.get("required_headcount", pd.Series(dtype=float)), errors="coerce"))
    ).astype(int)
    wfm_view["low_training"] = (
        pd.to_numeric(wfm_view.get("training_compliance_rate", pd.Series(dtype=float)), errors="coerce")
        < THRESHOLDS["wfm_training_warn"]
    ).fillna(False).astype(int)
    wfm_agg = wfm_view.groupby("service", as_index=False).agg(
        required_headcount=("required_headcount", "sum"),
        checked_in_headcount=("checked_in_headcount", "sum"),
        critical_shift_gaps=("critical_gap", "sum"),
        low_training_shifts=("low_training", "sum"),
    )
    wfm_agg["staffing_fill_rate"] = (
        pd.to_numeric(wfm_agg["checked_in_headcount"], errors="coerce")
        / pd.to_numeric(wfm_agg["required_headcount"], errors="coerce").replace(0, pd.NA)
    ).fillna(0.0)

    access_view = access_governance.copy()
    access_view["low_mfa"] = (
        pd.to_numeric(access_view.get("mfa_coverage_rate", pd.Series(dtype=float)), errors="coerce")
        < THRESHOLDS["iam_mfa_warn"]
    ).fillna(False).astype(int)
    access_view["privileged_exception"] = (
        access_view.get("privileged_access_flag", pd.Series(dtype=bool)).fillna(False).astype(bool)
        & (
            (pd.to_numeric(access_view.get("pending_approvals", pd.Series(dtype=float)), errors="coerce").fillna(0) > 0)
            | (pd.to_numeric(access_view.get("stale_accounts", pd.Series(dtype=float)), errors="coerce").fillna(0) > 0)
            | (pd.to_numeric(access_view.get("mfa_coverage_rate", pd.Series(dtype=float)), errors="coerce") < THRESHOLDS["iam_mfa_warn"])
            | access_view.get("segregation_of_duties_flag", pd.Series(dtype=bool)).fillna(False).astype(bool)
        )
    ).fillna(False).astype(int)
    access_agg = access_view.groupby("service", as_index=False).agg(
        pending_access_approvals=("pending_approvals", "sum"),
        stale_accounts=("stale_accounts", "sum"),
        low_mfa_roles=("low_mfa", "sum"),
        privileged_exceptions=("privileged_exception", "sum"),
    )

    matrix = base.merge(readiness_agg, on="service", how="left").merge(wfm_agg, on="service", how="left").merge(access_agg, on="service", how="left")
    fill_defaults = {
        "red_gates": 0,
        "amber_gates": 0,
        "hold_flag": False,
        "required_headcount": 0,
        "checked_in_headcount": 0,
        "critical_shift_gaps": 0,
        "low_training_shifts": 0,
        "staffing_fill_rate": 1.0,
        "pending_access_approvals": 0,
        "stale_accounts": 0,
        "low_mfa_roles": 0,
        "privileged_exceptions": 0,
    }
    for column, default in fill_defaults.items():
        if column in matrix.columns:
            matrix[column] = matrix[column].fillna(default)

    parking = parking_mobility_summary(parking_mobility)
    arrival_hotspot = parking["worst_areas"][0]["venue_area"] if parking["worst_areas"] else "-"
    arrival_status = "CRIT"
    if (
        parking["max_occupancy_pct"] is not None
        and parking["max_occupancy_pct"] < THRESHOLDS["parking_occupancy_warn"]
        and (parking["max_queue_minutes"] is None or parking["max_queue_minutes"] < THRESHOLDS["parking_queue_warn_min"])
    ):
        arrival_status = "OK"
    elif (
        (parking["max_occupancy_pct"] is not None and parking["max_occupancy_pct"] < THRESHOLDS["parking_occupancy_crit"])
        and (parking["max_queue_minutes"] is None or parking["max_queue_minutes"] < THRESHOLDS["parking_queue_crit_min"])
        and (parking["max_ingress_time_min_p95"] is None or parking["max_ingress_time_min_p95"] < THRESHOLDS["parking_ingress_crit_min"])
    ):
        arrival_status = "WARN"

    arrival_exposed_systems = {"Ticketing", "Access Control", "POS", "Wi-Fi", "Signage", "Guest CRM"}
    matrix["arrival_exposed"] = matrix.get("primary_system", pd.Series(dtype=str)).fillna("").isin(arrival_exposed_systems)
    matrix["arrival_dependency_status"] = matrix["arrival_exposed"].map(lambda exposed: arrival_status if exposed else "OK")
    matrix["arrival_hotspot"] = matrix["arrival_exposed"].map(lambda exposed: arrival_hotspot if exposed else "-")

    arrival_score = matrix["arrival_dependency_status"].map({"OK": 0, "WARN": 1, "CRIT": 2}).fillna(0)
    matrix["dependency_score"] = (
        pd.to_numeric(matrix["red_gates"], errors="coerce").fillna(0) * 3
        + pd.to_numeric(matrix["amber_gates"], errors="coerce").fillna(0)
        + matrix["hold_flag"].astype(bool).astype(int) * 4
        + pd.to_numeric(matrix["critical_shift_gaps"], errors="coerce").fillna(0) * 2
        + (pd.to_numeric(matrix["staffing_fill_rate"], errors="coerce").fillna(1.0) < THRESHOLDS["wfm_fill_rate_warn"]).astype(int) * 2
        + pd.to_numeric(matrix["pending_access_approvals"], errors="coerce").fillna(0).ge(THRESHOLDS["iam_pending_privileged_warn"]).astype(int) * 2
        + pd.to_numeric(matrix["low_mfa_roles"], errors="coerce").fillna(0)
        + pd.to_numeric(matrix["privileged_exceptions"], errors="coerce").fillna(0)
        + arrival_score
    )

    matrix["overall_status"] = "OK"
    crit_mask = (
        matrix["hold_flag"].astype(bool)
        | pd.to_numeric(matrix["red_gates"], errors="coerce").fillna(0).ge(2)
        | pd.to_numeric(matrix["critical_shift_gaps"], errors="coerce").fillna(0).ge(2)
        | pd.to_numeric(matrix["dependency_score"], errors="coerce").fillna(0).ge(8)
        | (matrix["arrival_dependency_status"] == "CRIT")
    )
    warn_mask = (
        ~crit_mask
        & (
            pd.to_numeric(matrix["amber_gates"], errors="coerce").fillna(0).gt(0)
            | pd.to_numeric(matrix["critical_shift_gaps"], errors="coerce").fillna(0).gt(0)
            | (pd.to_numeric(matrix["staffing_fill_rate"], errors="coerce").fillna(1.0) < 1.0)
            | pd.to_numeric(matrix["pending_access_approvals"], errors="coerce").fillna(0).gt(0)
            | pd.to_numeric(matrix["low_mfa_roles"], errors="coerce").fillna(0).gt(0)
            | (matrix["arrival_dependency_status"] == "WARN")
        )
    )
    matrix.loc[warn_mask, "overall_status"] = "WARN"
    matrix.loc[crit_mask, "overall_status"] = "CRIT"

    return matrix.sort_values(["dependency_score", "red_gates", "critical_shift_gaps", "service"], ascending=[False, False, False, True])
