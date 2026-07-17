# Look & Branding — Zero-CPU Chrome Theme + Design Tokens + 235-File Locale Rebrand — Developer Track

> **Topic:** `08-look` · **Files:** `browser/themes/shared/master-redirect.css (injected via @import)`, `browser/themes/shared/browser-shared.css`, `browser/themes/shared/jar.inc.mn`, `toolkit/themes/shared/findbar.css`, `toolkit/themes/shared/icons/warning.svg`, `toolkit/themes/shared/design-system/dist/semantic-categories.mjs`, `toolkit/themes/shared/design-system/dist/tokens-table.mjs`, `branding/gorilla/* (nebula.jpg, icons, fonts — via mozconfig flag)`, `browser/locales/en-US/**/*.ftl + toolkit/locales/en-US/**/*.ftl (235 files)`
> **Generated:** 2026-07-17

---

## Module Summary

Visual identity layer with a hard performance constraint: the chrome theme must render entirely on the Intel HD 4000 GPU with zero CPU-side layout recalculation. master-redirect.css forces color-scheme: dark, maps all color variables to the Gorilla palette (#000000 base, #00FFFF accent, #FFC0CB active tab), and neutralizes transitions/animations (duration 0.01ms). Enforces the project CSS invariants: animate only opacity/transform; outline not border; no scale/translate transforms on .toolbarbutton-1 / .tabbrowser-tab / XUL children; will-change: auto globally (prevents WebRender VRAM over-promotion on HD 4000); contain: layout style (not paint) on major containers. Design tokens (semantic-categories.mjs, tokens-table.mjs) are the palette source of truth. Deep rebrand replaces Firefox/Mozilla -> Gorilla across 235 en-US .ftl files in browser/ and toolkit/. Branding assets wired via mozconfig branding flag (Topic 05).

## Architecture

- **Pattern:** Single-source-of-truth theming (design tokens) + injected override stylesheet (master-redirect.css via @import) + mechanical locale rebrand. The zero-CPU constraint is the governing rule, not an afterthought.
- **Trust Boundary:** N/A — cosmetic. One note: the branding rename is legitimate product identity, distinct from the project's no-brand-spam rule which governs NEW code identifiers, not user-visible product name.
- **Attack Surface:** N/A
- **Dependencies:** `mozconfig branding flag (Topic 05) points build at branding/gorilla`, `Topic 07 enforces the theme cannot be user-swapped (LightweightThemeManager lock)`

## Kill Switches

### `master-redirect.css — color-variable remap + animation neutralization` — HARD ⚠️

- **Condition:** loaded via @import into browser chrome
- **Effect:** Repaints chrome in Gorilla palette; sets transition/animation durations to 0.01ms so no motion triggers CPU reflow.
- **Reversibility:** reversible
- **Notes:** Loaded via chrome://browser/skin/ — cannot reach chrome://global/skin/ widgets (see findbar note).

### `toolkit/themes/shared/findbar.css (+ warning.svg)` — HARD ⚠️

- **Condition:** always
- **Effect:** Styles the toolkit-side widgets (find-bar, notifications) that master-redirect.css physically cannot reach because they load via chrome://global/skin/.
- **Reversibility:** reversible
- **Notes:** This is WHY two of the four non-locale patches exist — the chrome/global skin path boundary.

### `design-system tokens (semantic-categories.mjs, tokens-table.mjs)` — HARD ⚠️

- **Condition:** always
- **Effect:** Palette + type source of truth. Referenced by name rather than hard-coded hex.
- **Reversibility:** reversible
- **Notes:** Change a token, everything referencing it updates. Also touched by Topic 07 (theme lock).

### `235 en-US .ftl files — Firefox/Mozilla -> Gorilla` — HARD ⚠️

- **Condition:** always
- **Effect:** All user-visible product-name strings rebranded.
- **Reversibility:** reversible
- **Notes:** FTL structural fragility: NEVER edit text inside < > tags (breaks data-l10n-name -> DOM hydration -> invisible window); blank line between a Fluent value and its .description attribute is FATAL; grep for 'Gorilla Gorilla' double-replacements after automated passes.

## Performance Profile

- **CPU:** The governing metric. Theme renders on GPU; no animation/transition wakes the CPU for a reflow. Not benchmarked as a number here, but the constraint is the design's reason for existing.
- **Memory:** will-change: auto globally prevents WebRender from over-promoting layers into VRAM (which thrashes the HD 4000's shared memory). contain: layout style isolates reflows without breaking XUL flexbox.
- **I/O:** Branding assets (nebula.jpg, fonts) loaded once at startup.
- **Timer Interval:** Animations effectively disabled (0.01ms).

## Security Analysis

### User Profiling

N/A

### Targeting

N/A

### Trust Chain

N/A

### Abuse Potential

N/A — cosmetic layer.

## Implementation Flow

1. **`chrome load -> master-redirect.css @import`** — Injected into browser chrome; remaps color vars + kills animations.
   *Side effects:* Entire chrome repainted dark/cyan; no motion.
2. **`findbar.css / warning.svg (toolkit skin)`** — Styles the global-skin widgets master-redirect cannot reach.
   *Side effects:* Find-bar + notifications match the theme.
3. **`design token resolution`** — Named tokens resolve to Gorilla palette values.
   *Side effects:* Consistent palette across all token consumers.
4. **`FTL load (235 files)`** — Fluent strings show Gorilla branding.
   *Side effects:* Every user-visible Firefox/Mozilla string reads Gorilla.

## Technical Debt

🟠 **MEDIUM** — 235-file locale rebrand is a large surface for FTL-structural regressions on version bumps
  - *Recommendation:* Add a preflight that parses every patched .ftl and fails on (a) edited text inside < >, (b) blank line before a .description, (c) 'Gorilla Gorilla' doubles. Cheap, catches the three known-fatal patterns.

🟡 **LOW** — master-redirect.css / findbar.css split (chrome-skin vs global-skin) is a non-obvious boundary a future maintainer will trip on
  - *Recommendation:* Add a comment at the top of master-redirect.css noting it cannot reach chrome://global/skin/ and pointing to findbar.css.

🟡 **LOW** — Palette hexes appear in both master-redirect.css and design tokens
  - *Recommendation:* Ensure master-redirect.css references tokens rather than re-hard-coding #00FFFF etc., so there is one source of truth.

## Impact If Removed / Disabled

Reverting: browser looks and is named like stock Firefox; default animations return and wake the CPU on the HD 4000 during ordinary interaction; the chrome/global-skin widgets lose their matching style; branding assets revert to Firefox defaults.

## Testing Notes

Visual: chrome is dark with cyan accents, active tab pink, nebula wallpaper on new tab. Perf: interact with tabs/buttons while watching CPU — should stay low (no reflow spikes from animation). FTL integrity: `./mach build faster` must succeed and no window should render blank (blank window = broken data-l10n-name). grep -r 'Gorilla Gorilla' browser/locales toolkit/locales -> expect zero.

## Changelog Notes

Branding assets created FF153 (2026-06-08/09); FF154 rebase re-mapped assets + updated FTL to 154 structure (2026-07-05); branding verification (2026-07-10). Note: the Firefox->Gorilla rename here is legitimate product branding and is the intended exception to the project-wide no-new-gorilla-identifiers rule (that rule governs code identifiers/filenames, not the public product name in user-visible strings).

---
*Developer Track. Human Track twin: `08-look.LAYMAN.md`.*