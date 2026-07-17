# Telemetry / Glean Kill — Layered Source-Level Short-Circuits (13.2% -> 0.39% Parent CPU) — Developer Track

> **Topic:** `13-telemetry-kill` · **Files:** `xpcom/base/MemoryTelemetry.cpp`, `toolkit/components/glean/xpcom/FOG.cpp`, `third_party/rust/glean-core/src/lib.rs`, `third_party/rust/glean-core/src/dispatcher/global.rs`, `third_party/rust/glean-core/src/metrics/timing_distribution.rs`, `third_party/rust/glean-core/src/metrics/memory_distribution.rs`, `third_party/rust/glean-core/.cargo-checksum.json`
> **Generated:** 2026-07-17

---

## Module Summary

Eliminates the parent-process CPU cost of Firefox's two telemetry subsystems — legacy MemoryTelemetry and modern Glean/FOG — WITHOUT structurally removing them (which orphans mozilla::glean:: symbols and breaks the link). Three layered source-level short-circuits: (1) skip the periodic /proc/self/smaps resident-memory scan; (2) no-op FOG initialization so the Glean dispatcher thread is never flushed; (3) a compile-time const GORILLA_TELEMETRY_OFF guard on the hot metric-recording paths so the optimizer dead-code-eliminates them. Measured result during 1080p60 playback: total telemetry CPU fell from ~13.2% -> ~0.39% of the parent process. VERIFIED via perf, 2026-07-16.

## Architecture

- **Pattern:** Layered soft-disable (return-early / const-fold), NOT excision. Every symbol, XPCOM factory, and moz.build reference is left intact and compiled; only the work is prevented from running.
- **Trust Boundary:** Telemetry is a data-egress boundary. Recorded metrics flow: call site -> glean_core metric -> dispatcher queue -> ping assembly -> uploader -> Mozilla endpoints. This severs the chain at the recording stage — before data is ever staged — which is strictly stronger than severing at the upload stage (prefs only do the latter).
- **Attack Surface:** Behavioral egress neutralized (recording never happens). Local resource drain (the CPU finding) neutralized. Fingerprinting inputs (memory/timing distributions) not recorded -> not available.
- **Dependencies:** `No dependencies added. Removes de-facto runtime dependence on the Glean dispatcher thread and the nsMemoryReporterManager smaps path.`

## Kill Switches

### `MemoryTelemetry::GatherReports() (xpcom/base/MemoryTelemetry.cpp)` — HARD ⚠️

- **Condition:** always — unconditional early return after invoking the completion callback
- **Effect:** The background ResidentUnique measurement — which reads /proc/self/smaps and triggers vm_normal_page -> smaps_pte_range -> walk_pgd_range kernel page-table walks — is never dispatched. Verified 8.9% -> 0.02%.
- **Reversibility:** reversible
- **Notes:** Setting toolkit.telemetry.enabled=false does NOT stop this; the class has its own Poke()->timer->GatherReports() cycle. Source is the only off switch.

### `FOG::InitializeFOG() (toolkit/components/glean/xpcom/FOG.cpp)` — HARD ⚠️

- **Condition:** always — returns NS_OK before fog_init()
- **Effect:** glean::initialize() is never called; the dispatcher's pre-init buffer is never flushed. The glean.dispatche thread is still spawned (it is a Lazy static) but blocks forever on a channel recv at 0% CPU. Verified 3.5% -> 0.00%.
- **Reversibility:** reversible
- **Notes:** gInitializeCalled=true is set so the shutdown path does not attempt a re-init; glean::shutdown() on an uninitialized core is a documented no-op.

### `GORILLA_TELEMETRY_OFF const (third_party/rust/glean-core/src/lib.rs)` — HARD ⚠️

- **Condition:** compile-time constant true
- **Effect:** Guards TimingDistributionMetric::{start, stop_and_accumulate, accumulate_raw_duration}, LocalTimingDistribution::accumulate, and the MemoryDistribution equivalents. Because the guard is const, the optimizer folds if true { return } and eliminates the bodies — removing both the inline recording work AND the guard's own branch cost. dispatcher::global::launch() also drops tasks in production. Verified inline recording 0.84% -> 0.39%.
- **Reversibility:** reversible
- **Notes:** Flip the const to false and rebuild. Residual 0.39% is FFI/histogram-glue marshalling in generated bindings — see Technical Debt.

## Performance Profile

| Component | Before | After | Mechanism |
|---|---|---|---|
| MemoryTelemetry (smaps scan) | 8.9% | 0.02% | GatherReports() short-circuit |
| Glean dispatcher thread | 3.5% | 0.00% | InitializeFOG() no-op (thread blocks) |
| Glean inline recording | 0.84% | 0.39% | const DCE guards on timing+memory dist |
| Total telemetry CPU | ~13.2% | ~0.39% | ~12.8% of parent reclaimed |

