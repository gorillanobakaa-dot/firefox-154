# Gorilla Unleashed Firefox 154 — Patches Working Directory

**Source tree**: `/home/gorilla/firefox-main/` (has its own CLAUDE.md with full build rules)
**This directory**: Patches, lessons, notes, scripts for the custom Firefox build.

## CRITICAL: Before modifying ANY source code, read the source tree CLAUDE.md first:
- `/home/gorilla/firefox-main/CLAUDE.md` — ALL mandatory rules for media, GFX, CSS, locale, build

## Key files in this directory:
- `patches/GOLDEN_RULES.md` — One-line rule table, every rule proven by a real bug
- `patches/Mega.Lessons/MEDIA_CODEC_LESSONS.md` — 9 media bugs (A-I), 6-layer codec gate
- `patches/FIrefox.154.Look/notes/UI_Tweaks_Master_Collection/CSS_UI_TWEAKS_MEGA_LESSON.md` — CSS/theme/branding lessons
- `patches/PATCH.READINESS.txt` — Status tracker for all 11 patch groups (292 modified files)
- `patches/Compile.errors.fixed.so.far..txt` — Build error history (ERROR 1-9)
- `doc-audit/` — Unified doc + audit toolkit (offline pre-check, dual-track docs, IBM audit).
  Read `doc-audit/AGENT.md` before writing any topic documentation.

## Hardware target:
Intel i7-3632QM, Intel HD 4000 (Ivy Bridge), i965 VA-API, 16 GiB DDR3L (UMA-shared with GPU), Debian 13 Trixie, Wayland/GNOME 48

## GNOME desktop icon — do NOT reinvent this, use the script
The GNOME app grid icon for Gorilla Unleashed 154 has a documented padding/sizing problem
(vault master PNG is 2598x2626 with transparent border → renders smaller than neighbours).
The fix is already scripted. Any agent touching the desktop icon MUST run this instead of
copying PNGs manually or guessing at paths. Canonical invocation (via the toolkit):

    ~/Documents/firefox/gorilla-firefox-toolkit/firefox-build-brand-patch brand icons-fix

The underlying script (same logic) also lives in the vault:

    /home/gorilla/Documents/firefox/Firefox.Scripts.Vault.Docs.backup/Safety.Vault.Scripts/Firefox.Icon.For.Dash.and.APP.GRID/wayland_dual_icon_bug_fixer.sh

What the script does: reads the vault master PNG, trims transparent padding with ImageMagick,
Lanczos-resamples to 1024x1024 square, deploys to all hicolor sizes, regenerates the
.desktop entry with correct Exec/StartupWMClass for the 154 build, flushes GNOME caches.
Canonical source icon: `.../deb_template/usr/share/icons/hicolor/1024x1024/apps/gorilla-unleashed.png`

## Top 3 rules that agents keep forgetting:
1. GPU process MUST stay ForceDisabled on Wayland → black window otherwise (ERROR 9)
2. `UserForceEnable()` outranks gfxInfo blocklist; `UserEnable()` does NOT
3. VA-API runs in RDD process, NOT GPU process — they are completely separate

## CSS `@import` position is MECHANICALLY ENFORCED (not advisory)
An `@import`/`@charset` placed after any style rule is silently dropped by the CSS
parser — no error, the line just does nothing. This killed the theme for every
toolkit input field for weeks (the master-redirect import sat at the END of
`global-shared.css`). You do not need to remember this: `patches/lint/check_css_import_position.py`
gates the **git pre-commit hook**, **`build_gorilla.sh`**, and **`dual-track precheck`** —
a late `@import` refuses the commit and the build, for every agent (Claude, Gemini,
Kiro, Bob, agy), because the gate sits below the instruction-file layer. Append style
RULES to the bottom; PREPEND `@import` into the leading import block. See GOLDEN_RULES
C9/C10 and brain concept `CSS_Import_Position_Dead_Theme_And_The_Gate_Below_The_Agent_Layer`.

