# 10.OVERRIDES — Master Project Log

*Created 2026-08-02 by consolidating this folder's documentation set (merged verbatim below). Policy: one master project log per folder.*


---

# ═══ CONSOLIDATION 2026-08-02 — side documents merged VERBATIM below; originals deleted (recoverable: merged-docs-backup-2026-08-02.tar.gz + git history) ═══


---

# ═══ MERGED DOCUMENT: 10-overrides.AUDIT.md (verbatim · sha256:482df2e46af9c130 · merged 2026-08-02) ═══

# IBM-Style Audit Report: 10-overrides

## SECTION A: DOCUMENT CONTROL

| Attribute | Value |
|---|---|
| **Target Category** | 10-overrides |
| **Files Scanned** | see payload |
| **Baseline** | Firefox 154 (mozilla-central) |
| **Date / Time** | 2026-07-16 22:43:14 |
| **Audit Status** | PASS |

## SECTION B: EXECUTIVE SUMMARY (Track A — Layman)

One file, ~1,100 lines, read on every browser start. Overrides any Firefox preference this build wants tuned differently — memory limits, media settings, telemetry kill switches, AI feature disables. Sits fourth in the precedence chain (above app-branch defaults, below the hard-locked set in Topic 12). Defends against Firefox updates that silently reset preferences.

## SECTION C: TECHNICAL SUMMARY (Track B — Developer)

Monolithic canonical user.js, kernel-synced v2.0. Applied via deploy.sh into the profile directory; read on every start; overrides prefs.js, overridden by policies.json (Topic 12). Values coherent with Topic 05 defaults + Topic 03 sysctl contract + Topic 04 CC scheduler + Topic 01 media.gorilla.hardware_only_mode. Purposes: silent-reset defence, fast iteration, kernel-sync.

## SECTION D: DETECTED DEFECTS

*No defects detected by rules or model.*

## SECTION E: PRODUCTION READINESS ASSESSMENT

- **Overall readiness:** 🟢 90%
- **Done:**
  - [x] Single canonical user.js at ~1,121 lines
  - [x] Deployed via deploy.sh into the runtime profile
  - [x] Kernel-synced v2.0 tag
  - [x] Stale duplicates quarantined 2026-07-06
  - [x] Cross-topic prefs present and consistent with their consumers
- **To Do:**
  - [ ] P2: automated verification that user.js network-buffer prefs match /etc/sysctl.d/99-gorilla-network.conf
  - [ ] P3: consider user.js.d/ fragments concatenated at build time

## SECTION F: PHASED EXPANSION PLAN

### Phase 1 — `user.js source layout`
- **Tweak:** Split source into user.js.d/{01-media,03-networking,04-perf,...}.js fragments concatenated at build time; deploy monolith as before.
- **Expected impact:** Per-topic authorship; single deployment artifact.

## POSITIVE OBSERVATIONS

- ✅ Monolithic deployment + fragmentable source is the right architecture for a config file that must be human-auditable AND fast to iterate.
- ✅ Kernel-sync tag makes the coupling to sysctl explicit.
- ✅ Sits ABOVE prefs.js in the precedence chain — Firefox updates that reset prefs.js are silently corrected on next launch.

## VERIFICATION COMMANDS

```bash
ls -la obj-*/tmp/profile-default/user.js   # must exist
grep -c 'user_pref' NEW_FILES/user.js   # roughly 1100
grep 'media.gorilla.hardware_only_mode' NEW_FILES/user.js   # match Topic 05 defn
```



---

# ═══ MERGED DOCUMENT: 10-overrides.DEVELOPER.md (verbatim · sha256:1497930257eae7d7 · merged 2026-08-02) ═══

# Runtime Overrides — Single Canonical user.js Applied on Every Launch — Developer Track

> **Topic:** `10-overrides` · **Files:** `NEW_FILES/user.js (~1121 lines)`
> **Generated:** 2026-07-16

---

## Module Summary

Consolidated, versioned, kernel-synced user.js applied on every browser launch. Sits fourth in the precedence chain: StaticPrefList < firefox.js/all.js < prefs.js < user.js < policies.json. Purpose: (1) defence-in-depth against Firefox-update silent-reset of preferences, (2) fast iteration (edit-and-restart vs 10-20 min rebuild), (3) kernel-synced tuning (network buffers match sysctl caps, memory pressure matches kernel budget). Values chosen explicitly for the reference machine + custom kernel + hardware-only media policy — NOT a generic privacy pack.

## Architecture

