# MASTER PROJECT LOG — FIREFOX 154 TOOLKIT PATCHES

---

## Part 1: History, Roadmap & Overview
*(Originally from 00_TOOLKIT_HISTORY_AND_ROADMAP.md)*

### Document Control
- **Category:** Toolkit Lockdown & UI Modifications
- **Last Updated:** 2026-07-10
- **Status:** Active Development
- **Verification Required:** Yes (see Validation section)
- **Related Documents:** 
  - `../DOCUMENTATION_TEMPLATES.md` (IBM format guide)
  - `../MAP.md` (cross-category index)
  - `../08.Look/00_LOOK_HISTORY_AND_ROADMAP.md` (visual branding)
  - `../10.OVERRIDES/user.js` (preference layer)
  - `../12.MOZAMBIQUE.DRILL/policies.json` (locked preferences)

---

### Executive Summary

**What This Does (Plain Language):**
This folder makes Firefox a sealed, opinionated appliance. Four main changes:
1. **Blocks all add-on/extension/theme installations** (security hardening).
2. **Disables translations and language packs** (monolinguality).
3. **Removes sponsored content from new tab page** (clean interface).
4. **Forces Gorilla Nebula theme** (consistent appearance).

**Technical Summary:**
Toolkit lockdown layer for Sony VAIO SVE14A3AJ. Implements: (1) API lobotomy blocking all extension/theme install routes (AMO, web, file), (2) translation/langpack download disabled, (3) new-tab sponsored content excised (discovery feed, topsites, shortcuts), (4) forced Gorilla Nebula theme enforcement, (5) QuickSuggest/urlbar/context-menu locks.

**Critical Context:**
> **This is a sealed appliance.** You cannot install extensions or themes. No built-in translation. New-tab content and theme are not user-configurable. These are deliberate trade-offs for security and consistency.

---

### Mission Statement

### Mission: Sealed Appliance Philosophy
If other folders make the browser *fast* and *private*, this one makes it **sealed and opinionated**. The philosophy: a browser you can't extend is a browser strangers can't quietly extend either. A clean, ad-free, fixed surface is worth giving up configurability for.

1. **No Extensions/Themes** — Security over flexibility.
2. **Monolinguality** — Lean over multilingual.
3. **Clean New Tab** — Quiet over monetized.
4. **Fixed Appearance** — Consistent over customizable.

---

### Component Documentation

#### 1. AddonManager.sys.mjs & AddonRepository.sys.mjs — Installation Blocks
- **Status:** Modified | **Deploy Path:** `toolkit/mozapps/extensions/internal/` | **Last Verified:** 2026-07-10
- **What It Does (Plain Language):** Prevents installation of external add-ons, scripts, or extensions.
- **Technical Description:** Blocks AMO backend calls, web install interfaces, and raw file installs by throwing custom errors at the manager API layer.

#### 2. XPIInstall.sys.mjs — Installation Disabler
- **Status:** Modified | **Deploy Path:** `toolkit/mozapps/extensions/internal/XPIInstall.sys.mjs` | **Last Verified:** 2026-07-10
- **Tuning:** Short-circuits install paths to strictly abort with a block log, preventing side-loading.

#### 3. ExperimentAPI.sys.mjs — Study Bypass
- **Status:** Modified | **Deploy Path:** `toolkit/components/nimbus/lib/ExperimentAPI.sys.mjs` | **Last Verified:** 2026-07-10
- **Tuning:** Returns empty default mock objects for dynamic telemetry experiment queries to prevent runtime failures.

#### 4. TranslationsParent.sys.mjs — Translations Blocker
- **Status:** Modified | **Deploy Path:** `toolkit/components/translations/TranslationsParent.sys.mjs` | **Last Verified:** 2026-07-10
- **Tuning:** Prevents translation model engine downloads to force monolingual offline execution security.

---

### Chronological History (Recovered)

#### 2026-06-08/09
Initial toolkit lobotomy implementations applied in Firefox 153.

#### 2026-07-05
**Firefox 154 Rebase:**
Toolkit modules re-patched and adapted. Resolves conflicts in Javascript Modules (sys.mjs paths).

