# Architecture & Decision Log

> Auto-generated during bootstrap on 2026-03-03. Update as decisions evolve.

---

## D-001 · Recommendation engine split (schema / heuristic / groq / service)

**Decision**: Wrap all recommendation logic inside `src/recommendations/` with four clear layers:
- `schema.py` — canonical JSON schema + stdlib validation (no Pydantic dependency)
- `heuristic.py` — deterministic offline fallback producing valid schema output
- `groq_adapter.py` — thin adapter over Groq SDK with streaming support
- `service.py` — public entry point; tries Groq first, falls back automatically

**Why**: Separation of concerns; fallback is unit-testable in isolation; UI is decoupled from API availability.

---

## D-002 · No Pydantic

**Decision**: Use stdlib `json` + custom schema validation helper to avoid adding Pydantic.

**Why**: requirements.txt already present; adding Pydantic adds ~15 MB and transitive deps. Simple dict-key validation is enough for the output schema.

---

## D-003 · API key handling

**Decision**: Key lookup order — (1) `st.secrets["GROQ_API_KEY"]`, (2) `os.environ["GROQ_API_KEY"]`. Session-in-browser input is also supported for demos but explicitly not written to disk.

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

**Decision**: CI runs `pytest -q` with no GROQ_API_KEY; Groq is fully mocked. No secrets required in the runner environment.

---

## D-008 · Packaging scripts

**Decision**: Provide both `scripts/package_zip.ps1` (Windows) and `scripts/package_zip.sh` (bash) producing `seven_control_tower_gemini_demo.zip`.

**Exclusions**: `.venv/`, `.streamlit/secrets.toml`, `evidence/`, `*.log`, `__pycache__/`.

---

## D-009 · System landscape registry

**Decision**: Create `src/system_landscape.py` as the single source of truth for all system category definitions, label pools, ID patterns, and anomaly thresholds.

**Why**: Centralising landscape labels prevents drift between seed data, UI badge display, and recommendation context. A frozen dataclass (`SystemCategory`) is simpler than a config file and is type-checkable.

**Safe default**: Non-optional categories are listed in `CORE_BADGE_CATEGORIES`; all pages show the same badge row.

---

## D-010 · OT events schema and generation

**Decision**: `ot_events.csv` uses 80 rows over a 7-day window with `EVT-OT-XXXXXX` IDs, severity 1–4, subsystems BMS/AccessControl/CCTV, and NaT for unacknowledged events.

**Why**: 80 rows provides enough variance for meaningful filter/chart interactions while staying fast. NaT `ack_time` is the canonical representation of unacked state — avoids a separate `is_acked` boolean.

---

## D-011 · Ticketing KPI schema and generation

**Decision**: `ticketing_kpis.csv` uses 15-minute intervals × 48 hours × 6 venue areas with ~5% peak windows having injected anomalies.

**Anomaly thresholds** (in `THRESHOLDS`):
- `scan_success_rate_warn = 0.97`, `scan_success_rate_crit = 0.94`
- `latency_warn_ms = 800`, `latency_crit_ms = 1500`

**Why**: 15-min granularity matches typical ops dashboards. 48h window spans full event-day rehearsal + Day-One. 5% anomaly injection provides realistic demo signal without overwhelming the charts.

---

## D-012 · Recommendation schema extension

**Decision**: Add four new required keys to the schema: `ot_signals`, `ticketing_signals`, `incident_improvements`, `vendor_flags`.

**Why**: Both the heuristic and Groq paths must always produce these fields so the UI can unconditionally render them. Making them required (not optional) prevents silent omissions from Groq and simplifies validation.

**Safe default**: Each key defaults to a single-item list with a "nominal" or "no issues detected" message when no signal conditions are triggered.

---

## D-013 · Auto-seed on startup

**Decision**: `app.py` calls `ensure_data_present()` on every page load (deferred import inside the function to avoid circular). Pages use `ensure_data_and_load()` from `src/data.py`.

**Why**: Eliminates the manual "Generate data" button as a first-run friction point. The check is O(n file stat calls) and completes in <10 ms if all files exist. If regeneration is needed, it runs once and is not repeated.

**Safe default**: Generation errors surface as `st.error()` banners; the app does not crash.

**Decision**: Both `.ps1` (Windows PowerShell) and `.sh` (WSL/Linux/macOS) packaging scripts produce `seven_control_tower_gemini_demo.zip`, excluding `.venv/`, `.streamlit/secrets.toml`, `evidence/`, and `*.log`.
