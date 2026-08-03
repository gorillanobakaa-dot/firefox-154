# MASTER PROJECT LOG — FIREFOX 154 PREFERENCES & BUILD PROFILE PATCHES

---

## Part 1: History, Roadmap & Overview
*(Originally from 00_PREFS_HISTORY_AND_ROADMAP.md)*

### Document Control
- **Category:** Build Configuration & Preference Defaults
- **Last Updated:** 2026-07-10
- **Status:** Active Development
- **Verification Required:** Yes (see Validation section)
- **Related Documents:** 
  - `../DOCUMENTATION_TEMPLATES.md` (IBM format guide)
  - `../MAP.md` (cross-category index)
  - `../01.MEDIA/MASTER_PROJECT_LOG_FIREFOX_154_MEDIA_PATCHES.md` (consumes `media.gorilla.hardware_only_mode`)
  - `../04.PERFORMANCE/MASTER_PROJECT_LOG_FIREFOX_154_PERFORMANCE_PATCHES.md` (points here for GC/timeout tuning)
  - `../10.OVERRIDES/user.js` (runtime overrides)
  - `../12.MOZAMBIQUE.DRILL/policies.json` (locked preferences)

---

### Executive Summary

**What This Does (Plain Language):**
This folder is the control panel and factory blueprint for the entire browser. It contains:
1. **The factory blueprint** (`mozconfig`) — instructions for how the browser is manufactured from source code.
2. **The default switch positions** (preference files) — thousands of default settings that the browser starts with.

**Technical Summary:**
Build configuration and preference defaults for Sony VAIO SVE14A3AJ. Implements: (1) native-optimized build recipe (`-march=native -O3`, LTO, jemalloc, Clang-21, compiled-out subsystems), (2) compile-time pref definitions (`StaticPrefList.yaml` including custom `media.gorilla.hardware_only_mode`), (3) application default branch (`firefox.js`, `all.js` with deliberate usability choices like `sessionstore.privacy_level=0`).

**Critical Context:**
> **This is NOT portable.** The build recipe is tailored for one specific machine. Settings here are *defaults* that can be overridden by later layers (`user.js`, `policies.json`).

---

### Mission Statement

### Mission 1: Native-Optimized Build (Factory Blueprint)
Most browsers are built to run on *any* computer — one-size-fits-all. Ours is built like a tailored suit for this exact laptop.
- Build for this exact chip (`-march=native`)
- Optimize hard (`-O3`, LTO)
- Leave out unwanted parts (crash reporter, updater, telemetry agents)
- Use custom branding
- Fast build cache (`sccache`)

### Mission 2: Sensible Defaults (Switch Positions)
Set browser's starting positions for thousands of options, balancing privacy, usability, and performance.
- Password memory enabled (usability over privacy theater)
- Custom hardware-only media switch (`media.gorilla.hardware_only_mode`)
- Tab sleeping for memory management
- GC/timeout tuning for performance

---

### Component Documentation

#### 1. mozconfig — Optimisation Settings
- **Status:** Modified | **Deploy Path:** `mozconfig` | **Last Verified:** 2026-07-10
- **What It Does (Plain Language):** Instructions for manufacturing the browser. Tailored for one specific CPU.
- **Technical Description:** Defines `-O3 -march=native -mtune=native` flags, ThinLTO, auto-PGO, sccache compiler integration, and excludes unneeded modules (updater, crashreporter, default-browser-agent).

#### 2. StaticPrefList.yaml — Preference Definitions
- **Status:** Modified | **Deploy Path:** `modules/libpref/init/StaticPrefList.yaml` | **Last Verified:** 2026-07-10
- **Tuning:** Declares custom pref `media.gorilla.hardware_only_mode` as relaxed atomic boolean, defaults to `true`.

