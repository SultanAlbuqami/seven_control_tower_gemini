from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.seed import REQUIRED_FILES, generate

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"


def _assert_clean_render(app: AppTest) -> None:
    assert len(app.exception) == 0, f"Unexpected streamlit exception elements: {list(app.exception)}"
    assert len(app.error) == 0, f"Unexpected streamlit error elements: {list(app.error)}"


def test_app_auto_seed_regenerates_missing_csvs() -> None:
    for filename in REQUIRED_FILES:
        path = DATA_DIR / filename
        if path.exists():
            path.unlink()

    app = AppTest.from_file(str(ROOT_DIR / "app.py"), default_timeout=20)
    app.run(timeout=20)

    for filename in REQUIRED_FILES:
        assert (DATA_DIR / filename).exists(), f"{filename} was not regenerated"
    _assert_clean_render(app)


@pytest.mark.parametrize(
    "relative_path",
    [
        "pages/0_Overview.py",
        "pages/1_Readiness_Heatmap.py",
        "pages/2_Evidence_Pack.py",
        "pages/3_Incidents.py",
        "pages/4_Vendor_Scorecards.py",
        "pages/6_OT_Events.py",
        "pages/7_Ticketing_KPIs.py",
        "pages/8_System_Landscape.py",
        "pages/9_Operations_Dependencies.py",
    ],
)
def test_pages_render_without_errors(relative_path: str) -> None:
    generate()
    app = AppTest.from_file(str(ROOT_DIR / relative_path), default_timeout=20)
    app.run(timeout=20)
    _assert_clean_render(app)


def test_recommendations_page_runs_offline() -> None:
    generate()
    import os

    old_value = os.environ.pop("GROQ_API_KEY", None)
    secrets_path = ROOT_DIR / ".streamlit" / "secrets.toml"
    backup_path = ROOT_DIR / ".streamlit" / "secrets.toml.offline-test"
    if secrets_path.exists():
        secrets_path.replace(backup_path)
    try:
        app = AppTest.from_file(str(ROOT_DIR / "pages/5_Recommendations.py"), default_timeout=20)
        app.run(timeout=20)
        _assert_clean_render(app)
        app.button[0].click()
        app.run(timeout=20)
        _assert_clean_render(app)
        assert app.session_state["recommendation_payload"] is not None
    finally:
        if backup_path.exists():
            backup_path.replace(secrets_path)
        if old_value:
            os.environ["GROQ_API_KEY"] = old_value
