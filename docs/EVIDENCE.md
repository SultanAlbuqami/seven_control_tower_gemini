# Execution Evidence

All commands below were executed from `v:\seven_control_tower_gemini`.

## Phase 1 - Baseline audit

### Repo state

Command:

```powershell
git status --short --branch
git remote -v
```

Result:

- Branch started on `main`
- `origin` pointed to `https://github.com/SultanAlbuqami/seven_control_tower_gemini.git`

### Secret and placeholder scan

Command:

```powershell
git ls-files .env .streamlit/secrets.toml
```

Result:

- No tracked `.env`
- No tracked `.streamlit/secrets.toml`

Command:

```powershell
rg -n --hidden -g '!.git/*' -g '!.venv/*' -g '!.streamlit/secrets.toml' -g '!.env' 'sk-|AIza|gsk_[A-Za-z0-9]+'
```

Result:

- No matches

Command:

```powershell
rg -n --hidden -g '!.git/*' -g '!.venv/*' -g '!.streamlit/secrets.toml' -g '!.env' 'GROQ_API_KEY|GEMINI_API_KEY|api_key|\.env|secrets\.toml'
```

Result:

- Matches were limited to placeholder files, docs, tests, and code paths that intentionally reference key handling
- No live secret values were present in the scanned working tree content

## Phase 2 - Dependency sanity

### Global environment check

Command:

```powershell
pip check
```

Result:

- Failed in the global Python environment because of unrelated workstation packages (`graphql-core` conflicts)
- Repository verification was moved to the repo-local `.venv` per decision D-008

### Repo-local environment

Command:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
```

Result:

- Dependency install completed
- `No broken requirements found.`

## Phase 3 - Test suite

Command:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Result:

- `71 passed in 3.88s`

Notes:

- Includes schema tests
- Includes heuristic and recommendations integration tests
- Includes Streamlit `AppTest` smoke coverage for all pages
- Includes offline recommendations page generation
- Includes auto-seed verification by deleting CSVs and re-running `app.py` under `AppTest`

## Phase 4 - Data generation

Command:

```powershell
.\.venv\Scripts\python.exe -m src.seed
```

Result:

- `Deterministic demo data generated.`

## Phase 5 - Live Streamlit startup smoke

Command:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.headless true --server.port 8503
```

Execution notes:

- Local `.streamlit/secrets.toml` was temporarily moved out of the way for the offline-safe check and restored afterward
- `GROQ_API_KEY` was removed from the process environment for the same check
- The server was polled at `http://127.0.0.1:8503/`

Result:

- `READY=1`
- HTTP root returned successfully

Important limitation:

- A raw HTTP GET only confirms server startup; it does not execute the Streamlit page script end-to-end
- Auto-seed regeneration and page rendering were verified by the `AppTest` smoke suite in pytest, not by the bootstrap HTTP response

## Phase 6 - Packaging

### PowerShell packaging

Command:

```powershell
.\scripts\package_zip.ps1
```

Result:

- `[package] Built seven_control_tower_gemini_demo.zip (96.7 KB, 57 files)`

### Bash packaging

Command:

```bash
bash scripts/package_zip.sh
```

Result:

- `[package] Built seven_control_tower_gemini_demo.zip (57 files)`

### Zip inspection

Command:

```powershell
python - <<'PY'
from pathlib import Path
from zipfile import ZipFile
zip_path = Path(r'v:\seven_control_tower_gemini\seven_control_tower_gemini_demo.zip')
blocked_exact = {'.env', '.streamlit/secrets.toml'}
blocked_segments = ['.venv/', 'venv/', 'evidence/', 'logs/', '.pytest_cache/', '.mypy_cache/', '.ruff_cache/', '/dist/', '/build/']
with ZipFile(zip_path) as archive:
    names = archive.namelist()
violations = [name for name in names if name in blocked_exact or any(segment in name for segment in blocked_segments)]
print(len(names), len(violations))
PY
```

Result:

- `ENTRY_COUNT=57`
- `VIOLATIONS=0`

## Phase 7 - CI workflow

File checked:

```text
.github/workflows/ci.yml
```

Result:

- Python matrix remains `3.11` and `3.12`
- `pip check` is included before pytest
- No secrets are required for CI

## Phase 8 - Feature branch commits

### Product changes commit

Command:

```powershell
git add app.py .streamlit/config.toml pages/0_Overview.py pages/1_Readiness.py pages/1_Readiness_Heatmap.py pages/2_Evidence_Pack.py pages/3_Incidents.py pages/4_Vendor_Scorecards.py pages/5_Recommendations.py pages/6_OT_Events.py pages/7_Ticketing_KPIs.py pages/8_System_Landscape.py src/ai/groq_recommender.py src/data.py src/domain/constants.py src/metrics.py src/recommendations/__init__.py src/recommendations/groq_adapter.py src/recommendations/heuristic.py src/recommendations/schema.py src/recommendations/service.py src/recommendations/snapshot.py src/seed.py src/system_landscape.py src/ui.py tests/test_heuristic.py tests/test_recommendations_integration.py tests/test_schema.py tests/test_app_smoke.py
git commit -m "feat(control-tower): upgrade shell recommendations and operations views"
```

Result:

- Commit created: `911a956`
- Commit title: `feat(control-tower): upgrade shell recommendations and operations views`

### Quality and packaging commit

Command:

```powershell
git add .env.example .github/workflows/ci.yml .gitignore .streamlit/secrets.toml.example README.md docs/DECISIONS.md docs/EVIDENCE.md scripts/package_zip.ps1 scripts/package_zip.sh
git commit -m "chore(quality): harden packaging docs and secret handling"
```

Result:

- Commit created: `7db2b28`
- Commit title: `chore(quality): harden packaging docs and secret handling`

## Phase 9 - Merge and push

Command:

```powershell
git fetch origin
git checkout main
git merge --no-ff feat/visual-identity-dual-llm-ot-ticketing
git push -u origin main
git status --short --branch
git log --oneline --decorate -6
git rev-parse --short HEAD
git rev-parse --short origin/main
```

Result:

- Merge commit created on `main`: `9ede7f6`
- Push succeeded: `14e074f..9ede7f6  main -> main`
- `HEAD` = `9ede7f6`
- `origin/main` = `9ede7f6`
- `git status --short --branch` returned only `## main...origin/main`, which confirms no local file modifications