#### 2026-07-10
**Audit Verification:**
Completed static checks. Confirmed all `.rej` files are cleared, and the toolkit codebase is 100% stable.

---

## Part 2: Rule-Based Code Audit & Validation (2026-07-10)

We completed a static code audit of the toolkit patches:
1. **AddonManager**: Installation interface blocks verified.
2. **XPIInstall**: Side-load pathways correctly throw installation block overrides.
3. **ExperimentAPI**: Returns mock values safely without throwing runtime null pointer errors in the URL bar or setup sequence.

The category passes all code guidelines.


---

# ═══ CONSOLIDATION 2026-08-02 — side documents merged VERBATIM below; originals deleted (recoverable: merged-docs-backup-2026-08-02.tar.gz + git history) ═══


---

# ═══ MERGED DOCUMENT: 07-toolkit.AUDIT.md (verbatim · sha256:f456eff94db20146 · merged 2026-08-02) ═══

# IBM-Style Audit Report: 07-toolkit

## SECTION A: DOCUMENT CONTROL

| Attribute | Value |
|---|---|
| **Target Category** | 07-toolkit |
| **Files Scanned** | see payload |
| **Baseline** | Firefox 154 (mozilla-central) |
| **Date / Time** | 2026-07-17 08:13:33 |
| **Audit Status** | PASS |

## SECTION B: EXECUTIVE SUMMARY (Track A — Layman)

This folder turns Firefox into a sealed appliance: no add-ons or themes can be installed (every install route blocked), no sponsored content on the new tab or in the address bar, no built-in translation, and a fixed appearance. The security case is that a browser you cannot extend is a browser strangers cannot quietly extend either. The clever part: the experiment API that 145+ components depend on is made to return safe empty answers so nothing crashes while no experiment runs. Honest trade-off: you give up extensions, themes, and translation.

## SECTION C: TECHNICAL SUMMARY (Track B — Developer)

19-file sealed-appliance layer. Five workstreams: (1) install lockdown (AddonManager/AddonRepository throw at API boundary, XPIInstall short-circuits side-load, LightweightThemeManager locks theme); (2) new-tab sponsored-content excision (Base/DiscoveryStreamBase/TopSites React components); (3) address-bar de-sponsoring (QuickSuggest + 2 Urlbar providers + Merino Rust backend + search-config JSON, no keystroke egress); (4) translations disable (TranslationsParent + browserLanguages.js); (5) ExperimentAPI empty-mock for the 145+ Nimbus consumers — toolkit-side companion to Topic 12's network-side neutralization. Three neutralization strategies matched to three failure tolerances: fail-closed throw for installs, excision for UI, fail-safe mock for the experiment API.

## SECTION D: DETECTED DEFECTS

*No defects detected by rules or model.*

## SECTION E: PRODUCTION READINESS ASSESSMENT

- **Overall readiness:** 🟢 90%
- **Done:**
  - [x] All three extension install routes blocked (AMO, web, file/side-load)
  - [x] Theme locked (LightweightThemeManager + design-system tokens)
  - [x] New-tab discovery feed + sponsored tiles + sponsored shortcuts excised
  - [x] Address-bar QuickSuggest/Merino de-sponsored — keystrokes not sent remotely
  - [x] Translations + langpack downloads disabled
  - [x] ExperimentAPI returns safe empty mocks — 145+ consumers do not crash
  - [x] Coherent with Topic 12 (Nimbus network side) and Topic 05 (Pocket/TopSites prefs)
  - [x] FF154 rebase clean — all .rej cleared (2026-07-10 audit)
- **To Do:**
  - [ ] P2: revisit translations disable for the global distribution audience (roadmap-flagged; consider on-device models on a locked mirror)
  - [ ] P2: add a boot smoke-test asserting zero ExperimentAPI/Nimbus console errors across urlbar/first-run/settings
  - [ ] P3: consolidate the three install-throw sites behind one isInstallAllowed() policy gate

## SECTION F: PHASED EXPANSION PLAN

