# NEW MASTER CSS — Rebuild Plan (works WITH Firefox 154, not against it)

> ## ▶ RESUME HERE (fresh session — read this first)
> Full state checkpoint: brain `Brain.XML/theme_rebuild_checkpoint_2026_07_18.xml` (+ reflection in
> `Core/LLM_Zen_Garden_Journal.md` Entry 8). Draft under review: `NEW_master-redirect.DRAFT.css` (NOT
> deployed; backup in `_BACKUP_20260718_121537/`). **Before editing the theme: READ
> `patches/Mega.Lessons/CSS_UI_TWEAKS_MEGA_LESSON.md` fully.** Draft still needs: XUL layout fixes
> (§15), `* { will-change: auto }` suppression, the universal-vs-targeted animation-kill decision.
> Decisions locked: glyphs ABANDONED (keep native controls, recolor cyan); text-only tabs (+ pinned
> label restore); 600px logo + pill + funny strings live elsewhere, don't touch. Watch context budget
> (0.9) — last session hit ~677k without noticing (the Highway Robbery blind spot).

**A living scratchpad for a one-man show + the AI. Read it before acting; update it after acting.**
It exists so neither of us loses the vision, and so no agent re-scans the tree into a
600-million-token "highway robbery" again. Grounded in the 238 lessons in
`GATHERED_BRAIN_LESSONS/` and the failure pattern in `MASTER_UI_TIMELINE.md`.

Vision (never drop it): de-branded, **zero-CPU** theme — GPU/ASIC-native CSS only, strip the
noise, ONE referenced icon, black `#000000` / cyan `#00FFFF` / pink `#FFC0CB`, lean like early
Firefox. Full vision: memory `zero-cpu-theme-vision`.

Status legend:  `[ ]` todo · `[~]` in progress · `[x]` done · `[!]` blocked/needs-decision
Every step: do ONE, verify, tick it, then move on. No batching destructive steps.

---

## PHASE 0 — GROUND RULES (the anti-runaway, anti-repeat-mistake contract)

- [ ] 0.1 **Work WITH the cascade.** Theme by SETTING Firefox 154's own CSS variables
  (`--lwt-*`, `--toolbar-*`, `--toolbar-field-*`, `--panel-*`, `--arrowpanel-*`, `--tab-*`,
  `--urlbar-*`, `--newtab-*`, `--color-*`). Do NOT hard-override every element with `!important`.
- [ ] 0.2 **Never `appearance:none` on native widgets** (`menupopup`, `panel`, `menuitem`,
  doorhangers). → ERR-UI-004 black-box menus. Leave native chrome native; recolor via variables.
- [ ] 0.3 **Never delete/hollow live UI** (icons, SVGs) to save CPU. → the 788-SVG disaster
  (400 menus vanished). Style, don't strip. Removal of whole subsystems is BUILD-TIME, not CSS.
- [ ] 0.4 **GPU-native properties ONLY** for anything dynamic: `opacity`, `transform`, `outline`.
  Forbidden (CPU reflow): width/height, margin/padding, border, top/left/right/bottom, `transition: all`.
- [ ] 0.5 **Universal selectors — NUANCED (corrected after reading the mega-lesson).** Avoid `*` for per-element STYLING. BUT the project deliberately keeps TWO global `*` suppressions as an accepted HD-4000 tradeoff: the animation-duration kill (comprehensive coverage > traversal cost) and `* { will-change: auto }` below. Universal animation-kill vs targeted is the USER's call.
- [ ] 0.6 **will-change: SUPPRESS, never PROMOTE (I had this BACKWARDS).** NEVER `will-change: transform/opacity` (promotion thrashed WRSceneBuilder -> CPU spike). DO keep `* { will-change: auto !important }` to globally SUPPRESS WebRender auto-promotion. This is WANTED, not banned.
- [ ] 0.7 **Single source of truth for the icon**: reference `chrome://branding/content/about-logo.svg`.
  NEVER copy the master icon into per-page folders (storage bloat, drift).
