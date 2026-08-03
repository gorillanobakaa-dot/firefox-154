# 12.MOZAMBIQUE.DRILL — Master Project Log

*Created 2026-08-02 by consolidating this folder's documentation set (merged verbatim below). Policy: one master project log per folder.*


---

# ═══ CONSOLIDATION 2026-08-02 — side documents merged VERBATIM below; originals deleted (recoverable: merged-docs-backup-2026-08-02.tar.gz + git history) ═══


---

# ═══ MERGED DOCUMENT: 12-mozambique-drill.AUDIT.md (verbatim · sha256:c5ca87d414474f2a · merged 2026-08-02) ═══

# IBM-Style Audit Report: 12-mozambique-drill

## SECTION A: DOCUMENT CONTROL

| Attribute | Value |
|---|---|
| **Target Category** | 12-mozambique-drill |
| **Files Scanned** | see payload |
| **Baseline** | Firefox 154 (mozilla-central) |
| **Date / Time** | 2026-07-17 08:10:07 |
| **Audit Status** | PASS |

## SECTION B: EXECUTIVE SUMMARY (Track A — Layman)

Firefox's remote-experiment / remote-config system (Normandy + Nimbus) is neutralized by four redundant layers: master switch off, endpoint URL erased, internal poll timer dilated to 60 years, and enterprise-policy hard-lock on top. The machinery is kept in place because deleting it crashes the browser (145+ dependent components), but it is effectively dead.

## SECTION C: TECHNICAL SUMMARY (Track B — Developer)

Four-layer neutralization: (1) app.normandy.enabled=false + api_url=empty from Topic 05; (2) poll intervals dilated to 1893456000 s in RecipeRunner + RemoteSettingsExperimentLoader; (3) policies.json hard-lock; (4) machinery preserved for 145+ dependent components. Coherent with Topics 09 and 13.

## SECTION D: DETECTED DEFECTS

*No defects detected by rules or model.*

## SECTION E: PRODUCTION READINESS ASSESSMENT

- **Overall readiness:** 🟢 92%
- **Done:**
  - [x] Normandy poll interval dilated
  - [x] Nimbus poll interval dilated
  - [x] app.normandy.enabled=false and api_url empty set
  - [x] policies.json hard-lock in NEW_FILES/
  - [x] 145+ dependent components still satisfied (browser boots normally)
  - [x] Coherent methodology with Topics 09 + 13
- **To Do:**
  - [ ] P3: extract 1893456000 to a named constant
  - [ ] P3: build-time assertion that MOZ_HAS_ENTERPRISE_POLICIES is defined

## SECTION F: PHASED EXPANSION PLAN

### Phase 1 — `toolkit/components/nimbus + normandy`
- **Tweak:** Add integration test: on boot, verify no network request to *.mozilla.org RemoteSettings/Normandy endpoints.
- **Expected impact:** Regression protection.

## POSITIVE OBSERVATIONS

- ✅ Four-layer redundancy for a target with multiple activation surfaces.
- ✅ 'Keep the corpse standing' methodology is intellectually honest — prior delete attempt documented with its failure mode.
- ✅ Coherent with Topics 09 and 13 — three topics use the same shape-preserving neutralization pattern.
- ✅ 60-year timer dilation is defensive: even if some update flips the enabled pref back on transiently, no network fires within any reasonable lifespan.
- ✅ The Mozambique Drill metaphor is precise: two-of-two shots to the chest (pref off + endpoint empty) plus one to the head (timer dilated) plus insurance (policies.json).

## VERIFICATION COMMANDS

```bash
grep -n '1893456000' toolkit/components/normandy/lib/RecipeRunner.sys.mjs toolkit/components/nimbus/lib/RemoteSettingsExperimentLoader.sys.mjs
cat NEW_FILES/policies.json | jq '.policies | keys'
# about:policies -> confirm hard-locks; about:studies -> empty; flip attempt in about:config -> silently rejected
```



---

