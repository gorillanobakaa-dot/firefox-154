# MASTER PROJECT LOG — FIREFOX 154 PERFORMANCE & COMPATIBILITY PATCHES

---

## Part 1: History, Roadmap & Overview
*(Originally from 00_PERFORMANCE_HISTORY_AND_ROADMAP.md)*

### Document Control
- **Category:** Performance & Build Compatibility
- **Last Updated:** 2026-07-10
- **Status:** Active Development
- **Verification Required:** Yes (see Validation section)
- **Related Documents:** 
  - `../DOCUMENTATION_TEMPLATES.md` (IBM format guide)
  - `../MAP.md` (cross-category index)
  - `../05.PREFS/00_PREFS_HISTORY_AND_ROADMAP.md` (actual performance tuning)
  - `../05.PREFS/StaticPrefList.yaml` (GC/timeout settings)
  - `../10.OVERRIDES/user.js` (runtime performance prefs)

---

### Executive Summary

**What This Does (Plain Language):**
Despite the name "performance," this folder is mostly about making Firefox **compile** on the new, stricter compiler (Clang-21). It contains one small but critical fix that prevents build failures, plus one privacy improvement (telemetry removal). The actual speed tuning lives in the settings folder (`05.PREFS`), not here.

**Technical Summary:**
Build compatibility fixes for Clang-21 toolchain plus telemetry lobotomy, plus IVB cycle-collector tuning. Implements: (1) SFINAE `IsComplete<T>` trait guards to prevent incomplete-type trait evaluation (ERR-BUILD-008), (2) telemetry removal in JS compile cache (`Stencil.cpp`), (3) `kICC*` cycle-collector cadence pinned for Ivy Bridge in `CCGCScheduler.cpp`. The behavioral GC/timeout *policy* is pref-driven (`05.PREFS`); the CC scheduler cadence is pinned here.

**Critical Context:**
> **The name is misleading.** This folder's job is to make the browser *build* on Clang-21, not to make it *fast*. The real performance knobs are settings in `05.PREFS`. We're honest about this rather than pretending the folder does more than it does.

---

### Mission Statement

### Mission 1: Build Compatibility (Primary)
When we upgraded to Clang-21 (newer, stricter compiler), the build broke on incomplete-type errors. The compiler tried to evaluate traits on types that weren't fully defined yet — like asking "how big is this box?" before the box exists.

**Our Response:**
Added small SFINAE `IsComplete<T>` trait guards that check "does this type exist yet?" before evaluating traits. Without this fix, Firefox 154 doesn't build at all on Clang-21.

### Mission 2: Privacy (Secondary)
One more telemetry wire cut in the JS compile cache, consistent with network stack lobotomy.

---

### Component Documentation

#### 1. MaybeStorageBase.h — SFINAE Completeness Trait (ERR-BUILD-008)
- **Status:** Modified | **Deploy Path:** `mfbt/MaybeStorageBase.h` | **Last Verified:** 2026-07-06
- **What It Does (Plain Language):** This defines a test that checks "does this type fully exist yet?" before trying to use it. It's the foundation of the Clang-21 fix.
- **Technical Description:** SFINAE completeness trait that detects whether a type is fully defined.

#### 2. CCGCScheduler.cpp — IVB Cycle-Collector Tuning (Performance, Hardcoded)
- **Status:** Modified | **Deploy Path:** `dom/base/CCGCScheduler.cpp` | **Last Verified:** 2026-07-10
- **What It Does (Plain Language):** Pins the Cycle Collector (CC) timing limits specifically to prevent micro-stuttering on your 4-core VAIO CPU.
- **Technical Description:** Pins `kICCIntersliceDelay` to 120ms and `kICCSliceBudget` to 4ms to ensure garbage collection fits cleanly within GNOME Wayland frame budgets (16.6ms at 60Hz).

---

### Chronological History (Recovered)

#### 2026-05-29
Initial completeness traits drafted under Firefox 153 compilation.

#### 2026-07-05
**Firefox 154 Migration:**
`Maybe.h` and `MaybeStorageBase.h` migrated to 154.

#### 2026-07-08
**Folder Hygiene:**
Cleaned up vanilla files (`ContentChild.cpp`, `ContentParent.cpp`, `TimeoutManager.cpp`, `nsJSEnvironment.cpp`, `RDDParent.cpp`) that carried zero Gorilla edits.

#### 2026-07-10
**Glean Scouring:**
Surgically gated JIT self-host compile cache metrics under `#ifndef GLEAN_DISABLED` inside `Stencil.cpp` to prevent runtime telemetry leaks.

---
 
## Part 3: Clang 21 Pre-Flight Guard (2026-07-11)
 
The Clang 21 migration uncovered 5 breakage patterns across the tree (see `preflight-clang21.py`). This category's `Maybe.h` / `MaybeStorageBase.h` fixes address **Pattern 1** (protected `mIsSome` accessed from template instantiations). The automated pre-flight script `preflight-clang21.py` (in `firefox-source/` root) catches all 5 patterns before every build:
 
1. `MaybeStorage::mIsSome` protected → template access error (fixed here)
2. Forward-declared union class used as field type → incomplete type
3. Duplicate union class definitions across generated headers
4. Missing required union methods (`Init`, `TraceUnion`, `ToJSVal`, etc.)
5. `UnionMember.Construct()` wrong method name (should be `.SetValue()`)
 
**Pre-flight runs automatically** via `01_build_orchestrator.py setup preflight` before every `./mach build`. UI-only changes (CSS/FTL) skip preflight.
 
---

## Part 2: Rule-Based Code Audit & Validation (2026-07-10)

We completed a static code audit of the performance patches:

1. **MaybeStorageBase.h**: Trait implementation `IsComplete` verified on lines 16-20. Safe SFINAE guards return `false` on incomplete structures.
2. **CCGCScheduler.cpp**: Cycle-collector slice limits verified at `4ms` budget (line 32), keeping main thread iterations within the Wayland frame cycle.
3. **Stencil.cpp**: JS compile cache Glean triggers (`hits.AddToNumerator` and `total.Add`) are gated under `#ifndef GLEAN_DISABLED` (lines 3113-3116, 3144-3146).

The category passes all code guidelines.
