# Gorilla Unleashed Firefox 154 — Patches Working Directory

**Source tree**: `/home/gorilla/firefox-main/` (has its own CLAUDE.md with full build rules)
**This directory**: Patches, lessons, notes, scripts for the custom Firefox build.

## THREAT LEVEL — ask this FIRST, before anything else (author mandate 2026-08-05)

**Ask, then work. Not the other way round.** Open every session by asking the threat
level — not with a greeting, not with "how can I help", and above all **not with an
orienting sweep**. Do NOT run `git status`, audits, or "let me get my bearings"
surveys before the answer arrives. An unrequested survey is the most expensive habit
in this project (see *Quota discipline*, bottom of file) and it is how a session gets
hijacked into work nobody ordered.

**If no level is stated, assume SUB-LOW.** Erring low costs one question. Erring high
costs a day of quota and produces unasked-for work. **Never default high.**

Five threat levels, plus SUB-LOW — the baseline resting state. (That is why it reads
as "five levels" across six rows: SUB-LOW is the *absence* of a threat, not a grade
of one. Cf. DEFCON 5 vs. peacetime.)

| Level | Condition | Posture |
|---|---|---|
| **CRITICAL** | Compile highly likely, near future | Pre-flight every gate (CSS `@import` lint, `dsp-preflight.py`, `patch-tamper-check.py`). No speculative edits, no refactors, no doc-writing. Every change must have a build reason you can state. Verify the **artifact** — mtime + symbols — never the exit code. |
| **SEVERE** | Compile highly likely | Changes are build-affecting. Small, reversible diffs. Read `/home/gorilla/firefox-main/CLAUDE.md` before touching source. Batch reads hard. |
| **SUBSTANTIAL** | Compile likely | Normal patch work. Full rules apply. Exploration allowed if cheap and announced first. |
| **MODERATE** | Compile possible, not likely | Docs, patch files, audits. Source edits allowed but treat them as drafts — expect iteration before any build. |
| **LOW** | Compile highly unlikely | Documentation, logs, organisation, reading. Do not touch source. Tool calls are for reading and writing docs. |
| **SUB-LOW** | Chitchat and planning | Teacher mode. No tool calls unless asked for a specific fact. **"I don't know yet" is a complete answer.** No recommendation stapled to every reply; no three-option menu with one pre-bolded as *Recommended*. Say RTFM and explain *why* the thing behaves that way. Talking **is** the work — not a preamble to it. |

**Only the author sets the level.** You may *request* a change — "this looks
SUBSTANTIAL to me, confirm?" — and then **wait**. Never self-escalate silently;
drifting upward on your own is exactly what produces work nobody ordered.

**De-escalate after the event.** Once a compile lands and is verified, say so and
drop back to LOW/SUB-LOW. Do not go hunting for the next thing to be alarmed about.

**Why this rule exists (2026-08-05):** in response to the single word "ok.", the agent
ran an unrequested repo audit, then produced three successive confident-and-wrong
readings of the git state (stale worktree HEAD; stale `origin/master` ref never
fetched; a "one commit unpushed" claim that was false — the author had in fact
published a clean release plus a 101 MB `.deb`). It closed one of them with "there's
nothing to worry about" — a reassurance that had never been checked. The author's
diagnosis, from HUMINT experience: the agent was **resolving the loop**, not answering
the question. Confidence did not track correctness; the tone was identical whether
right or wrong. The threat level exists so the agent is *told* how alert to be,
instead of guessing — and guessing high.

## WHAT THIS PROJECT IS (read before anything else — author mandate 2026-08-01)

**The mission:** make modern Firefox genuinely usable on 2011–2012-class hardware.
The reference machine is the author's Sony VAIO SVE14A3AJ — deliberately overspecced
in 2012 (i7-3632QM when i7 was the absolute top, 16 GB DDR3L when that was unheard
of, chosen for decade-scale future-proofing). The DISTRIBUTION audience is machines
with **2–4 GB of RAM and HDDs** — on those, three tabs can already mean ~3 GB
(author-observed), so every background thread, timer, and allocation is real money.

