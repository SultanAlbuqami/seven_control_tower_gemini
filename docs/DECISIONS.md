# Architecture and Decision Log

## D-001 - Recommendation engine layering

Decision: keep recommendation logic split across `schema.py`, `heuristic.py`, `groq_adapter.py`, `service.py`, and `snapshot.py`.

Why: the LLM path, the deterministic fallback path, and the snapshot aggregation path need to be testable in isolation.

## D-002 - No heavy schema dependency

Decision: keep schema validation in stdlib-only code instead of adding Pydantic or other validation frameworks.

Why: the response contract is small, deterministic, and already covered by tests.

## D-003 - Key lookup order

Decision: resolve LLM credentials in this order:

1. `st.secrets["GROQ_API_KEY"]`
2. `GROQ_API_KEY` environment variable
3. Optional session-only paste held in Streamlit session state

Why: this matches the required security model while avoiding any writes to disk.

## D-004 - Offline-safe recommendation contract

Decision: `service.recommend()` never raises and always returns a valid canonical JSON payload, even if the LLM path fails.

Why: the demo must remain usable with no key and with no network.

## D-005 - Deterministic seed timestamp

Decision: move the seed off `now()` and anchor it to a fixed UTC timestamp.

Why: a random seed alone is not enough if timestamps drift on every run; the CSV outputs must be stable across regenerations.

## D-006 - Example-system wording

Decision: keep all system labels explicitly marked as examples and repeat the source-agnostic disclaimer in both the UI shell and the README.

Why: the system landscape is illustrative, not a claim about an actual deployment.

## D-007 - Typical destination stack registry

Decision: store the system landscape in `src/system_landscape.py` as the single source of truth for categories, label pools, trace fields, and ID-format rules.

Why: seed generation, lineage panels, and the System Landscape page all need the same definitions.

## D-008 - Project-local dependency verification

Decision: run dependency and test verification from the repo-local `.venv`.

Why: the global Python installation on the workstation contains unrelated package conflicts that are outside this repository.

## D-009 - Dual-model recommendation strategy

Decision: use a small Groq model for the streamed Draft preview and a larger Groq model for the Final authoritative JSON.

Why: the preview improves perceived responsiveness, while the final pass preserves a strict structured contract.

## D-010 - Authoritative result boundary

Decision: only the Final authoritative JSON is allowed to populate structured recommendation panels and exports.

Why: the Draft preview is intentionally non-authoritative text.

## D-011 - Single repair attempt

Decision: allow exactly one local repair pass on LLM JSON before falling back to the heuristic engine.

Why: this satisfies the strict-output requirement without adding another remote round trip.

## D-012 - Data lineage on every page

Decision: every page ends with a Data lineage section that exposes `source_system` and representative trace references.

Why: the interview narrative is stronger when every chart and table can be traced back to an example source and ID pattern.

## D-013 - Standard app shell

Decision: centralize the page shell in `src/ui.py` with a common title, purpose line, disclaimer, sidebar guide, status badges, and KPI-card styling.

Why: the repo needed consistent visual hierarchy and status semantics instead of page-by-page variations.

## D-014 - Fixed OK/WARN/CRIT semantics

Decision: keep the same OK/WARN/CRIT colors and thresholds across readiness, incidents, vendors, OT, and ticketing views.

Why: executive viewers should not have to re-interpret colors from page to page.

## D-015 - Streamlit smoke coverage

Decision: add `AppTest` smoke tests for the app shell, every page, and offline recommendation generation.

Why: this is the most reliable local proof that the multi-page Streamlit app still renders after code changes.

## D-016 - Packaging exclusions

Decision: both packaging scripts exclude local secrets, logs, venvs, build artifacts, caches, evidence folders, and existing zip files.

Why: the distributable zip must stay demo-clean and secret-free.

## D-017 - CI dependency sanity

Decision: add `pip check` to the GitHub Actions workflow before test execution.

Why: dependency health is part of the required quality gate, not just a local convenience.

## D-018 - Local secret-file handling during offline smoke

Decision: when offline smoke verification is required, temporarily move the local `.streamlit/secrets.toml` file out of the way and restore it after the check.

Why: a local developer secret should not accidentally convert an offline smoke into a live LLM test.

## D-019 - Hover glossary for acronym badges

Decision: keep acronym expansions in `src/system_landscape.py` and expose them through native hover tooltips on the shared landscape badges.

Why: the abbreviations are common in operations programs, but interview viewers should not have to guess what `ITSM`, `CMDB`, `CMMS`, or `EDMS` mean.

## D-020 - PMIS as an optional extension, not a core dependency

Decision: add `PMIS` to the system landscape as an optional Project Controls extension and include it in ORR tracker example labels, without making it a mandatory source for the demo.

Why: PMIS is useful when the conversation needs stronger project-controls and handover traceability, but the control tower still runs coherently with CMDB, ORR, EDMS, ITSM, OT, and ticketing sources alone.

## D-021 - Complete optional extension coverage for workforce, project, arrival, command, and identity layers

Decision: add `WFM / Rostering`, `CDE / BIM / Handover`, `Parking / Traffic / Mobility`, `CAD / Dispatch / Radio`, and `IAM / SSO` as optional system-landscape categories with example labels, trace fields, ID rules, and acronym expansions.

Why: these layers materially strengthen the interview narrative for operational readiness, handover quality, arrival management, security command, and access governance without forcing new datasets or pages into the core demo path.

## D-022 - Promote staffing, arrival, and access governance into first-class synthetic datasets

Decision: add deterministic `wfm_roster.csv`, `parking_mobility.csv`, and `access_governance.csv` datasets, then expose them through a dedicated `Operations Dependencies` page and summary metrics.

Why: workforce coverage, arrival pressure, and access governance are real launch dependencies; keeping them only in the system-landscape narrative would leave a visible gap in the control-tower demo.
