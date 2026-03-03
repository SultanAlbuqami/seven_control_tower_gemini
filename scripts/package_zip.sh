#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ZIP_NAME="seven_control_tower_gemini_demo.zip"
OUT_PATH="$ROOT_DIR/$ZIP_NAME"
PYTHON_BIN="${PYTHON_BIN:-}"

if [[ -z "$PYTHON_BIN" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  else
    PYTHON_BIN="python"
  fi
fi

rm -f "$OUT_PATH"

ROOT_DIR="$ROOT_DIR" OUT_PATH="$OUT_PATH" "$PYTHON_BIN" - <<'PY'
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
import os

root = Path(os.environ["ROOT_DIR"])
out_path = Path(os.environ["OUT_PATH"])

exclude_segments = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".nox",
    ".tox",
    "build",
    "dist",
    "evidence",
    "logs",
    ".idea",
    ".vscode",
}

exclude_leaf_names = {
    ".env",
    "secrets.toml",
    "secrets.toml.offline-test",
    "seven_control_tower_gemini_demo.zip",
}

exclude_suffixes = {".pyc", ".pyo", ".pyd", ".log", ".zip"}


def should_exclude(path: Path) -> bool:
    for part in path.parts:
        if part in exclude_segments:
            return True
        if part in exclude_leaf_names:
            return True
        if any(part.endswith(suffix) for suffix in exclude_suffixes):
            return True
    return False


files = []
for path in root.rglob("*"):
    if path.is_file():
        relative = path.relative_to(root)
        if not should_exclude(relative):
            files.append(relative)

with ZipFile(out_path, "w", compression=ZIP_DEFLATED) as archive:
    for relative in files:
        archive.write(root / relative, arcname=relative.as_posix())

print(f"[package] Built {out_path.name} ({len(files)} files)")
PY