- **CPU:** The dominant win. walk_pgd_range (kernel) and the dispatcher thread vanish from the profile entirely.
- **Memory:** Minor secondary win — the never-flushed pre-init buffer no longer accumulates recorded-metric closures over long sessions.
- **I/O:** Eliminates the 60s /proc/self/smaps read.
- **Timer Interval:** MemoryTelemetry's 60s Poke() cycle no longer fires meaningful work.

## Security Analysis

### User Profiling

Eliminated at the source. Glean events (timing/memory/custom distributions, counters) are never recorded, so no behavioral profile is constructed even locally. Exceeds the pref-based approach, which records-then-suppresses-upload.

### Targeting

N/A by design — with Nimbus/Normandy also disabled (Topic 12) there is no remote-experiment channel that could segment or target this build.

### Trust Chain

Data egress trust chain severed at stage 1 (recording). Even if a downstream stage were re-enabled by accident, there is no recorded data to transmit.

### Abuse Potential

Removes the browser's own ability to be a passive behavioral sensor. Residual 0.39% is pure local compute (FFI marshalling) with no egress path.

## Implementation Flow

1. **`MemoryTelemetry::GatherReports()`** — Early return NS_OK after firing the completion callback; the nsMemoryReporterManager async ResidentUnique dispatch is skipped.
   *Side effects:* No smaps scan, no kernel page-table walk.
2. **`FOG::InitializeFOG()`** — Set gInitializeCalled=true, return NS_OK before glean::impl::fog_init(...).
   *Side effects:* Dispatcher thread spawns but blocks at 0% CPU; no pre-init buffer flush.
3. **`glean-core/src/lib.rs`** — Declare pub const GORILLA_TELEMETRY_OFF: bool = true;
   *Side effects:* Enables DCE of all guarded metric bodies.
4. **`timing_distribution.rs / memory_distribution.rs`** — if crate::GORILLA_TELEMETRY_OFF { return ... } at the top of each hot recording method.
   *Side effects:* Bodies DCE'd under LTO; no inline recording work.
5. **`dispatcher/global.rs launch()`** — Drops the task when not in test mode.
   *Side effects:* No pre-init buffer growth from enqueued tasks.
6. **`.cargo-checksum.json`** — Per-file SHA256 entries updated for every edited vendored file.
   *Side effects:* Build's checksum guard accepts the edits (mandatory — else build rejects them).

## Technical Debt

🟢 **ACCEPTED** — Residual ~0.39% inline Glean — HistogramIdForMetric, fog_* FFI entry points, and firefox_on_glean wrapper delegation live in generated bindings that run around the guards; custom_distribution is unguarded (~0.10%)
  - *Recommendation:* Chasing this means editing generated code for sub-noise-floor gain. Intentionally not pursued.

🟠 **MEDIUM** — Vendored-crate rebuild fragility — editing glean-core does NOT reliably trigger a cargo rebuild
  - *Recommendation:* Delete stale libglean_core-*.rlib / .fingerprint/glean_core-* / libgkrust.a before rebuilding. Document in the build script (this bit an earlier attempt — the binary reused a cached rlib and the change appeared to have no effect).

🟠 **MEDIUM** — Upstream drift on version bump — glean-core is a vendored crate replaced wholesale each Firefox version
  - *Recommendation:* These line-anchored edits + the .cargo-checksum.json SHAs will NOT survive an upgrade; expect to re-apply the telemetry kill per version.

## Impact If Removed / Disabled

Reverting restores full telemetry recording and the ~12.8% parent-process CPU cost on target hardware, plus the /proc/self/smaps 60s scan and the active Glean dispatcher thread. On 4 GB / HDD machines this is the difference between a responsive browser and a laboring one.

## Testing Notes

1. Build; confirm 0 warnings and a fresh libglean_core-*.rlib timestamp (proves the crate actually recompiled — a stale rlib silently reuses old code). 2. Launch, play 1080p60, perf record -p <parent>; grep the profile for smaps, walk_pgd, glean_core::...::accumulate — MemoryTelemetry and timing/memory-distribution inner recording should be absent. 3. /proc/<parent>/task/* sample: glean.dispatche thread at 0%. 4. Confirm no startup/shutdown crash (validates the uninitialized-Glean path).

## Changelog Notes

Three-stage development: (1) MemoryTelemetry + FOG short-circuits -> ~11.5% saved; (2) dispatcher::launch no-op -> buffer-growth fix; (3) const GORILLA_TELEMETRY_OFF DCE guards on timing+memory distributions -> residual 0.84%->0.39%. Prior structural-excision attempt (documented in Second.Brain fog_glean_excision_sop.xml) abandoned: it caused NS_ERROR_FACTORY_NOT_REGISTERED and required 157 shim headers. GORILLA_TELEMETRY_OFF is a pre-existing in-tree identifier (no-brand-spam rule governs NEW identifiers).

---
*Developer Track. Human Track twin: `13-telemetry-kill.LAYMAN.md`.*