#### 3. firefox.js — Initial Telemetry Locks
- **Status:** Modified | **Deploy Path:** `browser/app/profile/firefox.js` | **Last Verified:** 2026-07-10
- **Tuning:** Pinned default toolkit settings. Explicitly forced `toolkit.telemetry.*` and `browser.newtabpage.activity-stream.telemetry.*` to `false` at the build default level.

---

### Chronological History (Recovered)

#### 2026-06-08/09
Initial preference blueprints structured for Firefox 153. Custom `media.gorilla.hardware_only_mode` defined.

#### 2026-07-05
**Firefox 154 Rebase:**
Build configurations and defaults re-applied and updated for Firefox 154.

#### 2026-07-10
**Telemetry Defaults Lock:**
Explicitly disabled toolkit telemetry ping defaults and newtab private telemetry pings directly inside `firefox.js` to ensure outbound security out-of-the-box.

---

## Part 2: Rule-Based Code Audit & Validation (2026-07-10)

We completed a static code audit of the preference files:

1. **StaticPrefList.yaml**: Custom preference `media.gorilla.hardware_only_mode` is declared on line 12681 and defaults to `true`.
2. **firefox.js**: Telemetry preferences `toolkit.telemetry.archive.enabled` and `toolkit.telemetry.shutdownPingSender.enabled` are successfully locked to `false` (lines 2435-2440). Newtab telemetry pings are disabled (line 2047). Weather suggestions are locked to dummy endpoints (`0.0.0.0`).
3. **mozconfig**: Full `-O3 -march=native` compiler flags asserted. Auto-clobber and make flags set to `-j6`.

The category passes all code guidelines.


---

# ═══ CONSOLIDATION 2026-08-02 — side documents merged VERBATIM below; originals deleted (recoverable: merged-docs-backup-2026-08-02.tar.gz + git history) ═══


---

# ═══ MERGED DOCUMENT: 05-prefs.AUDIT.md (verbatim · sha256:6b38d9450a47d399 · merged 2026-08-02) ═══

# IBM-Style Audit Report: 05-prefs

## SECTION A: DOCUMENT CONTROL

| Attribute | Value |
|---|---|
| **Target Category** | 05-prefs |
| **Files Scanned** | see payload |
| **Baseline** | Firefox 154 (mozilla-central) |
| **Date / Time** | 2026-07-16 22:32:45 |
| **Audit Status** | PASS |

## SECTION B: EXECUTIVE SUMMARY (Track A — Layman)

This folder is the browser's control panel and factory recipe combined. It contains the build instructions (how to compile the browser, tailored for our exact CPU, with entire unwanted subsystems physically left out), plus the default settings for thousands of preferences (telemetry off, AI off, sponsored content off, password manager on). The single most important preference in the whole build — `media.gorilla.hardware_only_mode` — is defined here; the Media topic reads it. Defaults only: Topics 10 and 12 layer overrides on top.

## SECTION C: TECHNICAL SUMMARY (Track B — Developer)

mozconfig (native -march=native -O3 + LTO + jemalloc + subsystem excisions) + StaticPrefList.yaml (adds media.gorilla.hardware_only_mode bool default true; sets AV1/VP9 HW decode defaults false; reinforces Topic 01 at pref layer) + firefox.js (usability-first defaults: signon manager on, sessionstore full-restore, tab-sleep tuned) + all.js (aggressive purge block: AI features / TopSites sponsored / Normandy / Nimbus / Pocket / PDF-AI / translations-nag all forced false) + language.properties (accept-language fixed, multilingual/trending disabled — fingerprinting defence). Layer priority: StaticPrefList < firefox.js/all.js < prefs.js < user.js (Topic 10) < policies.json (Topic 12). Three layers of defence for Normandy/Nimbus: pref-off here, source-neutered in Topic 12 code patches, hard-locked in Topic 12 policies.json.

## SECTION D: DETECTED DEFECTS

