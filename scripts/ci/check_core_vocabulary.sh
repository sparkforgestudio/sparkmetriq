#!/usr/bin/env bash
# scripts/ci/check_core_vocabulary.sh
#
# Enforce "core vocabulary neutrality" by scanning core directories for
# forbidden product tokens.
#
# Robust version:
# - Requires ripgrep (rg) and fails hard if rg errors.
# - Uses rg exit codes correctly (0=found, 1=not found, 2=error).
# - Excludes tests/docs/venv/node_modules/etc via --glob='!pattern' (rg-compatible).
# - Optional allowlist for legacy env tokens (MUSAI_ / legacy / fallback) to avoid noise.

set -euo pipefail

TOKENS_FILE="${1:-/tmp/core_blacklist_tokens.txt}"
CORE_DIRS=("saasentialcore" "api/core")

echo "=== Core Vocabulary Check ==="
echo "Tokens file : $TOKENS_FILE"
echo "Core dirs   : ${CORE_DIRS[*]}"
echo

# --- Preconditions ------------------------------------------------------------

command -v rg >/dev/null 2>&1 || {
  echo "ERROR: 'rg' (ripgrep) is required but not found in PATH." >&2
  echo "Install ripgrep, then retry." >&2
  exit 2
}

[[ -f "$TOKENS_FILE" ]] || {
  echo "ERROR: Missing tokens file: $TOKENS_FILE" >&2
  echo "Create it, e.g.:" >&2
  echo "  cat > $TOKENS_FILE <<'EOF'" >&2
  echo "  sparkmetriq" >&2
  echo "  sparkpusher" >&2
  echo "  predyq" >&2
  echo "  musai" >&2
  echo "  muse" >&2
  echo "  ppv" >&2
  echo "  funnel" >&2
  echo "  instagram" >&2
  echo "  tiktok" >&2
  echo "  threads" >&2
  echo "  EOF" >&2
  exit 2
}

# --- Exclusions ---------------------------------------------------------------
# NOTE: ripgrep expects --glob='!pattern' as ONE argument; do NOT split it.
RG_EXCLUDES=(
  "--glob=!**/.git/**"
  "--glob=!**/.venv/**"
  "--glob=!**/venv/**"
  "--glob=!**/node_modules/**"
  "--glob=!**/__pycache__/**"
  "--glob=!**/.pytest_cache/**"
  "--glob=!**/docs/**"
  "--glob=!**/tests/**"
  "--glob=!**/test_*.py"
  "--glob=!**/*tests.py"
)

# Allowlist lines that are acceptable to contain legacy env names during transition.
# This does NOT "hide" real product coupling; it only avoids flagging fallback env var strings.
ALLOWLINE_REGEX='MUSAI_|legacy|fallback'

found=0
matches_tmp="$(mktemp -t core_vocab_matches.XXXXXX)"
trap 'rm -f "$matches_tmp"' EXIT

# --- Scan ---------------------------------------------------------------------

while IFS= read -r token || [[ -n "$token" ]]; do
  # Strip whitespace
  token="$(echo "$token" | sed -e 's/^[[:space:]]\+//' -e 's/[[:space:]]\+$//')"
  # Skip empty lines and comments
  [[ -z "$token" ]] && continue
  [[ "$token" =~ ^# ]] && continue

  for d in "${CORE_DIRS[@]}"; do
    [[ -d "$d" ]] || continue

    echo ">> scanning $d for token: $token"

    # Run rg; handle exit codes properly:
    # 0 => matches found (collect them)
    # 1 => no matches (fine)
    # 2 => error (fail)
    set +e
    rg -n --hidden --no-ignore-vcs -S "${RG_EXCLUDES[@]}" "$token" "$d" 2>&1 \
      | rg -v -n "$ALLOWLINE_REGEX" >> "$matches_tmp"
    rc="${PIPESTATUS[0]}"
    set -e

    if [[ "$rc" -eq 0 ]]; then
      found=1
    elif [[ "$rc" -eq 1 ]]; then
      : # no matches, OK
    else
      echo "ERROR: rg failed while scanning token '$token' in '$d' (exit=$rc)." >&2
      echo "This usually means an invalid glob/flag or an I/O problem." >&2
      exit 2
    fi
  done
done < "$TOKENS_FILE"

echo

# --- Report -------------------------------------------------------------------

if [[ "$found" -eq 1 ]]; then
  echo "ERROR: Forbidden product vocabulary detected in core directories." >&2
  echo "Matches (after allowlist filtering):" >&2
  echo "-----------------------------------" >&2
  cat "$matches_tmp" >&2 || true
  echo "-----------------------------------" >&2
  exit 1
fi

echo "OK: core vocabulary clean"
exit 0

