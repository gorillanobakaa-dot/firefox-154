# 06.QUOTA — Master Project Log

*Created 2026-08-02 by consolidating this folder's documentation set (merged verbatim below). Policy: one master project log per folder.*


---

# ═══ CONSOLIDATION 2026-08-02 — side documents merged VERBATIM below; originals deleted (recoverable: merged-docs-backup-2026-08-02.tar.gz + git history) ═══


---

# ═══ MERGED DOCUMENT: 06-quota.AUDIT.md (verbatim · sha256:f7f8855297d54286 · merged 2026-08-02) ═══

# IBM-Style Audit Report: 06-quota

## SECTION A: DOCUMENT CONTROL

| Attribute | Value |
|---|---|
| **Target Category** | 06-quota |
| **Files Scanned** | see payload |
| **Baseline** | Firefox 154 (mozilla-central) |
| **Date / Time** | 2026-07-16 22:41:22 |
| **Audit Status** | PASS |

## SECTION B: EXECUTIVE SUMMARY (Track A — Layman)

Three small correctness fixes in one file: whitelist Firefox's own about:home page from the storage-permission prompt; enable a console diagnostic on this build's channel; remove a stale shutdown cleanup that no longer needs to run. Not exciting. Correct.

## SECTION C: TECHNICAL SUMMARY (Track B — Developer)

ActorsParent.cpp: adds kAboutHomeOriginPrefix and whitelists it in the first-quota-prompt bypass; swaps NIGHTLY_BUILD for EARLY_BETA_OR_EARLIER in a console-diagnostic gate; deletes a redundant mOriginToStorageOriginMap/mStorageOriginToOriginMap clear from temporary-storage shutdown.

## SECTION D: DETECTED DEFECTS

*No defects detected by rules or model.*

## SECTION E: PRODUCTION READINESS ASSESSMENT

- **Overall readiness:** 🟢 95%
- **Done:**
  - [x] about:home storage-prompt bypass in place
  - [x] Diagnostic gate widened to EARLY_BETA_OR_EARLIER
  - [x] Stale origin-map clear removed

## POSITIVE OBSERVATIONS

- ✅ Small and correct — the kind of patch that catches issues without introducing new ones.
- ✅ The stale-clear removal is a quiet win only careful review turns up.

## VERIFICATION COMMANDS

```bash
grep -n 'kAboutHomeOriginPrefix' dom/quota/ActorsParent.cpp
grep -n 'EARLY_BETA_OR_EARLIER' dom/quota/ActorsParent.cpp
```



---

# ═══ MERGED DOCUMENT: 06-quota.DEVELOPER.md (verbatim · sha256:1c6fdd7854bd7c2c · merged 2026-08-02) ═══

# Quota Manager — About:home Origin Whitelist + Build-Channel Gate + Origin-Map Cleanup — Developer Track

> **Topic:** `06-quota` · **Files:** `dom/quota/ActorsParent.cpp`
> **Generated:** 2026-07-16

---

## Module Summary

Three surgical corrections to the quota-manager parent actor: (1) adds `kAboutHomeOriginPrefix = "moz-safe-about:home"` and whitelists it in the first-quota-prompt bypass alongside chrome:// and resource://; (2) changes a console-diagnostic build gate from `NIGHTLY_BUILD || DEBUG` to `EARLY_BETA_OR_EARLIER || DEBUG` so the message appears on this build's channel; (3) removes a redundant clear of `mOriginToStorageOriginMap` / `mStorageOriginToOriginMap` during temporary-storage shutdown — those maps are managed elsewhere and the clear was a stale-mutex-hold hazard.

## Architecture

- **Pattern:** Point fixes — no shared theme.
- **Trust Boundary:** moz-safe-about:home whitelist change is safe: that URL is served by Firefox itself.
- **Attack Surface:** N/A

## Kill Switches

### `ActorsParent.cpp — origin whitelist StringBeginsWith checks` — HARD ⚠️

- **Condition:** always
- **Effect:** moz-safe-about:home no longer triggers the first-quota-prompt.
- **Reversibility:** reversible
- **Notes:** Trivially reversible — delete the added StringBeginsWith line.

### `ActorsParent.cpp — EARLY_BETA_OR_EARLIER gate` — HARD ⚠️

- **Condition:** compile-time
- **Effect:** Console diagnostic reachable on this build's channel.
- **Reversibility:** reversible
- **Notes:** One-line preprocessor swap.

### `ActorsParent.cpp — origin-map clear removal` — HARD ⚠️

- **Condition:** compile-time (dead code deletion)
- **Effect:** Redundant clear-under-mutex removed.
- **Reversibility:** reversible
- **Notes:** Diff removes 6 lines including the MutexAutoLock scope.

## Performance Profile

- **CPU:** Marginal — one fewer mutex acquisition on shutdown.
- **Memory:** No change.
- **I/O:** No change.
- **Timer Interval:** N/A

## Security Analysis

### User Profiling

N/A

### Targeting

N/A

### Trust Chain

Whitelisting moz-safe-about:home is safe.

### Abuse Potential

N/A

## Implementation Flow

1. **`IsFirstOriginQuotaPromptRequired (predicate)`** — Now returns true (bypass) for moz-safe-about:home in addition to chrome:// and resource://.
   *Side effects:* No prompt on first about:home storage request.