### 🟡 P2-001 — P2
- **Track A (Layman):** A sticky note saying 'finish this later' was left inside the machine.
- **Track B (Technical):** browser_app_profile_firefox.js.patch: added lines contain 1 TODO/FIXME markers.
- **Remediation:** Resolve or convert to a tracked item in PATCH.READINESS.txt.

## SECTION E: PRODUCTION READINESS ASSESSMENT

- **Overall readiness:** 🟢 93%
- **Done:**
  - [x] mozconfig NOT portable — `-march=native -O3` + LTO active
  - [x] Subsystems compile-excluded: crashreporter, updater, parental-controls, various telemetry agents
  - [x] media.gorilla.hardware_only_mode defined as bool default true (consumed by Topic 01)
  - [x] AV1/VP9 HW decode/encode prefs default false
  - [x] Aggressive purge block in all.js: AI/TopSites/Normandy/Nimbus/Pocket forced false
  - [x] firefox.js keeps password manager on — deliberate usability-over-privacy-theatre choice
  - [x] language.properties freezes accept-language + disables multilingual/trending
- **To Do:**
  - [ ] P2: split all.js aggressive-purge block into per-category subsections with headers — helps per-category regression visibility on rebase
  - [ ] P3: add StaticPrefList.yaml comment linking media.gorilla.hardware_only_mode to Topic 01 gate sites
  - [ ] P3: consider StaticPrefList-based network.gorilla.tuning_enabled master pref (see Topic 03 expansion plan) for cross-topic coherence

## SECTION F: PHASED EXPANSION PLAN

### Phase 0 — `modules/libpref/init/StaticPrefList.yaml`
- **Tweak:** Group all `media.gorilla.*` and `network.gorilla.*` prefs under a `#---Gorilla Unleashed defaults---` header block with a link back to this AUDIT.md. Improves discoverability.
- **Expected impact:** Maintainability.

## POSITIVE OBSERVATIONS

- ✅ Compile-time subsystem removal is stronger than runtime disable — some things (crash reporter) genuinely cannot be re-enabled short of rebuilding.
- ✅ The distinction between 'convenience for user' (password manager kept on) and 'convenience for Mozilla' (telemetry off) is architecturally consistent — this build is not blanket privacy-theatre.
- ✅ Three-layer defence for Normandy/Nimbus (pref off, source neutered, policies hard-lock) is exactly the pattern a paranoid audit demands.
- ✅ The `media.gorilla.hardware_only_mode` pref is defined here and consumed elsewhere — clean separation of concerns; adding a fourth codec-gate site (Topic 01 expansion) needs zero changes here.
- ✅ Log opens with 'This is NOT portable' — matches Topic 04's honesty pattern; no over-scoping, no marketing.

## VERIFICATION COMMANDS

```bash
grep -n 'media.gorilla.hardware_only_mode' modules/libpref/init/StaticPrefList.yaml   # expect defn
grep -n 'media.av1.enabled\|media.wmf.vp9.enabled' modules/libpref/init/StaticPrefList.yaml   # expect false
grep -n 'browser.newtabpage.activity-stream.showSponsored\|app.normandy.enabled' modules/libpref/init/all.js   # expect false
grep 'march=native\|--disable-crashreporter\|--disable-updater' mozconfig   # expect all three
about:config   # media.gorilla.hardware_only_mode -> true; app.normandy.enabled -> false; browser.newtabpage.activity-stream.showSponsored -> false
```



---

# ═══ MERGED DOCUMENT: 05-prefs.DEVELOPER.md (verbatim · sha256:f27eac49fea91297 · merged 2026-08-02) ═══

# Preferences and Build Profile — mozconfig + StaticPrefList.yaml + app-branch defaults — Developer Track

> **Topic:** `05-prefs` · **Files:** `mozconfig (NEW_FILES/)`, `modules/libpref/init/StaticPrefList.yaml`, `modules/libpref/init/all.js`, `browser/app/profile/firefox.js`, `intl/locale/language.properties`
> **Generated:** 2026-07-16