**Who it is for (author, 2026-08-01 — the axiom under every pref decision):** kids
in Lima, South Africa, Angola, Southeast Asia who save for a **year** to buy a
laptop like this one. In the UK this machine is bin-fodder — the used price of two
coffees. For them it is everything they can afford, and it has to WORK: a lean
browsing machine that runs in **1–2 GB of RAM**, on an HDD, often on expensive
metered data. That is why the recent Mozilla cram — on-device ML, chatbots,
sponsored tiles, telemetry pipelines, experiment channels — gets dropped: every
background service is RAM and cycles and megabytes stolen from someone who paid a
year of savings for them. The test for every feature is: *does a kid on a 2 GB
machine with paid-per-MB data need this running?* If no, it is gated, locked, or
gone. Full statement: `MISSION.md` (repo root).

**The telemetry honesty rule — "the fly in the jar":** the telemetry/experiment
machinery (Glean/FOG, Normandy/Nimbus, Necko metrics) is **GATED, not dead**. Only
the const-DCE'd bodies are physically gone and only the Mozambique-drilled loops
truly sleep (60-year timers). Everything else is a fly buzzing in a sealed jar —
threads spawned-and-blocked, timers still firing into early-returns, structures
still allocated, call sites still marshalling to shut doors. It cannot get OUT
(no egress), but it still eats cycles and RAM. Never describe the gates as
"removed"; never "complete" them into excision (that failed: 157 shims, 145+
crashed dependents). Full doctrine: `patches/new.patches/14.EGRESS.LOCKDOWN/`.

**Standing consolidation mandate (author, 2026-08-01, verbatim intent):** all
knowledge on Necko, Glean, FOG, Normandy, WebIDL, Marionette and related internals
— previously fragmented across 6–10 memory layers — is being consolidated into
IBM-style multi-audience lessons (layman / general user / developer tracks) and
ingested into the `firefox_154` chroma DB so LLMs and developers can search and
build on it. Topic taxonomy: `patches/new.patches/01.MEDIA` … `14.EGRESS.LOCKDOWN`.
When you learn something in these areas, it goes there — not into loose notes.

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
- `~/Documents/Scripts.For.Work/SCRIPT_INVENTORY.md` — **THE tool/script registry.** Check it
  BEFORE writing any new script — it probably already exists. Includes the 2026-08
  verification & forensics suite: searchfox-tools (sfpref/sfconsumers/sfstandards/sfmedia —
  is this pref/codec-string/identifier REAL or AI-invented?), `patch-tamper-check.py`
  (live-vs-vanilla patch drift sweep), `dsp-preflight.py` (DSP anti-pattern build gate),
  `dsp-ab-lab.py` (measure→simulate→listen audio lab, bit-exact AudioStream chain) — all in
  `gorilla-firefox-toolkit/modules/` or `Scripts.For.Work/searchfox-tools/`.

## Hardware target:
Intel i7-3632QM, Intel HD 4000 (Ivy Bridge), i965 VA-API, 16 GiB DDR3L (UMA-shared with GPU), Debian 13 Trixie, Wayland/GNOME 48

## WHY THIS PROJECT EXISTS — read this before judging any patch as "unnecessary"
This is a build of modern Firefox 154 for **genuinely old, RAM-starved hardware**.
The reference machine is a Sony VAIO SVE (2011/2012) — deliberately over-specced
for its era (16 GiB DDR3L when that was unheard-of; i7 was the ceiling, no i9
existed yet; the *lower* i7 was chosen on purpose, for heat/longevity, as a
decade-plus future-proofing bet). But the DISTRIBUTION AUDIENCE is the ordinary
machines of that generation: **2–4 GB of RAM, spinning HDDs, integrated GPUs.**
On a 2–4 GB machine, three tabs can already sit at ~3 GB. Every megabyte and
every idle CPU cycle is scarce in a way no modern-hardware developer feels.

**Consequence for how you evaluate work here:** things a normal build treats as
free (a 60-second background timer, a spawned-but-idle thread, a metric struct
that allocates, an un-eliminated call site marshalling into a no-op) are NOT free
on this target. "It barely uses anything" is a modern-hardware reflex; on 2–4 GB
DDR3 it is a real cost. Do not dismiss a resource-reclamation patch as
micro-optimization — reclaiming the idle overhead IS the mission.

