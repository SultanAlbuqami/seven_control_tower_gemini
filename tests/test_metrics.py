from __future__ import annotations

import pandas as pd

from src.metrics import compute_mtta_minutes, compute_mttr_minutes, readiness_score


def test_mtta_mttr_basic():
    df = pd.DataFrame(
        {
            "opened_at": pd.to_datetime(
                ["2026-03-01T10:00:00Z", "2026-03-01T11:00:00Z"], utc=True
            ),
            "ack_at": pd.to_datetime(
                ["2026-03-01T10:10:00Z", "2026-03-01T11:20:00Z"], utc=True
            ),
            "resolved_at": pd.to_datetime(
                ["2026-03-01T11:00:00Z", "2026-03-01T12:30:00Z"], utc=True
            ),
        }
    )
    assert abs(compute_mtta_minutes(df) - 15.0) < 1e-6
    assert abs(compute_mttr_minutes(df) - 75.0) < 1e-6


def test_readiness_score_ordering():
    readiness = pd.DataFrame(
        {
            "service": ["A", "A", "B", "B"],
            "status": ["RED", "GREEN", "AMBER", "AMBER"],
        }
    )
    out = readiness_score(readiness)
    # Service A has a RED gate -> should rank above B in terms of risk (reds desc, score asc)
    assert out.iloc[0]["service"] == "A"
