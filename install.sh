#!/usr/bin/env bash
#
# craftharness installer — copies the OSS harness into your Claude Code home so
# you can use it TODAY, BYO-keys, with no hosted uDAPI required.
#
# What it installs:
#   harness/skills/*  ->  ~/.claude/skills/            (the method: research-spine + deliverables)
#   harness/lib/*     ->  ~/.claude/craftharness/lib/  (validate_claims.py + shared code)
#   harness/hooks/*   ->  ~/.claude/craftharness/hooks/ (quality-control hooks, opt-in wiring)
#
# It is idempotent and non-destructive: it only writes into craftharness-owned
# locations, never touches unrelated files, and re-running it simply refreshes
# the installed copies.
#
# Usage:
#   ./install.sh                 # install into ~/.claude
#   ./install.sh --dest DIR      # install into DIR instead of ~/.claude
#   CRAFTHARNESS_HOME=DIR ./install.sh
#   ./install.sh --dry-run       # show what would happen, change nothing
#
set -euo pipefail

# ---------------------------------------------------------------------------
# Pretty output (no external deps; colors disabled when not a TTY).
# ---------------------------------------------------------------------------
if [ -t 1 ]; then
  BOLD="$(printf '\033[1m')"; DIM="$(printf '\033[2m')"
  GREEN="$(printf '\033[32m')"; YELLOW="$(printf '\033[33m')"
  BLUE="$(printf '\033[34m')"; RED="$(printf '\033[31m')"; RESET="$(printf '\033[0m')"
else
  BOLD=""; DIM=""; GREEN=""; YELLOW=""; BLUE=""; RED=""; RESET=""
fi

info()  { printf '%s\n' "${BLUE}==>${RESET} $*"; }
ok()    { printf '%s\n' "${GREEN} ok${RESET} $*"; }
warn()  { printf '%s\n' "${YELLOW} !!${RESET} $*"; }
err()   { printf '%s\n' "${RED}err${RESET} $*" >&2; }
die()   { err "$*"; exit 1; }

# ---------------------------------------------------------------------------
# Resolve the repo root from this script's own location (works via symlink,
# from any CWD, and when piped is not supported — run it from a checkout).
# ---------------------------------------------------------------------------
SOURCE="${BASH_SOURCE[0]:-$0}"
while [ -h "$SOURCE" ]; do
  DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  case "$SOURCE" in /*) ;; *) SOURCE="$DIR/$SOURCE" ;; esac
done
REPO_ROOT="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"

# ---------------------------------------------------------------------------
# Parse arguments.
# ---------------------------------------------------------------------------
DEST_ROOT="${CRAFTHARNESS_HOME:-$HOME/.claude}"
DRY_RUN=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --dest)     shift; [ "$#" -gt 0 ] || die "--dest needs a directory"; DEST_ROOT="$1" ;;
    --dest=*)   DEST_ROOT="${1#*=}" ;;
    --dry-run)  DRY_RUN=1 ;;
    -h|--help)
      sed -n '2,20p' "$SOURCE" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) die "unknown argument: $1 (try --help)" ;;
  esac
  shift
done

SRC_SKILLS="$REPO_ROOT/harness/skills"
SRC_LIB="$REPO_ROOT/harness/lib"
SRC_HOOKS="$REPO_ROOT/harness/hooks"

SKILLS_DEST="$DEST_ROOT/skills"
LIB_DEST="$DEST_ROOT/craftharness/lib"
HOOKS_DEST="$DEST_ROOT/craftharness/hooks"

# ---------------------------------------------------------------------------
# copy_dir SRC DST LABEL  — mirror one directory idempotently.
# Copies each top-level entry of SRC into DST. Honors --dry-run.
# ---------------------------------------------------------------------------
copy_dir() {
  src="$1"; dst="$2"; label="$3"
  if [ ! -d "$src" ]; then
    warn "$label: nothing to install (missing $src) — skipping"
    return 0
  fi
  # Any entries at all?
  if [ -z "$(ls -A "$src" 2>/dev/null)" ]; then
    warn "$label: $src is empty — skipping"
    return 0
  fi
  count=0
  for entry in "$src"/*; do
    [ -e "$entry" ] || continue
    name="$(basename "$entry")"
    if [ "$DRY_RUN" -eq 1 ]; then
      printf '%s\n' "${DIM}   would copy${RESET} $name -> $dst/"
    else
      mkdir -p "$dst"
      # -R for dirs/files; refresh in place (idempotent overwrite of our own files).
      rm -rf "$dst/$name"
      cp -R "$entry" "$dst/$name"
    fi
    count=$((count + 1))
  done
  ok "$label: $count item(s) -> $dst"
}

echo
info "${BOLD}craftharness installer${RESET}"
printf '%s\n' "${DIM}   source : $REPO_ROOT${RESET}"
printf '%s\n' "${DIM}   dest   : $DEST_ROOT${RESET}"
[ "$DRY_RUN" -eq 1 ] && warn "dry-run: no files will be written"
echo

copy_dir "$SRC_SKILLS" "$SKILLS_DEST" "skills"
copy_dir "$SRC_LIB"    "$LIB_DEST"    "lib"
copy_dir "$SRC_HOOKS"  "$HOOKS_DEST"  "hooks"

# Make the validator executable if it landed.
if [ "$DRY_RUN" -eq 0 ] && [ -f "$LIB_DEST/validate_claims.py" ]; then
  chmod +x "$LIB_DEST/validate_claims.py" 2>/dev/null || true
fi

# ---------------------------------------------------------------------------
# Next steps.
# ---------------------------------------------------------------------------
echo
info "${BOLD}Next steps${RESET}"
cat <<EOF

  1. Restart Claude Code (or run /skills) so it picks up the new skills.

  2. Try it — in any Claude Code session, just ask:

       ${BOLD}do competitor research on Notion vs Coda${RESET}

     The research-spine skill auto-invokes: it SCOPEs the question, GATHERs
     evidence with real tools (WebSearch / WebFetch / Bash), SYNTHESIZEs,
     VALIDATEs each claim against its cited source (finder != validator), and
     DELIVERs a cited artifact. See examples/competitor-research.md.

  3. ${BOLD}BYO-keys${RESET} — the skills work with ${BOLD}no keys at all${RESET} using Claude Code's
     built-in WebSearch / WebFetch / Bash. Keys are optional and only unlock
     extra data adapters:

       ${DIM}# optional: keyword/SERP volume via the conduit dataforseo adapter${RESET}
       export DATAFORSEO_LOGIN="your-login"
       export DATAFORSEO_PASSWORD="your-password"

     No hosted uDAPI is required yet — everything runs locally against the tools
     you already have.
EOF

if [ -d "$HOOKS_DEST" ] && [ -n "$(ls -A "$HOOKS_DEST" 2>/dev/null || true)" ]; then
  cat <<EOF

  4. ${BOLD}Optional — enforce quality with a hook${RESET} (Claude Code only). Skills can only
     suggest; a Stop hook is the real gate. To block un-cited deliverables, add
     this to ${DEST_ROOT}/settings.json under "hooks" (merge, don't overwrite):

       "hooks": {
         "Stop": [
           { "matcher": "", "hooks": [
             { "type": "command",
               "command": "$HOOKS_DEST/validate-claims-gate.sh" }
           ] }
         ]
       }

     The installer does NOT edit settings.json for you — wiring hooks is opt-in.
EOF
fi

echo
ok "${BOLD}craftharness installed.${RESET} Skills are BYO-keys — no account needed to start."
echo
