#!/usr/bin/env bash
# Bash: create a clean distributable ZIP of the demo
# Usage: bash scripts/package_zip.sh
# Output: seven_control_tower_gemini_demo.zip (in workspace root)

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ZIP_NAME="seven_control_tower_gemini_demo.zip"
OUT_PATH="$ROOT_DIR/$ZIP_NAME"

echo "[package] Building $ZIP_NAME from $ROOT_DIR"

# Remove old zip
rm -f "$OUT_PATH"

# Exclusions
EXCLUDE_ARGS=(
  --exclude="*/.venv/*"
  --exclude="*/__pycache__/*"
  --exclude="*/.git/*"
  --exclude="*/evidence/*"
  --exclude="*/.idea/*"
  --exclude="*/.vscode/*"
  --exclude="*.pyc"
  --exclude="*.log"
  --exclude="*/.env"
  --exclude="*/secrets.toml"
  --exclude="*/$ZIP_NAME"
)

cd "$ROOT_DIR"
zip -r "$OUT_PATH" . "${EXCLUDE_ARGS[@]}"

FILE_COUNT=$(unzip -l "$OUT_PATH" | tail -1 | awk '{print $2}')
SIZE_KB=$(du -k "$OUT_PATH" | cut -f1)
echo "[package] Done: $OUT_PATH (${SIZE_KB} KB, ${FILE_COUNT} entries)"
