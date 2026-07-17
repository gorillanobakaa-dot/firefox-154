# 🧍 The Look — A Distinctive Identity That Costs the Graphics Chip Almost Nothing — Plain English Guide

> *Topic `08-look` of the Gorilla Unleashed Firefox 154 build · Written for everyone · 2026-07-17*

---

## 🌍 The Big Picture

This is the biggest folder by file count (239 files) and, paradoxically, one of the least complicated to explain. It is everything about how the browser *looks* and what it is *called*: the dark theme, the colours, the logos and wallpaper, and a word-for-word rename of the entire interface from 'Firefox' to 'Gorilla Unleashed' across 235 language files.

But there is one genuinely clever engineering idea buried in the prettiness, and it is worth understanding: **the theme is designed to cost the graphics chip almost nothing.** Normally, fancy borders, hover effects, and animations force the computer to constantly recalculate the layout of the page — which wakes up the main processor (CPU) and burns battery. On a modern laptop you would never notice. On a 2012 machine with a weak processor, a busy theme can make the whole browser feel sluggish just from *looking* styled.

The solution here is a rule the whole theme obeys: **only use visual effects the graphics chip (the Intel HD 4000) can do entirely by itself, without waking the main processor.** That means effects like colour and opacity (cheap, GPU-native) are fine, but effects like resizing borders or sliding things around (expensive, CPU-bound) are banned. The result is a browser that looks deliberately styled — deep black with cyan accents, a pink active tab, a nebula wallpaper — and stays cool while doing it.

## 🎭 The Main Characters

| Name | What It Is | Real-World Comparison |
|---|---|---|
| **master-redirect.css** | The single stylesheet that repaints the whole browser interface in the Gorilla colours | One master paint order that recolours every room in the building at once |
| **Zero-CPU rule** | The design constraint: only visual effects the graphics chip handles alone, so the CPU stays asleep | Decorating with paint and lighting (free once installed) instead of moving walls around (needs a work crew every time) |
| **Design Tokens** | The underlying palette and type system — the single source of truth for every colour and font | The official paint-chip card the whole building is decorated from — change one chip, everything using it updates |
| **The 235-file locale rebrand** | Every visible word changed from 'Firefox'/'Mozilla' to 'Gorilla' across all the interface text files | Repainting the name on every door, sign, and letterhead in the building |
| **Nebula wallpaper + fonts** | The branding assets — the deep-space wallpaper, the custom logos, the bundled fonts | The building's actual decor and signage — the visible identity |

## 🔢 How It Works — Step by Step

### Step 1: The zero-CPU stylesheet repaints everything

`master-redirect.css` is injected into the browser's own interface. It forces a dark colour scheme, maps every colour variable to the Gorilla palette (deep black `#000000`, cyan `#00FFFF` accents, a pink `#FFC0CB` active tab), and — crucially — turns off animations by setting their duration to a near-zero `0.01ms`. No sliding, no fading, no CPU-waking layout recalculation.

### Step 2: Only GPU-friendly properties are allowed

