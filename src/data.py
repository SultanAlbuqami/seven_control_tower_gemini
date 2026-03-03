from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import pandas as pd

ROOT_DIR: Final[Path] = Path(__file__).resolve().parents[1]
DATA_DIR: Final[Path] = ROOT_DIR / "data"

logger = logging.getLogger(__name__)


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


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing data file: {path}. Generate it with: python -m src.seed"
        )
    return pd.read_csv(path)


def _read_csv_optional(path: Path) -> pd.DataFrame:
    """Return empty DataFrame if file is missing (graceful degradation)."""
    if not path.exists():
        logger.warning("Optional data file missing: %s", path)
        return pd.DataFrame()
    return pd.read_csv(path)


def ensure_data_and_load() -> "DataBundle":
    """Auto-generate missing datasets then load.

    Avoids importing seed at module level to prevent circular imports.
    """
    from src.seed import ensure_data_present  # noqa: PLC0415 (deferred import)

    ensure_data_present()
    return load_data()


def load_data() -> DataBundle:
    services = _read_csv(DATA_DIR / "services.csv")
    readiness = _read_csv(DATA_DIR / "readiness.csv")
    evidence = _read_csv(DATA_DIR / "evidence.csv")
    incidents = _read_csv(DATA_DIR / "incidents.csv")
    vendors = _read_csv(DATA_DIR / "vendors.csv")
    kpis = _read_csv(DATA_DIR / "kpis.csv")
    ot_events = _read_csv_optional(DATA_DIR / "ot_events.csv")
    ticketing_kpis = _read_csv_optional(DATA_DIR / "ticketing_kpis.csv")

    # Normalize datetimes
    for df, cols in [
        (readiness, ["last_updated"]),
        (evidence, ["updated_at"]),
        (incidents, ["opened_at", "ack_at", "resolved_at"]),
        (vendors, ["last_review"]),
        (kpis, ["ts"]),
        (ot_events, ["event_time", "ack_time", "cleared_time"]),
        (ticketing_kpis, ["ts"]),
    ]:
        for c in cols:
            if c in df.columns:
                df[c] = pd.to_datetime(df[c], errors="coerce", utc=True)

    return DataBundle(
        services=services,
        readiness=readiness,
        evidence=evidence,
        incidents=incidents,
        vendors=vendors,
        kpis=kpis,
        ot_events=ot_events,
        ticketing_kpis=ticketing_kpis,
    )
