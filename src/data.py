from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

import pandas as pd

from src.seed import ensure_data_present

ROOT_DIR: Final[Path] = Path(__file__).resolve().parents[1]
DATA_DIR: Final[Path] = ROOT_DIR / "data"

DATASET_SPECS: Final[dict[str, tuple[str, ...]]] = {
    "services": (),
    "readiness": ("last_updated",),
    "evidence": ("updated_at",),
    "incidents": ("opened_at", "ack_at", "resolved_at"),
    "vendors": ("last_review",),
    "kpis": ("ts",),
    "ot_events": ("event_time", "ack_time", "cleared_time"),
    "ticketing_kpis": ("ts",),
}


@dataclass(frozen=True)
class DataBundle:
    services: pd.DataFrame
    readiness: pd.DataFrame
    evidence: pd.DataFrame
    incidents: pd.DataFrame
    vendors: pd.DataFrame
    kpis: pd.DataFrame
    ot_events: pd.DataFrame
    ticketing_kpis: pd.DataFrame


def _read_csv(name: str) -> pd.DataFrame:
    path = DATA_DIR / f"{name}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing data file: {path}")
    df = pd.read_csv(path)
    for column in DATASET_SPECS.get(name, ()):
        if column in df.columns:
            df[column] = pd.to_datetime(df[column], errors="coerce", utc=True)
    return df


def load_data() -> DataBundle:
    return DataBundle(
        services=_read_csv("services"),
        readiness=_read_csv("readiness"),
        evidence=_read_csv("evidence"),
        incidents=_read_csv("incidents"),
        vendors=_read_csv("vendors"),
        kpis=_read_csv("kpis"),
        ot_events=_read_csv("ot_events"),
        ticketing_kpis=_read_csv("ticketing_kpis"),
    )


def ensure_data_and_load() -> DataBundle:
    ensure_data_present()
    return load_data()