- [ ] 0.8 **Smart-Compile only for CSS**: edit raw file → flush `startupCache` → restart. NO `mach build`,
  NO `--enable-release`, NO `mach package` for CSS iteration. (C++/build stripping is a separate track.)
- [ ] 0.9 **Context budget**: consult THIS plan + `GATHERED_BRAIN_LESSONS/`, not fresh tree scans.
  If context climbs past ~150k tokens, stop, offload notes to the brain (`brain write`), reset.
- [ ] 0.10 **Approval gate**: audit → propose → user approves → implement ONE step → verify. No YOLO,
  no background blind execution (the baseline 10-step workflow).

## PHASE 1 — BASELINES & SAFETY NET (know the ground before touching it)

- [x] 1.1 Locate the pristine theme CSS in the Vault (`SafetyVault.Firefox/firefox-main/browser/themes/`)
  and confirm it matches upstream 154 (the guaranteed-clean baseline).
- [x] 1.2 Snapshot the CURRENT live theme files (master-redirect.css + any edited shared CSS) to a
  dated backup dir before any change. Reversible-first.
- [x] 1.3 Confirm the two injection points still exist and are correct:
  `browser/themes/shared/browser-shared.css` and `toolkit/themes/shared/global-shared.css`
  each `@import` the redirect. (Verified 2026-07-18.)
- [x] 1.4 Diff current `master-redirect.css` vs the last-known-good (patch `08.Look/NEW_FILES` — now synced)
  to enumerate exactly which rules the hallucinating agent added/changed. Record findings here.
- [x] 1.5 DECIDED: **rebuild the redirect from a blank file matching this plan** (clean slate).
  BUT clean slate ≠ throwing away good work — harvest first (1.6). Losing proven work IS the failure pattern.

## PHASE 1.5b — HARVEST KNOWN-GOOD (preserve VERBATIM before the blank slate)

These already work and the user is happy with them. Extract the exact rules/assets and carry
them into the new file unchanged. Do NOT "improve" them.

- [x] 1.6 **Funny FTL messages — DO NOT TOUCH (not CSS, intentional):** "Search with Gorilla or
  enter address you Apple Moron", the URL top-bar message, etc. Live in
  `browser/locales/en-US/browser/browser.ftl`, `.../newtab/newtab.ftl`,
  `.../aboutPrivateBrowsing.ftl`. The CSS rebuild must not disturb these strings.
- [x] 1.7 **Pill-shaped searchbox geometry** — harvest the exact rules (border-radius / dimensions)
  from the current theme (`urlbar-searchbar.css` + the newtab search wrapper). Keep as-is.
- [x] 1.8 **Big Gorilla logo ABOVE the pill searchbox — placement is perfect.** Harvest the exact
  positioning/sizing rules from the current newtab CSS. Keep as-is.
- [x] 1.9 **THE CRISP-ICON TECHNIQUE (hidden gem — `Lessons_Learned_SVG_Injection.xml`):** do NOT
  upscale a small icon (CSS `background-size` interpolation = blur). Instead Lanczos-**downsample**
  the canonical master PNG to the wrapper's EXACT intrinsic size and embed it base64 inside
  `<svg><image width=W height=H .../></svg>`. Tool: `generate_crisp_svgs.py` (= `brand crisp-svgs`).
  This is the rule for every logo the theme injects. Record the exact intrinsic sizes used.
- [x] 1.10 Save the harvested snippets into a `HARVESTED_GOOD.css` reference block IN this folder so
  the new file assembles from proven parts, not from memory.

## PHASE 2 — ARCHITECTURE OF THE NEW REDIRECT (structure before styling)

- [ ] 2.1 One file, four clearly-commented sections: (A) variable overrides, (B) branding/icon,
  (C) targeted chrome fixes, (D) native-widget restoration. Provenance header per our convention.
- [ ] 2.2 Section A = a single `:root` (+ `#main-window`, `#browser-window`) block that sets the palette
  via variables. This is 90% of the theme and the safest lever.
