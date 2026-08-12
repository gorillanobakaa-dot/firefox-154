#!/usr/bin/env bash
# =============================================================================
# apply.sh — apply the Gorilla Unleashed Firefox 154 patch set to a source tree
#
# 🧸 LAYMAN: takes a clean, unmodified copy of Firefox 154 and lays all of our
#    changes onto it — the codec tweaks, the prefs, the theme, the telemetry
#    removals — so it becomes Gorilla Unleashed. Run it once against a fresh
#    Firefox checkout. `--check` first if you just want to test, not touch.
#
# 💻 DEVELOPER: applies every NN.TOPIC/*.patch with `patch -p1`, copies each
#    NEW_FILES/ tree into the source, and (if a profile is given) drops
#    10.OVERRIDES/NEW_FILES/user.js into the profile. Idempotent-ish via
#    --forward (already-applied hunks are skipped, not double-applied).
#
# USAGE:
#   apply.sh --check [SRC_TREE]        # dry-run: report which patches (don't) apply
#   apply.sh SRC_TREE [PROFILE_DIR]    # apply for real
#
# SRC_TREE default: /home/gorilla/firefox-main
# =============================================================================
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MODE="apply"
if [ "${1:-}" = "--check" ]; then MODE="check"; shift; fi
SRC="${1:-/home/gorilla/firefox-main}"
PROFILE="${2:-}"

[ -d "$SRC" ] || { echo "FATAL: source tree not found: $SRC" >&2; exit 1; }
[ -f "$SRC/browser/config/version.txt" ] || { echo "FATAL: $SRC does not look like a Firefox tree" >&2; exit 1; }

# Only the numbered topic rooms carry patches; skip snapshots/orchestration/etc.
mapfile -t PATCHES < <(find "$HERE" -regextype posix-extended \
  -regex '.*/[0-9]{2}\.[^/]+/.*\.patch' 2>/dev/null | sort)

echo "== Gorilla Unleashed patch set =="
echo "   patches : ${#PATCHES[@]}"
echo "   target  : $SRC"
echo "   mode    : $MODE"
echo

ok=0; fail=0; skip=0; declare -a FAILED=()
for p in "${PATCHES[@]}"; do
  rel="${p#$HERE/}"
  if [ "$MODE" = "check" ]; then
    if patch -p1 --dry-run --force -d "$SRC" < "$p" >/dev/null 2>&1; then
      ok=$((ok+1))
    elif patch -p1 --dry-run -R --force -d "$SRC" < "$p" >/dev/null 2>&1; then
      skip=$((skip+1))            # reverse-applies clean => already present
    else
      fail=$((fail+1)); FAILED+=("$rel")
    fi
  else
    if patch -p1 --forward --batch -d "$SRC" < "$p" >/dev/null 2>&1; then ok=$((ok+1))
    else fail=$((fail+1)); FAILED+=("$rel"); fi
  fi
done

# NEW_FILES: copy brand-new files into the tree (all rooms EXCEPT the profile-only user.js)
copied=0
if [ "$MODE" = "apply" ]; then
  while IFS= read -r nf; do
    room="$(basename "$(dirname "$nf")")"
    # 10.OVERRIDES/NEW_FILES/user.js is a PROFILE file, handled separately
    rel="${nf#*/NEW_FILES/}"
    case "$nf" in */10.OVERRIDES/NEW_FILES/user.js) continue;; esac
    dest="$SRC/$rel"; mkdir -p "$(dirname "$dest")"
    cp -a "$nf" "$dest" && copied=$((copied+1))
  done < <(find "$HERE" -path '*/NEW_FILES/*' -type f 2>/dev/null)
fi

# profile user.js
if [ "$MODE" = "apply" ] && [ -n "$PROFILE" ]; then
  ujs="$HERE/10.OVERRIDES/NEW_FILES/user.js"
  [ -f "$ujs" ] && { mkdir -p "$PROFILE"; cp -a "$ujs" "$PROFILE/user.js"; echo "   user.js -> $PROFILE/user.js"; }
fi

echo
echo "== RESULT =="
echo "   applied/clean : $ok"
[ "$MODE" = "check" ] && echo "   already-present: $skip"
[ "$MODE" = "apply" ]  && echo "   new files copied: $copied"
echo "   FAILED        : $fail"
if [ "$fail" -gt 0 ]; then
  printf '     - %s\n' "${FAILED[@]}"
  echo
  echo "Some patches did not apply cleanly. On a FRESH vanilla 154 tree this should be 0;"
  echo "a non-zero count means the tree is not vanilla, or a patch has drifted."
  exit 1
fi
echo "   ALL CLEAN ✓"