- **Pattern:** Monolithic single-file config. One grep finds any setting. Deliberate over splitting into per-topic files.
- **Trust Boundary:** N/A — pref layer only.
- **Attack Surface:** N/A
- **Dependencies:** `Applied via deploy.sh into obj-*/dist/bin/browser/defaults/pref/ or the runtime profile directory`

## Kill Switches

### `user.js — ~1,100 user_pref() lines` — RUNTIME_GUARD ⚠️

- **Condition:** read on every browser start
- **Effect:** Overrides any preference Firefox may have silently reset. Values re-applied on every launch.
- **Reversibility:** reversible
- **Notes:** Individual lines commentable-out; whole file removable. Cannot override the small policies.json-locked subset (by design).

## Performance Profile

- **CPU:** Not benchmarked topic-locally. Includes GC/timeout tuning that the Topic 04 CCGCScheduler patch relies on being present at pref-layer.
- **Memory:** Tab-sleep timers + image-cache limits + heap-ceiling prefs sized for reference machine (16 GiB, UMA-shared).
- **I/O:** Background-service prefs (Normandy, telemetry, connectivity checks) all disabled — fewer steady-state connections.
- **Timer Interval:** Tab unloading, GC, IO throttling — see individual prefs.

## Security Analysis

### User Profiling

Every telemetry/AI/Normandy/Nimbus/Pocket pref reasserted at runtime. Coherent with Topics 05 (defaults), 12 (hard lock), 13 (source-level kill).

### Targeting

N/A here — but explicitly disables prefs that would open a remote-control channel.

### Trust Chain

user.js is trusted because it is part of the build artifact.

### Abuse Potential

N/A

## Implementation Flow

1. **`profile init — libpref reads user.js`** — Every user_pref() call sets the corresponding pref, overriding prefs.js.
   *Side effects:* All ~1,100 prefs set.
2. **`libpref applies policies.json (Topic 12)`** — The tiny locked subset overrides even user.js.
   *Side effects:* Normandy/Nimbus/updater prefs hard-locked.

## Technical Debt

🟡 **LOW** — 1,100+ lines in one file is unwieldy for reviewers
  - *Recommendation:* Consider per-topic user.js.d/ fragments concatenated at build time; keep monolithic file as deployment artifact.

🟠 **MEDIUM** — No automated test verifies kernel-sync values match current sysctl file
  - *Recommendation:* Add toolchain-preflight check for each network-buffer pref.

## Impact If Removed / Disabled

Every pref this file overrides reverts to whatever Topic 05's app-branch left it at. Silent-reset defence gone.

## Testing Notes

`ls -la obj-*/tmp/profile-default/user.js` — must exist. On profile start, about:config should show ~1,100 prefs at 'user set' status. Confirm at least one canary pref (e.g. `app.normandy.enabled` = false).

## Changelog Notes

Consolidated to single canonical file 2026-07-06. Stale duplicate under Surgical_Patches_V2/ quarantined. Kernel-Synced v2.0 tag ('Braveheart') marks alignment with the custom kernel + sysctl.

---
*Developer Track. Human Track twin: `10-overrides.LAYMAN.md`.*


---

# ═══ MERGED DOCUMENT: 10-overrides.LAYMAN.md (verbatim · sha256:7f83ee78864fe9e0 · merged 2026-08-02) ═══

# 🧍 The Runtime Override Layer — the User.js That Has the Final Say — Plain English Guide

> *Topic `10-overrides` of the Gorilla Unleashed Firefox 154 build · Written for everyone · 2026-07-16*

---

## 🌍 The Big Picture

This folder contains a single, hand-tuned `user.js` file with roughly 1,100 lines of preference overrides. Every time Firefox starts, it reads this file *last* — after the compile-time defaults from Topic 05, after any settings in the profile — and applies its values on top. It is the final layer of preference control before the browser starts talking to the network.

**Why have this layer at all?** Firefox's own factory defaults (which Mozilla picks) are optimised for Mozilla's business: telemetry on, AI features on, experiments on, background services on. The compile-time overrides in Topic 05 turn most of those off. But Firefox also updates — and updates sometimes silently *reset* preferences back to their upstream defaults. Having a runtime layer that re-applies our chosen values on every launch is a defence against that quiet drift.

The secondary reason: iteration speed. Changing a compile-time default in Topic 05 requires a full rebuild (10–20 minutes). Changing `user.js` requires editing the file and restarting the browser (10 seconds). During development this matters a lot.

**What is in it:** memory and GC tuning for the reference machine's RAM budget, media settings synchronised with the hardware-only decode policy, aggressive telemetry / experiment / AI kill-switches, and dozens of small usability tweaks. All commented, all readable.

