Param(
  [string]$Key = ""
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\.venv")) {
  python -m venv .venv
}

.\.venv\Scripts\Activate.ps1
pip install -U pip
pip install -r requirements.txt

if (-not (Test-Path ".\data\services.csv")) {
  python -m src.seed
}

if ($Key -ne "") {
  $env:GROQ_API_KEY = $Key
}

streamlit run app.py