## Technical Debt

🟡 **LOW** — The three fixes are unrelated — folder is a catch-all
  - *Recommendation:* Merge into a broader category on next re-org.

## Impact If Removed / Disabled

First about:home visit prompts for storage; diagnostic misses this build channel; shutdown does a stale mutex-guarded clear.

## Testing Notes

Visit about:home on a fresh profile — expect NO storage prompt.

## Changelog Notes

Three-change surgical patch. Small folder.

---
*Developer Track. Human Track twin: `06-quota.LAYMAN.md`.*


---

# ═══ MERGED DOCUMENT: 06-quota.LAYMAN.md (verbatim · sha256:a72f557be198f95d · merged 2026-08-02) ═══

# 🧍 The Quota Housekeeping — Three Small But Correct Fixes — Plain English Guide

> *Topic `06-quota` of the Gorilla Unleashed Firefox 154 build · Written for everyone · 2026-07-16*

---

## 🌍 The Big Picture

This folder contains one file (`ActorsParent.cpp`) with three small changes to Firefox's storage-quota system. This is the code that decides how much disk space a website is allowed to use for things like IndexedDB, cache, and downloaded assets. The changes are surgical, and none of them are dramatic — but each one fixes a real, small correctness issue: making `about:home` not pop up a storage-permission prompt for the user's own homepage; changing which build channel prints diagnostic console messages; and removing a stale cleanup step for private-browsing origins that no longer needs to run.

This is the shortest topic in the whole build. It fits on one screen.

## 🎭 The Main Characters

| Name | What It Is | Real-World Comparison |
|---|---|---|
| **Quota Manager** | The subsystem that decides how much disk each website can use | The building super who allocates storage lockers |
| **about:home** | Firefox's own homepage / new-tab page | The front lobby of the building — it's the browser's own room, not a tenant |
| **Origin whitelist** | A short list of URLs Firefox treats as its own rather than as external websites | The staff-only door codes |

## 🔢 How It Works — Step by Step

### Step 1: Whitelist about:home for storage prompts

Firefox pops up a 'this site wants to store data' prompt on the first request. That prompt should never appear for the browser's own homepage — it's not a website, it's part of Firefox. A new constant `kAboutHomeOriginPrefix = "moz-safe-about:home"` is added to the prompt-bypass list alongside chrome:// and resource://.

### Step 2: Widen the console-log build gate

A diagnostic that used to only print on Nightly builds now prints on 'EARLY_BETA_OR_EARLIER' — which includes our build. Small change; the diagnostic is now visible in the console.

### Step 3: Remove a stale private-browsing origin-map clear

A block that used to clear a pair of maps during quota shutdown is deleted. Those maps are managed elsewhere; the clear was redundant and, on some paths, held a mutex that was already contested. Deletion, not disable — the code path no longer needs it.

## 🤔 Quirky Things Worth Knowing

### ⚠️ This is what a healthy patch looks like — small, boring, correct

Big flashy fixes get attention. Three-line correctness fixes like this one keep the build boring, which is exactly what we want. The whole folder is 20 lines of diff.

## 💻 What Does This Mean For YOU?

### 🔋 Battery, Speed & Memory

Negligible. One fewer prompt on first about:home visit; one dead code path removed.

### ⚡ Speed

Marginal.

### 🕵️ Your Privacy

Same as before — quota housekeeping, not a policy change.

### 🌐 Your Internet

Zero change.

## 🔴 The Kill Switch — Explained

**What it is:** None — these are point corrections, not toggleable behaviour.

**Without it:** First about:home visit prompts you to allow storage; console misses a diagnostic; shutdown does a redundant mutex-guarded clear.

**Think of it like:** Not a switch — three fresh screws where three worn ones used to be.

## 🌐 Open Source & Why It Matters To You

You can see every line. Three changes; the whole patch fits on one screen.

## 📖 Glossary (Plain English Dictionary)

**Quota Manager** — The Firefox subsystem that tracks and enforces per-origin disk-space limits for storage APIs.

**Origin** — A website's identity — protocol + host + port.

**moz-safe-about:** — Internal URL prefix Firefox uses for its own privileged 'about:' pages.

---
*Human Track. Its Developer Track twin (`06-quota.DEVELOPER.md`) covers the same changes in technical detail. Neither is a simplified copy of the other — they are the same truth in two languages.*


---

# ═══ MERGED DOCUMENT: 06-quota.PRECHECK.json (verbatim · sha256:4f53cda18c2baa0c · merged 2026-08-02) ═══

```json
[]
```


---

# ═══ MERGED DOCUMENT: 06-quota.PRECHECK.md (verbatim · sha256:e8fa338d705b3b07 · merged 2026-08-02) ═══

# Offline Pre-Check: 06-quota

*Generated 2026-07-16 22:41:22 by doc_audit.py (rule-based, no model involved).*

## File Inventory

| File | Lang | Lines | Complexity | SHA256 (16) |
|---|---|---|---|---|
| dom_quota_ActorsParent.cpp.patch | patch | 42 | 7 | `2814f13dbeb54536` |

## Rule Findings (0)

*All offline rules passed.*