### Phase 0 — `toolkit/mozapps/extensions`
- **Tweak:** Introduce a single isInstallAllowed() returning false, called by all three throw sites. One-line-auditable install policy.
- **Expected impact:** Maintainability + audit clarity.

### Phase 2 — `toolkit/components/translations`
- **Tweak:** Allow on-device translation models fetched from a trusted, telemetry-free mirror while keeping Mozilla model-server + langpack download locked. Restores translation for the global audience without opening a telemetry channel.
- **Expected impact:** Addresses the one sealed-appliance choice that cuts against the target audience.

## POSITIVE OBSERVATIONS

- ✅ Three neutralization strategies matched to three failure tolerances (fail-closed throw for installs, excision for UI, fail-safe mock for ExperimentAPI) — the right tool per problem, not one blunt instrument.
- ✅ Blocking all three install routes (not just AMO) is thorough — the side-load block via XPIInstall is what stops OS-level malware dropping an XPI, which a store-only block would miss.
- ✅ ExperimentAPI empty-mock is the correct companion to Topic 12: Topic 12 cuts the network side (poll timers/endpoint), this cuts the code side (safe mocks). Neither alone is complete; together they are.
- ✅ Extension-install elimination is arguably the single largest attack-surface reduction in the whole build — compromised/malicious extensions are a top browser threat vector.
- ✅ The roadmap is honest about the translations trade-off cutting against the global audience — it does not pretend the sealed-appliance choice is free.

## VERIFICATION COMMANDS

```bash
# Install any extension from AMO -> blocked with error
# Drag an .xpi onto the browser -> refused (grep XPIInstall.sys.mjs for the block short-circuit)
grep -n 'ExperimentAPI\|getExperiment\|getVariable' toolkit/components/nimbus/ExperimentAPI.sys.mjs   # expect mock returns
# New tab -> no sponsored tiles / no discovery feed
# Network capture while typing in urlbar -> no request to merino.services.mozilla.com
# Boot + navigate urlbar/first-run/settings -> zero ExperimentAPI/Nimbus console errors
```



---

# ═══ MERGED DOCUMENT: 07-toolkit.DEVELOPER.md (verbatim · sha256:c042b2299385cba8 · merged 2026-08-02) ═══

# Toolkit Lockdown — Extension/Theme Install Block, Sponsored-Content Excision, Translations Disable, ExperimentAPI Mock — Developer Track

> **Topic:** `07-toolkit` · **Files:** `toolkit/mozapps/extensions/AddonManager.sys.mjs`, `toolkit/mozapps/extensions/internal/AddonRepository.sys.mjs`, `toolkit/mozapps/extensions/internal/XPIInstall.sys.mjs`, `toolkit/mozapps/extensions/LightweightThemeManager.sys.mjs`, `toolkit/components/nimbus/ExperimentAPI.sys.mjs`, `toolkit/components/translations/actors/TranslationsParent.sys.mjs`, `browser/components/urlbar/QuickSuggest.sys.mjs`, `browser/components/urlbar/UrlbarProviderQuickSuggest.sys.mjs`, `browser/components/urlbar/UrlbarProviderSearchSuggestions.sys.mjs`, `browser/extensions/newtab/content-src/components/{Base,DiscoveryStreamBase,TopSites}`, `browser/base/content/nsContextMenu.sys.mjs`, `browser/components/preferences/{config/appearance.mjs,dialogs/browserLanguages.js}`, `third_party/application-services/components/merino/src/lib.rs`, `services/settings/dumps/main/search-config-v2.json`, `toolkit/themes/shared/design-system/dist/{semantic-categories,tokens-table}.mjs`
> **Generated:** 2026-07-17

---

## Module Summary

Sealed-appliance layer across 19 files. Five workstreams: (1) extension/theme install lockdown — AddonManager/AddonRepository throw at the API layer, XPIInstall short-circuits the file/side-load route, LightweightThemeManager locks the theme; (2) sponsored-content excision — new-tab Base/DiscoveryStreamBase/TopSites React components strip the discovery feed + sponsored tiles/shortcuts; (3) address-bar de-sponsoring — QuickSuggest + two Urlbar providers + Merino Rust backend + search-config JSON stop remote/sponsored suggestions (no keystroke egress); (4) translations disable — TranslationsParent blocks model downloads, browserLanguages.js disables langpack UI; (5) ExperimentAPI returns empty default mocks for all Nimbus queries so the 145+ dependent components (urlbar, first-run, settings) never hit a null — the toolkit-side companion to Topic 12's network-side Mozambique Drill.

