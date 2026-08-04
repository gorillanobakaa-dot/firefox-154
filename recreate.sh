#!/usr/bin/env bash
# =============================================================================
# recreate_success.sh — THE BIG GREEN BUTTON (2026-08-04 rewrite, patch-based)
# =============================================================================
# 🧸 LAYMAN: one command that recreates Gorilla Unleashed from nothing. It
#    downloads a clean copy of Firefox's source code, lays all our changes onto
#    it, compiles it, and (if you want) wraps it into an installable .deb. Grab
#    a coffee — the download and the compile each take a while.
#
# 💻 DEVELOPER: cold-start reproducer. Clones mozilla-unified, applies the
#    Gorilla patch set via new.patches/apply.sh (fuzz-tolerant, see BASELINE.txt),
#    copies the tuned mozconfig, builds through the hardened capture wrapper, and
#    optionally packages the .deb. Replaces the OLD graft-based script, whose
#    universal_freedom_installer/precheck.sh dependencies no longer exist and
#    whose file-copy method this project deliberately abandoned.
#
# USAGE:  recreate_success.sh [SRC_DIR]
#   SRC_DIR default: ~/gorilla-recreate/firefox-src  (a FRESH dir; never your
#                    existing working tree — this clones from scratch)
#
# -----------------------------------------------------------------------------
# 🦍 YO, PAY ATTENTION — WHY BUILDING BEATS DOWNLOADING:
#
#   Because you build from MY mozconfig, you get the added bonus -march=native,
#   and if I'm in a good mood I'll even throw in a few other goodies like -O3,
#   BIOTCHES. 😎
#
#   Translation for the sane: `-march=native` tells the compiler "optimise for
#   the EXACT chip you're compiling on" — YOUR laptop, not mine. It uses every
#   instruction your CPU actually has instead of the museum-safe baseline that
#   shipped binaries must assume. Same for -O3 and LTO. That is the whole point:
#
#     * the prebuilt .deb on the Releases page was compiled for MY machine
#       (Ivy Bridge / Intel HD 4000). It RUNS elsewhere, but it is tuned to me.
#     * this script compiles for YOU. Your cache sizes, your instruction set.
#       That is a better browser than anything I can hand you prebuilt.
#
#   The cost is time (the compile is long on an old machine) and disk (~10-15 GB
#   of build tree). If you have neither, grab the prebuilt .deb instead — it
#   works fine. If you have a spare evening, build it. It's your silicon; use it.
#
#   ⚠ One honest catch: a binary built with -march=native may NOT run on a
#   DIFFERENT/older CPU. Build it on the machine you'll run it on. Don't compile
#   on your shiny new laptop and copy the .deb to grandma's 2009 netbook — it
#   will die with "Illegal instruction". Build there, or use the generic .deb.
# -----------------------------------------------------------------------------
# =============================================================================
set -euo pipefail

# ---- resolve repo root from THIS script's location (portable; no hardcoded paths) ----
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCHSET="$REPO/patches"
MOZCONFIG_SRC="$REPO/mozconfig"                    # the tuned clang-21 mozconfig (bundled)
SRC="${1:-$HOME/gorilla-recreate/firefox-src}"
UPSTREAM="https://github.com/mozilla-firefox/firefox.git"  # mozilla-unified mirror
BASELINE_DATE="2026-07-10"

B_G='\033[1;32m'; B_C='\033[1;36m'; B_Y='\033[1;33m'; B_R='\033[1;31m'; NC='\033[0m'
say(){ echo -e "${B_C}$*${NC}"; }
ok(){ echo -e "${B_G}✓ $*${NC}"; }
warn(){ echo -e "${B_Y}⚠ $*${NC}"; }
die(){ echo -e "${B_R}✗ $*${NC}" >&2; exit 1; }

echo -e "${B_G}"
echo "   ╔══════════════════════════════════════════════╗"
echo "   ║   G O R I L L A   U N L E A S H E D   1 5 4    ║"
echo "   ║        recreate our success — one button       ║"
echo "   ╚══════════════════════════════════════════════╝"
echo -e "${NC}"

