#!/usr/bin/env bash
# verify.sh — read-only sanity check for the Firefox LSP setup. Nothing here
# installs or modifies anything. Reports what is live, what version, and
# whether the LSP config in gorilla-opencode picks up clangd and friends.

set -u
CYAN=$'\033[36m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; RED=$'\033[31m'; RESET=$'\033[0m'

pass=0 warn=0 fail=0
check() {
  local label="$1" cmd="$2" note="${3:-}"
  if eval "$cmd" >/dev/null 2>&1; then
    printf '  %sok  %s%s\n' "$GREEN" "$RESET" "$label"; pass=$((pass+1))
  else
    printf '  %sMISS%s %s' "$RED" "$RESET" "$label"
    [ -n "$note" ] && printf '   — %s' "$note"
    printf '\n'; fail=$((fail+1))
  fi
}
warn_row() { printf '  %swarn%s %s\n' "$YELLOW" "$RESET" "$1"; warn=$((warn+1)); }

echo "${CYAN}== TOOL PRESENCE ==${RESET}"
check "clangd on PATH"                     "command -v clangd"                     "install with: sudo apt install clangd"
check "rust-analyzer on PATH"              "command -v rust-analyzer"              "rustup component add rust-analyzer, or apt install rust-analyzer"
check "vscode-css-language-server on PATH" "command -v vscode-css-language-server" "npm install -g vscode-langservers-extracted"
check "vscode-html-language-server on PATH" "command -v vscode-html-language-server" "same npm package as css"
check "vscode-json-language-server on PATH" "command -v vscode-json-language-server" "same npm package as css"

echo
echo "${CYAN}== VERSIONS ==${RESET}"
for t in clangd rust-analyzer vscode-css-language-server; do
  if command -v "$t" >/dev/null; then
    # css server prints nothing on --version; be tolerant
    v="$("$t" --version 2>&1 | head -1 || echo '?')"
    printf '  %-32s %s\n' "$t" "${v:-(no version output — normal for vscode-* servers)}"
  fi
done

echo
echo "${CYAN}== FIREFOX TREE ==${RESET}"
: "${FIREFOX_SRC:=$HOME/firefox-main}"
if [ -f "$FIREFOX_SRC/mach" ]; then
  printf '  %sok%s   Firefox source at %s\n' "$GREEN" "$RESET" "$FIREFOX_SRC"
  if [ -f "$FIREFOX_SRC/compile_commands.json" ]; then
    lines=$(wc -l <"$FIREFOX_SRC/compile_commands.json")
    age=$(( ( $(date +%s) - $(stat -c %Y "$FIREFOX_SRC/compile_commands.json") ) / 86400 ))
    printf '  %sok%s   compile_commands.json present (%s lines, %d days old)\n' \
           "$GREEN" "$RESET" "$lines" "$age"
    [ "$age" -gt 30 ] && warn_row "compile_commands.json is >30 days old — regenerate after next build"
  else
    warn_row "no compile_commands.json in $FIREFOX_SRC — clangd will not understand C++ in the tree"
    printf '         %sto fix: cd \$FIREFOX_SRC && ./mach build-backend -b clangd%s\n' "$YELLOW" "$RESET"
  fi
else
  warn_row "no mach at $FIREFOX_SRC — set FIREFOX_SRC or ignore if you're not on this box"
fi

echo
echo "${CYAN}== gorilla-opencode LSP CONFIG ==${RESET}"
cfg="$HOME/.config/gorilla-opencode/config.json"
if [ -f "$cfg" ]; then
  for k in clangd rust-analyzer vscode-css-language-server; do
    if grep -q "\"$k\"" "$cfg"; then
      printf '  %sok%s   %s registered in %s\n' "$GREEN" "$RESET" "$k" "$cfg"
    else
      warn_row "$k not registered in $cfg"
    fi
  done
  if grep -q "clangd\|css-language-server\|rust-analyzer" "$cfg"; then :; else
    printf '         paste the block from %sconfig-snippet.json%s (see this folder)\n' "$YELLOW" "$RESET"
  fi
else
  warn_row "no gorilla-opencode config.json — run gorilla-opencode once to create it"
fi

echo
printf "${CYAN}== SUMMARY ==${RESET}  %sok%s=%d  %swarn%s=%d  %sfail%s=%d\n" \
  "$GREEN" "$RESET" "$pass" \
  "$YELLOW" "$RESET" "$warn" \
  "$RED" "$RESET" "$fail"
[ "$fail" -eq 0 ] || exit 2
[ "$warn" -eq 0 ] || exit 1
