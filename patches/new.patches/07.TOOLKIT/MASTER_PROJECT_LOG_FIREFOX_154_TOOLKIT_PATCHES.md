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
