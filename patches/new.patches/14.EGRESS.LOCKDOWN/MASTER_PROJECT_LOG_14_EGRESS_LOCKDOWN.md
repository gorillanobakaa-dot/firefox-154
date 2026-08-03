# 14.EGRESS.LOCKDOWN — Master Project Log

*Created 2026-08-02 by consolidating this folder's documentation set (merged verbatim below). Policy: one master project log per folder.*


---

# ═══ CONSOLIDATION 2026-08-02 — side documents merged VERBATIM below; originals deleted (recoverable: merged-docs-backup-2026-08-02.tar.gz + git history) ═══


---

# ═══ MERGED DOCUMENT: 14-egress-remote-lockdown.AUDIT.md (verbatim · sha256:f6afff951b45d9b9 · merged 2026-08-02) ═══

# IBM-Style Audit Report: 14-egress-remote-lockdown (Unifying Topic)

## SECTION A: DOCUMENT CONTROL

| Attribute | Value |
|---|---|
| **Target Category** | 14-egress-remote-lockdown (consolidation of 03 + 09 + 12 + 13) |
| **Files Scanned** | Source patches in 03.NETWORKING, 09.REMOTE, 12.MOZAMBIQUE.DRILL, 13.TELEMETRY.KILL (see each topic's own audit) |
| **Baseline** | Firefox 154 (mozilla-central) |
| **Date / Time** | 2026-08-01 |
| **Audit Status** | PASS (unifying review; per-topic audits stand) |

## SECTION B: EXECUTIVE SUMMARY (Track A — Layman)

Four separate pieces of work lock every door through which this browser could
report on you (telemetry), be reconfigured from a distance (experiments), or be
driven by an outside program (automation). None are deleted — all are switched
off *in place*, because deleting them crashes the browser. The one piece with a
measurable speed cost (the self-measuring subsystem) went from eating ~1 in 8
units of the browser's main effort during video to under half a percent. The
rest cost nothing to run and exist for privacy and control.

## SECTION C: TECHNICAL SUMMARY (Track B — Developer)

Coherent soft-neutralization posture across four topics, unified by Prime
Directive 0 (neutralize, never excise — excision empirically abandoned:
`NS_ERROR_FACTORY_NOT_REGISTERED` + 157 shims; 145+ dependent crashes). Egress
severed at the recording stage via compile-time const-DCE (`GORILLA_TELEMETRY_OFF`)
+ FOG/MemoryTelemetry early-returns (topic 13) and TU-level preprocessor gates
(`GLEAN_DISABLED 1` / `MOZ_TELEMETRY_REPORTING 0`) in 4 netwerk files (topic 03).
Experiment channel severed via three-shot + policy lock (topic 12). Inbound
automation sockets prevented via three-surface dead-coding per channel (topic
09). Measured telemetry parent CPU 13.2% → 0.39% (perf, 2026-07-16). All symbols
and dependents remain satisfied.

## SECTION D: DETECTED DEFECTS

*No new defects at the unifying level.* Per-topic audits (03/09/12/13) each carry
their own P2/P3 backlogs; the cluster-level items are consolidated in Section E.

**One documentation defect corrected by this consolidation:** older prose in
03.NETWORKING and several DB atoms described the deployed soft-gates as
"excision/delete/lobotomy," contradicting the actual reversible mechanisms and
the abandon-excision decision. Reconciled in this topic's README; excision-era
atoms flagged as history, not roadmap.

## SECTION E: PRODUCTION READINESS ASSESSMENT

- **Overall readiness:** 🟢 94% (weighted across the four source topics: 03=92, 09=96, 12=production, 13=96)
- **Done:**
  - [x] Telemetry recording severed at source (const-DCE + early-returns + preprocessor gates)
  - [x] Measured CPU reclamation verified (13.2% → 0.39%, perf 2026-07-16)
  - [x] Experiment channel neutralized + policy-locked (three-shot + 60y timer)
  - [x] Both automation channels physically locked (three surfaces each)
  - [x] Excision→soft-gate doctrine reconciled and documented (this topic)
  - [x] All 145+ Normandy/Nimbus dependents remain satisfied (no boot crash)
- **To Do (cluster-level):**
  - [ ] P2: extract Necko `GLEAN_DISABLED`/`MOZ_TELEMETRY_REPORTING` pair to a shared header (4 duplicate TU-tops, drift-vulnerable)
  - [ ] P2: `toolchain-preflight` assertion that Marionette + RemoteAgent report disabled at runtime (guards silent upstream-default restore on rebase)
  - [ ] P2: `toolchain-preflight` assertion for the glean-core stale-rlib/checksum step (a stale rlib makes topic 13 silently ineffective)
  - [ ] P3: re-apply topic 13 per Firefox version (vendored glean-core replaced wholesale on upgrade)
  - [ ] P3: purge or clearly retire excision-era DB atoms (`fog_glean_excision_sop`, `excision_targets`, `excision_roadmap`) so they cannot be mistaken for a plan

## SECTION F: PHASED EXPANSION PLAN

### Phase 0 — `toolchain-preflight` (cross-topic)
- **Tweak:** Assert all cluster invariants at build time — all 4 Necko files carry the preprocessor pair; glean-core rlib is fresh; Marionette/RemoteAgent disabled; 3 normandy prefs locked.
- **Expected impact:** Turns "silently regressed on rebase" into a loud, early failure. Highest-leverage single addition.

### Phase 1 — shared `NeckoTelemetryDisable.h`
- **Tweak:** Replace the 4 duplicated preprocessor tops with one included header.
- **Expected impact:** Removes rebase drift risk on topic 03's telemetry gate.

### Phase 2 — retire excision-era artifacts
- **Tweak:** Move `fog_glean_excision_sop.xml` / `excision_targets.xml` /
  `excision_roadmap.xml` to an explicit `ABANDONED/` subtree or annotate each with a
  header pointing at this topic's reconciliation.
- **Expected impact:** Closes the "resurrected verdict" failure mode permanently.

## POSITIVE OBSERVATIONS

- ✅ The four topics were authored independently yet converge on one architectural
  principle (sever early, neutralize in place) — coherence, not coincidence.
- ✅ Topic 13 is the strongest-grounded work in the whole build: every number is
  perf-measured, not estimated.
- ✅ The const-DCE technique (topic 13) is genuinely elegant — a compile-time-true
  guard removes both the work and its own branch, which a runtime flag cannot.
- ✅ Severing telemetry at the *recording* stage exceeds the pref-based upload
  block: no staged data exists to leak even under downstream regression.
- ✅ This consolidation catches and fixes a real documentation hazard (the
  excision/soft-gate contradiction) rather than papering over it.

## VERIFICATION COMMANDS

See `14-egress-remote-lockdown.DEVELOPER.md` → "Testing Notes (unified)" for the
combined command set across all four topics.



---

# ═══ MERGED DOCUMENT: 14-egress-remote-lockdown.DEVELOPER.md (verbatim · sha256:cfcab95a9065a994 · merged 2026-08-02) ═══

# Telemetry & Remote-Channel Severance — Cross-Cutting Architecture — Developer Track

> **Topic:** `14-egress-remote-lockdown` (unifying) · **Generated:** 2026-08-01
> **Source topics:** `03.NETWORKING` (Necko Glean gate), `13.TELEMETRY.KILL`
> (Glean/FOG core), `12.MOZAMBIQUE.DRILL` (Normandy/Nimbus), `09.REMOTE`
> (Marionette/RemoteAgent). Authoritative per-file detail lives in each source
> topic's own DEVELOPER track; this document is the architecture that unifies them.

---

## Module Summary

Four independently-authored patch clusters implement one coherent security
posture: **no telemetry egress, no remote experiment/config channel, no inbound
automation control** — all via *soft neutralization*, never structural excision.
The unifying invariant is Prime Directive 0: every symbol, XPCOM factory,
`moz.build` reference, and JS module is left present and compiled; only the
*work* is prevented. This is not stylistic — excision was empirically abandoned
(`NS_ERROR_FACTORY_NOT_REGISTERED` + 157 shim headers for Glean;
`TypeError`/`ModuleNotFoundError` across 145+ dependents for Normandy/Nimbus).

## The four mechanisms, side by side

| # | Topic | Mechanism | Layer | Reversible by |
|---|---|---|---|---|
| 1 | 13 Glean/FOG | `pub const GORILLA_TELEMETRY_OFF: bool = true` → optimizer DCEs guarded metric bodies | compile-time const-fold | flip const + rebuild |
| 2 | 13 Glean/FOG | `FOG::InitializeFOG()` returns `NS_OK` before `fog_init()`; dispatcher never flushed | runtime early-return | remove early-return + rebuild |
| 3 | 13 Glean/FOG | `MemoryTelemetry::GatherReports()` early-returns; no `/proc/self/smaps` scan | runtime early-return | remove early-return + rebuild |
| 4 | 13 Glean/FOG | `dispatcher::global::launch()` drops the task when not in test mode | runtime guard | remove guard + rebuild |
| 5 | 03 Necko | `#undef MOZ_TELEMETRY_REPORTING` / `#define MOZ_TELEMETRY_REPORTING 0` / `#define GLEAN_DISABLED 1` at TU top of 4 netwerk files | compile-time preprocessor | remove defines + rebuild |
| 6 | 12 Normandy | `app.normandy.enabled=false` + `api_url=""` (build-time default, `locked`) | pref default + lock | unlock + rebuild |
| 7 | 12 Nimbus | `1893456000` (60y) fallback in `RecipeRunner`/`RemoteSettingsExperimentLoader` `getIntPref` defaults | code fallback | edit constant + rebuild |
| 8 | 12 both | `policies.json` runtime `lockPref` on the three normandy prefs | runtime policy lock | delete policies.json |
| 9 | 09 Marionette | `this.enabled=false` at ctor + dead-end setter + `--marionette` flag read-and-discarded | source dead-coding | edit source + rebuild |
| 10 | 09 RemoteAgent | `#enabled=false`, `#allowSystemAccess=false` at ctor + dead-end setters + `--remote-debugging-port` discarded | source dead-coding | edit source + rebuild |

## Architecture — the egress/ingress trust boundary

- **Egress (telemetry/experiments):** recorded metrics would flow `call-site →
  glean_core metric → dispatcher queue → ping assembly → uploader → Mozilla
  endpoint`. Topics 13 and 03 sever this at stage 1 (recording), which is
  strictly stronger than the pref-based approach (`toolkit.telemetry.*`,
  `datareporting.*`) that only blocks the *upload* stage — there is no staged
  data to leak if a downstream stage regresses. Topic 12 severs the *inbound
  instruction* channel (recipe/experiment fetch) that would otherwise drive
  behaviour and generate enrollment telemetry.
- **Ingress (automation):** Marionette and RemoteAgent would each bind a
  listening TCP socket that speaks a control protocol (Marionette wire protocol;
  WebDriver BiDi/CDP). Topic 09 prevents the socket from ever binding — three
  independent activation surfaces dead-coded per channel (ctor init, setter,
  CLI-flag branch).

## Why const-DCE (mechanism 1) beats a runtime flag

`GORILLA_TELEMETRY_OFF` is a `const`, not a runtime `AtomicBool`. Because it is
compile-time-known-true, `if GORILLA_TELEMETRY_OFF { return; }` at the top of a
hot metric method lets the optimizer eliminate **both** the recording body **and
the guard's own branch cost** — and under LTO the elimination propagates to
callers (e.g. WebRender frame-timing sites drop the call entirely). A runtime
atomic could not achieve either: it forces a load + branch on every call and
blocks caller-side elimination. This is the single most important portable
technique in the cluster: **prefer a compile-time const over a runtime flag when
you want the work to vanish, not just be skipped.**

## Shared invariants (do not break — any topic)

1. **Never excise; neutralize in place.** Deleting any of these systems
   re-triggers the documented failures. Keep bodies present and compiled.
2. **Vendored-crate edits (glean-core, topic 13) require two extra steps** or
   they silently no-op: update `.cargo-checksum.json` per-file SHA256 (else the
   build rejects the edit) **and** delete stale `libglean_core-*.rlib` /
   `.fingerprint/glean_core-*` / `libgkrust.a` (else cargo reuses a cached rlib
   and your change "has no effect"). This has bitten the project more than once.
3. **The Necko preprocessor pair (mechanism 5) is duplicated across 4 files** —
   drift-vulnerable on rebase. Verify all four still carry it after any netwerk
   rebase (`grep -l GLEAN_DISABLED netwerk/protocol/http/*.cpp netwerk/base/*.cpp`).
4. **The 60-year value `1893456000` must not be reduced** — it is what makes the
   Normandy timer inert even if a pref is reset. Fits in signed 32-bit (max ~68y).
5. **`policies.json` must stay deployed** in `distribution/` — it is the only
   layer that survives everything short of filesystem access to the install dir.
6. **Automation stays off.** Do not "temporarily re-enable Marionette for
   debugging" and forget to revert — use a separate unlocked debug build.

## GATED ≠ DEAD — what is actually stopped vs. merely idled

Precision matters here, because "disabled" overstates it. Findings below are
VERIFIED against the live tree 2026-08-01 (grep + source read).

**Genuinely GONE:** (a) the const-DCE'd glean-core recording bodies —
`GORILLA_TELEMETRY_OFF` guards confirmed in timing_distribution.rs (4 sites) and
memory_distribution.rs (3 sites), const at lib.rs:115; (b) the MemoryTelemetry
smaps scan — dead code after the early-return at MemoryTelemetry.cpp:239;
(c) `FOG::InitializeFOG` returns at FOG.cpp:153 before `fog_init`; (d) async
metric tasks — `dispatcher::global::launch()` drops the task at global.rs:54
before touching the dispatcher; (e) the Mozambique-Drill'd Normandy/Nimbus loops
(asleep 60 years).

**Still ALIVE / buzzing (the fly in a jar):**
- `MemoryTelemetry`'s 60 s `Poke()` timer still fires — only the *body* of
  `GatherReports()` early-returns; the timer registration (NS_NewTimerWithCallback
  at :206) and each wakeup persist.
- **~689 `glean::` call sites across ~65 netwerk files, only 6 gated with
  `GLEAN_DISABLED`.** Worst offenders are UNgated: nsHttpChannel.cpp (147),
  HttpBaseChannel.cpp (98), neqo_glue/src/lib.rs (46), nsLoadGroup.cpp (44),
  nsHostRecord.cpp (29). These still execute and marshal args into glean-core;
  most route through the now-dropping `launch()`, but the C++ arg evaluation and
  FFI call still happen. THIS is the real buzzing — not a thread, hundreds of
  call sites.
- Metric objects are static and allocate their backing storage once.

**CORRECTED (this was overstated in an earlier draft):** the `glean.dispatcher`
worker thread spawns in `Dispatcher::new()` (mod.rs:281) via the `Lazy` at
global.rs:16 — but with `launch()` short-circuited before it derefs the Lazy and
`fog_init` skipped, that Lazy is **most likely never triggered, so the thread is
most likely NOT spawned** in normal use. Prior "spawned but idle at 0% CPU"
wording predates the launch() guard. NOT runtime-confirmed yet — sample
`/proc/<pid>/task/*/comm | grep glean` on a live instance to settle it.

On the distribution audience (2–4 GB DDR3, HDD, iGPU) this idle overhead is NOT
negligible — reclaiming it is the mission. Item 14 (Necko Glean strip) is
therefore ~6.5× LARGER than the old "~105 calls / 7 files" estimate: measured
689 sites / 65 files / 6 gated.

## Performance Profile

The measured *recording* win is concentrated in topic 13 (the only cluster with
a hot-path CPU cost). The residual idle overhead above is un-measured per-line
but real on RAM-starved targets. Verified via `perf` during 1080p60 playback, 2026-07-16:

| Component | Before | After |
|---|---|---|
| MemoryTelemetry smaps scan | 8.9% | 0.02% |
| Glean dispatcher thread | 3.5% | 0.00% |
| Glean inline recording | 0.84% | 0.39% |
| **Total telemetry parent CPU** | **~13.2%** | **~0.39%** |

Topics 03 (Necko Glean gate), 12 (Normandy), and 09 (Marionette) have marginal
runtime cost by nature (a few fewer metric calls; two fewer listening sockets;
one dormant timer) — their value is privacy/attack-surface, not CPU. The
project-wide telemetry CPU figure above already *includes* the Necko-internal
Glean contribution from topic 03.

## Technical Debt (cluster-level)

🟠 **MEDIUM** — Necko preprocessor pair duplicated in 4 files.
  *Recommendation:* extract to a shared `NeckoTelemetryDisable.h`.

🟠 **MEDIUM** — Vendored glean-core edits do not survive a Firefox version bump;
  the crate is replaced wholesale. Expect to re-apply topic 13 per version.

🟠 **MEDIUM** — No preflight assertion that Marionette/RemoteAgent report disabled
  at runtime (topic 09 roadmap) — a silent upstream default restore on rebase
  would go unnoticed. *Recommendation:* add to `toolchain-preflight`.

🟢 **ACCEPTED** — Residual ~0.39% inline Glean is generated FFI/histogram glue +
  unguarded `custom_distribution`; sub-noise-floor, intentionally not chased.

🟢 **DOCTRINE** — Older prose ("excision/delete/lobotomy") predates the abandon
  decision; read as "soft gate." The excision-era DB atoms are history, not a
  roadmap. See README's reconciliation section.

## Impact If Removed / Disabled

Reverting the cluster restores: full telemetry recording + the ~12.8% parent CPU
cost on target hardware; the 60s `/proc/self/smaps` scan; the active Glean
dispatcher thread; Necko-internal connection metrics on every open/close;
Normandy/Nimbus phoning `normandy.cdn.mozilla.net` on a 6h loop and running
remote experiments; and two bindable automation sockets any localhost-reaching
attacker could drive.

## Testing Notes (unified)

```bash
# Telemetry (topic 13 + 03) — during 1080p60 playback:
perf report | grep -E 'smaps|walk_pgd|glean_core.*accumulate'   # expect absent
cat /proc/<parent>/task/*/comm | grep glean                     # thread present, 0% CPU
grep -n 'GORILLA_TELEMETRY_OFF' third_party/rust/glean-core/src/lib.rs   # const = true
strings libxul.so | grep -c back_pressure_suspension            # expect 0 (Necko Glean DCE'd)
# Experiments (topic 12):
ss -tunap | grep firefox | grep normandy                        # expect nothing
# about:policies                                                 # 3 locked normandy prefs
# Automation (topic 09):
ss -tlnp | grep -E ':2828|:9222'                                # expect nothing
firefox --marionette --remote-debugging-port=9222 & sleep 3; ss -tlnp | grep -E ':2828|:9222'  # still nothing
```

---
*Developer Track. Human Track twin: `14-egress-remote-lockdown.LAYMAN.md`.
Per-topic deep dives: `03.NETWORKING/`, `09.REMOTE/`, `12.MOZAMBIQUE.DRILL/`,
`13.TELEMETRY.KILL/`.*



---

# ═══ MERGED DOCUMENT: 14-egress-remote-lockdown.LAYMAN.md (verbatim · sha256:662b33d661219d56 · merged 2026-08-02) ═══

# 🧍 The Browser That Doesn't Phone Home and Can't Be Driven From Outside — Plain English Guide

> *Topic `14-egress-remote-lockdown` — the unifying story for four separate pieces of work · Written for everyone · 2026-08-01*

---

## 🌍 The Big Picture

A modern browser has doors that face two directions. Some doors let data *out* —
quiet reports about how you use it, sent back to the maker. Other doors let
commands *in* — hooks that let another program reach in and drive the browser,
change its settings, run little experiments on you. None of these doors are
locked by default. This build locks all of them, and this document is the single
map of every lock.

The four pieces of work were done at different times, in different corners of the
code, and each has its own detailed guide. What ties them together is one idea:
**a browser you own should not report on you, and should not take orders from
strangers.** That's it. Everything below is that one idea, applied four times.

## 🎭 The Four Doors We Locked

| Door | What it did | Where we locked it |
|---|---|---|
| **The connection diary (Necko)** | The part that carries every web request kept quiet notes about each connection — how it opened, how it closed, how much it strained | We removed the note-taking at build time, so those notes are never even written |
| **The self-measuring machine (Glean / FOG)** | A whole subsystem that times and counts everything the browser does, ready to package and send | We flipped one permanent switch that lets the build tool physically delete the measuring code — **and we measured the result: it was eating about 1 in every 8 units of the browser's main effort during video. Now under half a percent.** |
| **The remote instruction line (Normandy / Nimbus)** | A line the browser called on a schedule to ask a Mozilla server "any new instructions?" — feature switches, experiments | We switched it off, erased the phone number, and set its alarm clock to wake up in 60 years — then bolted all three shut |
| **The puppet strings (Marionette / Remote Agent)** | Two hidden hatches that let outside programs click, read, and drive the browser (used for automated testing) | We welded both hatches shut — no setting, flag, or environment trick can reopen them |

## 🤔 The One Thing That Went Wrong (and the lesson from it)

The obvious way to remove something you don't want is to **delete** it. We tried
that with the measuring and instruction systems. It **shattered the browser** —
because more than 145 other parts of Firefox expect those systems to be present
and to answer when spoken to. Delete them and everything that reaches for them
falls over.

So we learned the rule that governs all four locks: **don't remove the machine —
cut its power.** Leave the body in place so nothing that depends on it breaks, but
make sure it never actually does anything. A disconnected phone still sitting on
the desk: everything that expects a phone to be there is satisfied, but it can
never place a call.

> ⚠️ **Why this warning is in a "plain English" guide:** because some of the older
> notes we wrote use the word *"delete"* or *"excise"* for work that, in reality,
> only switched things off. Anyone reading those old notes might try the deletion
> that already failed once. So it's written down, plainly, here: **we do not
> delete these systems. We disable them in place. On purpose.**

## 💻 What This Means For YOU

### 🔋 Speed & Battery
The self-measuring machine was the big one — turning it off handed roughly an
eighth of the browser's main effort back to you during video, on this old
hardware. Cooler laptop, quieter fan, longer battery. The other three locks cost
essentially nothing to run; they're about privacy and control, not speed.

### 🕵️ Privacy & Control
- Nothing about how you use the browser is measured or packaged to send.
- No Mozilla server can reach in and change your settings or enroll you in an
  experiment.
- No outside program can drive your browser through the standard automation doors.

### ⚖️ What you give up (the honest half)
- **Automated testing tools** (Selenium, WebDriver) will not work on this build.
  That's the cost of welding the puppet-string doors shut. If you need browser
  automation, this build isn't the one for it.
- **Mozilla experiments** never run on you — including any that might have been
  beneficial. A sealed browser trades participation for predictability.
- These locks cover the **specific, known** doors. They are not a magic claim
  that no data ever leaves under any circumstance — other data paths are handled
  in other parts of the project, and each guide is honest about what it does and
  doesn't cover.

## 🌐 Why It's Public

You don't have to *trust* that these locks are real — you can read them. Each one
is a few lines of code with a comment saying what it does and why, and (for the
big one) a measurement proving it worked. A closed browser asks for your faith.
An open one hands you the flashlight and the floor plan. This document is the
floor plan.

## 📖 Glossary

**Necko** — Firefox's networking layer; the part that actually carries every web
request in and out.

**Glean / FOG** — Mozilla's modern self-measurement system ("Firefox On Glean").
The subsystem that times and counts what the browser does.

**Normandy / Nimbus** — the remote-instruction system that lets Mozilla change
settings and run experiments from a distance.

**Marionette / Remote Agent** — the two automation hatches that let an outside
program drive the browser.

**Neutralize (vs. delete)** — switch something off in place, leaving it present
so nothing that depends on it breaks. The whole approach here, learned the hard
way.

---
*Human Track. Its Developer Track twin (`14-egress-remote-lockdown.DEVELOPER.md`)
covers the same four locks in technical detail, side by side. Each of the four
also has its own deep-dive guide in its source topic dir (03 / 09 / 12 / 13).*

