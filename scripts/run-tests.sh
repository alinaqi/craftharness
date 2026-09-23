#!/usr/bin/env bash
# craftharness test runner — walks you through the TEST-CASES.md suite.
#
# The cases are qualitative: you paste each PROMPT into a Claude Code session
# (with the skills installed via ./install.sh) and score the output against the
# rubric. This script prints each prompt cleanly, captures your score + note, and
# writes a dated scoresheet. TC-10 (the adapter) it can run for you directly.
#
# Usage:
#   scripts/run-tests.sh           # interactive walkthrough (score as you go)
#   scripts/run-tests.sh --list    # just print all prompts (copy/paste), no scoring
set -euo pipefail

BOLD=$'\033[1m'; DIM=$'\033[2m'; GRN=$'\033[32m'; YEL=$'\033[33m'; CYN=$'\033[36m'; RST=$'\033[0m'
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LIST_ONLY=0; [ "${1:-}" = "--list" ] && LIST_ONLY=1

# id | skill | prompt | pass criteria (what "good" looks like)
IDS=(TC-01 TC-02 TC-03 TC-04 TC-05 TC-06 TC-07 TC-08 TC-09 TC-10)
SKILLS=(competitive-intel market-research business-plan business-plan competitive-intel content-studio market-research competitive-intel market-research "adapter/terminal")
PROMPTS=(
"Do competitor research on Notion vs Asana for a PM-tool pitch."
"Market research on the AI coding-agent market — players, segments, trends."
"Draft a business plan for Bravo (getbravo.io), the employee recognition and rewards platform."
"Business plan for a new commercial data-API product (uDAPI) that powers AI research harnesses."
"Competitive landscape for zenloop in the NPS / customer-experience space."
"Write a launch thread (X/LinkedIn) for craftharness — the open-source harness for knowledge work."
"Research craftharness — what it is, who's behind it, how it compares."
"What is zenloop's exact ARR and churn rate, with a competitive breakdown?"
"Research the current pricing of Linear — resolve any conflicting numbers you find."
"python3 -m conduit.adapters.dataforseo volume \"notion\" \"asana\""
)
PASS=(
"cited positioning/pricing/feature-gap matrix; a needs-validation section; no uncited pricing"
"real players cited; TAM as [ASSUMPTION] if unsourced; honest gaps"
"market/competitors cited; every number tagged [FACT]/[ASSUMPTION]/[PROJECTION]; NO invented Bravo financials"
"competitors/market cited; unit economics as labelled assumptions; honest financials"
"real competitors (Qualtrics/Medallia…) cited; zenloop internals flagged unverifiable"
"on-brand; every factual claim grounded, not overstated; no invented features/benchmarks"
"★ ADMITS near-zero public footprint; cites only the GitHub repo; invents NOTHING"
"states the numbers are private/not public; ranges only as labelled estimates, or declines"
"surfaces the conflict, cites each source, states which is current + why"
"returns real monthly volumes + cost line (needs DATAFORSEO_LOGIN/PASSWORD; empty+health=False if unset)"
)

hr(){ printf '%s\n' "${DIM}────────────────────────────────────────────────────────${RST}"; }

if [ "$LIST_ONLY" -eq 1 ]; then
  for i in "${!IDS[@]}"; do
    printf '%s[%s · %s]%s\n%s\n\n' "$BOLD" "${IDS[$i]}" "${SKILLS[$i]}" "$RST" "${PROMPTS[$i]}"
  done
  exit 0
fi

# preflight
if [ ! -d "$HOME/.claude/skills/research-spine" ]; then
  printf '%s! skills not installed.%s Run: %sbash install.sh%s  then open a NEW Claude Code window.\n\n' \
    "$YEL" "$RST" "$BOLD" "$RST"
fi
STAMP="$(date +%F-%H%M)"
OUT="$ROOT/docs/test-results-$STAMP.md"
printf '# craftharness test results — %s\n\n| Case | Skill | Score | Note |\n|---|---|---|---|\n' "$STAMP" > "$OUT"

printf '%scraftharness test walkthrough%s  — paste each prompt into Claude Code, score the output.\n' "$BOLD" "$RST"
printf '%sRubric: grounding · honesty-about-gaps · no-hallucination · method-visible · deliverable-quality (0-2 each)%s\n' "$DIM" "$RST"

for i in "${!IDS[@]}"; do
  hr
  printf '%s%s%s  ·  skill: %s%s%s\n\n' "$BOLD" "${IDS[$i]}" "$RST" "$CYN" "${SKILLS[$i]}" "$RST"
  printf '  %sPASTE THIS%s:\n\n      %s\n\n' "$GRN" "$RST" "${PROMPTS[$i]}"
  printf '  %spass =%s %s\n\n' "$DIM" "$RST" "${PASS[$i]}"

  if [ "${IDS[$i]}" = "TC-10" ]; then
    printf '  This one is a terminal command. Run it now? [y/N] '
    read -r yn
    if [ "${yn:-N}" = "y" ] || [ "${yn:-N}" = "Y" ]; then
      ( cd "$ROOT" && eval "${PROMPTS[$i]}" ) || printf '  %s(no DataForSEO key set — expected empty/health=False)%s\n' "$DIM" "$RST"
    fi
  fi

  printf '  score /10 (blank to skip): '; read -r score
  printf '  note: '; read -r note
  printf '| %s | %s | %s | %s |\n' "${IDS[$i]}" "${SKILLS[$i]}" "${score:-–}" "${note:-}" >> "$OUT"
done

hr
printf '%s✓ scoresheet written:%s %s\n' "$GRN" "$RST" "$OUT"
printf '%sPaste any output that felt off back to Claude and it will tune the skills from the real failure.%s\n' "$DIM" "$RST"
