# CSS.UI.TWEAKS MEGA LESSON — Gorilla Unleashed Firefox 154

## Unified Reference for All UI, CSS, Theming, Branding, Icon, Locale, and Desktop Integration Lessons

**Hardware Target**: Intel i7-3632QM, Intel HD 4000 (Ivy Bridge Gen 7), 8GB RAM, Debian 13 Trixie, Wayland/GNOME 48
**Source Tree**: `/home/gorilla/firefox-main/` (mozilla-central 154)
**Build Object Dir**: `obj-x86_64-pc-linux-gnu/`
**Profile Dir**: `obj-x86_64-pc-linux-gnu/tmp/profile-default/`

---

## TABLE OF CONTENTS

1. [Architecture: The Master Redirector Pattern](#1-architecture-the-master-redirector-pattern)
2. [Zero-CPU Rendering Pipeline (Intel HD 4000)](#2-zero-cpu-rendering-pipeline-intel-hd-4000)
3. [Color System: Pure Black / Cyan Palette](#3-color-system-pure-black--cyan-palette)
4. [Tab System](#4-tab-system)
5. [Navigation Controls: Unicode Glyph Replacements](#5-navigation-controls-unicode-glyph-replacements)
6. [URL Bar & Shadow DOM Pierce](#6-url-bar--shadow-dom-pierce)
7. [Menus, Panels & Popups](#7-menus-panels--popups)
8. [Window Controls (CSD) — Close/Min/Max Buttons](#8-window-controls-csd--closeminmax-buttons)
9. [New Tab Button Visibility](#9-new-tab-button-visibility)
10. [Branding & Icons: Lanczos Resampling Pipeline](#10-branding--icons-lanczos-resampling-pipeline)
11. [Desktop Integration: .desktop, XDG hicolor, Wayland](#11-desktop-integration-desktop-xdg-hicolor-wayland)
12. [Localization: Fluent FTL Safety & Rebranding](#12-localization-fluent-ftl-safety--rebranding)
13. [Asset Ablation: Ghost Shims & Icon Purge Pipeline](#13-asset-ablation-ghost-shims--icon-purge-pipeline)
14. [CSS Performance Traps](#14-css-performance-traps)
15. [XUL Layout Bugs & Fixes](#15-xul-layout-bugs--fixes)
16. [Build, Deploy & Debugging](#16-build-deploy--debugging)
17. [Firefox Preferences (user.js / firefox.js)](#17-firefox-preferences-userjs--firefoxjs)
18. [Key File Paths Reference](#18-key-file-paths-reference)
19. [Quick Command Reference](#19-quick-command-reference)

---

## 1. ARCHITECTURE: THE MASTER REDIRECTOR PATTERN

### The Problem
Standard Firefox ships 70+ individual CSS theme files. Patching each one is fragile and bloated.

### The Solution
A single `master-redirect.css` file injected via `@import` into the two core theme entry points:

**Injection Points:**
```
browser/themes/shared/browser-shared.css  →  @import url("chrome://browser/skin/master-redirect.css");
toolkit/themes/shared/global-shared.css   →  @import url("chrome://global/skin/master-redirect.css");
```

**Live file location in source tree:**
```
browser/themes/shared/master-redirect.css
```

This single file overrides all CSS variables at `:root` level, forcing the entire browser chrome to adopt Pure Black (#000000) backgrounds and Pure Cyan (#00FFFF) text. Every other theme file's colors are automatically neutralized because the CSS variable cascade flows downstream.

### Why This Works
Firefox's theme system uses CSS custom properties (variables) defined on `:root`. By overriding these at the highest specificity (`!important` on `:root`), every downstream consumer — tabs, panels, menus, toolbars, URL bar — inherits the forced values without needing per-file patches.

### Design Tokens
The full color token system lives in two files:
- `tokens-shared.css` — 1126 lines defining color variables (Black, Blue, Cyan, Gray, Green, Orange, Pink, Purple, Red, Violet, Yellow, White with alpha variants), plus border, button, card, checkbox, focus, font, icon, input, panel, size, space, table, text, toolbar, toolbarbutton token mappings
- `tokens-brand.css` — Brand-specific accent colors using `light-dark()` CSS function for theme switching

Both are overridden by master-redirect.css's `:root` block.

---

## 2. ZERO-CPU RENDERING PIPELINE (INTEL HD 4000)

### The Rendering Pipeline
Firefox renders every frame through four stages:

| Stage | Thread | What It Does |
|-------|--------|-------------|
| 1. Style Calc | CPU Main | CSS selector matching against DOM |
| 2. Layout | CPU Main | Box model computation, positioning |
| 3. Paint | CPU Main | Rasterize elements into texture tiles |
| 4. Composite | GPU Compositor | Assemble pre-baked textures on screen |

**Target**: All theme interactions must live entirely in Stage 4 (Composite) — zero CPU involvement.

### Intel HD 4000 Hardware Units

| Unit | Function | CSS Property |
|------|----------|-------------|
| Fixed-Function Transform Unit | Matrix math | `transform: translate()`, `transform: scale()` |
| ROP (Raster Operations Pipeline) | Alpha blending | `opacity` |
| TMU (Texture Mapping Unit) | Texture/image sampling | `background-image` (static only) |
| 16 Execution Units (EUs) | Programmable shaders | `filter: brightness()`, `filter: contrast()` |

### APPROVED CSS Properties (GPU-Native, Zero CPU)

| Property | GPU Unit | Notes |
|----------|----------|-------|
| `transform: translate()` | Fixed-Function Transform | Pure matrix multiply |
| `transform: scale()` | Fixed-Function Transform | Pure matrix multiply |
| `opacity` | ROP Alpha Blend | Hardware blend, zero CPU |
| `filter: brightness()` | Execution Units | Simple per-pixel math |
| `filter: contrast()` | Execution Units | Simple per-pixel math |
| `outline` | — | Does NOT trigger layout reflow |

### FORBIDDEN CSS Properties (CPU Reflow Triggers)

| Property | Why Forbidden |
|----------|--------------|
| `width`, `height` | Triggers full layout recalculation |
| `margin`, `padding` | Cascades box model changes through DOM tree |
| `border` | Changes box model dimensions → layout thrash |
| `top`, `left`, `bottom`, `right` | Positional reflow on every frame |
| `transition: all` | Forces CPU to monitor ALL properties including layout ones |
| `backdrop-filter: blur()` | Heavy compositing pass, expensive even on GPU |
| `box-shadow` | Expensive blend operation |

### GPU Layer Promotion
To force Intel HD 4000 to promote an element to its own compositor layer:
```css
.container {
    transform: translate3d(0, 0, 0);  /* Promote to GPU layer */
}
.interactive-element {
    will-change: opacity;  /* Must be set BEFORE interaction */
}
```

### Global will-change Suppression
WebRender over-promotes elements to independent graphics layers, thrashing VRAM on older Intel HD 4000 GPUs and inducing WebRender scene builder stalls:
```css
* { will-change: auto !important; }
```

### Containment Isolation
Prevents style invalidation from cascading up the DOM tree:
```css
#navigator-toolbox {
    contain: layout style;  /* Isolates subtree */
}
```
**CRITICAL**: Use `contain: layout style`, NOT `contain: paint` — the latter breaks XUL flexbox contexts.

### Z-Index Minimalism
Aggressively high `z-index` values (like 2147483647) force unnecessary new stacking contexts and compositor layers, wasting shared VRAM on integrated graphics. Use absolute minimum values (e.g., `z-index: 2`).

### XUL Transform Prohibition
**NEVER** apply `transform: scale()` or `transform: translate()` to:
- `.toolbarbutton-1`
- `.tabbrowser-tab`
- XUL toolbar children

This completely collapses XUL layout. Transforms are safe on non-XUL content areas only.

---

## 3. COLOR SYSTEM: PURE BLACK / CYAN PALETTE

### The Palette
| Role | Color | Hex |
|------|-------|-----|
| All backgrounds | Pure Black | `#000000` |
| All text / icons | Pure Cyan | `#00FFFF` |
| Active tab background | Pink | `#FFC0CB` |
| Active tab text | Black | `#000000` |
| Active tab close button | Navy Blue | `#000080` |
| Close button hover | Red | `#FF3750` |
| Global dark mode | — | `color-scheme: dark` |

### CSS Variable Override Block
All of these are set on `:root, #main-window, #browser-window, window` with `!important`:

```css
/* Base Blacks */
--lwt-accent-color: #000000;
--lwt-frame: #000000;
--tabpanel-background-color: #000000;
--color-gray-05 through --color-gray-90: #000000;
--panel-background: #000000;
--panel-background-color: #000000;
--arrowpanel-background: #000000;
--toolbar-bgcolor: #000000;
--chrome-content-separator-color: #000000;
--toolbar-field-background-color: #000000;
--lwt-toolbar-field-background-color: #000000;
--urlbar-box-bgcolor: #000000;
--urlbar-box-background-color: #000000;
--input-bgcolor: #000000;
--newtab-background-color: #000000;
--newtab-background-color-secondary: #000000;

/* Text Visibility */
--lwt-tab-text: #FFFFFF;
--panel-text-color: #00FFFF;
--toolbar-field-color: #00FFFF;
--lwt-toolbar-field-color: #00FFFF;
--input-color: #00FFFF;
--newtab-text-primary-color: #00FFFF;

color-scheme: dark;
```

### The Color Mutation Trap
If a color renders completely wrong (e.g., LightPink instead of Aquamarine), it's likely caused by property stacking. A rogue `outline: 2px solid #FFC0CB` rule HIGH in the cascade will NOT be overwritten by a later `border: 1px solid #7FFFD4` — both render simultaneously, producing a mutated pixel blend.

**Fix**: Search for and destroy overlapping `outline`, `box-shadow`, and `border` rules when defining new colors.

---

## 4. TAB SYSTEM

### Active Tab — Pink Background with Black Text
```css
.tabbrowser-tab[selected] .tab-background {
    background-color: #FFC0CB !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
}
.tabbrowser-tab[selected] .tab-label {
    color: #000000 !important;
    font-weight: normal !important;
}
.tabbrowser-tab[selected] .tab-close-button {
    color: #000080 !important;
    fill: #000080 !important;
    font-weight: bold !important;
}
```

### Inactive Tab — Cyan Text on Black
```css
.tabbrowser-tab:not([selected]) .tab-label {
    color: #00FFFF !important;
}
.tabbrowser-tab:not([selected]) .tab-close-button {
    color: #00FFFF !important;
    fill: #00FFFF !important;
}
```

### Inactive Tab Hover — GPU-Only Outline
No borders, no padding changes. Pure outline and GPU opacity:
```css
.tabbrowser-tab:not([selected]):hover .tab-background {
    background-color: transparent !important;
    outline: 1px solid #00FFFF !important;
    outline-offset: -1px !important;
    opacity: 0.8 !important;  /* HD4000 ROP handles alpha blend natively */
}
```

### Tab Close Button (SVG Excision Technique)
Hides native SVG-based close button icon, converts to text glyph:
1. Hide native icon: `.tab-close-button > .toolbarbutton-icon { display: none !important; }`
2. Convert parent to flex: `.tab-close-button { display: -moz-box !important; }`
3. Inject monospace glyph: `content: "\00D7"` (multiplication sign x)

### Website Favicon Purge
Eliminates runtime CPU paint cycles when tabs load or change website favicons:
```css
.tab-icon-image, .tab-sharing-icon-overlay, .tab-icon-overlay {
    display: none !important;
}
```

### Tab Hover Previews Excision
Disables heavy layout and thumbnail generation engine:
```
browser.tabs.hoverPreview.enabled = false
browser.tabs.hoverPreview.showThumbnails = false
browser.tabs.groups.hoverPreview.enabled = false
```
**JS Modification**: Patched `browser/components/tabbrowser/content/tab.js` mouse enter/leave listeners to prevent dispatching custom XUL events (`TabHoverStart`, `TabHoverEnd`) if preference is disabled. Stops event creation, object allocation, and DOM bubbling overhead on mouse movement.

### Phantom Tab Pin Box Bug
Fixed by applying:
```css
#pinned-drop-indicator-text, #pinned-drop-indicator {
    display: none !important;
}
```

---

## 5. NAVIGATION CONTROLS: UNICODE GLYPH REPLACEMENTS

Replace SVG vector icons with lightweight Unicode characters to eliminate XML parsing, Skia vector path evaluation, and VRAM texture upload thrashing:

| Button | Glyph | Unicode | Font Size |
|--------|-------|---------|-----------|
| Back | `<` | U+003C | 16px |
| Forward | `>` | U+003E | 16px |
| Reload | `↻` | U+21BB | 16px |
| Stop | `■` | U+25A0 | 12px (visual harmony) |
| Home | `⌂` | U+2302 | 16px |
| Tab Close | `x` | U+00D7 | 16px monospace |

### Implementation Pattern
For each toolbar button:
1. Hide native SVG icon: `.toolbarbutton-icon { display: none !important; }`
2. Set display to flex: `display: -moz-box !important;`
3. Inject glyph via `::before` pseudo-element: `content: "<"; font-family: monospace; color: #00FFFF;`

### XUL Menubar Ghost Text Buttons
For unclickable text buttons injected over native XUL buttons: do NOT rely on pseudo-elements alone. Set the native button to `display: -moz-box !important`, `min-width: 48px`, `min-height: 24px` to ensure the click target perfectly overlaps the injected text. AVOID `position: relative` on menubars — it causes flexbox collapse.

---

## 6. URL BAR & SHADOW DOM PIERCE

### Placeholder Text
```css
.urlbar-input::placeholder, .searchbar-textbox::placeholder {
    opacity: 1 !important;
    color: #00FFFF !important;
}
```

### Focus Ring
```css
#urlbar[focused="true"] > #urlbar-background {
    outline: 2px solid #00FFFF !important;
    outline-offset: -2px !important;
    border: none !important;
    box-shadow: none !important;
}
```

### Shadow DOM Pierce (Search Pill)
The new tab search pill is a Web Component using Shadow DOM (`<content-search-handoff-ui>`), which hardcodes `opacity: 0.54` on `.fake-textbox`. Standard CSS overrides fail — you must pierce the Shadow DOM directly in the component's internal stylesheet:

```css
/* In browser/components/search/content/contentSearchHandoffUI.css */
.fake-textbox {
    opacity: 1 !important;
    color: #00FFFF !important;
}
```

---

## 7. MENUS, PANELS & POPUPS

### Menu Item Styling
```css
#categories > .category, #categories > radio, .menu-item, .toolbarbutton {
    appearance: none !important;
    -moz-default-appearance: none !important;
    background-color: #000000 !important;
    border: none !important;
    outline: none !important;
}
```

### Menu Hover — GPU Outline
```css
.menu-item:hover, .toolbarbutton:hover {
    outline: 1px solid #00FFFF !important;
    outline-offset: -1px !important;
    background-color: #000000 !important;
}
```

### Extensions & Private Browsing Cleanup
Remove `.info-border` to prevent purple FOUC during window resizes:
```css
#unified-extensions-panel { background-color: #000000 !important; }
.info-border { display: none !important; }
```

### About:Addons Theme Recommendations Lobotomy
```css
.theme-disabled-section,
footer[is="recommended-themes-footer"],
recommended-themes-section,
.theme-recommendation,
.amo-link-container {
    display: none !important;
}
```

### Popup Artifact Override — Autocomplete Icon Clamping
Runaway autocomplete login/favicon icons cause visual artifacts:
```css
.ac-site-icon,
panel[type="autocomplete-richlistbox"] image,
panel[type="autocomplete-richlistbox"] img {
    max-width: 16px !important;
    max-height: 16px !important;
    object-fit: contain !important;
}
autocomplete-row-item {
    --icon-width: 16px !important;
    --icon-height: 16px !important;
}
```

---

## 8. WINDOW CONTROLS (CSD) — CLOSE/MIN/MAX BUTTONS

### The Problem
Titlebar buttons (close, minimize, maximize) are SVG icons that inherit color from the theme. When all theme colors are forced to #000000, the buttons become invisible (black on black).

### The Fix
```css
.titlebar-button > .toolbarbutton-icon {
    color: #00FFFF !important;
    fill: #00FFFF !important;
    -moz-context-properties: fill, fill-opacity, stroke !important;
}
.titlebar-close:hover > .toolbarbutton-icon {
    color: #FF3750 !important;
    fill: #FF3750 !important;
}
```

### Key Detail: `-moz-context-properties`
Firefox SVG icons use a special mechanism where the SVG reads `fill` and `stroke` colors from the parent element via `-moz-context-properties`. Without declaring this property on the parent, `fill: #00FFFF` has no effect on the SVG content.

---

## 9. NEW TAB BUTTON VISIBILITY

### The Problem
The "+" new tab button is black-on-black when all colors are forced to #000000.

### The Fix
```css
#tabs-newtab-button,
#vertical-tabs-newtab-button,
#TabsToolbar #new-tab-button {
    color: #00FFFF !important;
    fill: #00FFFF !important;
}
#tabs-newtab-button > .toolbarbutton-icon,
#vertical-tabs-newtab-button > .toolbarbutton-icon,
#new-tab-button > .toolbarbutton-icon {
    color: #00FFFF !important;
    fill: #00FFFF !important;
    -moz-context-properties: fill, fill-opacity !important;
}
#tabs-newtab-button:hover,
#vertical-tabs-newtab-button:hover,
#new-tab-button:hover {
    outline: 1px solid #00FFFF !important;
    outline-offset: -1px !important;
}
```

---

## 10. BRANDING & ICONS: LANCZOS RESAMPLING PIPELINE

### The Master Icon
All icons are derived from a single high-resolution master: `icon1024.png` (1015x1024 pixels, in `browser/branding/gorilla/`).

### Lanczos Resampling Technique
Python PIL with `Image.LANCZOS` filter provides highest quality anti-aliasing for downsampling. The process:

```python
from PIL import Image

master = Image.open("icon1024.png")
# Crop to square (1015x1024 → 1015x1015)
size = min(master.size)
master = master.crop((0, 0, size, size))
# Downsample to target
target = master.resize((64, 64), Image.LANCZOS)
target.save("icon64.png")
```

### Branding Icon Sizes Required
All in `browser/branding/gorilla/`:

| File | Pixel Size | Purpose |
|------|-----------|---------|
| `icon16.png` | 16x16 | Favicon |
| `icon32.png` | 32x32 | Window icon |
| `icon48.png` | 48x48 | Task switcher |
| `icon64.png` | 64x64 | About dialog (small) |
| `icon128.png` | 128x128 | About dialog (large) |
| `icon256.png` | 256x256 | System icon |
| `icon512.png` | 512x512 | HiDPI system icon |
| `default16.png` | 16x16 | XUL window icon |
| `default32.png` | 32x32 | XUL window icon |
| `default48.png` | 48x48 | XUL window icon |
| `default64.png` | 64x64 | XUL window icon |
| `default128.png` | 128x128 | XUL window icon |
| `default256.png` | 256x256 | XUL window icon |

**CRITICAL**: Every file MUST contain a PNG at its stated pixel dimensions. Do NOT copy the same large PNG to all filenames — Firefox uses the actual pixel data, and oversized icons waste VRAM.

### About Dialog Logo

**aboutDialog.css** (line 24) references:
```css
background-image: url("chrome://branding/content/about-logo.png");
background-size: 500px 500px;
```

**activity-stream.css** (line ~1447) references:
```css
.logo-and-wordmark .logo {
    background: url("chrome://branding/content/about-logo.png") no-repeat center;
    background-size: 500px;
}
```

Both use `chrome://branding/content/about-logo.png` — this serves files from `browser/branding/gorilla/content/`.

### PNG vs SVG: The Critical Distinction

**RULE**: Files referenced via CSS `background-image: url(...)` MUST be actual PNG files, not SVG content masquerading as .png.

| File | Format | Size | Purpose |
|------|--------|------|---------|
| `about-logo.png` | Actual PNG | 500x500 | CSS background-image (aboutDialog, activity-stream) |
| `about-logo@2x.png` | Actual PNG | 1000x1000 | HiDPI CSS background-image |
| `about-logo.svg` | SVG wrapping base64 PNG | 800x800 | Direct SVG references (`<image>` tags) |
| `about-logo-private.png` | Actual PNG | 500x500 | Private browsing variant |
| `about-logo-private@2x.png` | Actual PNG | 1000x1000 | Private browsing HiDPI |

**The SVG-as-PNG Trap**: If you copy SVG content into a .png file, Firefox's CSS `background-image` loader silently rejects it — logos show blank/nothing. The chrome:// protocol does NOT sniff content-type; it trusts the file extension.

### SVG Logo Construction
The about-logo.svg wraps a Lanczos-resampled PNG in an SVG container:
```xml
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="800">
  <image width="800" height="800"
    href="data:image/png;base64,iVBORw0KGgo..." />
</svg>
```

**CSS Overrides for SVG display**:
```css
background-size: contain;  /* Prevent cropping of 800x800 intrinsic SVG */
```

### Splash Logo (about:welcome)
The welcome page splash logo lives at:
```
browser/components/aboutwelcome/assets/splash-logo.svg
```
Replace with gorilla SVG. It's symlinked from:
```
dist/bin/browser/chrome/browser/content/activity-stream/data/content/assets/splash-logo.svg
```

### Master Icon Variable
In master-redirect.css:
```css
:root {
    --gorilla-master-icon: url("chrome://branding/content/about-logo.svg");
}
```

Used to override illustration classes:
```css
.illustration, .info-icon, .error-icon, .panel-illustration, .category-icon {
    content: var(--gorilla-master-icon) !important;
    background-image: var(--gorilla-master-icon) !important;
    background-size: contain !important;
    background-repeat: no-repeat !important;
    background-position: center !important;
    -moz-context-properties: none !important;
    filter: none !important;
}
```

---

## 11. DESKTOP INTEGRATION: .desktop, XDG hicolor, Wayland

### The .desktop File
Location: `~/.local/share/applications/firefox-gorilla.desktop`

```ini
[Desktop Entry]
Version=1.0
Name=Gorilla Unleashed 154
GenericName=Web Browser
Comment=Firefox Unleashed optimized low-RAM build synced with BBR pacing
Exec=env MOZ_ENABLE_WAYLAND=1 /home/gorilla/firefox-main/obj-x86_64-pc-linux-gnu/dist/bin/firefox --class gorilla-unleashed -no-remote -profile /home/gorilla/firefox-main/obj-x86_64-pc-linux-gnu/tmp/profile-default %u
Icon=firefox-gorilla
Terminal=false
Type=Application
MimeType=text/html;text/xml;application/xhtml+xml;...
StartupNotify=true
StartupWMClass=gorilla-unleashed
Categories=Network;WebBrowser;
Actions=new-window;new-private-window;
```

### Critical .desktop Rules

| Field | Rule | Why |
|-------|------|-----|
| `Icon=` | Use basename only (no path, no extension) | GNOME on Wayland ignores absolute paths |
| `StartupWMClass=` | Must match `--class` flag value | GNOME uses this to associate windows with the .desktop entry |
| `Exec=` | Must include `--class gorilla-unleashed` | Sets Wayland `app_id` for window matching |
| `Exec=` | Must include `-no-remote` | Prevents IPC to existing Firefox instance |
| `Exec=` | Must include `-profile <path>` | Uses custom profile directory |
| `Exec=` | Must include `env MOZ_ENABLE_WAYLAND=1` | Forces Wayland backend |

### Orphan .desktop Cleanup
Only ONE .desktop file should exist. Remove any orphans:
```bash
rm -f ~/.local/share/applications/firefox-unleashed.desktop
```

### XDG hicolor Icon Theme
GNOME on Wayland requires icons in the hicolor theme directory. The `Icon=firefox-gorilla` field in .desktop looks up:
```
~/.local/share/icons/hicolor/{size}x{size}/apps/firefox-gorilla.png
```

**Required sizes**: 16, 22, 24, 32, 48, 64, 128, 256, 512

**Installation**:
```bash
for size in 16 22 24 32 48 64 128 256 512; do
    mkdir -p ~/.local/share/icons/hicolor/${size}x${size}/apps
    # Generate properly sized PNG from master icon
    python3 -c "
from PIL import Image
img = Image.open('icon1024.png')
s = min(img.size)
img = img.crop((0,0,s,s)).resize(($size,$size), Image.LANCZOS)
img.save('$HOME/.local/share/icons/hicolor/${size}x${size}/apps/firefox-gorilla.png')
"
done
```

**index.theme**: Required for `gtk-update-icon-cache`:
```ini
# ~/.local/share/icons/hicolor/index.theme
[Icon Theme]
Name=Hicolor
Comment=Fallback Icon Theme
Directories=16x16/apps,22x22/apps,24x24/apps,32x32/apps,48x48/apps,64x64/apps,128x128/apps,256x256/apps,512x512/apps

[16x16/apps]
Size=16
Context=Applications
Type=Fixed
...
```

**Rebuild icon cache**:
```bash
gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor/
update-desktop-database ~/.local/share/applications/
```

### Generic Placeholder in Dock/Dash
If Firefox shows a generic gear/placeholder icon in the GNOME dash while running, the cause is `app_id` mismatch:
1. The running window's `app_id` (set by `--class gorilla-unleashed`) must match `StartupWMClass=gorilla-unleashed` in the .desktop file
2. The .desktop file's `Icon=firefox-gorilla` must resolve to actual PNGs in hicolor

---

## 12. LOCALIZATION: FLUENT FTL SAFETY & REBRANDING

### The Fluent HTML Interpolation Bug

Mozilla's Fluent localization framework supports HTML element mapping via `data-l10n-name`:
```fluent
bookmarks-toolbar-empty-message = For quick access, place your bookmarks here. <a data-l10n-name="manage-bookmarks">Manage bookmarks...</a>
```

**DANGER**: Naive regex replacement (Firefox → Gorilla) mutates attribute values:
```
data-l10n-name="manage-bookmarks"  →  data-l10n-name="manage-Gorilla bookmarks"
```

During DOM hydration, the renderer searches for ID `manage-bookmarks`, fails to find it → Promise rejects → blocks instantiation of entire UI panel → invisible windows or silent crashes.

### The Fix
All text replacement regex must implement strict boundaries:
- Use negative lookbehinds to skip content between `<` and `>`
- Or use a dedicated tag-stream parser that ignores HTML tag content
- Only modify visible, external strings — never touch `data-l10n-name`, `data-l10n-id`, or any HTML attribute

### The "Gorilla Gorilla" Duplicate Bug
Automated Firefox → Gorilla replacement creates doubles when "Firefox" appears after another word that gets "Gorilla" appended:

| Before | Broken Result | Correct |
|--------|--------------|---------|
| "Open Link in New Firefox Tab" | "Open Link in New Gorilla Container Gorilla Tab" | "Open Link in New Container Gorilla Tab" |
| "Open Link in New Firefox Window" | "Open Link in New Private Gorilla Window" | "Open Link in New Private Gorilla Window" |
| "Firefox Bookmark Firefox Page" | "Gorilla Bookmark Gorilla Page" | "Gorilla Bookmark Page" |

**Fix**: Manual review and sed correction across all locale files:
```bash
sed -i 's/Gorilla Container Gorilla Tab/Container Gorilla Tab/g' browser/locales/en-US/browser/browserContext.ftl
sed -i 's/Gorilla Bookmark Gorilla/Gorilla Bookmark/g' browser/locales/en-US/browser/browserContext.ftl
```

### Affected Locale Files
Files that commonly contain duplicates after automated rebranding:
- `browser/locales/en-US/browser/browserContext.ftl`
- `browser/locales/en-US/browser/syncedTabs.ftl`
- `browser/locales/en-US/chrome/browser/browser.properties`
- `browser/locales/en-US/chrome/browser/taskbar.properties`
- `browser/locales/en-US/browser/addonNotifications.ftl`

### Fluent Parser Strictness
The `.ftl` parser is extremely strict about indentation:
- Blank lines between a message value and its `.description` attribute are FATAL
- Inconsistent indentation silently drops attributes
- Always validate after editing: check that Firefox starts and the UI renders

### Localization Blast Radius
Standard `brand.ftl` and `brand.properties` cover only high-level application name variables (`{ -brand-short-name }`). Hardcoded UI strings exist in component-specific files. Total rebranding requires recursing through the entire `locales` tree — 235+ FTL files:
- `browser/appmenu.ftl` (Hamburger Menu)
- `browser/newtab/newtab.ftl` (about:home page)
- `toolkit/about/aboutAddons.ftl` (Extensions manager)
- `browser/tabContextMenu.ftl` (Right-click menus on tabs)

---

## 13. ASSET ABLATION: GHOST SHIMS & ICON PURGE PIPELINE

### The Problem
Gecko engine treats hidden/0-byte UI nodes as first-class citizens. CSS `display: none` or 1x1 transparent SVGs DO NOT stop rendering calculations. The engine still executes:
1. **DOM Allocation**: C++ object instantiation in RAM
2. **Layout & Reflow**: Bounding box, margin, padding, flex computation
3. **Network/Cache Polling**: JS controllers request/decode favicon data
4. **Accessibility Tree**: Node mapping to OS-level accessibility APIs
5. **CSSOM Parsing**: Memory retention of CSS rules

### The Solution: Source-Level Ablation
Elements must be physically ripped from source tree BEFORE compilation so the binary linker never sees them.

### The 63-Byte Transparent SVG Ghost Shim
For assets that can't be deleted (build system expects them), replace with:
```xml
<svg xmlns="http://www.w3.org/2000/svg"/>
```
This satisfies the build engine and CSS loaders, parses instantly, and paints nothing.

### Four-Step Ablation Pipeline (Run Before `./mach build`)

**Step 1: Markup Ablation (XHTML/HTML/XUL)**
```bash
TARGET_CLASSES="tab-icon-image|tab-icon-overlay|bookmark-icon"
find browser/ toolkit/ -type f \( -name "*.xhtml" -o -name "*.html" -o -name "*.inc" \) \
    -exec sed -i -E "/<(image|img|svg)[^>]*class=\"[^\"]*($TARGET_CLASSES)[^\"]*\"[^>]*>/d" {} +
```

**Step 2: CSS Purge (State-Machine Brace Depth Tracking)**
Regex fails on nested CSS — use Python state machine:
```python
def purge_css_block(filepath, target_classes):
    with open(filepath, 'r') as f:
        content = f.read()
    for cls in target_classes:
        pattern = re.compile(r'([^{]*\.' + cls + r'[^{]*)\{')
        while match := pattern.search(content):
            start_idx = match.start()
            depth = 1
            curr_idx = match.end()
            while depth > 0 and curr_idx < len(content):
                if content[curr_idx] == '{': depth += 1
                elif content[curr_idx] == '}': depth -= 1
                curr_idx += 1
            content = content[:start_idx] + content[curr_idx:]
    with open(filepath, 'w') as f:
        f.write(content)
```

**Step 3: Logic Neutering (JavaScript/C++/Rust)**
```bash
sed -i '/_updateIcon(aURI)/,/^  }/c\  _updateIcon(aURI) { return; }' \
    browser/base/content/tabbrowser-tab.js
```

**Step 4: Asset Manifest Unlinking (jar.mn)**
```bash
TARGET_ASSETS="default.png|icon16.svg|bookmark.svg"
find browser/ toolkit/ -name "jar.mn" -exec sed -i -E "/($TARGET_ASSETS)/d" {} +
```

---

## 14. CSS PERFORMANCE TRAPS

### Trap 1: The Universal Selector Annihilation (CRITICAL)
```css
/* BAD — forces CPU to traverse EVERY node on EVERY layout change */
*, *::before, *::after {
    animation-duration: 0.01ms !important;
}

/* BETTER — target only known animating elements */
.tab-throbber, .tab-loading-burst, .urlbar-input, .tab-background, .tabbrowser-tab {
    animation-duration: 0.01ms !important;
}
```

**Note**: The current master-redirect.css still uses the universal selector for animation annihilation. This is a known tradeoff — comprehensive coverage vs CPU cost. For the Intel HD 4000, the animation kill is more important than the selector traversal cost.

### Trap 2: Linear-Gradient Compositing
```css
/* BAD — dynamic gradient over large image forces constant re-rasterization */
background-image: linear-gradient(...), url("nebula.jpg") !important;

/* FIX — pre-composite the image offline, serve as flat texture */
background-image: url("pre-composited.png") !important;
```

### Trap 3: Border vs Outline (Layout Thrash)
```css
/* BAD — border changes box model dimensions → layout recalc */
border: 1px solid #00FFFF !important;

/* GOOD — outline sits outside box model → no reflow */
outline: 1px solid #00FFFF !important;
outline-offset: -1px !important;
```

### Trap 4: Throbber and Progress Animation Kill
```css
.tab-throbber, .tab-loading-burst, .tab-icon-pending, .tab-icon-image,
progress, .progress-bar, #tabbrowser-tabpanels {
    animation: none !important;
    transition: none !important;
    background-image: none !important;
}
```

---

## 15. XUL LAYOUT BUGS & FIXES

### Bug 1: The Parentheses "( )" Effect
**Symptom**: Tabs render as `( )` instead of `[ ]` after adding borders.
**Cause**: Physical `border` on `.tab-background` increases element width/height. Parent `#TabsToolbar` has strict `max-height: 36px` — border expansion exceeds bounds, clipping top and bottom edges off-screen.
**Fix**:
```css
.tab-background {
    box-sizing: border-box !important;
}
```
Ensures borders draw *inward* without affecting element footprint.

### Bug 2: The "Sunken Floor" Tab Alignment
**Symptom**: Tabs appear sunk into the navigation bar after resizing.
**Cause**: Firefox uses `align-items: flex-end` on tabs. Shrunk tabs (30px) inside larger container (36px) get pulled entirely to the bottom.
**Fix**:
```css
.tabbrowser-tab {
    margin-top: auto !important;
    margin-bottom: auto !important;
}
.tab-background {
    margin-block: 0px !important;
}
```
Mathematically centers tab with guaranteed padding above and below.

### Bug 3: Invisible Flex Spacers
**Symptom**: After removing standard icons around URL bar, native `toolbarspring` spacers become massive gray blocks.
**Fix**:
```css
#urlbar-container {
    max-width: none !important;
    flex-grow: 1 !important;
}
toolbarspring {
    background-color: #000000 !important;
}
```

### Bug 4: Native Variable Injection vs Hardcoded Bounds
**Bad**: Hardcoding `max-height` or `min-height` on `.tabbrowser-tab` elements disrupts XUL flexbox calculations.
**Better**: Inject native Firefox variable:
```css
:root {
    --tab-min-height: 30px !important;
}
```
Parent containers (`#tabbrowser-tabs`, `.tabbrowser-arrowscrollbox`) inherit the variable and the native layout engine computes constraints seamlessly.

---

## 16. BUILD, DEPLOY & DEBUGGING

### Incremental Build (After CSS/Locale/Branding Changes)
```bash
cd /home/gorilla/firefox-main
./mach build faster
```
Re-scans source tree and syncs changes to `obj-x86_64-pc-linux-gnu/dist/bin/`. No full recompilation needed for CSS, locale, and branding asset changes.

### Full Build (After C++/Rust Source Changes)
```bash
./mach build
```

### startupCache Flush
**REQUIRED** after changing branding/CSS/locale files. Firefox caches parsed XUL, CSS, and locale data:
```bash
rm -rf obj-x86_64-pc-linux-gnu/tmp/profile-default/startupCache/*
```

### Zombie Profile Lock (.parentlock)
If `mach run` exits immediately with code 0 in ~2 seconds without compiler error, the profile database is locked. Happens after `pkill firefox`:
```bash
rm -f obj-x86_64-pc-linux-gnu/tmp/profile-default/.parentlock
```

### Launch Firefox
```bash
pkill firefox 2>/dev/null; sleep 1
rm -f obj-x86_64-pc-linux-gnu/tmp/profile-default/.parentlock
rm -rf obj-x86_64-pc-linux-gnu/tmp/profile-default/startupCache/*
MOZ_ENABLE_WAYLAND=1 ./mach run --class gorilla-unleashed -no-remote -profile obj-x86_64-pc-linux-gnu/tmp/profile-default
```

### Theme Injection Without Rebuild (Live Patching)
For installed Firefox (not dev build), `live_patch_injector.py` copies patches directly into `/usr/lib/gorilla-unleashed/` and clears startupCache. For dev builds, `mach build faster` is the equivalent.

### Prevent Mixing Old/New Binaries
When upgrading versions (153 → 154), completely nuke the install directory before copying:
```bash
rm -rf /usr/lib/gorilla-unleashed
```
Then purge startup cache to force XUL cache invalidation:
```bash
rm -rf ~/.cache/mozilla/firefox/*/startupCache
```

---

## 17. FIREFOX PREFERENCES (user.js / firefox.js)

### Baked into firefox.js (Active Out-of-Box)
```javascript
general.smoothScroll = false
dom.timeout.throttling_delay = 30000
dom.min_background_timeout_value = 10000
dom.timer.minimum_firing_delay_tolerance_ms = 1
dom.timeout.background_throttling_max_budget = 0
dom.wakelock.enabled = false
gfx.webrender.highlight-painted-layers = false
layout.animation.prerender.enabled = false
```

### Tab Hover Preview Kill
```javascript
browser.tabs.hoverPreview.enabled = false
browser.tabs.hoverPreview.showThumbnails = false
browser.tabs.groups.hoverPreview.enabled = false
```

### VA-API and GPU Compositing (from MEDIA_CODEC_LESSONS.md)
```javascript
media.ffmpeg.vaapi.enabled = true
media.hardware-video-decoding.force-enabled = true
media.hardware-video-decoding.enabled = true
widget.dmabuf.force-enabled = true
media.ffvpx.enabled = false
media.rdd-ffmpeg.enabled = true
gfx.webrender.compositor.force-enabled = true
media.ffmpeg.vaapi.allow-non-4k = true
media.av1.enabled = false
media.navigator.mediadatadecoder_vpx_enabled = true
layers.acceleration.force-enabled = true
gfx.canvas.accelerated = true
gfx.webrender.all = true
media.ffmpeg.vaapi.dma-buf.enabled = true
media.ffmpeg.vaapi.zero-copy.enabled = 1
```

---

## 18. KEY FILE PATHS REFERENCE

### Source Tree (mozilla-central 154)
```
browser/themes/shared/master-redirect.css          — The Master Redirector (core theme)
browser/themes/shared/browser-shared.css            — Injection point (@import)
toolkit/themes/shared/global-shared.css             — Injection point (@import)
browser/branding/gorilla/content/about-logo.png     — 500x500 actual PNG
browser/branding/gorilla/content/about-logo@2x.png  — 1000x1000 actual PNG
browser/branding/gorilla/content/about-logo.svg     — 800x800 SVG (base64 PNG)
browser/branding/gorilla/content/aboutDialog.css    — About dialog layout
browser/branding/gorilla/icon*.png                  — Branding icons (16-1024)
browser/branding/gorilla/default*.png               — XUL window icons (16-256)
browser/components/aboutwelcome/assets/splash-logo.svg — Welcome page logo
browser/components/search/content/contentSearchHandoffUI.css — Shadow DOM pierce
browser/components/tabbrowser/content/tab.js        — Tab hover preview JS
browser/locales/en-US/browser/branding/brand.ftl    — Brand name variables
browser/locales/en-US/browser/browserContext.ftl    — Context menu strings
```

### System Integration
```
~/.local/share/applications/firefox-gorilla.desktop
~/.local/share/icons/hicolor/{size}x{size}/apps/firefox-gorilla.png
~/.local/share/icons/hicolor/index.theme
```

### Build/Profile
```
obj-x86_64-pc-linux-gnu/dist/bin/firefox            — Built binary
obj-x86_64-pc-linux-gnu/tmp/profile-default/         — Dev profile
obj-x86_64-pc-linux-gnu/tmp/profile-default/.parentlock — Zombie lock
obj-x86_64-pc-linux-gnu/tmp/profile-default/startupCache/ — Must flush
obj-x86_64-pc-linux-gnu/tmp/profile-default/user.js  — Runtime prefs
```

### Documentation
```
patches/FIrefox.154.Look/master-redirect.css                              — Patch copy
patches/FIrefox.154.Look/tokens-brand.css                                 — Brand tokens
patches/FIrefox.154.Look/tokens-shared.css                                — Shared color system
patches/FIrefox.154.Look/MASTER_PROJECT_LOG_FIREFOX_154_LOOK_PATCHES.md   — Project log
patches/FIrefox.154.Look/notes/UI_Tweaks_Master_Collection/               — All lesson files
patches/MEDIA_CODEC_LESSONS.md                                            — VA-API/codec lessons
```

---

## 19. QUICK COMMAND REFERENCE

```bash
# Kill Firefox and clean locks
pkill firefox; sleep 1; rm -f obj-x86_64-pc-linux-gnu/tmp/profile-default/.parentlock

# Flush startup cache
rm -rf obj-x86_64-pc-linux-gnu/tmp/profile-default/startupCache/*

# Incremental build (CSS/locale/branding only)
./mach build faster

# Full build (C++/Rust changes)
./mach build

# Launch dev Firefox
MOZ_ENABLE_WAYLAND=1 ./mach run --class gorilla-unleashed -no-remote -profile obj-x86_64-pc-linux-gnu/tmp/profile-default

# Rebuild icon cache after installing hicolor icons
gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor/
update-desktop-database ~/.local/share/applications/

# Generate Lanczos-resampled icon
python3 -c "from PIL import Image; img=Image.open('icon1024.png'); s=min(img.size); img.crop((0,0,s,s)).resize((SIZE,SIZE), Image.LANCZOS).save('iconSIZE.png')"

# Find Gorilla Gorilla duplicates in locale files
grep -rn "Gorilla.*Gorilla" browser/locales/en-US/
```

---

## SOURCES

This document consolidates lessons from:
- `zero_cpu_theme_architecture_intel_hd4000.xml`
- `zero_cpu_tab_controls_and_hover_previews.xml`
- `Zero_CPU_UI_Glyphs_and_Rust_LTO.xml`
- `firefox_css_layout_clipping_and_variable_injection.xml`
- `Lessons_Learned_CSS_Performance.xml`
- `theme_zero_cpu_optimization.xml`
- `Theme_Guide.xml`
- `Icons_0_FOOTPRINT_ABLATION_PIPELINE.xml`
- `UI_TWEAKS_DOCUMENTATION.xml`
- `refactoring_theme_injector.xml`
- `UI_Tweaks_Mega_Lesson.md`
- `SVG_Injection_Lesson.md` / `Lessons_Learned_SVG_Injection.xml`
- `Menu.change.Theme. Injection.Firefox.154.md`
- `MASTER_PROJECT_LOG_FIREFOX_154_LOOK_PATCHES.md`
- `master-redirect.css` (deployed version — Firefox 154, session of 2026-07-15)
- `firefox-gorilla.desktop` (deployed version — 2026-07-15)
- `MEDIA_CODEC_LESSONS.md` (VA-API / hardware decoding section)
- Direct session work: window controls CSD fix, new tab button fix, inactive tab text fix, about-logo PNG vs SVG fix, desktop file XDG consolidation, hicolor icon deployment (2026-07-15)
