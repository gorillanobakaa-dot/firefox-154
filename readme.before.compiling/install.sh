#!/usr/bin/env bash
# install.sh — idempotent LSP setup for Firefox 154 work on Debian 13.
#
# Safe to run repeatedly. Every step is check-then-act: if the tool is present
# at a working version, we say so and move on. Nothing is uninstalled or
# downgraded. sudo is only asked for when apt actually needs to change
# something; npm installs are user-scoped and need no sudo.
#
# Read readme.before.compiling.md for what each tool does.

set -euo pipefail

CYAN=$'\033[36m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; RED=$'\033[31m'; RESET=$'\033[0m'
say()  { printf '%s[install]%s %s\n' "$CYAN" "$RESET" "$*"; }
ok()   { printf '  %sok%s   %s\n' "$GREEN" "$RESET" "$*"; }
warn() { printf '  %swarn%s %s\n' "$YELLOW" "$RESET" "$*"; }
fail() { printf '  %sfail%s %s\n' "$RED" "$RESET" "$*"; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

apt_install() {
  local pkg="$1" bin="${2:-$1}"
  if have "$bin"; then
    ok "$bin already at $(command -v "$bin")"
  else
    say "installing $pkg (apt)…"
    sudo apt-get install -y "$pkg"
    have "$bin" || fail "$pkg installed but '$bin' still not in PATH"
    ok "$bin now at $(command -v "$bin")"
  fi
}

# ─── 1. clangd ────────────────────────────────────────────────────────────
say '1/4  clangd (C/C++ language server — for the AI to see errors live)'
apt_install clangd clangd

# ─── 2. rust-analyzer ─────────────────────────────────────────────────────
say '2/4  rust-analyzer (for Stylo, WebRender and other Rust in Firefox)'
if have rust-analyzer; then
  ok "rust-analyzer at $(command -v rust-analyzer)"
elif have rustup; then
  say 'rustup found — adding rust-analyzer via rustup component'
  rustup component add rust-analyzer
else
  apt_install rust-analyzer rust-analyzer
fi

# ─── 3. CSS / HTML / JSON servers (the pain point — three servers, one pkg) ──
say '3/4  vscode-langservers-extracted (CSS + HTML + JSON — the CSS pain point)'
if have vscode-css-language-server; then
  ok "vscode-css-language-server at $(command -v vscode-css-language-server)"
else
  have npm || fail 'npm not on PATH. This box has node via nvm; open a shell where nvm is loaded, or `sudo apt install nodejs npm`.'
  say 'installing vscode-langservers-extracted (npm, user-scoped)…'
  # -g installs into the currently-active node prefix — with nvm, that lands in
  # ~/.nvm/versions/node/<v>/bin so no sudo needed.
  npm install -g vscode-langservers-extracted
  have vscode-css-language-server || fail 'npm reported success but vscode-css-language-server not on PATH.
        Try: which npm  ->  its prefix should be in your PATH.'
  ok "vscode-css-language-server now at $(command -v vscode-css-language-server)"
fi

# ─── 4. print the config snippet + follow-up steps ────────────────────────
say '4/4  writing config-snippet.json…'
snippet="$(dirname "$0")/config-snippet.json"
cat >"$snippet" <<'JSON'
{
  "lsp": {
    "cpp":  { "command": "clangd",                       "args": ["--background-index"] },
    "c":    { "command": "clangd",                       "args": ["--background-index"] },
    "rust": { "command": "rust-analyzer",                "args": [] },
    "css":  { "command": "vscode-css-language-server",   "args": ["--stdio"] },
    "html": { "command": "vscode-html-language-server",  "args": ["--stdio"] },
    "json": { "command": "vscode-json-language-server",  "args": ["--stdio"] }
  }
}
JSON

cat <<EOF

────────────────────────────────────────────────────────────────
${GREEN}Install complete.${RESET}

Next steps:

  1) Merge the block in $snippet into
     ~/.config/gorilla-opencode/config.json

  2) One-time per meaningful build config change, generate the
     clangd compilation database:

       cd ~/firefox-main
       ./mach build-backend -b clangd

     Requires a completed \`./mach build\` first. Takes 1-2 min.

  3) Restart gorilla-opencode. Edit a .cpp or .css file inside
     ~/firefox-main. The tool response should now include
     <file_diagnostics>…</file_diagnostics> from the appropriate
     server. If it doesn't, run ./verify.sh to see what's wrong.

Optional (see the Fluent section of readme.before.compiling.md):
     cargo install fluent-lsp    # for the 194 .ftl files
   Not installed here because it is community-maintained; try
   manually first if you want it.
────────────────────────────────────────────────────────────────
EOF
