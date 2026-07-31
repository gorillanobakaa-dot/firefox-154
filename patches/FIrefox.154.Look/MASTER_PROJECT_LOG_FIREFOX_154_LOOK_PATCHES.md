# MASTER PROJECT LOG — FIREFOX 154 LOOK & BRANDING PATCHES

---

## Part 1: History, Roadmap & Overview
*(Originally from 00_LOOK_HISTORY_AND_ROADMAP.md)*

### Document Control
- **Category:** Visual Identity & Branding
- **Last Updated:** 2026-07-10
- **Status:** Active Development
- **Verification Required:** Yes (see Validation section)
- **Related Documents:** 
  - `../DOCUMENTATION_TEMPLATES.md` (IBM format guide)
  - `../MAP.md` (cross-category index)
  - `../05.PREFS/mozconfig` (branding build flag)
  - `../07.TOOLKIT/MASTER_PROJECT_LOG_FIREFOX_154_TOOLKIT_PATCHES.md` (forced theme enforcement)

---

### Executive Summary

**What This Does (Plain Language):**
This folder contains everything about how the browser looks and what it's called. Four main areas:
1. **Theme** — Colors, spacing, tabs, animations (Gorilla visual style).
2. **Branding** — Name, logos, icons, wallpaper (Gorilla Unleashed identity).
3. **Design Tokens** — Underlying palette and type system.
4. **Deep Localization** — Every word changed from "Firefox" to "Gorilla".

**Technical Summary:**
Visual identity and branding system for Sony VAIO SVE14A3AJ. Implements: (1) zero-CPU chrome theme (`master-redirect.css` injected via `@import`, GPU-native properties only), (2) complete branding assets (`branding/gorilla` with nebula.jpg, custom fonts, icons), (3) design token system (colors/fonts source of truth), (4) deep 235-file en-US locale rebrand (browser/ + toolkit/ .ftl tree).

**Critical Context:**
> **This is cosmetic + identity work.** The look is fixed, not user-customizable. The "zero-CPU" theme approach helps battery by using only GPU-native effects on the Intel HD 4000 graphics engine.

---

### Mission Statement

### Mission: Distinctive Identity with Zero CPU Cost
Create a distinctive visual identity for Gorilla Unleashed while maintaining performance. The unusual constraint: **only use visual effects the graphics chip can do by itself, so the main processor stays asleep.**
- Fancy borders and animations normally make the CPU recalculate layouts constantly.
- Gorilla theme deliberately sticks to effects the 2012 graphics chip handles in hardware — looks styled and stays cool.

---

### Component Documentation

#### 1. master-redirect.css — Zero-CPU Style Sheet
- **Status:** Modified | **Deploy Path:** `browser/themes/shared/master-redirect.css` | **Last Verified:** 2026-07-10
- **What It Does (Plain Language):** Overrides standard Firefox colors and shapes with Gorilla Black and Cyan without using layout-resizing tricks that consume processor power.
- **Technical Description:** Forces `color-scheme: dark`, maps all color variables to `#000000` / `#00FFFF`, maps the active tab to `#FFC0CB`, and suppresses transitions/animations (set to `0.01ms`).

#### 2. Deep Branded Locales — Language Override
- **Status:** Modified | **Deploy Path:** `browser/locales/en-US/` & `toolkit/locales/en-US/` | **Last Verified:** 2026-07-10
- **Tuning:** Complete word-for-word string rebrand across 235 `.ftl` files to replace all instances of "Firefox" and "Mozilla" with "Gorilla".

---

### Chronological History (Recovered)

#### 2026-06-08/09
Initial branding assets created for Firefox 153. Zero-CPU CSS redirection drafted.

#### 2026-07-05
**Firefox 154 Rebase:**
Visual assets re-mapped and localization files updated to match Firefox 154's FTL structure.

#### 2026-07-10
**Branding Verification:**
Completed static checks. Verified all image assets, layout colors, and font declarations map cleanly to target locations.

---

## Part 2: Rule-Based Code Audit & Validation (2026-07-10)

We completed a static code audit of the look and branding configurations:
1. **master-redirect.css**: Confirmed all layout-changing CSS attributes are blocked. Replaces layout modifications with GPU-native `outline` and `opacity` properties. Transitions are fully annihilated (`0.01ms` duration).
2. **Branding Assets**: Verified `PrivateBrowsing` and `VisualElements` icon assets match target specifications.
3. **Deep Locales**: Checked that the word replacements are correctly integrated.

The category passes all code guidelines.