- [ ] 2.3 Define the palette tokens once as CSS custom properties (`--g-black`, `--g-cyan`, `--g-pink`)
  and reference them — so a future colour change is one edit.
- [ ] 2.4 Declare `color-scheme: dark` at `:root` so Firefox 154's own light/dark(`light-dark()`)
  machinery resolves to dark natively (work WITH it).
- [ ] 2.5 Keep chrome (browser UI) and content (about: pages) concerns in separate labelled subsections;
  they inject via different shared files.

## PHASE 3 — CORE CHROME PALETTE (via variables, minimal element overrides)

- [ ] 3.1 Backgrounds → black: `--lwt-accent-color`, `--toolbar-bgcolor`, `--toolbar-field-background-color`,
  `--urlbar-box-bgcolor`, `--newtab-background-color`, the `--color-gray-*` ramp.
- [ ] 3.2 Text/foreground → cyan: `--toolbar-field-color`, `--lwt-toolbar-field-color`, `--input-color`,
  `--newtab-text-primary-color`, `--lwt-tab-text` (white where cyan-on-black is unreadable).
- [ ] 3.3 Active tab = pink background, black label (targeted `.tabbrowser-tab[selected]` — allowed,
  it's not a native OS widget). No border/box-shadow (CPU).
- [ ] 3.4 Inactive tab label = cyan; hover = cyan `outline` (not background swap → no repaint).
- [ ] 3.4b **No images/icons in tabs** (text-only): `display:none` on `.tab-icon-image, .tab-sharing-icon-overlay, .tab-icon-overlay` (proven selectors, Zero_CPU_UI_Glyphs). Add `.tab-throbber, .tab-icon-pending`; and restore `.tabbrowser-tab[pinned] .tab-label-container { display:flex }` so pinned tabs are not blank buttons. Close button + new-tab "+" + hitboxes stay intact.
- [ ] 3.5 URL bar focus ring = cyan `outline` + `outline-offset`, never `border`/`box-shadow`.
- [ ] 3.6 Placeholders (`::placeholder`) → `opacity:1` + cyan (pierce the grey-glass).
- [ ] 3.7 Titlebar/window-control icons + new-tab "+" → cyan `fill` (black-on-black fix); close hover = red.
- [ ] 3.8 VERIFY step: launch, eyeball toolbar/tabs/urlbar. Screenshot. No reflow jank.

## PHASE 4 — NATIVE MENUS & POPUPS (the thing that keeps breaking — handle with care)

- [ ] 4.1 DO NOT strip appearance from `menupopup`/`panel`. Keep the ERR-UI-004 restoration block:
  `menupopup { appearance:auto; --panel-background:Menu; --panel-text-color:MenuText; ... }`.
- [ ] 4.2 `menupopup menuitem/menu` → `appearance:auto`, `background:transparent`, `color:inherit`.
- [ ] 4.3 `menupopup menuseparator` + `.menu-iconic-icon`/`.menu-iconic-left` → native rendering,
  `-moz-context-properties: fill...`, `fill: currentColor`.
- [ ] 4.4 Clamp autocomplete/login-popup icons to 16px (`.ac-site-icon`, `autocomplete-row-item`
  `--icon-width/height`) — the ERR-UI-004 200px-explosion guard.
- [ ] 4.5 VERIFY: right-click menu (native borders/shadows), password-manager doorhanger, autocomplete
  dropdown, WebAuthn prompt — the four historical break points. Screenshot each.

## PHASE 5 — THE SINGLE-ICON BRANDING SYSTEM

- [ ] 5.1 Confirm `chrome://branding/content/about-logo.svg` resolves to the one master icon.
- [ ] 5.2 Redirect the standard illustration classes to it via `content:`/`background-image`
  (`.illustration, .info-icon, .error-icon, .category-icon, moz-promo img, #extensions-empty-illustration`).
- [ ] 5.3 Guard against oversizing: constrain injected logos (`background-size: contain`, sane max
  dimensions) so no page blows the icon up (the 200px lesson, again).
- [ ] 5.3b **Crisp, never blurry (from 1.9):** for any HERO logo the theme scales up, don't rely on
  CSS upscaling a bitmap — use the `about-logo.svg` whose base64 image was Lanczos-downsampled to
  its exact intrinsic size (`brand crisp-svgs`). CSS then only *places* it, never resamples it up.
- [ ] 5.4 VERIFY: a couple of about: pages show the single logo at a sane size; no duplicated asset on disk.

## PHASE 6 — THE 46 about: PAGES (triage first, then apply)

- [ ] 6.1 Rebuild the lost triage: from `about:about`, list the 46 pages; mark each
  **modifiable / no-opportunity / dangerous** using the gathered lessons (e.g. about:cache was
  intentionally skipped; about:preferences had a CSS-wipeout+Fluent-crash — handle carefully).
- [ ] 6.2 Record the triage table IN THIS DOC so we never re-derive it (the lost-script problem).
- [ ] 6.3 For each MODIFIABLE page: rely on the global-shared.css injection for palette; add page-specific
  rules only where needed. No per-page icon copies.
- [ ] 6.4 Known-careful pages get explicit notes: about:preferences (Fluent parser + CSS wipeout risk),
  about:newtab/home (strip topsites/weather/suggestions/AI — see Phase 7), about:mozilla (the
  "Book of Gorilla" easter egg — cosmetic, keep it).
- [ ] 6.5 VERIFY page-by-page in small batches (5–8 at a time), screenshot, tick off. Never "all 46 at once".

## PHASE 7 — NEW TAB / HOME: KILL THE NOISE (prefs + CSS, not deletion)

- [ ] 7.1 Disable via prefs (build-time firefox.js / user.js): topsites, weather, Pocket/stories,
  sponsored, snippets, AI chat/"helpers", search suggestions.
- [ ] 7.2 CSS: hide the residual containers with `display:none` on SPECIFIC selectors (not `*`),
  black background, cyan text. Confirm no layout thrash.
- [ ] 7.3 VERIFY: about:newtab is black/cyan, empty of noise, and does not spin the CPU at idle.

## PHASE 8 — REGRESSION GATE (prove we didn't repeat history)

- [ ] 8.1 Checklist against every documented past break: menus (black box), doorhangers, autocomplete
  200px, password manager, about:preferences crash, missing menus from over-stripping.
- [ ] 8.2 Idle-CPU check (`intel_gpu_top` / CPU): confirm near-zero at idle; GPU carries compositing.
- [ ] 8.3 No universal selectors, no `will-change`, no `appearance:none` on native widgets — grep the
  final file to prove it.
- [ ] 8.4 Brace/CSS structural check on the final file (balanced, no unterminated rules).

## PHASE 9 — LOCK IT IN (so a rebuild can't regress it)

- [ ] 9.1 Copy the final `master-redirect.css` into the patch source of truth
  (`patches/new.patches/08.Look/NEW_FILES/...`) — the thing that survives a clean rebuild.
- [ ] 9.2 Provenance header in the file (`// GORILLA OVERRIDE: ...` allowed/required) + a dated snapshot.
- [ ] 9.3 Write ONE dual-track lesson via `brain write lesson` summarising the new architecture +
  the triage table, so the knowledge is in the garden, not just on disk.
- [ ] 9.4 Update `MASTER_UI_TIMELINE.md` with a Phase-10 "clean rebuild" entry.

---

### Parking lot (capture, don't chase — keeps context clean)
- DECIDED: nav-control + close-button GLYPH replacement is ABANDONED. It worked (zero-CPU win) but users disliked it. Keep NATIVE SVG controls, recolored cyan for black-on-black visibility. Do not re-attempt glyphs.
- Rebuild the lost "gather assets / generate proposals" triage script? (only if worth it vs. the table)
- Build-time strip track (extensions, WebDriver BiDi/Marionette, locales, Nimbus/Normandy) — SEPARATE plan.
- pill-shaped searchbox exact geometry — confirm which lessons prescribe it.

**Draft — for your review. Add/remove/reorder steps; this is your scratchpad as much as mine.**
