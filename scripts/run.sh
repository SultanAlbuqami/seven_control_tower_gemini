#!/usr/bin/env bash
set -euo pipefail

KEY="${1:-}"

if [[ ! -d ".venv" ]]; then
  python -m venv .venv
fi

source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

if [[ ! -f "./data/services.csv" ]]; then
  python -m src.seed
fi

if [[ -n "$KEY" ]]; then
  export GEMINI_API_KEY="$KEY"
fi

streamlit run app.py
