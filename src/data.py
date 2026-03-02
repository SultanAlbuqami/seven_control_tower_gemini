from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

import pandas as pd

ROOT_DIR: Final[Path] = Path(__file__).resolve().parents[1]
DATA_DIR: Final[Path] = ROOT_DIR / "data"


@dataclass(frozen=True)
class DataBundle:
    services: pd.DataFrame
    readiness: pd.DataFrame
    evidence: pd.DataFrame
    incidents: pd.DataFrame
    vendors: pd.DataFrame
    kpis: pd.DataFrame


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing data file: {path}. Generate it with: python -m src.seed"
        )
    return pd.read_csv(path)


def load_data() -> DataBundle:
    services = _read_csv(DATA_DIR / "services.csv")
    readiness = _read_csv(DATA_DIR / "readiness.csv")
    evidence = _read_csv(DATA_DIR / "evidence.csv")
    incidents = _read_csv(DATA_DIR / "incidents.csv")
    vendors = _read_csv(DATA_DIR / "vendors.csv")
    kpis = _read_csv(DATA_DIR / "kpis.csv")

    # Normalize datetimes
    for df, cols in [
        (readiness, ["last_updated"]),
        (evidence, ["updated_at"]),
        (incidents, ["opened_at", "ack_at", "resolved_at"]),
        (vendors, ["last_review"]),
        (kpis, ["ts"]),
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
    )
