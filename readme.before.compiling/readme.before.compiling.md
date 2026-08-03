# readme.before.compiling — Firefox 154

*Written 2026-07-27 for Debian 13 (trixie), Firefox source tree at
`/home/gorilla/firefox-main/`, patches at `../patches/new.patches/`.
Read this once. Run `install.sh` once. Then re-run `verify.sh` any time
you doubt anything.*

The goal is simple: **the coding agent should catch mistakes in Firefox
source *while it is editing*, not twenty minutes into a `mach build` and not
after you notice the UI is broken.**

The evidence this matters: **three of the last builds broke on CSS the AI
edited but did not verify.** Missing closing braces and typoed properties
belong in the class of failures a language server catches before the file is
saved. Live diagnostics-in-the-tool-response fixes this — the agent sees the
error on the same turn it made the edit and corrects it, instead of you
finding out after `./mach build`.

## What your patches actually touch

Counted 2026-07-27 across every `.patch` in `../patches/new.patches/`:

| Extension | Files | What it is |
|---|---:|---|
| `.ftl` | 194 | Mozilla Fluent (translation / UI strings) |
| `.properties` | 42 | Older-style translation files |
| `.cpp` | 40 | Firefox core C++ |
| `.mjs` | 17 | JavaScript modules (chrome / frontend) |
| `.rs` | 5 | Rust (Stylo, WebRender bits) |
| `.jsx`, `.js` | 6 | JavaScript, React-flavoured or plain |
| `.h` | 3 | C++ headers |
| `.css` | 2 | Stylesheets |
| `.build` | 2 | `moz.build` (Python-syntax) |

Six real languages: **C++, Rust, JavaScript, Fluent, CSS**, plus small
Python-esque `moz.build` files. Servers below are chosen to cover the
languages that broke your builds; not every extension gets an LSP.

---

## What's installed and what needs installing

Verified 2026-07-27:

| Tool | For | Status |
|---|---|---|
| `clangd` 19.1.7 | C++ (40 .cpp + 3 .h) | ✅ already installed |
| `rust-analyzer` 1.95 | Rust (5 .rs) | ✅ already installed via rustup |
| `node` 24.15 + `npm` | required to install the CSS server | ✅ already installed via nvm |
| `vscode-css-language-server` | CSS (was the pain point) | ❌ **installs via npm** |
| `vscode-html-language-server` | comes in the same npm package as CSS | ❌ installs alongside CSS |
| `vscode-json-language-server` | for `.json` in the tree | ❌ installs alongside CSS |
| A Fluent (`.ftl`) LSP | 194 files, biggest volume | 🟡 **deliberately not automated** — see §Fluent |

The three `vscode-*-language-server` binaries all come from the single npm
package `vscode-langservers-extracted`. One install, three servers. That is
what `install.sh` adds; nothing else needs installing today.

## Deliberately not installed

- **`stylelint-lsp`** — stylistic linter, more opinionated, more setup.
  Overkill until the CSS server proves insufficient.
- **`typescript-language-server`** — would cover the 23 JS/MJS/JSX files, but
  Firefox chrome JS uses `Cu.import`, `ChromeUtils`, System dictionaries etc.
  that off-the-shelf TS servers don't understand. Signal-to-noise low today;
  install only if JS bugs start hurting the way CSS did.
- **`pylsp` / any Python LSP** — the 2 `.build` files are essentially Python
  but too small to justify a whole server for.

## Fluent (`.ftl`) — the honest position

**194 files. Biggest volume in your patch set. Not a solved problem for a
Debian-native setup.**

Options that exist:

- **`fluent-lsp`** (community, Rust) — active but small user base;
  no Debian package; installs via `cargo install fluent-lsp`. Works, but I'd
  not recommend adding it to the automated `install.sh` without you having a
  chance to try it manually first.
- **Mozilla's `pontoon` tooling** — server-side; not a local LSP.
- **Nothing** — Fluent syntax is simple enough that malformed `.ftl` files
  usually fail loudly at build time; the class of bug that hides in `.ftl` is
  smaller than in CSS.

`install.sh` **does not** install a Fluent LSP. The bottom of this file has a
short section on what to try if you want to experiment. My honest suggestion:
land the CSS + C++ + Rust setup first, use it for a week, and only come back
to Fluent if you notice the AI actually producing bad `.ftl` you have to fix.