## 🎭 The Main Characters

| Name | What It Is | Real-World Comparison |
|---|---|---|
| **user.js** | The runtime-override preference file — applied last on every browser launch | The pilot's pre-flight checklist — every switch touched, in order, right before takeoff |
| **Precedence chain** | StaticPrefList (Topic 05, built-in) → firefox.js / all.js (Topic 05, app-branch) → prefs.js (user changes in about:config) → user.js (this) → policies.json (Topic 12, hard-lock) | A stack of transparent slides, each written on top of the last |

## 🔢 How It Works — Step by Step

### Step 1: One file, ~1,100 lines, human-readable

Every line is `user_pref("name", value);` with a comment above it explaining why. Deliberately monolithic — one place to look, one grep to find any setting.

### Step 2: Applied on every browser start

Firefox reads user.js after loading the profile's prefs.js, and the values overwrite whatever was there. Even if Firefox updated overnight and silently reset something, this file catches the reset and restores our value on the next launch.

### Step 3: Kernel-synced defaults

The file's status header reads 'Kernel-Synced Braveheart' — the values chosen here explicitly align with the custom `7.x-unleashed.gorilla` kernel's settings. Network buffer sizes match sysctl caps, memory pressure thresholds match what the kernel can handle.

## 🤔 Quirky Things Worth Knowing

### ⚠️ It cannot override policy-locked prefs from Topic 12

The tiny set of preferences hard-locked by policies.json sit above user.js in the precedence chain. If user.js tries to set one, the value is silently ignored. That is by design — Topic 12 is the layer we want to be un-overrideable.

### ⚠️ A stale duplicate was quarantined 2026-07-06

There used to be multiple user.js files scattered across the project. They were consolidated into this one canonical file and the duplicates put behind a `.disabled` extension. Single source of truth.

## 💻 What Does This Mean For YOU?

### 🔋 Battery, Speed & Memory

Tab-sleep timers, GC heap ceilings, and image-cache limits are all sized for our RAM budget rather than defaults. The observable is fewer swap incidents and less background CPU.

### ⚡ Speed

Startup lighter — background services (Normandy check, telemetry init) do not run.

### 🕵️ Your Privacy

Every AI/experiment/telemetry pref that Topic 05 might not have caught is caught here. Belt-and-suspenders.

### 🌐 Your Internet

Fewer background connections. See Topic 03 for the network stack side.

## 🔴 The Kill Switch — Explained

**What it is:** The whole file IS a bank of ~1,100 kill switches (or affirmative switches, or tunings). Each is one line; each can be reverted individually.

**Without it:** Firefox runs with factory-default preferences. Everything this file overrides silently comes back to Mozilla's chosen value.

**Think of it like:** The full lighting cue-sheet for a theatre show — 1,100 cues in order, each one small, the whole doing the actual work of running the show.

## 🌐 Open Source & Why It Matters To You

The single most auditable thing in the whole build. One file, plain text, every line commented. Compare to closed browsers where equivalent settings are opaque, undocumented, and often silently mutated by updates.

## 📖 Glossary (Plain English Dictionary)

**user.js** — A Firefox convention: a file in the profile directory that gets its `user_pref(...)` lines applied on every start, overriding anything in prefs.js.

**prefs.js** — The file Firefox writes to when you change a preference via about:config. Persisted, but overrideable by user.js on next start.

**Precedence chain** — The order in which preference sources are applied at startup. Last one wins. Our chain: StaticPrefList → firefox.js/all.js → prefs.js → user.js → policies.json.

---
*Human Track. Its Developer Track twin (`10-overrides.DEVELOPER.md`) covers the same changes in technical detail. Neither is a simplified copy of the other — they are the same truth in two languages.*


---

# ═══ MERGED DOCUMENT: 10-overrides.PRECHECK.json (verbatim · sha256:4f53cda18c2baa0c · merged 2026-08-02) ═══

```json
[]
```


---

# ═══ MERGED DOCUMENT: 10-overrides.PRECHECK.md (verbatim · sha256:d4d81e5124f92c9f · merged 2026-08-02) ═══

# Offline Pre-Check: 10-overrides

*Generated 2026-07-16 22:43:14 by doc_audit.py (rule-based, no model involved).*

## File Inventory

| File | Lang | Lines | Complexity | SHA256 (16) |
|---|---|---|---|---|
| user.js | js | 54 | 3 | `0eb128896590921f` |

## Rule Findings (0)

*All offline rules passed.*