## Naming discipline (learned the hard way — 17,000+ occurrences removed):
This rule is about NAMES, for two reasons: terminal ergonomics (a "gorilla" prefix
repeated on every sibling kills tab-completion) and keeping noise out of context.
- DO NOT name files, folders, constants, or generated identifiers "gorilla". Name things
  by what they do (`doc-audit`, not `gorilla-doc-audit`; `cleanup_patches.py`, not
  `gorilla_cleanup.py`).
- Legitimate uses of the word: the `/home/gorilla` username path, the project's title
  "Gorilla Unleashed Firefox 154" used sparingly in doc headers, and code identifiers
  that already exist in the tree (`GORILLA_TELEMETRY_OFF`, `kGorillaUploadChunkSize`).
- Cleanup tooling if this NAMING rule slips: `Second.Brain/Firefox.154.Documentation/Doc.Tooling.Scripts/Sycophancy.Scripts/`.

## In-source provenance markers are REQUIRED (do NOT strip them):
This is the opposite of the naming rule and must not be confused with it. Comments like
`// GORILLA OVERRIDE: <what changed and why>` on our edits to Mozilla source are a
deliberate transparency/accountability convention — not vanity. They let a developer AND
a layperson audit exactly what we changed, why, and who did it (radical transparency, not
obfuscation). This is mandated by the project's Open Source Philosophy — see
`00.Open.Source.Philosophy (2).md`, Part Seven: "every patch carries a comment explaining
not just what changed but why." KEEP these markers. Never neutralize them as "de-vanity";
the naming ban above applies to NAMES only, never to these in-source comments.

## Tone
No flattery, no unearned superlatives, no "" without evidence. State results,
not sales copy. If something wasn't measured, say "not measured" — never estimate silently.

## Unpacked dev build — never package, iterate live (saves hours per change)
The build intentionally skips `./mach package` (no `--enable-release`) so there
is NO omni.ja: `dist/bin` keeps chrome/localization/components/modules as raw
dirs/symlinks. Front-end changes (CSS/FTL/properties/JS) = `env -u CLAUDECODE
./mach build faster` (~5 s) + startupCache flush + relaunch — or overwrite
directly under `dist/bin/` for an instant live test (then mirror back to source
or the next build clobbers it). C++-only = `./mach build binaries`. Full
compile is ONLY for configure/build-system changes. Canonical lesson:
`Firefox_OMNI_JA_Developer_Build_Workflow` (07.TOOLKIT, chroma DB + XML).

## Check the lessons BEFORE debugging (not a joke)
Every way this build can break has already broken and is documented with its
fix — lessons DB (`chroma_fx154`), 345 lesson XMLs, `Mega.Lessons/`, and the
append-only `patches/FIrefox.154.Look/notes/THEME_FIX_LOG_2026-07-31.md`.
Sweep with `SECOND.BRAIN/Firefox.Scripts.Used.For.Fixes/memory_tier_extract.py`.
Proven same-day: the FTL sed damage, the Wayland-GPU trap, and this very
workflow were all pre-documented. One caveat: identifiers inside lessons may be
scrub-corrupted — grep the tree before using them (mega lesson §F1).

## Quota / efficiency discipline (quota is scarce — a whole day can be 2 prompts)
1. BATCH massive reads. When surveying folders, read/grep everything in ONE tool
   call (loops, `find`, multi-path `cat`/`grep`), never one file per call. The same
   goes for generating many similar outputs — batch the shell work.
2. NEVER re-read a file the harness already tracks (anything you just read, wrote,
   or edited). Edit/Write already error if state is stale; re-reading to "verify" a
   change that succeeded is wasted quota. Trust the tool result.
3. Prefer many independent tool calls in a SINGLE message (parallel) over serial
   round-trips. Plan the whole batch, fire it once.
The cost of this project is the model's token/quota use, NOT the scripts (which run
locally for free). Treat every tool call as expensive.