## Architecture

- **Pattern:** Throw-at-the-boundary for installs (fail-closed), component-level excision for UI content, shape-preserving mock for ExperimentAPI (fail-safe). Three different neutralization strategies matched to three different failure tolerances.
- **Trust Boundary:** Removes the entire extension attack surface (installs impossible), the sponsored-content egress surface (no impression counting, no keystroke-to-Merino), and the translation-model download surface. ExperimentAPI mock preserves the internal API contract while cutting the experiment channel.
- **Attack Surface:** Extension install is one of the largest browser attack surfaces (malicious/compromised add-ons). Blocking all install routes eliminates it wholesale. Side-load block also stops OS-level malware that drops an XPI into the profile.
- **Dependencies:** `Coherent with Topic 12 (Normandy/Nimbus) — ExperimentAPI mock here + poll-timer dilation there`, `Coherent with Topic 05 (Pocket/TopSites prefs off) — this enforces at the code layer what 05 sets at the pref layer`

## Kill Switches

### `AddonManager.sys.mjs + AddonRepository.sys.mjs — install API layer` — HARD ⚠️

- **Condition:** any install attempt (AMO or web)
- **Effect:** Throws a custom install-block error before any download/unpack. AMO backend calls and web-install interfaces refused.
- **Reversibility:** reversible
- **Notes:** Fail-closed: the default is refuse.

### `XPIInstall.sys.mjs — file/side-load route` — HARD ⚠️

- **Condition:** any .xpi install attempt
- **Effect:** Short-circuits to abort with a block log, preventing side-loading (including OS-malware-dropped XPIs).
- **Reversibility:** reversible
- **Notes:** Closes the route store-review would not catch.

### `LightweightThemeManager.sys.mjs + design-system tokens` — HARD ⚠️

- **Condition:** always
- **Effect:** Theme locked; cannot be swapped by user, extension, or remote config.
- **Reversibility:** reversible
- **Notes:** Appearance is fixed by design.

### `ExperimentAPI.sys.mjs — Nimbus query interface` — SOFT ⚠️

- **Condition:** any getExperiment/getVariable/onUpdate query
- **Effect:** Returns empty default mock objects instead of live experiment data. 145+ dependent components get a valid 'nothing' answer; no experiment executes.
- **Reversibility:** reversible
- **Notes:** Shape-preserving mock — the toolkit-side companion to Topic 12. Removing (rather than mocking) would recreate the TypeError: ExperimentAPI is undefined cascade.

### `TranslationsParent.sys.mjs + browserLanguages.js` — HARD ⚠️

- **Condition:** any translation-model/langpack fetch
- **Effect:** Model downloads blocked; monolingual/offline. Langpack download UI disabled.
- **Reversibility:** reversible
- **Notes:** Known trade-off — flagged in the roadmap as the sealed-appliance choice most worth revisiting for a global distribution audience.

### `QuickSuggest + Urlbar providers + Merino lib.rs + search-config JSON` — HARD ⚠️

- **Condition:** address-bar typing
- **Effect:** No sponsored or remotely-fetched suggestions; partial keystrokes not sent to Merino.
- **Reversibility:** reversible
- **Notes:** Privacy win — the urlbar stops being a keystroke-egress channel.

### `New-tab Base.jsx / DiscoveryStreamBase.jsx / TopSites.jsx` — HARD ⚠️

- **Condition:** new-tab render
- **Effect:** Discovery feed + sponsored tiles + sponsored shortcuts removed from the component tree.
- **Reversibility:** reversible
- **Notes:** Enforces at the code layer what Topic 05 sets at the pref layer (defence in depth).

## Performance Profile

