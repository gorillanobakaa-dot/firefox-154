# Mozambique Drill — Normandy/Nimbus Three-Layer Neutralization with policies.json Hard-Lock — Developer Track

> **Topic:** `12-mozambique-drill` · **Files:** `toolkit/components/normandy/lib/RecipeRunner.sys.mjs`, `toolkit/components/nimbus/lib/RemoteSettingsExperimentLoader.sys.mjs`, `NEW_FILES/policies.json`
> **Generated:** 2026-07-17

---

## Module Summary

Four redundant layers: (1) app.normandy.enabled=false at Topic 05 firefox.js; (2) app.normandy.api_url=empty — endpoint erased; (3) internal poll timers in RecipeRunner + RemoteSettingsExperimentLoader dilated to 1893456000 s (~60 years) — threads exist and objects satisfy the 145+ dependent components, no network fires; (4) policies.json hard-locks the prefs. Coherent with Topics 09 and 13 — same 'keep the corpse standing so dependents do not crash' methodology. Applied because a delete-then-fix approach previously triggered a documented cascade of 145+ TypeError: ExperimentAPI is undefined failures.

## Architecture

- **Pattern:** Four-layer redundant neutralization + shape-preservation for 145+ dependent components.
- **Trust Boundary:** Closes the *targeting* boundary — Mozilla can no longer reach in via Normandy/Nimbus experiment channels. Complements Topic 13's cutting of the *reporting* channel.
- **Attack Surface:** Removes a class of supply-chain-style attack (compromised RemoteSettings endpoint pushing a malicious 'experiment').
- **Dependencies:** `policies.json parsing (enterprise policy engine)`, `Depends on Topic 05 setting the prefs`

## Kill Switches

### `RecipeRunner.sys.mjs — Normandy poll interval` — RUNTIME_GUARD ⚠️

- **Condition:** always at scheduler init
- **Effect:** Poll interval set to 1893456000 seconds (~60 years). Object exists — no callout within any reasonable lifespan.
- **Reversibility:** reversible
- **Notes:** Rebuild to reverse.

### `RemoteSettingsExperimentLoader.sys.mjs — Nimbus poll interval` — RUNTIME_GUARD ⚠️

- **Condition:** always
- **Effect:** Same 60-year dilation for Nimbus.
- **Reversibility:** reversible
- **Notes:** Rebuild to reverse.

### `Topic 05 firefox.js — app.normandy.enabled=false + api_url=empty` — HARD ⚠️

- **Condition:** compile-time default
- **Effect:** Two-of-two shots to the chest.
- **Reversibility:** reversible
- **Notes:** Can be overridden by user.js — which does not — but not by policies.json (which reinforces).

### `NEW_FILES/policies.json — hard lock` — HARD ⚠️

- **Condition:** runtime enterprise-policy read
- **Effect:** Prefs above are locked; about:config edits silently ignored.
- **Reversibility:** reversible
- **Notes:** The layer that makes the entire drill override-proof.

## Performance Profile

- **CPU:** Startup slightly faster; steady-state slightly lower.
- **Memory:** Marginal — dead threads still hold a stack.
- **I/O:** One fewer daily background connection to Mozilla RemoteSettings.
- **Timer Interval:** Both polls: 1893456000 s (~60 years).

## Security Analysis

### User Profiling

Complements Topic 13 — closes the targeting channel Topic 13 alone would not close.

### Targeting

Substantially reduced: Mozilla cannot A/B-test or push targeted experiments.

### Trust Chain

Reduces trust dependency on Mozilla-controlled RemoteSettings endpoint.

### Abuse Potential

Removes a documented supply-chain attack path.

## Implementation Flow

1. **`RecipeRunner init`** — Interval constant patched to 1893456000.
   *Side effects:* Poll thread never fires within useful lifespan.
2. **`RemoteSettingsExperimentLoader init`** — Same dilation.
   *Side effects:* Nimbus loader inert.
3. **`libpref reads policies.json at profile init`** — Locked prefs applied over user.js.
   *Side effects:* app.normandy.* cannot be flipped from about:config.

## Technical Debt

🟡 **LOW** — 1893456000 is a magic number without an in-code comment
  - *Recommendation:* Extract to kMozambiqueDrill60YearsInSeconds with a comment.

🟡 **LOW** — policies.json layer requires MOZ_HAS_ENTERPRISE_POLICIES
  - *Recommendation:* Build-time assertion to catch silent degradation.

## Impact If Removed / Disabled

Reverting: Mozilla regains the ability to remote-control this browser via Normandy/Nimbus experiment infrastructure.

## Testing Notes

about:policies -> confirm Normandy prefs hard-locked. about:config -> try to set app.normandy.enabled=true -> silently ignored. about:studies -> empty. Startup must NOT crash.

## Changelog Notes

Prior delete-then-fix attempt documented — cascade of TypeError: ExperimentAPI is undefined during boot. Sibling patterns: Topic 09, Topic 13.

---
*Developer Track. Human Track twin: `12-mozambique-drill.LAYMAN.md`.*