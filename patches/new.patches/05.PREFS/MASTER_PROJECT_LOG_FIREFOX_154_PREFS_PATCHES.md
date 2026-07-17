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
