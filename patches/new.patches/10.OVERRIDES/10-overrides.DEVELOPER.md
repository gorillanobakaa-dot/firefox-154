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