# ---- 0. sanity: tools + patch set present ----
[ -d "$PATCHSET" ] || die "patch set not found: $PATCHSET"
[ -x "$PATCHSET/apply.sh" ] || die "apply.sh missing/not executable in $PATCHSET"
for t in git python3 patch rsync; do command -v "$t" >/dev/null || die "missing required tool: $t"; done
command -v clang-21 >/dev/null || warn "clang-21 not found — the tuned mozconfig expects it; install LLVM/Clang 21 or edit the mozconfig."
say "Baseline: Firefox 154.0a1 nightly, snapshot ~${BASELINE_DATE}."
warn "154.0a1 is a NIGHTLY with no exact pinned changeset (see new.patches/BASELINE.txt)."
warn "A fresh clone is CLOSE to our baseline; patches apply with fuzz tolerance, and any"
warn "hunk that still won't apply will be reported (not silently skipped)."
echo

# ---- 1. fetch a clean source tree ----
if [ -d "$SRC/.git" ]; then
  say "Step 1/5  Reusing existing checkout at $SRC (git clean + reset)…"
  git -C "$SRC" clean -fdx >/dev/null 2>&1 || true
  git -C "$SRC" reset --hard >/dev/null 2>&1 || true
else
  say "Step 1/5  Cloning vanilla Firefox source (large — this is the long download)…"
  mkdir -p "$(dirname "$SRC")"
  git clone --depth 1 "$UPSTREAM" "$SRC" || die "clone failed"
fi
[ -f "$SRC/browser/config/version.txt" ] || die "clone does not look like a Firefox tree"
ok "vanilla source ready: $(cat "$SRC/browser/config/version.txt")"

# ---- 2. tuned mozconfig ----
say "Step 2/5  Installing the tuned mozconfig (clang-21 / sccache / Wayland)…"
if [ -f "$MOZCONFIG_SRC" ]; then cp "$MOZCONFIG_SRC" "$SRC/mozconfig"; ok "mozconfig installed";
else warn "tuned mozconfig not found at $MOZCONFIG_SRC — using tree default"; fi

# ---- 3. apply the Gorilla patch set (fuzz-tolerant) ----
say "Step 3/5  Applying the Gorilla Unleashed patch set…"
"$PATCHSET/apply.sh" --check "$SRC" || warn "some patches don't apply exactly on this clone (expected on a drifted nightly)."
applied=0; fuzzy=0; failed=0; declare -a FAILEDP=()
while IFS= read -r p; do
  if out=$(patch -p1 --forward --batch --fuzz=3 -d "$SRC" < "$p" 2>&1); then
    echo "$out" | grep -q 'with fuzz' && fuzzy=$((fuzzy+1)) || applied=$((applied+1))
  else failed=$((failed+1)); FAILEDP+=("$(basename "$p")"); fi
done < <(find "$PATCHSET" -regextype posix-extended -regex '.*/[0-9]{2}\.[^/]+/.*\.patch' | sort)
# NEW_FILES + profile user.js handled by a full apply.sh pass
"$PATCHSET/apply.sh" "$SRC" >/dev/null 2>&1 || true
ok "patches: ${applied} clean, ${fuzzy} applied-with-fuzz, ${failed} failed"
if [ "$failed" -gt 0 ]; then
  warn "these hunks need manual attention (upstream drifted past them):"
  printf '     - %s\n' "${FAILEDP[@]}"
fi

# ---- 4. build (hardened wrapper — never bare ./mach build) ----
say "Step 4/5  Building (hardened wrapper: unbuffered + telemetry-off)…"
read -p "$(echo -e "${B_C}Start the compile now? ~20-40 min with sccache. [y/N]: ${NC}")" ans || ans=n
if [[ "$ans" =~ ^[Yy]$ ]]; then
  bash "$REPO/scripts/run_build_and_capture.sh" "$SRC" || die "build failed — read the captured log"
  ok "build finished"
  # ---- 5. optional .deb ----
  read -p "$(echo -e "${B_C}Package a .deb now? [y/N]: ${NC}")" deb || deb=n
  if [[ "$deb" =~ ^[Yy]$ ]]; then
    bash "$REPO/scripts/build_deb.sh" "" "$SRC/obj-x86_64-pc-linux-gnu/dist/bin" "$(dirname "$SRC")/release" "$REPO/deb_template" "$SRC/browser/branding/gorilla" && ok "packaged"
  fi
else
  echo -e "\n${B_C}Build later with:${NC}  bash $REPO/scripts/run_build_and_capture.sh \"$SRC\""
fi

echo -e "\n${B_G}Done. Source tree: $SRC${NC}"
