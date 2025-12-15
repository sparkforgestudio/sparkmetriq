#!/usr/bin/env bash
set -euo pipefail

# Exiger rg (ripgrep)
command -v rg >/dev/null 2>&1 || {
  echo "ERROR: rg (ripgrep) is required. Install: sudo apt-get install -y ripgrep" >&2
  exit 2
}

CORE_DIRS=("saasentialcore" "api/core")
BANNED_IMPORT_PATTERNS=(
  "from[[:space:]]+products\\."
  "import[[:space:]]+products\\."
)

EXCLUDE_GLOBS=(--glob=!.venv/** --glob=!venv/** --glob=!node_modules/** --glob=!__pycache__/** --glob=!.pytest_cache/** --glob=!.git/** --glob=!docs/** --glob=!frontend/**)

found=0

for d in "${CORE_DIRS[@]}"; do
  [[ -d "$d" ]] || continue
  for p in "${BANNED_IMPORT_PATTERNS[@]}"; do
    echo ">> scanning $d for pattern: $p"
    if rg -n --hidden --no-ignore-vcs -S "${EXCLUDE_GLOBS[@]}" "$p" "$d" 2>/dev/null; then
      found=1
    fi
  done
done

if [[ "$found" -eq 1 ]]; then
  echo "ERROR: Forbidden imports from products/* detected in core directories." >&2
  exit 1
fi

echo "OK: no forbidden core->products imports"
