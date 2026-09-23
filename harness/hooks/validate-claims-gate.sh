#!/usr/bin/env bash
# craftharness quality gate — the enforcement leg of the harness.
#
# Wired as a Claude Code Stop hook (see hooks.json). If the working tree holds a
# claims.json, no turn may finish until every claim passes validate_claims.py:
# unique ids, grounded confirmed claims, finder != validator, and >=2 independent
# origins for high-risk confirmed claims. On failure this exits 2, which blocks
# the stop and feeds the violations back to the model to fix. When there is no
# claims.json, the gate is a no-op (exit 0) — it never gets in the way of work
# that isn't producing cited claims yet.
#
# Exit codes: 0 = pass / nothing to check · 2 = block (validation failed or the
# validator/python is missing while a claims.json exists).
set -uo pipefail

# Consume any hook JSON on stdin so we never block on a pipe; we don't need it.
if [ ! -t 0 ]; then
  cat >/dev/null 2>&1 || true
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VALIDATOR="$SCRIPT_DIR/../lib/validate_claims.py"

# Where to look for a claims file: the project dir Claude Code exports, else cwd.
WORK_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"

CLAIMS=""
for candidate in "$WORK_DIR/claims.json" "$PWD/claims.json"; do
  if [ -f "$candidate" ]; then
    CLAIMS="$candidate"
    break
  fi
done

# No claims artifact in play → nothing to enforce, pass cleanly.
if [ -z "$CLAIMS" ]; then
  exit 0
fi

if [ ! -f "$VALIDATOR" ]; then
  echo "craftharness gate: claims.json present ($CLAIMS) but validator not found at $VALIDATOR" >&2
  exit 2
fi

PY="$(command -v python3 || command -v python || true)"
if [ -z "$PY" ]; then
  echo "craftharness gate: claims.json present but no python3 on PATH to validate it" >&2
  exit 2
fi

if "$PY" "$VALIDATOR" "$CLAIMS" >&2; then
  exit 0
fi

echo "craftharness gate: BLOCKED — $CLAIMS has unproven or malformed claims. Fix the violations above (ground each confirmed claim, keep finder != validator, give high-risk claims >=2 independent sources) before finishing." >&2
exit 2