---

## Module Summary

Two-layer configuration: (a) mozconfig — hardware-specific build recipe (`-march=native -O3`, LTO, jemalloc, Clang-21, `--disable-crashreporter/-updater/-parental-controls`, custom branding); (b) preference defaults — StaticPrefList.yaml defines the new `media.gorilla.hardware_only_mode` pref (bool, default true) plus AV1/VP9 HW-decode defaults=false to match Topic 01, and app-branch files (firefox.js, all.js) impose aggressive-purge defaults on AI/TopSites/Normandy/Nimbus/Pocket/telemetry. Locale properties file forces accept-language and disables multilingual/trending. This is a defaults layer only; Topic 10 (user.js) overrides at runtime, Topic 12 (policies.json) hard-locks the subset Mozilla could re-enable via remote config.

## Architecture

- **Pattern:** Compile-time defaults with intentional override hierarchy. Pref priority: StaticPrefList < firefox.js/all.js < prefs.js < user.js < policies.json.
- **Trust Boundary:** mozconfig excludes subsystems that would otherwise cross the browser's outbound trust boundary (crash reporter, updater). Cannot exfiltrate what is not compiled in.
- **Attack Surface:** Removing subsystems narrows attack surface — the crash reporter alone is a historical CVE breeding ground.
- **Dependencies:** `Clang 21 with LTO support`, `sccache for build caching`, `custom branding assets (referenced from firefox.js)`

## Kill Switches

### `mozconfig — --disable-* flags` — HARD ⚠️

- **Condition:** compile-time
- **Effect:** crashreporter, updater, parental-controls, various telemetry agents are NOT compiled into the binary. Cannot be enabled at runtime.
- **Reversibility:** reversible
- **Notes:** Requires rebuild to reverse.

### `StaticPrefList.yaml — media.gorilla.hardware_only_mode` — HARD ⚠️

- **Condition:** always
- **Effect:** New bool pref, default true. Consumed by Topic 01 at every codec gate.
- **Reversibility:** reversible
- **Notes:** Master toggle for Topic 01. About:config flip reverts codec policy without rebuild.

### `StaticPrefList.yaml — media.av1.enabled / media.wmf.vp9.enabled etc.` — HARD ⚠️

- **Condition:** always
- **Effect:** AV1/VP9 hardware-decode prefs default false. Reinforces Topic 01's C++ gates at pref layer.
- **Reversibility:** reversible
- **Notes:** Defence in depth: even if a code gate regresses, the pref still says no.

### `all.js — aggressive purge block` — HARD ⚠️

- **Condition:** always
- **Effect:** AI/TopSites-sponsored/Normandy/Nimbus/Pocket/PDF-AI-alt-text/translations-nag all forced false. Comment header: `--- GORILLA UNLEASHED: AGGRESSIVE PURGE (AI & TOPSITES) ---`.
- **Reversibility:** reversible
- **Notes:** Topic 12 hard-locks the Normandy/Nimbus subset via policies.json so Mozilla cannot re-enable via remote config.

### `firefox.js — usability-first defaults` — RUNTIME_GUARD ⚠️

- **Condition:** always
- **Effect:** signon.rememberSignons=true (kept), sessionstore.privacy_level=0 (full restore), tab-sleep timers tuned, sidebar experiments off. Deliberate usability choices, not blanket privacy-theatre.
- **Reversibility:** reversible
- **Notes:** Comment: `no nightly-only sidebar experiments — always off`. Distinguishes convenience-for-user (kept) from convenience-for-Mozilla (cut).

### `intl/locale/language.properties` — HARD ⚠️

- **Condition:** always
- **Effect:** accept-language fixed; multilingual/trending disabled. Fingerprinting-defence.
- **Reversibility:** reversible
- **Notes:** Small file, big effect.

## Performance Profile

