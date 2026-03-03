# Day-One Operations Readiness Control Tower

A production-ready Streamlit demo for Day-One opening readiness, featuring:

- **Evidence-driven readiness gates** (G1–G5: Assets, Acceptance, SOPs, Monitoring, Dry Run)
- **Incident operations** — MTTA/MTTR, severity tracking, escalation logs
- **Vendor scorecards** — SLA compliance and breach visibility
- **OT Events monitor** — BMS / Access Control / CCTV alarm unacked tracking
- **Ticketing KPIs** — gate scan success rate, QR latency p95, throughput anomaly detection
- **Live AI recommendations** — Groq-powered (with heuristic offline fallback)

> ⚡ Synthetic dataset — evidence-driven readiness model — example system landscape labels  
> 🔑 Works fully offline without a Groq API key (heuristic mode)

---

## Typical Production Systems (Examples)

The demo labels data with realistic source-system references drawn from these categories:

| Category | Example Systems |
|---|---|
| CMDB / Asset Register | ServiceNow CMDB, Maximo Asset Mgr, IBM Control Desk |
| ITSM / Ticketing | ServiceNow ITSM, Jira Service Mgmt, Remedy ITSM |
| EDMS / Evidence | SharePoint Online, Confluence, Documentum |
| Monitoring / Observability | Dynatrace, Datadog, Grafana + Prometheus, Splunk |
| OT / BMS / Access Control | Siemens BMS, Johnson Controls Metasys, Honeywell EBI, CCURE-9000 |
| Venue Ticketing | Ticketmaster Archtics, AXS Hub, SEATAC, Paciolan |
| ORR Tracker | PowerBI Embedded, Jira Board, Smartsheet |

> These are **example labels only** — not indicative of any specific deployment.

---

## Quick Start

### 1. Create a virtual environment

**Windows PowerShell:**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**WSL / Linux / macOS:**
```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -U pip
pip install -r requirements.txt
```

### 3. Generate demo data
```bash
python -m src.seed
```

### 4. Set the Groq API key (optional — app works offline without it)

**Option A — environment variable (recommended):**
```powershell
# Windows PowerShell
$env:GROQ_API_KEY="YOUR_KEY_HERE"
```
```bash
# WSL / Linux / macOS
export GROQ_API_KEY="YOUR_KEY_HERE"
```

**Option B — Streamlit secrets (local only, never commit):**
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml and add your real key
```

### 5. Run the app
```bash
streamlit run app.py
```

**Or use the convenience scripts:**
```powershell
# Windows PowerShell (auto-creates venv, seeds data, launches app)
.\scripts\run.ps1 -Key "YOUR_KEY"  # Key is optional
```
```bash
# WSL / Linux / macOS
bash scripts/run.sh "YOUR_KEY"  # Key is optional
```

---

## 3-Minute Interview Demo Script

> Follow this click order when presenting to a hiring panel or stakeholder.

### Step 1 — Overview (30 s)
- Open **Overview** page
- Point to the 4 KPI cards: RED gates, missing evidence, open Sev-1/2 incidents, vendor breaches
- Say: *"This is the operational posture at a glance. Our Go/No-Go criterion is zero RED gates, zero open Sev-1/2, and evidence completion ≥ 90%."*

### Step 2 — Readiness Heatmap (45 s)
- Open **Readiness** page
- Use "Minimum criticality" filter → set to 3 (highest)
- Point to RED cells in the heatmap
- Scroll to the blocker table
- Say: *"The heatmap shows us exactly which service/gate combinations are blocking sign-off, and who owns each blocker."*

### Step 3 — Evidence Pack (30 s)
- Open **Evidence Pack** page
- Filter **Status = MISSING**
- Say: *"Here's the chase list. Every missing item has an owner and a note. I can download this and run a chase email in 30 seconds."*

### Step 4 — Incidents (30 s)
- Open **Incidents** page
- Look at MTTA/MTTR KPI cards
- Filter **Severity = 1**
- Say: *"MTTA and MTTR are the key escalation discipline metrics. Sev-1 incidents with no RCA completed are red flags before Day-One."*

### Step 5 — OT Events (30 s)
- Open **OT Events** page
- Filter **Unacked only = ON**
- Point to Sev-1 / Sev-2 unacked cards and mean ack time
- Say: *"Unacked Sev-1 alarms before Day-One are an automatic Go/No-Go blocker. The subsystem cluster chart shows which zone is the hotspot."*

### Step 6 — Ticketing KPIs (30 s)
- Open **Ticketing KPIs** page
- Point to anomaly windows KPI card and the scan success rate chart
- Say: *"Gate scan success below 97% or QR latency above 1500 ms is flagged as an anomaly. The offline-fallback counter tells us if payment connectivity is unreliable."*

### Step 7 — Recommendations (45 s)
- Open **Recommendations** page
- Click **Generate Recommendations**
- Point to OT Signals, Ticketing Signals, Top Risks, Actions — Next 24h
- Say: *"The recommendation schema now carries OT and ticketing signals alongside incident and vendor data. Schema validation and heuristic fallback are always active."*

### Closing
> *"The full stack is: data seed → system landscape → metrics → structured recommendations → schema validation → graceful fallback. Everything is testable and auditable."*

---

## Data Model

| File | Description |
|---|---|
| `data/services.csv` | 6 services with criticality, vendor, source_system, CI ID |
| `data/readiness.csv` | Service × gate status (GREEN/AMBER/RED) with blockers |
| `data/evidence.csv` | Evidence items with owner, status, doc_ref, approval |
| `data/incidents.csv` | Incidents with MTTA/MTTR timestamps, category, SLA breach flag |
| `data/vendors.csv` | Vendor SLA targets vs actuals, escalation level, penalty risk |
| `data/kpis.csv` | Hourly KPI time series (7 days) |
| `data/ot_events.csv` | OT/BMS/Access/CCTV alarms (80 rows, 7-day window, EVT-OT IDs) |
| `data/ticketing_kpis.csv` | Gate ticketing KPIs at 15-min intervals × 48 h × 6 venue areas |

All files are auto-generated on startup by `ensure_data_present()` (deterministic, seed=42).
Manual regeneration: `python -m src.seed`

### Data lineage
Every record carries:
- `source_system` — example label from production system category (CMDB, ITSM, OT, etc.)
- Appropriate trace IDs: `ci_id`, `source_id`, `doc_ref`, `punch_list_id`, `dashboard_ref`, `event_id`, `device_id`

---

## Architecture

```
app.py                          # Streamlit entry point (auto-seeds on startup)
pages/
  0_Overview.py                 # KPI dashboard
  1_Readiness.py                # Heatmap + blocker table
  2_Evidence_Pack.py            # Evidence chase list
  3_Incidents.py                # MTTA/MTTR analysis
  4_Vendor_Scorecards.py        # SLA compliance
  5_Recommendations.py          # Groq + fallback (OT + ticketing signals)
  6_OT_Events.py                # BMS/Access Control/CCTV alarm monitor
  7_Ticketing_KPIs.py           # Gate scan success, QR latency, throughput
