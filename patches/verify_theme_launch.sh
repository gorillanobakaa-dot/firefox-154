#!/usr/bin/env bash
# =============================================================================
# verify_theme_launch.sh — launch the freshly built Firefox 154 with a
# THROWAWAY profile for the 2026-07-31 theme-fix visual check.
#
# What the human checker must confirm (agents cannot see the GUI):
#   1. Text inputs render themed — BLACK (#000000) background, CYAN (#00FFFF)
#      text — NOT the pale OS default:
#        - the urlbar
#        - the find bar (Ctrl+F)
#        - the about:preferences search box
#   2. Urlbar results dropdown separators are SOFT, not harsh full-colour lines.
#
# startupCache is flushed first: CSS changes NEVER appear without it.
# =============================================================================
set -euo pipefail

BIN=/home/gorilla/firefox-main/obj-x86_64-pc-linux-gnu/dist/bin/firefox
[[ -x $BIN ]] || { echo "ERROR: built binary not found at $BIN — build not finished?"; exit 1; }

# Flush ALL startupCache instances (brain lesson: stale cache hides CSS changes)
rm -rf ~/.cache/mozilla/firefox/*/startupCache/ 2>/dev/null || true

PROFILE=$(mktemp -d /tmp/ff154-theme-check-XXXXXX)
trap 'rm -rf "$PROFILE"' EXIT
echo "Throwaway profile: $PROFILE"
echo "Launching. Check: urlbar / Ctrl+F find bar / about:preferences search box"
echo "  Expect: #000000 background, #00FFFF text; soft dropdown separators."

env -u CLAUDECODE MOZ_ENABLE_WAYLAND=1 "$BIN" -profile "$PROFILE" -no-remote about:preferences
