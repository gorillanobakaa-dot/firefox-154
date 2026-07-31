#!/usr/bin/env bash
# =============================================================================
# build_gorilla.sh — Gorilla Firefox 154 Build Launcher
# =============================================================================
# Always use this script instead of calling ./mach build directly.
#
# Fixes applied automatically:
#
#   1. CLAUDECODE env var detection bypass
#      mach detects AI agents via $CLAUDECODE (and $GEMINI_CLI, $CODEX_SANDBOX,
#      $OPENCODE) and silences all output to warnings/errors only. This makes
#      build errors invisible. We strip the var with `env -u` before mach sees it.
#      Source: python/mozbuild/mozbuild/util.py:91 is_running_under_coding_agent()
#
#   2. MOZ_* telemetry env vars rejected by FF154 configure
#      In FF154, MOZ_NORMANDY, MOZ_DATA_REPORTING, MOZ_TELEMETRY_REPORTING, and
#      MOZ_SERVICES_HEALTHREPORT all raise InvalidOptionError if set by environment.
#      Configure only accepts them from "implied" (internal logic), not from shell.
#      Telemetry removal is handled at compile time via #define GLEAN_DISABLED 1
#      and the C++ lobotomy patches in the source tree. No env vars needed.
#
# Usage:
#   ./build_gorilla.sh              — standard build
#   ./build_gorilla.sh --check      — configure-only check (no compilation)
#   ./build_gorilla.sh --log FILE   — write full log to FILE (default: ~/gorilla-build.log)
# =============================================================================

set -euo pipefail

FIREFOX_SRC="/home/gorilla/firefox-main"
LOG_FILE="${HOME}/gorilla-build.log"
CHECK_ONLY=0

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --check)    CHECK_ONLY=1; shift ;;
        --log)      LOG_FILE="$2"; shift 2 ;;
        *)          echo "Unknown argument: $1"; exit 1 ;;
    esac
done

# Colours
CYAN='\033[1;36m'; MAGENTA='\033[1;35m'; GREEN='\033[1;32m'
RED='\033[1;31m'; YELLOW='\033[1;33m'; NC='\033[0m'

echo -e "${MAGENTA}"
echo "  ▄▀▀▄  G O R I L L A   U N L E A S H E D"
echo "  ▀▀▀▀  F i r e f o x   1 5 4   B u i l d e r"
echo -e "${NC}"
echo -e "${CYAN}================================================================${NC}"

# Verify source tree exists
if [[ ! -d "$FIREFOX_SRC" ]]; then
    echo -e "${RED}ERROR: Firefox source not found at $FIREFOX_SRC${NC}"
    exit 1
fi

# Verify mach exists
if [[ ! -f "$FIREFOX_SRC/mach" ]]; then
    echo -e "${RED}ERROR: mach not found in $FIREFOX_SRC${NC}"
    exit 1
fi

# --- CSS correctness gate (Layer 2) ----------------------------------------
# Refuse to build if any theme CSS has an @import/@charset the parser will
# silently drop. This is the defect that broke the theme's input fields for
# weeks (global-shared.css:441). Same single validator the git hook uses — do
# not reimplement. A build is expensive on this hardware; fail before mach, not
# after a two-hour compile ships a dead theme.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CSS_LINT="$SCRIPT_DIR/lint/check_css_import_position.py"
if [[ -f "$CSS_LINT" ]]; then
    echo -e "${CYAN}Checking theme CSS @import positions...${NC}"
    css_files=()
    while IFS= read -r -d '' f; do css_files+=("$f"); done \
        < <(find "$SCRIPT_DIR/FIrefox.154.Look" -name '*.css' -print0 2>/dev/null)
    if [[ ${#css_files[@]} -gt 0 ]] && ! python3 "$CSS_LINT" "${css_files[@]}"; then
        echo -e "${RED}Build refused: fix the CSS @import position above first.${NC}"
        exit 1
    fi
    echo -e "${GREEN}  CSS @import positions OK.${NC}"
fi

echo -e "${CYAN}Source:${NC}  $FIREFOX_SRC"
echo -e "${CYAN}Log:${NC}     $LOG_FILE"
echo ""

# Environment sanity report
echo -e "${YELLOW}Environment fixes applied:${NC}"

UNSET_VARS=(CLAUDECODE GEMINI_CLI CODEX_SANDBOX OPENCODE
            MOZ_NORMANDY MOZ_DATA_REPORTING MOZ_TELEMETRY_REPORTING MOZ_SERVICES_HEALTHREPORT)

for var in "${UNSET_VARS[@]}"; do
    if [[ -n "${!var+x}" ]]; then
        echo "  - Stripping \$$var (would cause configure failure or silent output suppression)"
    fi
done

# Build env -u chain dynamically from UNSET_VARS
ENV_CMD=(env)
for var in "${UNSET_VARS[@]}"; do
    ENV_CMD+=(-u "$var")
done

echo ""

if [[ "$CHECK_ONLY" -eq 1 ]]; then
    echo -e "${CYAN}Running configure check only (no compilation)...${NC}"
    cd "$FIREFOX_SRC"
    "${ENV_CMD[@]}" ./mach configure 2>&1 | tee "$LOG_FILE"
    exit $?
fi

echo -e "${GREEN}Starting build...${NC}"
echo -e "${CYAN}================================================================${NC}"
echo ""

cd "$FIREFOX_SRC"
"${ENV_CMD[@]}" ./mach build 2>&1 | tee "$LOG_FILE"
BUILD_EXIT=${PIPESTATUS[0]}

echo ""
echo -e "${CYAN}================================================================${NC}"
if [[ $BUILD_EXIT -eq 0 ]]; then
    echo -e "${GREEN}BUILD SUCCEEDED${NC}"
    echo ""
    echo "Binary: $FIREFOX_SRC/obj-x86_64-pc-linux-gnu/dist/bin/firefox"
    echo ""
    echo "Next steps:"
    echo "  1. Flush startupCache before testing:"
    echo "     rm -rf $FIREFOX_SRC/obj-x86_64-pc-linux-gnu/tmp/profile-default/startupCache/*"
    echo "  2. Run: MOZ_ENABLE_WAYLAND=1 env -u CLAUDECODE ./mach run"
    echo "  3. Or direct: MOZ_ENABLE_WAYLAND=1 $FIREFOX_SRC/obj-x86_64-pc-linux-gnu/dist/bin/firefox"
    echo "  NOTE: MOZ_ENABLE_WAYLAND=1 required for native Wayland path (cairo-gtk3-wayland built in)."
    echo "        If Wayland fails: GDK_BACKEND=x11 env -u CLAUDECODE ./mach run  (X11 fallback)"
else
    echo -e "${RED}BUILD FAILED (exit code $BUILD_EXIT)${NC}"
    echo "Full log: $LOG_FILE"
    echo ""
    echo "Common causes:"
    echo "  - Configure rejected an env var  (grep 'can not be set by environment' in log)"
    echo "  - C++ compile error              (grep 'error:' in log)"
    echo "  - Missing dependency             (grep 'not found' in log)"
    echo "  - Brace mismatch in patched file (run structural_brace_checker.py)"
fi
echo -e "${CYAN}================================================================${NC}"

exit $BUILD_EXIT