src/
  system_landscape.py           # System category registry, badges, thresholds
  data.py                       # Data loader + ensure_data_and_load()
  metrics.py                    # MTTA/MTTR, readiness, vendor, OT, ticketing
  seed.py                       # Deterministic demo data generator (8 datasets)
  domain/constants.py           # Gate definitions, KPI targets
  ai/groq_recommender.py        # Groq SDK adapter (streaming)
  recommendations/
    schema.py                   # JSON schema + stdlib validation + is_valid()
    heuristic.py                # Offline deterministic recommender
    groq_adapter.py             # Groq call + JSON parse + repair
    service.py                  # Public entry point (Groq → fallback)
  utils/json_utils.py           # Robust JSON extraction from LLM output
tests/
  test_metrics.py
  test_ot_metrics.py            # OT event aggregation tests
  test_ticketing_metrics.py     # Ticketing KPI anomaly detection tests
  test_json_utils.py
  test_schema.py
  test_heuristic.py
  test_recommendations_integration.py
```

---

## Running Tests

```bash
pytest -q
```

Tests run fully offline — Groq is mocked. No API key required.

```bash
# With coverage (optional)
pip install pytest-cov
pytest -q --cov=src --cov-report=term-missing
```

---

## Packaging

Create a distributable ZIP (excludes `.venv`, secrets, evidence logs):

```powershell
# Windows
.\scripts\package_zip.ps1
```
```bash
# WSL / Linux / macOS
bash scripts/package_zip.sh
```

Output: `seven_control_tower_gemini_demo.zip`

---

## Security Notes

- API keys are read from `GROQ_API_KEY` env var or `.streamlit/secrets.toml` (excluded from git).
- No key is ever printed to logs or echoed in the UI.
- Session-paste input in the sidebar is held in memory only; never written to disk.
- `.gitignore` excludes `.env`, `secrets.toml`, `evidence/`, and `*.log`.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `FileNotFoundError: Missing data file` | Run `python -m src.seed` |
| `ModuleNotFoundError: groq` | Run `pip install -r requirements.txt` |
| Recommendations show "offline mode" | Set `GROQ_API_KEY` env var or use sidebar paste |
| Port 8501 in use | `streamlit run app.py --server.port 8502` |
| PowerShell execution policy error | `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| Streamlit not found after venv | `.\.venv\Scripts\Activate.ps1` then retry |

---

## CHANGELOG

### v2.0.0 — 2026-03-04
- System landscape registry (`src/system_landscape.py`) — category badges, ID patterns, anomaly thresholds
- 2 new datasets: `ot_events.csv` (80 rows, BMS/Access/CCTV alarms), `ticketing_kpis.csv` (15-min intervals, 48h, 6 areas)
- 5 existing datasets extended with `source_system`, trace IDs, and domain fields
- Auto-seed on `app.py` startup via `ensure_data_present()`
- 2 new pages: OT Events monitor (page 6), Ticketing KPIs (page 7)
- Landscape badge row on every page
- Recommendations schema extended: `ot_signals`, `ticketing_signals`, `incident_improvements`, `vendor_flags`
- Groq prompt updated for strict JSON with new schema keys
- 2 new test files (61 tests total, all green)

### v1.0.0 — 2026-03-03
- Initial production-quality release
- Multi-page Streamlit app with 6 pages
- Deterministic data seed (6 services, 5 gates, incidents, vendors, KPI time series)
- `src/recommendations/` package: schema, heuristic, groq adapter, service layer
- Groq streaming + one-shot modes with schema validation + repair
- Heuristic offline fallback (no API key required)
- 5 test files: metrics, json_utils, schema, heuristic, integration (all mocked)
- GitHub Actions CI (Python 3.11, 3.12)
- Packaging scripts (PowerShell + bash)
- `docs/DECISIONS.md` and `docs/EVIDENCE.md`
