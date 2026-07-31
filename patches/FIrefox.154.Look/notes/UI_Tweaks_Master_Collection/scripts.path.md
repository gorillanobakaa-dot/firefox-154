# UI Tweaking Scripts Registry

> **SUPERSEDED (2026-07-18).** This registry is historical. Most scripts below were
> consolidated into the toolkit `~/Documents/gorilla-firefox-toolkit/` and their standalone
> copies retired, and the vault was renamed (old `Firefox.Scripts.Backup.Docs/
> Do.Not.Delete.Safety.Vault.Backup/` → now `Firefox.Scripts.Vault.Docs.backup/` with
> `Safety.Vault.Scripts` / `SafetyVault.Firefox` / `Safety.Vault.Theme`). The canonical
> registry is now the toolkit: run `firefox-build-brand-patch --help`. The paths below are
> kept as a historical snapshot and are NOT reliable for locating files today.

This document lists all scripts gathered for UI tweaking, theme injection, branding, and asset ablation, along with their absolute source paths and descriptions.

## 1. Branding & Rebranding
* **`gorilla_branding_engine.py`**
  * **Source:** `/home/gorilla/Documents/FIrefox.154.Work/scripts/gorilla_branding_engine.py`
  * **Description:** Main engine for applying core metadata and branding logic.
* **`branding_engine.py`**
  * **Source:** `/home/gorilla/Documents/Second.Brain/branding_engine.py`
  * **Description:** Legacy/Alternate branding logic pipeline.
* **`global_gorilla_branding.py`**
  * **Source:** `/home/gorilla/Documents/FIrefox.154.Work/Firefox.Scripts.Vault.Docs.backup/Do.Not.Delete.Safety.Vault.Backup/Safety.Vault.Scripts/global_gorilla_branding.py`
  * **Description:** Orchestrates the modification of FTL files, disconnects Mozilla infrastructure/telemetry, and bakes the custom user.js preferences.
* **`gorilla_master_branding_suite.py`**
  * **Source:** `/home/gorilla/Documents/FIrefox.154.Work/Firefox.Scripts.Vault.Docs.backup/Do.Not.Delete.Safety.Vault.Backup/Safety.Vault.Scripts/gorilla_master_branding_suite.py`
  * **Description:** Comprehensive orchestration script running the full branding suite.
* **`firefox_unleashed.py`**
  * **Source:** `/home/gorilla/Documents/FIrefox.154.Work/Firefox.Scripts.Vault.Docs.backup/Do.Not.Delete.Safety.Vault.Backup/Safety.Vault.Scripts/firefox_unleashed.py`
  * **Description:** Orchestrates build modifications and applies zero-noise overlays for the final Unleashed build.
* **`rebrand_locales_automator.py`**
  * **Source:** `/home/gorilla/Documents/FIrefox.154.Work/patches/Gorilla.Look/Menu.change.Theme. Injection.Firefox.154/rebrand_locales_automator.py`
  * **Description:** Automates parsing, modifying, and safely re-injecting Fluent (`.ftl`) localization strings while protecting HTML anchor tags.

## 2. Icon Ablation & SVG Shimming
* **`mass_zero_byte_ghost.py`**
  * **Source:** `/home/gorilla/Documents/Do.Not.Delete.Ideas.Working.On/mass_zero_byte_ghost.py`
  * **Description:** Implements the 0-byte or 63-byte transparent ghost shim technique to completely eliminate heavy SVG rendering weight.
* **`svg_to_text_icons_v2.py`**
  * **Source:** `/home/gorilla/Documents/FIrefox.154.Work/scripts/snippets/svg_to_text_icons/svg_to_text_icons_v2.py`
  * **Description:** An advanced CSS overlay generator that intercepts SVG background/mask URL requests and replaces them entirely with ultra-lightweight text/Unicode glyphs via `::before` pseudo-elements.
* **`map_svg_references.py`**
  * **Source:** `/home/gorilla/Documents/FIrefox.154.Work/Firefox.Scripts.Vault.Docs.backup/Do.Not.Delete.Safety.Vault.Backup/Safety.Vault.Scripts/map_svg_references.py`
  * **Description:** Scans stylesheets to map all actual SVG references. Precursor step for deciding which icons to shim and which single canonical icon to symlink.
* **`generate_crisp_svgs.py`**
  * **Source:** `/home/gorilla/Documents/FIrefox.154.Work/patches/Gorilla.Look/Menu.change.Theme. Injection.Firefox.154/generate_crisp_svgs.py`
  * **Description:** Utility for ensuring single canonical fallback icons are properly scaled without visual artifacting.
* **`extreme_scale_asset_neutralizer.py`**
  * **Source:** `/home/gorilla/Documents/FIrefox.154.Work/scripts/snippets/extreme_scale_asset_neutralizer/extreme_scale_asset_neutralizer.py`
  * **Description:** Hardline asset ablation to purge thousands of unneeded binary blobs across the repo.

## 3. CSS Themes & Styling
* **`gorilla_theme_injector.py`**
  * **Source:** `/home/gorilla/Documents/FIrefox.154.Work/scripts/gorilla_theme_injector.py`
  * **Description:** Injects CSS clipping, Z-index overrides, and hardware-accelerated layouts directly into Firefox theme internals.
* **`mass_dark_mode.py`**
  * **Source:** `/home/gorilla/Documents/FIrefox.154.Work/Firefox.Scripts.Vault.Docs.backup/Do.Not.Delete.Safety.Vault.Backup/Safety.Vault.Scripts/mass_dark_mode.py`
  * **Description:** Mass search-and-replace to force explicit dark-mode values into CSS rules to prevent flashbangs on load.

## 4. Janitorial & Workspace Prep
* **`janitorial_precleaner.py`**
  * **Source:** `/home/gorilla/Documents/FIrefox.154.Work/Firefox.Scripts.Vault.Docs.backup/Do.Not.Delete.Safety.Vault.Backup/Safety.Vault.Scripts/janitorial_precleaner.py`
  * **Description:** Basic sweeping logic to clear old objdir state and stale caches before injection.
* **`gorilla_prebuild_janitor.py`**
  * **Source:** `/home/gorilla/Documents/FIrefox.154.Work/Firefox.Scripts.Vault.Docs.backup/Do.Not.Delete.Safety.Vault.Backup/Safety.Vault.Scripts/gorilla_prebuild_janitor.py`
  * **Description:** Highly specific pre-build sequence that links the icon ablation logic, ensuring the build engine only compiles the single canonical icon and the ghost shims.