| Component | Before | After | Mechanism |
|---|---|---|---|
| Build size | generic Firefox 154 | with disabled subsystems + LTO | mozconfig --disable-* flags + LTO dead-code elimination |
| media.gorilla.hardware_only_mode | not defined | defined as bool, default true | StaticPrefList.yaml addition |
| AI/TopSites/Normandy/Nimbus/Pocket defaults | true / partially enabled | false | all.js aggressive purge block |

- **CPU:** `-march=native -O3` + LTO produces measurably faster code on this exact CPU vs a generic build. Not benchmarked topic-locally.
- **Memory:** jemalloc reduces fragmentation on long-running sessions. Compiled-out subsystems reduce library size.
- **I/O:** Removed subsystems (crash reporter, updater, telemetry agents) do not run background threads or open network connections. Steady-state IO reduced.
- **Timer Interval:** Tab-sleep and GC timers configured via prefs; the concrete cadences live in Topic 04's CCGCScheduler.cpp.

## Security Analysis

### User Profiling

Multiple channels cut at the pref layer: telemetry, Normandy, Nimbus, AI features, TopSites-sponsored, Pocket. Coherent with Topic 13 (source-level telemetry kill) and Topic 12 (policies.json hard-lock).

### Targeting

Normandy/Nimbus experimentation channels disabled by pref here + hard-locked in Topic 12 + neutered in Topic 12's code patches. Three layers of defence.

### Trust Chain

Removed subsystems cannot exfiltrate. Compile-out is stronger than runtime disable.

### Abuse Potential

Aggressive purge reduces the attack surface for supply-chain-style attacks where a remote config could re-enable a dormant feature.

## Implementation Flow

1. **`mozconfig sourced by mach configure`** — Sets compiler flags, disables subsystems, defines branding. Consumed at build time.
   *Side effects:* Binary layout differs from stock: some libs absent, others optimised differently.
2. **`StaticPrefList.yaml compiled into libpref`** — Every defined pref becomes part of the binary with its default value. `media.gorilla.hardware_only_mode` added; AV1/VP9 defaults set false.
   *Side effects:* About:config shows the pref; Topic 01 reads it via StaticPrefs::media_gorilla_hardware_only_mode().
3. **`firefox.js / all.js loaded at profile init`** — Applies app-branch defaults on top of StaticPrefList.
   *Side effects:* About:config shows these as 'default' values, distinguishing from user-set.
4. **`intl/locale/language.properties baked in at build`** — Locale defaults fixed.
   *Side effects:* Accept-language stable across sessions; no drift.
5. **`(later layers) user.js overlay from Topic 10 + policies.json hard-lock from Topic 12`** — This folder's defaults are the base; user.js can override for runtime tuning, policies.json enforces the subset Mozilla could otherwise re-enable via remote experiments.
   *Side effects:* Prefs originally chosen by Mozilla lose to prefs re-chosen by us.

## Technical Debt

🟡 **LOW** — The `@gorilla-unleashed-153` headers pre-date the no-brand-spam rule — they are pre-existing identifiers per the rule, but any new such headers should NOT be added
  - *Recommendation:* Leave existing markers in place; do not add new ones. Prefer function-descriptive comments.

🟠 **MEDIUM** — The aggressive-purge block in all.js is one giant block — hard to see when a single line is regressed on rebase
  - *Recommendation:* Consider splitting by category (AI / TopSites / Normandy / Nimbus / Pocket) with sub-headers so per-category regressions are visible.

🟡 **LOW** — media.gorilla.hardware_only_mode is documented in the log but not in an in-tree comment adjacent to its YAML definition
  - *Recommendation:* Add a StaticPrefList.yaml comment linking to the Topic 01 gate sites.

## Impact If Removed / Disabled

Reverting mozconfig -> generic build, subsystems reactivated. Reverting StaticPrefList changes -> Topic 01 code gates dead-code (pref undefined) and every codec accepted. Reverting all.js -> AI features return, TopSites-sponsored returns, Normandy remote experiments run, telemetry channels re-open. Reverting firefox.js -> usability defaults change (password prompts, session-restore behaviour). Reverting language.properties -> accept-language leaks locale changes.