The theme obeys a strict rule (documented in the project's CSS lessons): animate only `opacity` and `transform`, use `outline` instead of `border` for highlights (borders change the box model and cause layout thrash; outlines sit outside it), and never apply scaling transforms to toolbar buttons or tabs (that collapses the XUL layout). Every rule exists because breaking it was measured to hurt on this hardware.

### Step 3: Design tokens are the single palette source

The colour and type system lives in design-token files (`semantic-categories.mjs`, `tokens-table.mjs`). Instead of hard-coding `#00FFFF` in fifty places, the theme references a named token. Change the token, everything using it updates — the disciplined way to theme a large interface.

### Step 4: The deep rebrand — 235 language files

Every user-visible string that said 'Firefox' or 'Mozilla' is changed to 'Gorilla' across 235 `.ftl` (Fluent) localization files in the `browser/` and `toolkit/` trees. This is the mechanical bulk of the folder — tedious, careful work, because breaking the structure of an `.ftl` file (for instance, editing text inside an HTML tag or leaving a blank line in the wrong place) can make an entire window render blank.

### Step 5: Branding assets — wallpaper, icons, fonts

The `branding/gorilla` directory holds the nebula wallpaper, the custom logos and icons, and the bundled fonts. A build flag in `mozconfig` (Topic 05) points the build at this branding directory instead of the stock Firefox one.

## 🤔 Quirky Things Worth Knowing

### ⚠️ Looking styled and staying cool are usually in tension — here they are not

The insight is that visual richness does not have to cost CPU. Colour, contrast, and a good wallpaper are free once painted. It is *motion and layout change* that cost. By choosing a bold static palette over flashy animations, the theme is both distinctive and nearly free to render.

### ⚠️ One CSS file cannot reach everything

A documented gotcha: `master-redirect.css` is loaded via the browser's own chrome path (`chrome://browser/skin/`) and physically cannot reach toolkit widgets loaded via a different path (`chrome://global/skin/`) — things like the find-bar and notification popups. Those had to be styled by editing their source CSS directly (`toolkit/themes/shared/findbar.css`). Two of the four non-locale patches exist for exactly this reason.

### ⚠️ A .png must actually contain PNG data

Another hard-won lesson in the CSS notes: if you put SVG content inside a file named `.png` and reference it as a CSS `background-image`, the browser silently rejects it and the logo shows blank. Sounds obvious; cost real debugging time.

### ⚠️ The rebrand is the one place 'Gorilla' belongs everywhere

Across the project, the rule is to NOT sprinkle the word 'gorilla' onto new files and identifiers. But this folder is the exception that proves the rule: here, 'Gorilla Unleashed' is the product's actual public name, so replacing 'Firefox' with it in the user-visible strings is correct and intended — this is branding, not brand-spam.

## 💻 What Does This Mean For YOU?

### 🔋 Battery, Speed & Memory

The zero-CPU theme is the whole point: the interface renders on the GPU with the main processor staying idle, so the styled look does not cost battery. On a 2012 chip this is the difference between a theme that feels smooth and one that stutters.

### ⚡ Speed

Interface interactions (opening tabs, hovering buttons) stay snappy because none of them trigger a CPU layout recalculation.

### 🕵️ Your Privacy

None directly — this is cosmetic and identity work.

### 🌐 Your Internet

Zero — everything here is local rendering.

## 🔴 The Kill Switch — Explained

**What it is:** No runtime toggle — the look is fixed by design (Topic 07 also enforces the theme cannot be changed). The whole folder is the 'switch': it defines the appearance and the name.

**Without it:** The browser looks and is named like stock Firefox, and its theme uses default animations that wake the CPU on a machine that cannot spare it.

**Think of it like:** Not a switch — the paint job, the signage, and the rule that you decorate with light and colour instead of moving walls.

## 🌐 Open Source & Why It Matters To You

Every colour, every renamed string, every CSS rule is readable and changeable. Do not like cyan-on-black? It is one token. Want your own name instead of 'Gorilla Unleashed'? It is a find-and-replace across the locale tree. A closed browser's look is baked in; here it is a starting point you own.

## 📖 Glossary (Plain English Dictionary)

**Chrome (browser chrome)** — The browser's own interface — toolbars, tabs, menus — as opposed to the web page content. 'Chrome' here has nothing to do with Google Chrome; it is the older, general term.

**FTL / Fluent** — Mozilla's localization file format (.ftl). Holds the translated/branded text strings for the interface. Structurally fragile — a misplaced edit can blank a whole window.

**Design token** — A named reference to a colour, font, or spacing value, used instead of hard-coding the value everywhere. Change the token, everything using it updates.

**Zero-CPU theme** — A theme deliberately built to render entirely on the GPU, using only properties (colour, opacity, transform) that do not force the CPU to recalculate page layout.

**Layout thrash / reflow** — When a visual change forces the browser to recompute the position and size of elements — expensive, CPU-bound, and the thing this theme is built to avoid.

**XUL** — The older UI layout language Firefox's interface is built in. Some CSS effects (like scaling transforms) break XUL layout entirely, which is why the theme avoids them on toolbar elements.

---
*Human Track. Its Developer Track twin (`08-look.DEVELOPER.md`) covers the same changes in technical detail. Neither is a simplified copy of the other — they are the same truth in two languages.*