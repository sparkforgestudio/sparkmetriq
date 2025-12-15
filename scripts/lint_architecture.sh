#!/usr/bin/env bash
set -euo pipefail

echo "=== lint-architecture (bash) ==="
echo "[1/3] core imports"
./scripts/ci/check_core_imports.sh

echo "[2/3] core vocabulary"
TOKENS_FILE="${1:-/tmp/core_blacklist_tokens.txt}"
./scripts/ci/check_core_vocabulary.sh "$TOKENS_FILE"

echo "[3/3] workspace consistency"
python ./scripts/check_workspace_consistency.py

echo "✅ lint-architecture PASS"
