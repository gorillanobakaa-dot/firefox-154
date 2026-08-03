# 🦍 Gorilla Unleashed — UI/Theme Timeline: Trials, Errors, Mistakes & Additions

*Synthesized 2026-07-18 from the 238 gathered lessons in `GATHERED_BRAIN_LESSONS/`
(brain concepts + provenance snapshots + history docs). Dual-track, per the project philosophy.*

---

## The intent it started from (never lose this)

De-brand Firefox and replace its art with our own — **but smarter**. A **zero-CPU** theme:
every animation/transition offloaded to the **ASIC + Intel HD 4000 GPU**; the theme contains
only GPU-native instructions (`opacity`, `transform`, `outline`). Strip the CPU/attention
thieves — topsites, weather, suggestions, AI "helpers", telemetry (Glean/FOG), experiments
(Nimbus/Normandy), extensions + the ability to install them, remote automation (WebDriver
BiDi/Marionette), and unneeded locales — **at build time**. **ONE icon**, referenced across
all ~46 `about:` pages, never duplicated. Aesthetic: pure black `#000000`, bright cyan
`#00FFFF`, delicate pink `#FFC0CB`. Lean like early-2000s Firefox (~15 MB). *(Full vision saved
to agent memory: `zero-cpu-theme-vision`.)*

---

## LAYMAN TRACK — the story in plain English

It began as a paint job and turned into an engine rebuild. The clever core idea — one
"Master Redirector" stylesheet instead of patching 70 files — worked beautifully. But every
time the goal of "zero CPU" was pushed too hard, the browser's *usability* broke, and the
work had to be rescued from a pristine backup ("the Vault"). It broke, got fixed smarter,
grew, and eventually snowballed past what one person can easily hold in their head. That's
why we're standing back now to see the whole shape of it.

---

## DEVELOPER TRACK — chronological phases

### PHASE 1 — UI foundation & the Master Redirector (May 29–30, 2026)  ✅ ADDITION (the good idea)
- **11:47** — **`master-redirect.css` breakthrough.** Instead of patching 70+ theme files,
  one file is `@import`-injected into `browser-shared.css` + `global-shared.css` and overrides
  CSS variables globally. Black `#000000` / cyan `#00FFFF`.
- **Rapid tab-visibility trial-and-error** (the ~20 `master_redirect_css` provenance snapshots
  on May 29–30 are THIS iteration churn):
  - 12:05 active tab = 3px pink border → 12:24 solid pink background → 12:49 navy close-button
    for contrast → 12:53 text weight/color refinement.
  - 13:06 "Shadow-DOM pierce": force `opacity:1` + cyan on search/urlbar placeholders.
- **Lesson:** the redirector is the right architecture. The churn shows the look was tuned by
  eye, iteratively — expected, not the bug.

### PHASE 2 — Media engine (Jun 5–6)  · PHASE 3 — Networking/OSINT (Jun 13)  ·  (context, not UI)
- CubebUtils/AudioStream hardware-decode; user.js + nsUDPSocket/Http3Session network silencing.
  Listed for timeline completeness — these are the CPU wins that made the theme's zero-CPU goal real.

### PHASE 4 — Telemetry excision + Safety Vault (Jun 14–17)  ✅ ADDITION
- `FOG.cpp` (Glean) and `NimbusFeatures.cpp` lobotomized in source; pristine nightly stored in
  the Safety Vault. This is the "restore from vault" safety net that later phases depended on.

### PHASE 5 — ❌ THE HOLLOW-SVG DISASTER (Jun 19–20)  ← the archetypal mistake
- **Action:** `hollow_out_svgs.py` recursively **deleted 788 UI icons** to kill icon-render CPU.
- **Result:** 0.0% CPU — and **~400 internal controls and drop-down menus vanished.** "A
  mathematical success but a usability disaster." **This is the pattern to never repeat:
  deleting/stripping to chase zero-CPU destroys the UI.**

### PHASE 6 — ✅ RECOVERY: the Zero-CPU Master Architecture (Jun 22)
- **DEFCON-1 `rsync`** restore of all 788 SVGs from the Vault. Instead of *deleting*, author
  `gorilla-master-redirect.css` styling with **only `opacity`, `outline`, `transform`** —
  properties the HD 4000 composites without waking the CPU. Menus back; CPU flatlined.
- **Lesson:** the right lever is GPU-native CSS, not deletion.

### PHASE 7 — about: page branding, single-icon rule (154 work)  ✅ ADDITION
- All ~46 `about:` pages reference ONE logo via `background: url("chrome://branding/content/about-logo.svg")`.
  **PRIME DIRECTIVE — single source of truth:** never copy the master icon into per-page folders
  (storage bloat). Tooling: `gather_assets_for_all_pages.py`, `generate_proposals.py`, a 10-step
  approval workflow (no YOLO/background blind execution).

### PHASE 8 — ❌ ERR-UI-004 (Jul 10): menus turned to black boxes  ← same mistake, smaller
- `appearance: none !important` applied to global `panel`/`menupopup` stripped native OS chrome →
  doorhangers/menus rendered as flat borderless boxes; a rogue agent also hardcoded `200px` icons
  into the `autocomplete-row-item` web component.
- **Fix:** remove `panel`/`menupopup` from the `appearance:none` block; restore
  `autocomplete-row-item.css` from the Vault; add the menu-restoration block (`appearance:auto`).

### PHASE 9 — ❌ CURRENT: an agent "lost context and hallucinated" (recent)
- `master-redirect.css` was churned again; the ERR-UI-004 menu-restoration fix existed in the
  LIVE file but was **missing from the patch source of truth** (`new.patches/08.Look/NEW_FILES`) —
  a rebuild would have silently re-broken menus. **Already re-synced (2026-07-18).**
- Remaining: the theme "looks wrong" — confined to the **CSS themes** (the FTL "Gorilla" menu
  strings are intentional and correct). Plan: restore pristine theme CSS from the Vault, rebuild
  deliberately.

---

## The recurring failure mode (the one lesson above all)

> **Chasing zero-CPU by DELETING or hard-stripping UI (icons, `appearance:none` on native
> widgets) always breaks usability. The correct lever is GPU-native CSS (`opacity`/`transform`/
> `outline`) plus build-time removal of genuinely-unused subsystems — never runtime destruction
> of live UI. When it breaks, restore from the Vault, then re-apply the smart way.**

## Next step — revisit `UI.TWEAKS.AND.LOOKS`
Baseline concept: `Gorilla.Look.Internal.Pages.Ui.Tweaks.Baseline` (single-icon rule + 10-step
approval workflow). Related: `internal_ui_tweaks_about_pages`, `Gorilla_Unleashed_CSS_UI_Tweaks_Documentation`,
`UI_TWEAKS_DOCUMENTATION`. Open thread: identify the exact breaking CSS edit, restore pristine
theme files from the Vault, and re-derive the look from GPU-native rules only.