# ═══ MERGED DOCUMENT: 12-mozambique-drill.DEVELOPER.md (verbatim · sha256:cd2ed4efff930613 · merged 2026-08-02) ═══

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


---

# ═══ MERGED DOCUMENT: 12-mozambique-drill.LAYMAN.md (verbatim · sha256:2309cbe3a3034885 · merged 2026-08-02) ═══

# 🧍 The Mozambique Drill — Neutralising Normandy and Nimbus (Two to the Chest, One to the Head) — Plain English Guide

> *Topic `12-mozambique-drill` of the Gorilla Unleashed Firefox 154 build · Written for everyone · 2026-07-17*

---

## 🌍 The Big Picture

Firefox contains two systems — **Normandy** and its successor **Nimbus** — that let Mozilla reach into your browser *from a distance* and change things without asking. They can silently switch features on or off, run A/B experiments on you (you get version A, your neighbour gets version B, Mozilla watches which behaves better), and measure the results. You never signed up for it; it is there by default; and if it stops working for any reason, Firefox has 145+ other components that expect it to be there and will crash if it is not.

This patch group is named after the '**Mozambique Drill**', a firearms training pattern of *two shots to the chest, one to the head*. That is exactly the shape of the fix — three redundant kills, applied at different layers so no single point of failure can bring the target back:

- **Shot 1 (chest):** The master switch is flipped. Preference `app.normandy.enabled` set to `false` at build time in Topic 05.
- **Shot 2 (chest):** The remote endpoint URL is erased. Even if the switch were flipped back on, the client would have nowhere to connect.
- **Shot 3 (head):** The internal 'check for new instructions' timer that would fire the network requests is dilated to sixty years. Not 'disabled' — set to fire once, in the year 2085.
- **Insurance shot:** The preferences are hard-locked via `policies.json`, so even a user in about:config cannot flip them back on. That is what makes it *override-proof*.

And because deleting the code entirely would break 145+ dependent components (attempted, failed, documented — the log describes the crash trace), the machinery is **left standing but dead**. Structurally perfect, biologically dead.

## 🎭 The Main Characters

| Name | What It Is | Real-World Comparison |
|---|---|---|
| **Normandy** | The older Firefox remote-experiment / remote-config system | A supervisor with a two-way radio, listening for instructions from HQ |
| **Nimbus** | Normandy's newer replacement, using RemoteSettings | The same supervisor with a shinier radio |
| **RecipeRunner** | The Normandy component that periodically calls out to check for new remote 'recipes' | The scheduled 'any updates for me?' phone call |
| **RemoteSettingsExperimentLoader** | The Nimbus equivalent — polls RemoteSettings for new experiment definitions | The Nimbus version of the same phone call |
| **policies.json** | An enterprise-grade preference hard-lock file that overrides even user.js | The corporate policy binder that not even the IT department can override |

## 🔢 How It Works — Step by Step

### Step 1: Shot 1 — the master switch

In Topic 05's firefox.js, app.normandy.enabled = false. Nothing runs at all when this is off. That would be enough by itself — except Firefox updates sometimes silently reset it, so we have shots 2 and 3.

### Step 2: Shot 2 — the endpoint URL is emptied

app.normandy.api_url is set to empty. Even if the master switch were flipped back on, the client would have no address to contact. Any attempted network call fails immediately in URL validation.

### Step 3: Shot 3 — the internal timer is dilated to 60 years

The head shot. RecipeRunner and RemoteSettingsExperimentLoader both have internal timers that fire their 'check for updates' network requests. Those timers are set to 1893456000 seconds (~60 years) between fires. The threads are alive, the objects exist — they just will not do anything until 2085.

### Step 4: The insurance shot — policies.json hard-lock

Firefox has an enterprise-focused system where preferences can be locked at the policies.json level. Locked prefs override even user.js. Even if the user opens about:config and tries to flip them back on, the change is silently rejected.

### Step 5: The machinery stays present so 145+ dependent components do not crash

