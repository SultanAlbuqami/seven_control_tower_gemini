from __future__ import annotations

import pandas as pd

from src.system_landscape import THRESHOLDS


def _minutes_between(start: pd.Series, end: pd.Series) -> pd.Series:
    return (end - start).dt.total_seconds() / 60.0


def compute_mtta_minutes(incidents: pd.DataFrame) -> float | None:
    required = {"opened_at", "ack_at"}
    if not required.issubset(set(incidents.columns)):
        return None
    df = incidents.dropna(subset=["opened_at", "ack_at"]).copy()
    if df.empty:
        return None
    mins = _minutes_between(df["opened_at"], df["ack_at"]).dropna()
    return float(mins.mean()) if not mins.empty else None


def compute_mttr_minutes(incidents: pd.DataFrame) -> float | None:
    required = {"opened_at", "resolved_at"}
    if not required.issubset(set(incidents.columns)):
        return None
    df = incidents.dropna(subset=["opened_at", "resolved_at"]).copy()
    if df.empty:
        return None
    mins = _minutes_between(df["opened_at"], df["resolved_at"]).dropna()
    return float(mins.mean()) if not mins.empty else None


def readiness_score(readiness: pd.DataFrame) -> pd.DataFrame:
    """Compute per-service readiness score based on gate status."""
    status_map = {"GREEN": 2, "AMBER": 1, "RED": 0}
    df = readiness.copy()
    df["score"] = df["status"].map(status_map).fillna(-1).astype(int)
    out = (
        df.groupby("service", as_index=False)
        .agg(score=("score", "mean"), reds=("status", lambda s: int((s == "RED").sum())))
        .sort_values(["reds", "score"], ascending=[False, True])
    )
    return out


def evidence_completion(evidence: pd.DataFrame) -> pd.DataFrame:
    """Compute completion ratio by service and gate."""
    df = evidence.copy()
    df["is_complete"] = (df["status"] == "COMPLETE").astype(int)
    out = (
        df.groupby(["service", "gate"], as_index=False)
        .agg(items=("evidence_id", "count"), complete=("is_complete", "sum"))
    )
    out["completion"] = (out["complete"] / out["items"]).fillna(0.0)
    return out


def vendor_scorecard(vendors: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "vendor", "service", "sla_availability", "availability_actual",
        "mtta_target_min", "mtta_actual_min", "mttr_target_min",
        "mttr_actual_min", "open_critical", "last_review",
    ]
    out = vendors.copy()
    for c in cols:
        if c not in out.columns:
            out[c] = pd.NA

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
    breach_cols = ["availability_breach", "mtta_breach", "mttr_breach"]
    out["breach_count"] = out[breach_cols].fillna(False).sum(axis=1)
    return out[cols + breach_cols + ["breach_count"]]


# ── OT Event metrics ──────────────────────────────────────────────────────────

def ot_event_summary(ot_events: pd.DataFrame) -> dict:
    """Return aggregated OT signal summary for recommendations snapshot."""
    if ot_events is None or ot_events.empty:
        return {"unacked_sev1": 0, "unacked_sev2": 0, "total_open": 0, "clusters": []}

    df = ot_events.copy()
    # Unacked = ack_time is NaT
    if "ack_time" in df.columns:
        unacked = df[df["ack_time"].isna()]
    else:
        unacked = df

    sev_col = "severity" if "severity" in df.columns else None

    unacked_sev1 = int((unacked[sev_col] == 1).sum()) if sev_col else 0
    unacked_sev2 = int((unacked[sev_col] == 2).sum()) if sev_col else 0

    # Not yet cleared
    if "cleared_time" in df.columns:
        open_events = df[df["cleared_time"].isna()]
    else:
        open_events = df
    total_open = len(open_events)

    # Cluster by zone/subsystem
    clusters: list[dict] = []
    if sev_col and "zone" in df.columns and "subsystem" in df.columns:
        crit = unacked[unacked[sev_col].isin([1, 2])]
        if not crit.empty:
            grp = crit.groupby(["zone", "subsystem"], as_index=False).size()
            grp = grp.sort_values("size", ascending=False).head(5)
            clusters = grp.to_dict(orient="records")

    return {
        "unacked_sev1": unacked_sev1,
        "unacked_sev2": unacked_sev2,
        "total_open": total_open,
        "clusters": clusters,
    }


def compute_ot_mean_ack_minutes(ot_events: pd.DataFrame) -> float | None:
    """Mean acknowledgement time in minutes for acked OT events."""
    if ot_events is None or ot_events.empty:
        return None
    required = {"event_time", "ack_time"}
    if not required.issubset(set(ot_events.columns)):
        return None
    df = ot_events.dropna(subset=["event_time", "ack_time"]).copy()
    if df.empty:
        return None
    mins = _minutes_between(df["event_time"], df["ack_time"]).dropna()
    return float(mins.mean()) if not mins.empty else None


# ── Ticketing KPI metrics ─────────────────────────────────────────────────────

def ticketing_kpi_summary(ticketing_kpis: pd.DataFrame) -> dict:
    """Return aggregated ticketing signal summary for recommendations snapshot."""
    if ticketing_kpis is None or ticketing_kpis.empty:
        return {"anomaly_windows": 0, "min_success_rate": None, "max_latency_p95": None,
                "total_offline_fallbacks": 0, "total_denied": 0}

    df = ticketing_kpis.copy()
    warn_thresh = THRESHOLDS["ticketing_scan_success_rate_warn"]
    crit_thresh = THRESHOLDS["ticketing_scan_success_rate_crit"]
    lat_crit = THRESHOLDS["ticketing_latency_crit_ms"]

    anomaly_mask = (
        (pd.to_numeric(df.get("scan_success_rate", pd.Series(dtype=float)), errors="coerce") < warn_thresh)
        | (pd.to_numeric(df.get("qr_validation_latency_ms_p95", pd.Series(dtype=float)), errors="coerce") > lat_crit)
    )
    anomaly_windows = int(anomaly_mask.sum())

    min_sr = None
    max_lat = None
    if "scan_success_rate" in df.columns:
        sr = pd.to_numeric(df["scan_success_rate"], errors="coerce").dropna()
        min_sr = float(sr.min()) if not sr.empty else None
    if "qr_validation_latency_ms_p95" in df.columns:
        lat = pd.to_numeric(df["qr_validation_latency_ms_p95"], errors="coerce").dropna()
        max_lat = float(lat.max()) if not lat.empty else None

    total_offline = int(df.get("offline_fallback_activations", pd.Series([0])).fillna(0).sum())
    total_denied = int(df.get("denied_entries", pd.Series([0])).fillna(0).sum())

    return {
        "anomaly_windows": anomaly_windows,
        "min_success_rate": min_sr,
        "max_latency_p95": max_lat,
        "total_offline_fallbacks": total_offline,
        "total_denied": total_denied,
    }
