# Architecture & Decision Log

> Auto-generated during bootstrap on 2026-03-03. Update as decisions evolve.

---

## D-001 · Recommendation engine split (schema / heuristic / gemini / service)

**Decision**: Wrap all recommendation logic inside `src/recommendations/` with four clear layers:
- `schema.py` — canonical JSON schema + stdlib validation (no Pydantic dependency)
- `heuristic.py` — deterministic offline fallback producing valid schema output
- `gemini.py` — thin adapter over `google-genai` SDK with streaming support
- `service.py` — public entry point; tries Gemini first, falls back automatically

**Why**: Separation of concerns; fallback is unit-testable in isolation; UI is decoupled from API availability.

---

## D-002 · No Pydantic

**Decision**: Use stdlib `json` + custom schema validation helper to avoid adding Pydantic.

**Why**: requirements.txt already present; adding Pydantic adds ~15 MB and transitive deps. Simple dict-key validation is enough for the output schema.

---

## D-003 · API key handling

**Decision**: Key lookup order — (1) `st.secrets["GEMINI_API_KEY"]`, (2) `os.environ["GEMINI_API_KEY"]`. Session-in-browser input is also supported for demos but explicitly not written to disk.

**Safe default**: If key absent → heuristic fallback activates. No crash.

---

## D-004 · Offline-safe guarantee

**Decision**: `service.recommend()` NEVER propagates an exception to the UI. Any error (network, auth, parse) triggers heuristic fallback + a soft warning banner.

---

## D-005 · Data seed determinism

**Decision**: `src/seed.py` uses `random.Random(42)` and `numpy` with fixed operations for reproducible demo data.

---

## D-006 · Page naming convention

**Decision**: Pages use Streamlit numeric prefix (0-5) to enforce sidebar ordering. We keep the existing names to avoid breaking any bookmarks during iterative dev.

---

## D-007 · GitHub Actions CI

**Decision**: CI runs `pytest -q` with no GEMINI_API_KEY; Gemini is fully mocked. No secrets required in the runner environment.

---

## D-008 · Packaging scripts

**Decision**: Both `.ps1` (Windows PowerShell) and `.sh` (WSL/Linux/macOS) packaging scripts produce `seven_control_tower_gemini_demo.zip`, excluding `.venv/`, `.streamlit/secrets.toml`, `evidence/`, and `*.log`.
