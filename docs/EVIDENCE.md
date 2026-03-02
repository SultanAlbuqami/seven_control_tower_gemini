# Evidence Recording Guide

## Purpose
This file explains how to safely record terminal output as evidence of correct execution **without capturing secrets**.

---

## Rules

1. **Never paste raw `env` or `printenv` output** — it may contain API keys.
2. **Redact secrets before saving**: replace actual key values with `<REDACTED>`.
3. **Use `pytest --tb=short -q` output** directly — it contains no secrets.
4. Store evidence files in this `evidence/` folder (excluded from git via `.gitignore`).

---

## Recommended evidence commands

### Pytest run
```bash
pytest -q --tb=short 2>&1 | tee evidence/pytest_$(date +%Y%m%dT%H%M%S).txt
```

### Streamlit smoke check (headless)
```bash
python -c "from src.data import load_data; load_data(); print('data OK')" 2>&1 | tee evidence/data_check.txt
```

### Seed generation
```bash
python -m src.seed 2>&1 | tee evidence/seed.txt
```

---

## After recording
- Review the file for any secrets before committing or sharing.
- Keep evidence files local (they are gitignored).