- **CPU:** No add-on update-check threads; no new-tab sponsored-content fetch/render; no Merino round-trips. Not benchmarked topic-locally.
- **Memory:** Add-on subsystem still present (mocked/blocked) but does not load third-party extension code.
- **I/O:** Fewer background connections: no AMO pings, no Merino suggestion calls, no Pocket discovery feed, no translation-model downloads.
- **Timer Interval:** N/A

## Security Analysis

### User Profiling

Address-bar keystrokes no longer egress to Merino; new-tab impressions no longer counted; no add-on can read browsing data (none can install).

### Targeting

ExperimentAPI mock cuts the code-side experiment channel (complements Topic 12's network side).

### Trust Chain

Removing extension install removes trust dependency on AMO review, on extension signing, and on the user's judgement about what to install.

### Abuse Potential

Eliminates the compromised/malicious-extension attack class entirely — arguably the single largest reduction in attack surface in the whole build.

## Implementation Flow

1. **`AddonManager.installAddon / AddonRepository backend`** — Throws install-block error at the API boundary before any network/unpack.
   *Side effects:* Install UI surfaces an error; nothing is downloaded.
2. **`XPIInstall install pipeline`** — Short-circuits to abort with block log.
   *Side effects:* Side-load (including malware-dropped XPI) refused.
3. **`ExperimentAPI.getExperiment / getVariable / etc.`** — Returns empty default mock for every query.
   *Side effects:* 145+ dependent components receive a valid empty answer and proceed; no experiment runs.
4. **`TranslationsParent model-fetch path`** — Model download blocked.
   *Side effects:* Monolingual/offline; no Mozilla model-server connection.
5. **`Urlbar providers + Merino`** — Sponsored/remote suggestions suppressed; keystrokes not sent.
   *Side effects:* Address bar shows only local suggestions.
6. **`New-tab React render`** — Discovery/TopSites/sponsored components removed from the tree.
   *Side effects:* Quiet new-tab page.

## Technical Debt

🟠 **MEDIUM** — Translations disabled cuts against the global distribution audience
  - *Recommendation:* Revisit for distribution builds — consider allowing on-device translation models (no telemetry) while keeping the download path locked to a trusted mirror. Flagged in the roadmap.

🟡 **LOW** — Install-block is implemented by throwing rather than a single central policy gate
  - *Recommendation:* Consolidate the three throw-sites behind one `isInstallAllowed()` returning false, so the policy is one-line auditable.

🟠 **MEDIUM** — ExperimentAPI mock returns generic empties — a component expecting a specific-shaped variable could still misbehave
  - *Recommendation:* Add a smoke test that boots the browser and asserts no console error mentioning ExperimentAPI/Nimbus across urlbar/first-run/settings.

## Impact If Removed / Disabled

Reverting: extensions/themes installable (and side-loadable by malware); new-tab sponsored tiles + discovery feed return; address-bar keystrokes sent to Merino; translation models download on demand; ExperimentAPI returns live data and experiments can run. The sealed appliance becomes a normal extensible browser with its full sponsored-content and remote-experiment surface.

## Testing Notes

Try to install any extension from AMO -> blocked with error. Drag an .xpi onto the browser -> refused. Open a new tab -> no sponsored tiles, no discovery feed. Type in the address bar with network capture running -> no request to merino.services.mozilla.com. about:translations -> disabled. Boot + navigate urlbar/first-run/settings -> zero ExperimentAPI/Nimbus console errors (proves the mock is shaped correctly).

## Changelog Notes

Initial toolkit lobotomy in FF153 (2026-06-08/09); FF154 rebase resolved sys.mjs path conflicts (2026-07-05); static audit confirmed all .rej cleared, codebase stable (2026-07-10). ExperimentAPI mock is the toolkit-side companion to Topic 12's network-side neutralization.

---
*Developer Track. Human Track twin: `07-toolkit.LAYMAN.md`.*


---

# ═══ MERGED DOCUMENT: 07-toolkit.LAYMAN.md (verbatim · sha256:7bbdd219e31cdb7a · merged 2026-08-02) ═══

# 🧍 The Toolkit Lockdown — Turning Firefox Into a Sealed Appliance — Plain English Guide

> *Topic `07-toolkit` of the Gorilla Unleashed Firefox 154 build · Written for everyone · 2026-07-17*

---

## 🌍 The Big Picture

Most of the other topics make the browser *faster* or *more private*. This one makes it **sealed and opinionated** — it turns Firefox from a general-purpose, infinitely-customisable tool into a fixed appliance, like a kitchen microwave: it does a specific set of things well, and you cannot bolt new parts onto it.

Why would anyone want that? Because a browser you cannot extend is a browser that *strangers* cannot quietly extend either. Every add-on, every theme, every language pack, every 'suggested' new-tab tile is also a door — and doors are how malware, spyware, and unwanted content get in. On a machine belonging to someone who is not a security expert (which is most of the target audience), the safest door is the one that was welded shut before they ever got the machine.

Four big changes: (1) **no add-ons or themes can be installed** — every install route (Mozilla's add-on store, drag-and-drop of a file, a website trying to push an extension) is blocked at the source; (2) **no built-in translation** — the translation-model downloads are disabled, keeping the browser monolingual and offline; (3) **no sponsored content on the new-tab page** — the ad tiles, the 'discovery' feed, the sponsored shortcuts are all excised; (4) **a fixed theme** — the appearance is locked so it cannot be changed by the user or by anything pretending to be the user.

**This is a real trade-off, stated honestly:** you cannot install a password-manager extension, an ad-blocker extension, or a dark-mode theme on this build. If you need those, this build is not for you. What you get in exchange is a surface with no configurable attack points.

## 🎭 The Main Characters

| Name | What It Is | Real-World Comparison |
|---|---|---|
| **AddonManager** | The subsystem that installs, manages, and updates extensions and themes | The building's front desk that signs for every delivery — now instructed to refuse all packages |
| **XPIInstall** | The specific code that unpacks and installs an extension file (.xpi) | The loading dock — now with the door bolted, so even a package that got past the front desk cannot be unloaded |
| **New Tab (DiscoveryStream / TopSites)** | The page you see when you open a new tab — normally full of sponsored tiles and a 'recommended stories' feed | The lobby noticeboard, normally rented out to advertisers, now blank by choice |
| **QuickSuggest / Merino** | The address-bar feature that shows sponsored suggestions as you type | The helpful concierge who was secretly paid to recommend certain shops — now silent |
| **TranslationsParent** | The subsystem that downloads and runs language-translation models | The in-house translator whose reference books are no longer delivered |
| **ExperimentAPI** | The Nimbus query interface that 145+ components ask 'is experiment X on?' | The information desk that used to phone HQ for answers — now hands back a blank 'nothing to report' card so nobody waiting in line gets stuck |

## 🔢 How It Works — Step by Step

### Step 1: Block every add-on install route

There are three ways an extension can get installed: from Mozilla's official add-on store (AMO), from a website that pushes one, or from a raw file on disk (side-loading). `AddonManager.sys.mjs` and `AddonRepository.sys.mjs` block the store and web routes by throwing a custom error at the API layer; `XPIInstall.sys.mjs` short-circuits the file route to abort with a block-log message. All three doors, bolted.

### Step 2: Lock the theme

`LightweightThemeManager.sys.mjs` and the design-system token files are patched so the appearance is fixed. The theme cannot be swapped — not by the user in settings, not by an extension (which cannot install anyway), not by a remote config. Consistent appearance, one fewer surface to manipulate.

### Step 3: Strip sponsored content from the new tab

Three React components (`Base.jsx`, `DiscoveryStreamBase.jsx`, `TopSites.jsx`) are patched to remove the sponsored-tile grid, the 'recommended by Pocket' discovery feed, and the sponsored shortcuts. The new tab becomes quiet — your own content, nothing rented out to advertisers.

### Step 4: Silence the address-bar sponsors

QuickSuggest (`QuickSuggest.sys.mjs`, `UrlbarProviderQuickSuggest.sys.mjs`, `UrlbarProviderSearchSuggestions.sys.mjs`) and the Merino backend (`merino/src/lib.rs`, plus a search-config JSON) are patched so the address bar no longer shows sponsored or remotely-fetched suggestions as you type. Your keystrokes are not sent to a suggestion server.

### Step 5: Disable translations

`TranslationsParent.sys.mjs` and `browserLanguages.js` block the download of translation models and language packs. The browser stays monolingual and offline — no model-download connection to Mozilla, no language-pack fetch.

### Step 6: The clever bit — ExperimentAPI returns a safe mock

This is the subtle one. 145+ Firefox components ask the Nimbus ExperimentAPI 'is experiment X enabled?' If you just remove it, all 145 crash (this is the same lesson as Topic 12). Instead, `ExperimentAPI.sys.mjs` is patched to return an empty default mock object for every query — so every component gets a valid 'nothing to report' answer and keeps working, while no actual experiment ever runs. Corpse standing, again.

## 🤔 Quirky Things Worth Knowing

### ⚠️ The sealed-appliance philosophy is a genuine security position, not laziness

It is easy to read 'no extensions' as the build being unfinished. It is the opposite: it is a deliberate stance that the most secure configurable surface is one with no configurable surface. Every extension API is also an attack API. For a non-expert user, removing the ability to install things removes the ability to be tricked into installing things.

### ⚠️ It talks to Topic 12

The ExperimentAPI mock here is the toolkit-side companion to Topic 12's Mozambique Drill. Topic 12 kills the *network* side of Normandy/Nimbus (poll timers, endpoint). This topic makes the *code* side safe by handing back mocks. Same corpse, two different guarantees.

### ⚠️ Translations off is a real limitation for the target audience

Honest note: the target audience is global — people who may well want to translate an English page into their own language. Turning translations off is the one sealed-appliance choice that cuts against them. It is done for offline/security reasons, but it is the change most worth revisiting for a distribution build. (The roadmap flags this as a known trade-off.)

## 💻 What Does This Mean For YOU?

### 🔋 Battery, Speed & Memory

No add-on subsystem running background update checks; no translation-model downloads; no sponsored-content fetches on every new tab. Each is a small saving; together, less background work.

### ⚡ Speed

New-tab page renders faster with no sponsored-tile network fetch. Address bar responds instantly with no remote-suggestion round-trip.

### 🕵️ Your Privacy

Substantial. Your address-bar keystrokes are not sent to a suggestion server (Merino). Your new-tab impressions are not counted for ad revenue. No add-on can read your browsing.

### 🌐 Your Internet

Fewer background connections — no AMO update pings, no Merino suggestion calls, no Pocket discovery feed, no translation-model downloads.

## 🔴 The Kill Switch — Explained

**What it is:** This topic is a bank of related lockdowns: extension installs blocked, theme locked, sponsored content stripped, translations disabled, and the ExperimentAPI made to return safe mocks so nothing crashes.

**Without it:** Firefox behaves as a normal, extensible browser: extensions installable (and side-loadable by malware), sponsored tiles and discovery feed on every new tab, address-bar keystrokes sent to Merino, translation models downloaded on demand, theme changeable by anything.

**Think of it like:** Converting a customisable workshop into a sealed vending machine — you lose the ability to rearrange it, and in exchange nobody else can rearrange it either.

## 🌐 Open Source & Why It Matters To You

Every lock is a readable patch. You can see exactly which install routes are blocked, exactly what the new tab strips, exactly what the address bar no longer sends. A closed 'secure' browser asks you to trust its claims; here the sealed appliance is sealed in the open, where the seals can be inspected.

## 📖 Glossary (Plain English Dictionary)

**Add-on / Extension** — A piece of third-party code that adds features to the browser. Powerful and useful — also a common malware and spyware vector.

**XPI** — The file format for a Firefox extension (a zip archive). 'XPIInstall' is the code that unpacks and installs one.

**AMO** — addons.mozilla.org — Mozilla's official extension and theme store.

**Side-loading** — Installing an extension from a local file rather than the official store — a route malware uses to bypass store review.

**QuickSuggest / Merino** — Firefox's sponsored address-bar suggestion feature (QuickSuggest) and its backend server (Merino). Sends partial keystrokes to fetch suggestions.

**DiscoveryStream** — The 'recommended stories' feed (powered by Pocket) on the new-tab page. Ad-supported.

**TopSites** — The grid of site tiles on the new-tab page. Some are sponsored (paid placements).

**ExperimentAPI (Nimbus)** — The interface 145+ components query to check experiment/feature-flag state. Patched here to return safe empty mocks so nothing crashes while no experiment runs.

---
*Human Track. Its Developer Track twin (`07-toolkit.DEVELOPER.md`) covers the same changes in technical detail. Neither is a simplified copy of the other — they are the same truth in two languages.*


---

# ═══ MERGED DOCUMENT: 07-toolkit.PRECHECK.json (verbatim · sha256:4f53cda18c2baa0c · merged 2026-08-02) ═══

```json
[]
```


---

# ═══ MERGED DOCUMENT: 07-toolkit.PRECHECK.md (verbatim · sha256:4da7dd49387d6708 · merged 2026-08-02) ═══

# Offline Pre-Check: 07-toolkit

*Generated 2026-07-17 08:13:32 by doc_audit.py (rule-based, no model involved).*

## File Inventory

| File | Lang | Lines | Complexity | SHA256 (16) |
|---|---|---|---|---|
| browser_base_content_nsContextMenu.sys.mjs.patch | patch | 93 | 4 | `476cd9f5a5ac8f43` |
| browser_components_preferences_config_appearance.mjs.patch | patch | 334 | 8 | `2748a704f152e479` |
| browser_components_preferences_dialogs_browserLanguages.js.patch | patch | 63 | 7 | `a57696cff6bc24ad` |
| browser_components_urlbar_QuickSuggest.sys.mjs.patch | patch | 74 | 14 | `65f9cfd8766f1ecd` |
| browser_components_urlbar_UrlbarProviderQuickSuggest.sys.mjs.patch | patch | 63 | 4 | `035c7fb4eb252885` |
| browser_components_urlbar_UrlbarProviderSearchSuggestions.sys.mjs.patch | patch | 130 | 5 | `556d6242327c4966` |
| browser_extensions_newtab_content-src_components_Base_Base.jsx.patch | patch | 329 | 11 | `3c9bb98ba5d14ff2` |
| browser_extensions_newtab_content-src_components_DiscoveryStreamBase_DiscoveryStreamBase.jsx.patch | patch | 444 | 25 | `81fa7ddc0c63cc60` |
| browser_extensions_newtab_content-src_components_TopSites_TopSites.jsx.patch | patch | 242 | 12 | `18efdf83ea046996` |
| services_settings_dumps_main_search-config-v2.json.patch | patch | 7864 | 1 | `5a20b2936018be53` |
| third_party_application-services_components_merino_src_lib.rs.patch | patch | 8 | 1 | `2b54edbde0f0f608` |
| toolkit_components_nimbus_ExperimentAPI.sys.mjs.patch | patch | 206 | 20 | `426ee25288e6d531` |
| toolkit_components_translations_actors_TranslationsParent.sys.mjs.patch | patch | 391 | 32 | `2ffb4b9562bb29fa` |
| toolkit_mozapps_extensions_AddonManager.sys.mjs.patch | patch | 241 | 24 | `b30eaeb162169452` |
| toolkit_mozapps_extensions_LightweightThemeManager.sys.mjs.patch | patch | 162 | 17 | `bbbf4da2c382226e` |
| toolkit_mozapps_extensions_internal_AddonRepository.sys.mjs.patch | patch | 48 | 6 | `1dd365e177ebd78d` |
| toolkit_mozapps_extensions_internal_XPIInstall.sys.mjs.patch | patch | 80 | 10 | `3222ea34919deada` |
| toolkit_themes_shared_design-system_dist_semantic-categories.mjs.patch | patch | 2723 | 3 | `6e07f3b15a012a10` |
| toolkit_themes_shared_design-system_dist_tokens-table.mjs.patch | patch | 2717 | 3 | `bf4de9cf2cc0262e` |

## Rule Findings (0)

*All offline rules passed.*