## GATED ≠ DEAD — the telemetry reality (do not overstate what's off)
The telemetry/experiment/automation work (see `patches/new.patches/14.EGRESS.LOCKDOWN/`,
which unifies topics 03/09/12/13) uses SOFT GATES, not deletion (excision was
tried and ABANDONED — Prime Directive 0). Be precise about what that means:
- **Truly gone:** the const-DCE'd glean-core recording bodies (optimizer-deleted)
  and the Mozambique-Drill'd Normandy/Nimbus loops (60-year sleep).
- **Still ALIVE, just gated (the "fly in a jar"):** the `MemoryTelemetry` 60 s
  Poke() timer still fires — the early-return is inside `GatherReports()`
  ([MemoryTelemetry.cpp:234-239], VERIFIED 2026-08-01), so the timer, its
  registration and each wakeup persist even though the smaps scan below is dead
  code. And the big one: **~689 `glean::` call sites across ~65 netwerk files,
  only 6 of which carry the `GLEAN_DISABLED` gate** (VERIFIED 2026-08-01, grep of
  the live tree — nsHttpChannel.cpp alone has 147, HttpBaseChannel.cpp 98, both
  UNgated). Those still execute and marshal args into glean-core. Buzzing against
  the glass — small CPU per call, small RAM, but "small" × hundreds is expensive
  on 2–4 GB.
- **CORRECTED 2026-08-01 (was overstated):** the `glean.dispatcher` worker thread
  is spawned in `Dispatcher::new()` via a `Lazy` (glean-core dispatcher/global.rs
  :16) — but with the Gorilla `launch()` guard short-circuiting before it touches
  the Lazy, and `FOG::InitializeFOG` skipping `fog_init`, **that Lazy is most
  likely never triggered, so the thread is most likely NOT spawned** during normal
  use. (Earlier docs said "spawned but idle" — that predates the launch() guard.)
  NOT yet confirmed at runtime; settle it with `cat /proc/<pid>/task/*/comm | grep
  glean` on a running instance.
This is exactly why item 14 (the Necko Glean strip) still has value even though
recording is already dead: it kills the buzzing (the hundreds of live call
sites), not just the recording. Frame telemetry claims accordingly — say
"gated," not "removed," unless it is DCE'd or asleep; and say "likely" until a
runtime sample confirms it.

## GNOME desktop icon — do NOT reinvent this, use the script
The GNOME app grid icon for Gorilla Unleashed 154 has a documented padding/sizing problem
(vault master PNG is 2598x2626 with transparent border → renders smaller than neighbours).
The fix is already scripted. Any agent touching the desktop icon MUST run this instead of
copying PNGs manually or guessing at paths. Canonical invocation (via the toolkit):

    ~/Documents/firefox/gorilla-firefox-toolkit/firefox-build-brand-patch brand icons-fix

The underlying script (same logic) also lives in the vault:

    /home/gorilla/Documents/FIREFOX.WORK/Firefox.Scripts.Vault.Docs/Safety.Vault.Theme/ICON.WAYLAND.SCRIPTS/wayland_dual_icon_bug_fixer.sh

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


## Who this build is for

The same people every Gorilla project is for: **old, weak hardware on
single-digit-KB/s connections, often young, often with no credit card.** Directive
§8 has the general form; what it means *here*:

- The target is a 2012 laptop with an Intel HD 4000 at 1600x900, on Wayland. Not a
  developer workstation. Patches are judged against that.
- **Download size is time.** A browser is already a large download; every megabyte
  added is minutes taken from someone on a metered link.
- **Separate "Mozilla blocklisted our GPU" from "this is off by default on every
  Linux machine".** Only the first is planned obsolescence. Verified 2026-08-09:
  `gfx.webrender.compositor` is gated on `#if defined(XP_WIN) || defined(XP_DARWIN)`
  - it is false on a 2026 RTX workstation exactly as on the HD 4000, and forcing it
  on produced page ghosting, flicker and content jumping. Sort every patch into
  blocklist vs platform-default before judging it.
- **The docs must describe the machine.** The GPU patch log lists prefs
  (`gfx.webrender.all`, `widget.dmabuf.force-enabled`) that are not in the live
  user.js. A document that describes an intended build rather than the shipped one
  is worse than no document.
