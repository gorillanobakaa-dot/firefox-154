# Mega Lesson: The Gorilla Unleashed UI Tweak Architecture

This master document condenses all historical lessons, techniques, and methodologies regarding Firefox UI modification, asset excision, and rendering engine optimization into a single, unified architectural guide.

## The Prime Directive: Zero Footprint UI
The core philosophy is that any UI element that is not strictly necessary for the customized browsing experience should be surgically removed—not just hidden with CSS. Firefox's Gecko engine will still allocate DOM nodes, build CSSOM trees, and calculate layout for elements hidden via `display: none;`. True optimization requires source-level structural ablation.

### Technique 1: The Canonical Master Icon & Ghost Shims
**Problem:** A standard Firefox build ships with thousands of individual SVG icons, weighing down the IO and parsing layers.
**Solution:**
1. **The Single Source:** Create one single, canonical master icon (e.g., an 800x800 Lanczos-downsampled PNG injected into an SVG wrapper).
2. **Symlink Routing:** Route shared visual targets to this single file using symlinks or by overriding the `<image>` `href` attributes in CSS.
3. **The Ghost Shim:** For every other UI illustration or icon that must be removed without crashing the CSSOM or resource loaders, we do not delete the file. Instead, we replace it with a **63-byte transparent SVG** (or a 0-byte ghost file). This satisfies the build engine and the CSS loaders, but parses instantly and paints nothing.

### Technique 2: Text/Glyph Overlay Ablation (`svg_to_text_icons_v2.py`)
**Problem:** Rendering vectors is CPU intensive. When multiple icons exist in toolbars, menus, and context windows, the painting pipeline stutters.
**Solution:**
We use a CSS overlay method to intercept standard icon requests (`list-style-image`, `mask-image`, `background-image`).
1. We null out the SVG call: `list-style-image: none !important;`
2. We inject a plaintext unicode or ASCII character using pseudo-elements: `::before { content: "X" !important; font-family: monospace; }`.
This bypasses vector decoding completely and relies on highly optimized OS-level font rendering.

### Technique 3: Safe Fluent (.ftl) Injection
**Problem:** Naively searching and replacing text in `.ftl` (Fluent) files to rebrand the UI (e.g., replacing "Firefox" with "Gorilla") often breaks the UI rendering completely. Fluent strings can contain HTML element bindings like `<a data-l10n-name="manage-bookmarks">`. If the `data-l10n-name` attribute is accidentally changed by regex, Firefox's DOM hydration fails, causing invisible windows or silent crashes.
**Solution:**
All text replacement regex must implement strict boundaries (e.g., negative lookbehinds) or use a dedicated tag-stream parser to **ignore everything between `<` and `>`**. Only the visible, external strings may be modified.

### Technique 4: Zero-CPU Layout and Hardware Acceleration
**Problem:** Complex themes can trigger continuous repaints and software-compositing bottlenecks.
**Solution:**
- Prefer opacity toggles over full repaints.
- Use `transform: translate3d(...)` to promote UI panels to the GPU.
- Enforce strict `contain: layout style` to prevent DOM reflows from bubbling up the tree.
- Aggressively force Dark Mode CSS attributes across the board to prevent flashbangs on initial load.

## The Unified Deployment Strategy
Rather than running a dozen fragmented scripts, the application of these techniques must be orchestrated as a linear cascade:
1. **Janitorial Preclean:** Nuke old `objdir`, remove stale `startupCache`, and sever telemetry preferences in `firefox.js`.
2. **Asset Neutralization:** Scan the `browser/` and `toolkit/` directories. Map all SVGs, apply the 63-byte ghost shims to everything except the canonical icons.
3. **Locale Rebranding:** Safely rewrite the `.ftl` dictionaries, avoiding HTML attributes.
4. **CSS Overlay:** Inject the CSS `::before` text shims and zero-cpu layout rules into the core theme.
5. **Build & Package:** Run the lightweight `mach build faster` (or full build depending on depth) to sync `omni.ja` equivalents into the binaries.