---

## The three-plus-one commands that matter

### 1. Generate `compile_commands.json` (once per meaningful build config)

`clangd` needs to know what flags each C++ file is compiled with. Firefox
generates this file with `mach`:

```bash
cd ~/firefox-main
./mach build-backend -b clangd
```

Takes 1-2 minutes. Produces `compile_commands.json` at the tree root and
per-object directory. clangd auto-detects it.

Re-run any time you change `mozconfig` or add/remove build features.

### 2. Sync rust-analyzer with the Rust workspace (rare)

`rust-analyzer` reads `Cargo.toml` files under `firefox-main` and figures
itself out. If it seems confused after a large `mach` update:

```bash
cd ~/firefox-main
./mach cargo update    # if the Rust deps changed
```

Usually you touch nothing here.

### 3. Restart gorilla-opencode after adding the LSP config

Once the config block below is in `~/.config/gorilla-opencode/config.json`,
you need to restart the app once. Every subsequent edit to a covered file
gets diagnostics back in the tool response.

### 4. Add the LSP config to gorilla-opencode

Merge this into `~/.config/gorilla-opencode/config.json` (the exact snippet is
in `config-snippet.json` in this folder — copy-paste, don't retype):

```json
"lsp": {
  "cpp":  { "command": "clangd",                        "args": ["--background-index"] },
  "c":    { "command": "clangd",                        "args": ["--background-index"] },
  "rust": { "command": "rust-analyzer",                 "args": [] },
  "css":  { "command": "vscode-css-language-server",    "args": ["--stdio"] },
  "html": { "command": "vscode-html-language-server",   "args": ["--stdio"] },
  "json": { "command": "vscode-json-language-server",   "args": ["--stdio"] }
}
```

---

## Firefox-specific gotchas

Some real, some learned the hard way, some from your own notes:

1. **`-moz-*` prefixed CSS.** The CSS server will complain about
   `-moz-user-select` and friends as "unknown property". That's noise, not
   error. The **agent** may or may not repeat those warnings to you; either
   way, they don't fail your build. Two ways to silence:
   - Live with it (informational, not blocking)
   - Configure the server to accept the `-moz-` prefix (server-specific
     setting; not scripted here because it adds complexity for marginal gain)

2. **Chrome CSS lives in `.xhtml`, `.html`, and inline `.mjs` template
   literals**, not just `.css`. The CSS server only helps with the standalone
   `.css` files. The template-literal CSS the agent produces will still slip
   through. If you notice this class of bug repeating, tell me and we'll add
   a stylelint plugin that reaches into template literals.

3. **`.jsm` is dead in Firefox 154.** If any patch still emits `.jsm`, the
   patch is out of date — Firefox now uses `.mjs` (ES modules) throughout.
   No LSP needed to catch this, but worth knowing.

4. **`mach clang-tidy` and `mach clang-format`** are separate from clangd but
   share the same compilation database. Once `./mach build-backend -b clangd`
   has run, both tools work. Handy for one-off checks; not part of this LSP
   setup.

5. **Firefox tree is at `~/firefox-main/`, not under this docs directory.**
   The scripts in this folder default `FIREFOX_SRC=~/firefox-main` and can be
   overridden via env var.

6. **First `./mach build-backend -b clangd` can take a while** — it needs a
   completed build to work off. Do a full build first.

---

## What to run when

| When | Command |
|---|---|
| Fresh install of Debian, brand-new machine | `bash install.sh` — installs anything missing, prints the config snippet |
| Right after a fresh Firefox build config change | `cd ~/firefox-main && ./mach build-backend -b clangd` — refresh the LSP index |
| Doubting whether anything is set up correctly | `bash verify.sh` — tells you what's live and what's not |
| Curious about Fluent | see §Fluent above, then decide whether to try `cargo install fluent-lsp` manually |

---

## Files in this folder

- `readme.before.compiling.md` — this document
- `install.sh` — idempotent installer for every LSP the automated flow covers
- `verify.sh` — reports what's installed, what version, what config
- `config-snippet.json` — the LSP block to merge into gorilla-opencode config

Nothing here modifies your Firefox tree, your `mozconfig`, your PATH, or your
`~/.bashrc`. All state stays under `~/.config/gorilla-opencode/` and the
compile-commands file (which lives in the Firefox tree, not here).
