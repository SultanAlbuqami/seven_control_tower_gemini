# Al Hamra — Operations Readiness Control Tower

An interview-grade Streamlit demo for venue and destination operations readiness. The repository opens with meaningful data immediately, runs without an API key, and shows traceable readiness, evidence, incident, vendor, OT, and ticketing signals in one control tower.

> These are common example systems for large venues; the demo is source-agnostic and connectors can be swapped to match the actual environment.

## What the demo covers

- Overview
- Readiness heatmap
- Evidence pack
- Incidents
- Vendor scorecards
- Recommendations
- OT Events
- Ticketing KPIs
- System Landscape

## Key behaviors

- Deterministic synthetic data is auto-generated on startup if any required CSV is missing.
- The app works fully offline through a deterministic heuristic recommendations engine.
- If a Groq key is available, the Recommendations page streams a fast Draft preview first and then renders the Final authoritative structured JSON.
- Only the Final authoritative JSON drives the structured panels and exports.

## Quickstart

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

### WSL / Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

### Optional seed regeneration

```bash
python -m src.seed
```

The app normally handles this automatically through `ensure_data_present()`.

## Safe key setup

The key lookup order is:

1. `st.secrets["GROQ_API_KEY"]`
2. `GROQ_API_KEY` environment variable
3. Optional session-only paste in the Recommendations page

### Environment variable

```powershell
$env:GROQ_API_KEY="your-groq-api-key"
```

```bash
export GROQ_API_KEY="your-groq-api-key"
```

### Streamlit secrets

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Then edit `.streamlit/secrets.toml` locally. Do not commit it.

### No key

No key is required. The recommendations page will use the deterministic heuristic path and still return the same JSON schema as the LLM path.

## Typical Production Systems (Examples)

### Enterprise / Corporate

- ITSM/CMDB: ServiceNow, Jira Service Management, BMC Remedy, Freshservice
- CMMS/EAM: IBM Maximo, SAP PM, Oracle EAM
- EDMS/Document Control: SharePoint/M365, Generic EDMS
- ERP/Enterprise Apps: SAP S/4HANA, Oracle ERP
- Guest/CRM: Microsoft Dynamics 365, Adobe Experience, Sprinklr
- Observability/Monitoring: Azure Monitor/Log Analytics, Prometheus/Grafana, Datadog, New Relic
- Logging/SIEM: Splunk, Elastic/ELK, Microsoft Sentinel

### Venue / OT and Visitor Systems

- OT Events Feed: BMS / Access Control / CCTV Event Feed
- BMS/Facilities vendors: Honeywell, Siemens, Johnson Controls, Schneider Electric
- VMS/CCTV: Genetec, Milestone
- Access Control: HID
- Ticketing and Gate Validation: accesso Horizon, Generic Ticketing/Gate Validation Platform
- POS/Payments: POS System + Payment Gateway Telemetry
- Network/Wi-Fi/NAC: Network Monitoring Platform
- Queue/Footfall Analytics: Crowd/Queue Analytics
- Digital Signage: Signage CMS

> These labels are examples only and are not claims about a deployed environment.

## Data lineage

Every dataset includes `source_system` plus realistic traceable IDs. Examples:

- `services.csv`: `service_id`, `ci_id`
- `readiness.csv`: `source_system`, gate ownership, dependency context
- `evidence.csv`: `evidence_id`, `doc_ref`, `punch_list_id`
- `incidents.csv`: `incident_id`, `source_id`
- `vendors.csv`: `dashboard_ref`
- `kpis.csv`: `dashboard_ref`
- `ot_events.csv`: `ot_event_id`, `device_id`, `linked_incident_id`
- `ticketing_kpis.csv`: `linked_incident_id`, venue/time traces

Each page includes a Data lineage section that surfaces the example source labels and sample trace references used in the rendered view.

## Recommendations strategy

- Draft / Preview: small Groq model, streamed text, non-authoritative
- Final authoritative result: larger Groq model, strict JSON only
- Validation: stdlib schema validation with one repair attempt
- Failure path: deterministic heuristic fallback with the same schema

The canonical JSON sections are:

- `summary`
- `top_risks`
- `next_actions`
- `incident_improvements`
- `vendor_flags`
- `ot_signals`
- `ticketing_signals`

## 3-minute interview demo script

1. Overview
   Say: "This is the executive posture. The launch threshold is zero RED gates, zero open Sev-1/2 incidents, and a nearly complete evidence pack."
2. Readiness heatmap
   Say: "This shows exactly which service and gate combinations still block launch, plus the named owner and dependency."
3. Evidence pack
   Say: "Here is the document chase list with traceable refs, approvers, and approval status."
4. Incidents
   Say: "This is the live operational stability picture: MTTA, MTTR, severity mix, and SLA discipline."
5. Vendor scorecards
   Say: "This view shows which partners are inside or outside contract and where penalty exposure starts."
6. OT Events
   Say: "This is the facilities and security event picture with alarm severity, zones, acknowledgement discipline, and linked incidents."
7. Ticketing KPIs
   Say: "This is the guest-entry performance picture: scan success, QR latency, throughput, and fallback activation."
8. Recommendations
   Say: "The Draft preview is fast, but the Final authoritative JSON is the only structured output used by the page and exports."
9. System Landscape
   Say: "These are example system labels. The connectors can be swapped to match the real environment without changing the control tower contract."

## Tests and quality gates

```bash
pip check
pytest -q
```

The pytest suite includes:

- schema validation
- heuristic fallback behavior
- recommendations integration with mocked Groq calls
- metrics tests
- Streamlit page smoke tests
- auto-seed regeneration checks

## Packaging

Create the clean demo zip:

```powershell
.\scripts\package_zip.ps1
```

```bash
bash scripts/package_zip.sh
```

Output:

- `seven_control_tower_gemini_demo.zip`

The zip excludes local secrets, venvs, logs, evidence, caches, and other development artifacts.

## Repository structure

```text
app.py
pages/
src/
tests/
docs/
scripts/
```

## Troubleshooting

| Problem | Action |
| --- | --- |
| Missing CSV files | Run `python -m src.seed` or just open the app and let it auto-seed |
| Recommendations run in heuristic mode | Set `GROQ_API_KEY` through env, Streamlit secrets, or the session-only field |
| Streamlit port is busy | Run `streamlit run app.py --server.port 8502` |
| PowerShell blocks script activation | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| Packaging zip contains unwanted files | Re-run the packaging scripts from a clean working tree |

## CHANGELOG

### v2.1.0 - 2026-03-03

- Renamed the demo shell to Al Hamra — Operations Readiness Control Tower
- Added a fixed-timestamp deterministic seed so regenerated CSVs are stable across runs
- Added the System Landscape page and expanded source-system example coverage
- Standardized the app shell, data-lineage panels, executive status badges, and KPI card layout
- Rebuilt recommendations around the new strict JSON schema with Draft preview plus Final authoritative output
- Added Streamlit smoke tests for all pages and offline recommendation generation
- Hardened packaging, gitignore rules, and CI dependency checks

### v2.0.0 - 2026-03-03

- Added OT events and ticketing KPI datasets and pages
- Added heuristic fallback recommendations and Groq integration
- Added packaging scripts, CI, and initial evidence/decision docs