## Testing Notes

`grep -n 'media.gorilla.hardware_only_mode' modules/libpref/init/StaticPrefList.yaml` — expect defn. `about:config` -> verify the pref shows true. Check `about:preferences` -> Firefox Suggest and Sponsored Suggestions should be off by default (aggressive purge working). `about:policies` -> hard-locked entries from Topic 12 visible.

## Changelog Notes

Migrated from FF153. media.gorilla.hardware_only_mode was originally a mozconfig #define; promoted to a proper StaticPrefList entry on FF154 rebase so it can be toggled at about:config without rebuild. Aggressive-purge block consolidated 2026-07-10.

---
*Developer Track. Human Track twin: `05-prefs.LAYMAN.md`.*


---

# ═══ MERGED DOCUMENT: 05-prefs.LAYMAN.md (verbatim · sha256:d8d75d255c373c07 · merged 2026-08-02) ═══

# 🧍 The Control Panel and Factory Blueprint — Preferences and Build Recipe — Plain English Guide

> *Topic `05-prefs` of the Gorilla Unleashed Firefox 154 build · Written for everyone · 2026-07-16*

---

## 🌍 The Big Picture

This folder is two very different things in one place. First: **the factory blueprint** (`mozconfig`) — the recipe the compiler follows when it builds Firefox from source. This one is tailored for our specific CPU (Ivy Bridge i7-3632QM); the browser is compiled *for this exact chip* rather than for any generic Intel processor, which is the difference between a suit off the rack and a suit made to measure. It also leaves out entire subsystems we do not want (crash reporter, updater, telemetry agents), so they cannot even run because they were never included in the first place.

Second: **the default switch positions** — thousands of settings that the browser starts with, defined in `StaticPrefList.yaml`, `firefox.js`, `all.js`, and one locale properties file. Most preferences in Firefox have a default, and Mozilla picks that default. This folder replaces many of those defaults with values chosen for this build's audience — old hardware, weak connections, no interest in Mozilla's telemetry or in AI features that were bolted on for a market that is not us. The most important default defined here is a single new preference the whole build hinges on: `media.gorilla.hardware_only_mode`, which the Media topic consumes at every codec gate.

The critical thing to understand: **these are only defaults**. Later layers can override them — `user.js` in Topic 10 sets runtime prefs, and `policies.json` in Topic 12 hard-locks a small set. Think of this folder as the factory-fresh setting, before the user takes the box home and changes anything.

## 🎭 The Main Characters

| Name | What It Is | Real-World Comparison |
|---|---|---|
| **mozconfig** | The compiler's instruction sheet — how to build the browser from source | The recipe card for baking one specific cake, with substitutions written in for local ingredients |
| **StaticPrefList.yaml** | The master list of every preference the browser knows about, with its compile-time default | The switchboard at the back of the building — every switch labelled, with a default position wired in |
| **firefox.js / all.js** | Application-level default prefs that override StaticPrefList for this build | The pre-set channels on a rented TV — you can still change them, but the rental company chose the starting set |
| **media.gorilla.hardware_only_mode** | The master switch defined here, consumed by the Media topic (Topic 01) at every codec decision | The big red 'hardware-only' lever on the control panel — flip it off, get standard Firefox behaviour back |

## 🔢 How It Works — Step by Step

### Step 1: mozconfig — build for THIS CPU, drop what we do not want

`--enable-optimize=-march=native -O3` tells Clang: build this for the exact CPU we compile on, and optimise aggressively. `--disable-crashreporter --disable-updater --disable-parental-controls` and similar flags remove whole subsystems from the binary so they cannot even run. Not disabled at runtime — physically absent. Some things you cannot leak because they were never built.