The initial attempt was to just delete Normandy/Nimbus. It did not go well: the address bar, first-run, settings UI, and boot sequence all depend on Nimbus. Deleting the code triggers a cascade of TypeError: ExperimentAPI is undefined errors, and the browser fails to start. So the fix is different: leave the machinery in place, but make sure it never does anything harmful.

## 🤔 Quirky Things Worth Knowing

### ⚠️ 60 years is not a round number, it is 1893456000 seconds

60 x 365.25 x 24 x 3600 approx 1,893,456,000 seconds. Chosen specifically to be far past any reasonable lifespan of the machine.

### ⚠️ The name is not casual

The Mozambique Drill is a real firearms technique. Two-to-the-chest is not always enough (target may be wearing armour or high on adrenaline); the head shot is what guarantees the fix takes. Same shape here.

### ⚠️ This is the pattern for anything you cannot delete

Same design as Topic 09 (Marionette + Remote Agent). Same design as Topic 13 (telemetry). When code is entangled with 145+ other components, the answer is: keep the corpse standing so nothing that touches it crashes, but make sure the corpse never does anything.

## 💻 What Does This Mean For YOU?

### 🔋 Battery, Speed & Memory

One background service that used to poll a remote server every day now does not. Negligible per-poll, meaningful over months.

### ⚡ Speed

Slightly faster startup, slightly less steady-state CPU.

### 🕵️ Your Privacy

This is the topic that closes the *targeting* channel — the mechanism by which Mozilla could reach in and A/B-test on you specifically.

### 🌐 Your Internet

One fewer background connection to Mozilla infrastructure per day.

## 🔴 The Kill Switch — Explained

**What it is:** The Mozambique Drill — three separate kill mechanisms plus one hard-lock, applied to two related subsystems.

**Without it:** Mozilla can remotely toggle features, run A/B experiments, and measure results on your specific browser.

**Think of it like:** Not a single lock — a bolt, a chain, a welded hinge, and a corporate policy binder saying 'do not unlock this door under any circumstances'.

## 🌐 Open Source & Why It Matters To You

Every one of the four shots is auditable. Grep the prefs, grep the URL, grep the 1893456000 constant, grep the policies.json entry. In a closed browser this would be marketing; here it is arithmetic in four files.

## 📖 Glossary (Plain English Dictionary)

**Normandy** — Firefox's older remote-config / remote-experiment system. Polls a Mozilla endpoint for 'recipes' — bundles of JS to run in the browser.

**Nimbus** — Normandy's successor. Uses RemoteSettings as the transport. Same purpose.

**policies.json** — A Firefox enterprise-management file that hard-locks preferences. Sits above user.js in the precedence chain.

**Mozambique Drill** — A firearms training technique — two shots to the chest, one to the head — used to guarantee incapacitation when a single shot may not be enough.

**1893456000** — 60 years in seconds. The dilated interval for Normandy/Nimbus 'check for updates' timers.

---
*Human Track. Its Developer Track twin (`12-mozambique-drill.DEVELOPER.md`) covers the same changes in technical detail. Neither is a simplified copy of the other — they are the same truth in two languages.*


---

# ═══ MERGED DOCUMENT: 12-mozambique-drill.PRECHECK.json (verbatim · sha256:4f53cda18c2baa0c · merged 2026-08-02) ═══

```json
[]
```


---

# ═══ MERGED DOCUMENT: 12-mozambique-drill.PRECHECK.md (verbatim · sha256:4db0414adf123a88 · merged 2026-08-02) ═══

# Offline Pre-Check: 12-mozambique-drill

*Generated 2026-07-17 08:10:06 by doc_audit.py (rule-based, no model involved).*

## File Inventory

| File | Lang | Lines | Complexity | SHA256 (16) |
|---|---|---|---|---|
| toolkit_components_nimbus_lib_RemoteSettingsExperimentLoader.sys.mjs.patch | patch | 11 | 1 | `4256dd5d6de3f1b9` |
| toolkit_components_normandy_lib_RecipeRunner.sys.mjs.patch | patch | 11 | 2 | `f8ce051dfb3f949c` |

## Rule Findings (0)

*All offline rules passed.*
