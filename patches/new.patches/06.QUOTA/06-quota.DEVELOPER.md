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