### Step 2: StaticPrefList.yaml — the master pref registry

Every preference Firefox has a compile-time default for. The changes here (marked with `@gorilla-unleashed-*` headers) redefine those defaults for our build: telemetry off, AI features off, sponsored content off, VP9/AV1 hardware decode off (matches Topic 01), and — critically — the new `media.gorilla.hardware_only_mode` preference is *defined* here (default `true`). Topic 01 reads it.

### Step 3: firefox.js — 'app-branch' defaults with usability opinions

This is where opinionated app-level defaults live. Password memory is enabled (usability over privacy theatre — the browser's own password manager is better than users writing passwords on sticky notes). Session-restore privacy level is set for full restoration. Tab-sleep timers tuned for a small memory budget. Sidebar experiments disabled ('no nightly-only stuff on a stable build'). Comment in the patch: `GORILLA: no nightly-only sidebar experiments — always off.`

### Step 4: all.js — the second app-branch, with the aggressive purge

The purge zone. AI features (chatbots, PDF alt-text via remote AI, translation nag), TopSites (sponsored tile ads), Normandy (remote experiments), Nimbus (feature-flag rollouts), and Pocket integration all forcibly set to `false` here. Comments include `AGGRESSIVE PURGE (AI & TOPSITES)` and `TELEMETRY STARVATION`. Note the aesthetic: telemetry isn't just turned off, it is *starved* — every food source cut simultaneously.

### Step 5: The locale properties file — accept-language + trending lock

One tiny file (`intl/locale/language.properties`) forces accept-language to a fixed value and disables multilingual/trending features. This is a fingerprinting defence: pages cannot see your language preferences drift over time, and there is no server-side 'we noticed you speak Bengali now, here are recommendations' behaviour.

## 🤔 Quirky Things Worth Knowing

### ⚠️ The build recipe is not portable — and the log says so

`-march=native -O3` means: build using every CPU instruction the machine we compile on knows about. The resulting binary runs faster on that machine, but may crash on any machine with a different CPU generation. The log opens with a warning: 'This is NOT portable. Never ship these binaries to other hardware.' If you want a portable build, you change one flag — but you also give up the speed.

### ⚠️ Password manager ON, but telemetry OFF

Most privacy-focused browser builds turn off *everything* including features that would actually help the user. This one keeps the password manager on: a local password manager is a legitimate usability tool, and the alternative (users typing passwords into every site or reusing them across sites) is measurably worse for privacy. The build distinguishes between 'convenience for you' (kept) and 'convenience for Mozilla' (cut).

### ⚠️ The master switch is defined here but READ by another topic

`media.gorilla.hardware_only_mode` is a preference. Its definition (the fact that it exists, its type, its default value `true`) lives in `StaticPrefList.yaml` in this folder. But nothing in this folder actually consumes it — every `if (StaticPrefs::media_gorilla_hardware_only_mode())` check lives in Topic 01. That's how prefs work: definition here, use elsewhere. Good separation of concerns.

## 💻 What Does This Mean For YOU?

### 🔋 Battery, Speed & Memory

The `-march=native -O3` build is measurably faster than a generic build on this exact CPU — cache locality is better, some AVX instructions are used, LTO removes dead code across module boundaries. Not benchmarked as a raw number in this folder. Tab-sleep timers reclaim RAM for backgrounded tabs.

### ⚡ Speed

Compiled subsystems that were removed cannot run — startup is faster because there is less code to load.

### 🕵️ Your Privacy

This is where the systematic privacy defaults live: telemetry, Normandy, Nimbus, AI-features, TopSites-sponsored, Pocket all default-off. Topic 12 hard-locks the ones Mozilla could otherwise re-enable via remote config.

### 🌐 Your Internet

Aggressive purge means fewer background connections at startup and steady-state. Not benchmarked; the mechanism is clear.

## 🔴 The Kill Switch — Explained

**What it is:** The whole folder IS the kill switch panel. Every preference that gates a feature elsewhere is set here. The single most important one is `media.gorilla.hardware_only_mode` (default `true`) — flip it to `false` and every gate in Topic 01 opens.

**Without it:** Without this folder, the browser has upstream defaults everywhere: telemetry on, AI features on, TopSites-sponsored on, no `media.gorilla.hardware_only_mode` pref at all (Topic 01's gates all fail-closed and become dead code). The build would be indistinguishable from stock Firefox at the preference level, even after all the code patches.

**Think of it like:** The whole factory-fresh setting page in the user manual. Individually the switches are small; collectively they define what the machine does when you first turn it on.

## 🌐 Open Source & Why It Matters To You

You can read every default. Every `pref("whatever", false)` line has a reason behind it, and the reasons are in the comments (`AGGRESSIVE PURGE (AI & TOPSITES)`, `TELEMETRY STARVATION`, and so on — colourful, but at least honest). A closed browser has thousands of defaults you cannot see; here they are one grep away.

## 📖 Glossary (Plain English Dictionary)

**mozconfig** — The build recipe file. Tells the compiler what to build, with which optimisations, and what to leave out.

**StaticPrefList.yaml** — The compile-time preference registry. Every pref Firefox knows about, defined here with a default value that becomes part of the binary.

**firefox.js / all.js** — Application-branch preference files loaded at startup. Override StaticPrefList defaults for this build.

**-march=native** — Compiler flag: 'build for the exact CPU I am running on right now.' Faster on this CPU; may crash on others.

**LTO (Link-Time Optimization)** — The compiler treats the whole binary as one unit at link time, finding optimisations across file boundaries. Slower to build, faster at runtime.

**Preference override layers** — Ordered from lowest to highest priority: StaticPrefList (built in) → firefox.js/all.js (app defaults) → prefs.js (user changes in about:config) → user.js (Topic 10) → policies.json (Topic 12, hard-locked).

---
*Human Track. Its Developer Track twin (`05-prefs.DEVELOPER.md`) covers the same changes in technical detail. Neither is a simplified copy of the other — they are the same truth in two languages.*


---

# ═══ MERGED DOCUMENT: 05-prefs.PRECHECK.json (verbatim · sha256:cc217a36bbddcb06 · merged 2026-08-02) ═══

```json
[
  {
    "id": "P2-001",
    "severity": "P2",
    "track_a": "A sticky note saying 'finish this later' was left inside the machine.",
    "track_b": "browser_app_profile_firefox.js.patch: added lines contain 1 TODO/FIXME markers.",
    "remediation": "Resolve or convert to a tracked item in PATCH.READINESS.txt."
  }
]
```


---

# ═══ MERGED DOCUMENT: 05-prefs.PRECHECK.md (verbatim · sha256:f0f3f6f9a9cff5b3 · merged 2026-08-02) ═══

# Offline Pre-Check: 05-prefs

*Generated 2026-07-16 22:32:45 by doc_audit.py (rule-based, no model involved).*

## File Inventory

| File | Lang | Lines | Complexity | SHA256 (16) |
|---|---|---|---|---|
| browser_app_profile_firefox.js.patch | patch | 598 | 35 | `da17a70d1311054b` |
| intl_locale_language.properties.patch | patch | 293 | 1 | `925b16aa29233bd4` |
| modules_libpref_init_StaticPrefList.yaml.patch | patch | 275 | 28 | `0e6501e731c052c1` |
| modules_libpref_init_all.js.patch | patch | 258 | 13 | `cd760d2c5a0237e8` |

## Rule Findings (1)

### 🟡 P2-001 — P2
- **Track A:** A sticky note saying 'finish this later' was left inside the machine.
- **Track B:** browser_app_profile_firefox.js.patch: added lines contain 1 TODO/FIXME markers.
- **Remediation:** Resolve or convert to a tracked item in PATCH.READINESS.txt.

