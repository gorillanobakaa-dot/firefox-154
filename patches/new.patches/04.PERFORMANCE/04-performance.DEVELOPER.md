# Performance Folder — Clang-21 Build Compat + IVB CC Tuning + JIT Cache Telemetry Gate — Developer Track

> **Topic:** `04-performance` · **Files:** `mfbt/Maybe.h`, `mfbt/MaybeStorageBase.h`, `dom/base/CCGCScheduler.cpp`, `js/src/frontend/Stencil.cpp`
> **Generated:** 2026-07-16

---

## Module Summary

Small but load-bearing. Four files, three purposes: (1) SFINAE `IsComplete<T>` guards in `mfbt/Maybe.h` and `mfbt/MaybeStorageBase.h` — required for Firefox 154 to compile on Clang 21 (Clang-21 Pattern #1: protected `mIsSome` accessed from template instantiations); (2) hardcoded IVB-tuned Cycle Collector cadence in `dom/base/CCGCScheduler.cpp` (`kICCSliceBudget=4ms`, `kICCIntersliceDelay=120ms`) sized so CC slices fit inside a 60 Hz Wayland frame budget; (3) Necko-style Glean excision in `js/src/frontend/Stencil.cpp` for JIT self-host compile-cache metrics. Genuine performance policy lives in `05.PREFS` + `10.OVERRIDES`, not here — the log opens by saying so.

## Architecture

- **Pattern:** Point fixes across three unrelated subsystems. No shared architecture; the folder is defined by categorisation gap rather than functional cohesion.
- **Trust Boundary:** N/A
- **Attack Surface:** N/A
- **Dependencies:** `Clang 21 toolchain (build-time)`, `companion `preflight-clang21.py` in firefox-source root — catches the other 4 Clang-21 breakage patterns`

## Kill Switches

### `mfbt/Maybe.h + mfbt/MaybeStorageBase.h — IsComplete<T> SFINAE guards` — HARD ⚠️

- **Condition:** compile-time constexpr `if constexpr (IsComplete<T>::value)`
- **Effect:** Trait evaluation short-circuits to false on incomplete types instead of triggering a compiler error. Fixes ERR-BUILD-008.
- **Reversibility:** reversible
- **Notes:** Removing these breaks the build on Clang 21.

### `dom/base/CCGCScheduler.cpp — kICCSliceBudget / kICCIntersliceDelay` — RUNTIME_GUARD ⚠️

- **Condition:** always at CC scheduler init
- **Effect:** CC slice budget pinned to 4 ms; inter-slice delay pinned to 120 ms. Chosen so CC work fits inside a 16.6 ms Wayland frame at 60 Hz on a 4-core IVB CPU.
- **Reversibility:** reversible
- **Notes:** Patch comment: 'IVB (4c/8t) tuning — more eager cycle collection, smaller gaps.' Not benchmarked before/after.

### `js/src/frontend/Stencil.cpp — JIT compile-cache Glean` — HARD ⚠️

- **Condition:** compile-time preprocessor
- **Effect:** JIT self-host compile-cache metric expansions become no-ops under `#ifndef GLEAN_DISABLED`.
- **Reversibility:** reversible
- **Notes:** Coherent with Necko + Topic 13 methodology.

## Performance Profile

| Component | Before | After | Mechanism |
|---|---|---|---|
| CC slice budget | upstream default (variable) | 4 ms pinned | kICCSliceBudget constant |
| CC inter-slice delay | upstream default | 120 ms pinned | kICCIntersliceDelay constant |
| JIT compile-cache Glean metric | recorded per page load | compile-time DCE'd | GLEAN_DISABLED gate |

- **CPU:** CC slice cadence tightened so slices land inside frame budgets. Not benchmarked topic-locally.
- **Memory:** No change.
- **I/O:** No change.
- **Timer Interval:** CC: 4 ms budget × 120 ms delay between slices.

## Security Analysis

### User Profiling

One more Glean channel severed — JIT compile-cache statistics were an inferential-attack surface (compile-cache hit patterns leak sub-page navigation).

### Targeting

N/A

### Trust Chain

Unchanged

### Abuse Potential

N/A

## Implementation Flow

1. **`IsComplete<T> trait`** — SFINAE test returning true when sizeof(T) is available, false otherwise.
   *Side effects:* None (compile-time).
2. **`IsCopyConstructibleHelper / IsMoveConstructibleHelper / IsTriviallyDestructibleAndCopyableHelper`** — Guarded by if constexpr (IsComplete<T>::value) — returns false for incomplete types instead of blowing up compilation.
   *Side effects:* None.
3. **`CCGCScheduler init`** — Uses the pinned 4 ms / 120 ms constants for slice budget and delay.
   *Side effects:* CC slices land inside frame boundaries; visible stutter reduced.
4. **`Stencil compile-cache path`** — Glean metric expansion becomes no-op under GLEAN_DISABLED.
   *Side effects:* No JIT cache metric recorded.

## Technical Debt

🟡 **LOW** — The 4 ms / 120 ms constants are magic numbers — no comment linking them to the 16.6 ms frame budget rationale
  - *Recommendation:* Add a one-line comment referencing the Wayland-60Hz-frame-budget calc.

🟢 **ACCEPTED** — Folder name is misleading (mostly compile fixes)
  - *Recommendation:* Rename to something like `04.BUILD_COMPAT` on next re-org. Cost of rename outweighs benefit for now.

## Impact If Removed / Disabled

Reverting IsComplete guards -> Firefox 154 does not compile on Clang 21 (ERR-BUILD-008). Reverting CC tuning -> occasional frame-boundary hitches during heavy JS churn. Reverting Stencil telemetry gate -> JIT compile-cache metric resumes phoning home.

## Testing Notes

Build: `./mach build` must succeed on Clang 21. Runtime: about:memory -> Minimize memory usage; CC slices should be measurable at ~4 ms each. Telemetry: `strings libxul.so | grep -c stencil.*compile.*cache` should be 0.

## Changelog Notes

2026-05-29 initial completeness traits (FF153); 2026-07-05 migrated to FF154; 2026-07-08 folder hygiene (dropped 5 no-edit vanilla files); 2026-07-10 Stencil.cpp Glean gate added; 2026-07-11 Clang-21 preflight script covers the other 4 patterns.

---
*Developer Track. Human Track twin: `04-performance.LAYMAN.md`.*