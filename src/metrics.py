from __future__ import annotations

import pandas as pd


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
    if mins.empty:
        return None
    return float(mins.mean())


def compute_mttr_minutes(incidents: pd.DataFrame) -> float | None:
    required = {"opened_at", "resolved_at"}
    if not required.issubset(set(incidents.columns)):
        return None

    df = incidents.dropna(subset=["opened_at", "resolved_at"]).copy()
    if df.empty:
        return None

    mins = _minutes_between(df["opened_at"], df["resolved_at"]).dropna()
    if mins.empty:
        return None
    return float(mins.mean())


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
