#!/usr/bin/env bash
# =============================================================================
# run_build_and_capture.sh
# Part of the gorilla-unleashed / firefox-main build toolchain
#
# PURPOSE: Run ./mach build, capture all output, and generate a structured
#          summary report. Designed to be run overnight or unattended.
#
# ANALOGY: Like hiring a scribe to watch a long cooking process. They record
#          everything that happens, then when you wake up they hand you a clean
#          summary instead of thousands of lines of kitchen noise.
#
# USAGE:
#   bash run_build_and_capture.sh
#   bash run_build_and_capture.sh /custom/path/to/firefox-main
# =============================================================================

set -uo pipefail

FIREFOX_DIR="${1:-$HOME/firefox-src}"
LOG_DIR="${2:-$FIREFOX_DIR/build_logs}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/build_${TIMESTAMP}.log"
SUMMARY_FILE="$LOG_DIR/summary_${TIMESTAMP}.txt"
FIXES_MD="$LOG_DIR/fixes.applied.md"

mkdir -p "$LOG_DIR"

echo "=================================================="
echo " Firefox gorilla-unleashed Build Runner"
echo " Started: $(date)"
echo " Firefox dir: $FIREFOX_DIR"
echo " Log: $LOG_FILE"
echo "=================================================="

if [[ ! -d "$FIREFOX_DIR" ]]; then
    echo "ERROR: Firefox source directory not found: $FIREFOX_DIR"
    exit 1
fi

cd "$FIREFOX_DIR"

# Run the build, capturing everything
echo "Starting build... (this takes 5-60 minutes depending on what changed)"
START_TIME=$SECONDS

# GORILLA 2026-08-02: unset coding-agent env vars so mach does NOT limit output to
# warnings/errors (mozbuild/util.py is_running_under_coding_agent checks CLAUDECODE/
# CODEX_SANDBOX/GEMINI_CLI/OPENCODE). PIPESTATUS[0] captures mach's exit, not tee's.
# GORILLA 2026-08-04: DISABLE_TELEMETRY=1 is mach's own kill switch
# (python/mach/mach/telemetry.py:85). Without it mach can deadlock in its
# glean.dispatcher thread at startup: 0 CPU, 0 output, build never begins.
# GORILLA 2026-08-04: PYTHONUNBUFFERED=1 — mach can deadlock on EXIT (glean dispatcher
# thread never shuts down => Thread.join() blocks). Buffered output then never flushes and
# a hard config error looks identical to a silent hang. Unbuffered = errors visible instantly.
PYTHONUNBUFFERED=1 DISABLE_TELEMETRY=1 env -u CLAUDECODE -u CODEX_SANDBOX -u GEMINI_CLI -u OPENCODE ./mach build 2>&1 | tee "$LOG_FILE"
BUILD_EXIT=${PIPESTATUS[0]}

ELAPSED=$((SECONDS - START_TIME))
ELAPSED_HUMAN="${ELAPSED}s"
if [[ $ELAPSED -gt 60 ]]; then
    ELAPSED_HUMAN="$((ELAPSED / 60))m $((ELAPSED % 60))s"
fi

# Generate summary
{
    echo "=================================================="
    echo " BUILD SUMMARY"
    echo " Date: $(date)"
    echo " Duration: $ELAPSED_HUMAN"
    echo " Exit code: $BUILD_EXIT"
    echo "=================================================="
    echo ""
    
    if [[ $BUILD_EXIT -eq 0 ]]; then
        echo "  🎉 BUILD SUCCESSFUL"
    else
        echo "  ❌ BUILD FAILED"
    fi
    echo ""
    
    ERROR_COUNT=$(grep -c "^[[:space:]]*[0-9.:]* E " "$LOG_FILE" 2>/dev/null || echo 0)
    WARN_COUNT=$(grep -c "^[[:space:]]*[0-9.:]* W " "$LOG_FILE" 2>/dev/null || echo 0)
    echo "  Errors  : $ERROR_COUNT"
    echo "  Warnings: $WARN_COUNT"
    echo ""
    
    if [[ $ERROR_COUNT -gt 0 ]]; then
        echo "ERRORS:"
        grep "^[[:space:]]*[0-9.:]* E " "$LOG_FILE" | \
            sed 's|^.*E /home/[^/]*/firefox-main/||' | \
            sort -u | head -30
    fi
    
} | tee "$SUMMARY_FILE"

# Update the latest log symlink
ln -sf "$LOG_FILE" "$LOG_DIR/latest_build.log"
ln -sf "$SUMMARY_FILE" "$LOG_DIR/latest_summary.txt"

echo ""
echo "Full log saved to: $LOG_FILE"
echo "Summary saved to: $SUMMARY_FILE"

exit $BUILD_EXIT
