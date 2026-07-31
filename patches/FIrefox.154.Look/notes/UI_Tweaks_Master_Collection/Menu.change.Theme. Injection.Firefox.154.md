# Lesson: Deep UI Menu Rebranding & Theme Injection in Firefox 154

## 📖 The Layman's Walkthrough

Imagine you are trying to paint a massive mansion, but every room has hidden panels and trapdoors that are painted by completely different crews. Our first attempt only painted the front door (the basic `brand.ftl` file), but when you opened the door and walked inside, the kitchen, the bedrooms, and the basement still had the old paint. 

Worse, when we tried to aggressively spray paint *everything*, our paint sprayer accidentally got paint in the electronic lock mechanisms (the HTML formatting tags inside the translation files), causing the doors to jam and the house to burn down (Firefox crashed). 

Finally, even when we fixed the paint sprayer and painted the whole house, there was a ghost of the old house still floating around on the property, blocking the new house from showing up!

Here is exactly how we solved each of these problems permanently.

### Step 1: The Ghost Busters (Killing the Stuck Process)
**What happened:** When you tried to start the browser, nothing popped up. This wasn't because it was broken; it was because an invisible "zombie" version of the crashed browser was still running silently in your computer's memory. Firefox refuses to open two different realities at once.
**What we did:** We sent a signal to force-quit *all* Firefox processes, ensuring the system memory was completely clean before opening our new masterpiece.

### Step 2: Wiping the Old Canvas
**What happened:** Our old Firefox 153 browser was still sitting in the `/usr/lib/gorilla-unleashed/` installation folder. We were trying to put new Firefox 154 files in, but they were mixing together like oil and water.
**What we did:** We completely deleted the `/usr/lib/gorilla-unleashed/` folder and created a fresh, pure space. 

### Step 3: Deep Painting (Rebranding the Core UI)
**What happened:** Changing `brand.ftl` wasn't enough. Things like "New Tab", "Settings", and "Bookmarks Toolbar" don't live in the branding file. They live deep inside files named `appmenu.ftl`, `tabbrowser.ftl`, and `tabContextMenu.ftl`. 
**What we did:** Instead of changing 7 files, we ran our localizer tool on *over 100 files* across the entire `browser/locales/en-US` and `toolkit/locales/en-US` directories. 

### Step 4: Protecting the Wiring (The HTML Bug Fix)
**What happened:** The text strings in Firefox often look like this: `For quick access, click <a data-l10n-name="manage-bookmarks">Manage Bookmarks</a>`. Our old script aggressively changed that internal code to `"manage-Gorilla bookmarks"`. The browser couldn't understand this alien code and panicked.
**What we did:** We patched the `bulk_rebrander.py` script so that it completely ignores anything inside the `< >` brackets. It now only touches the text you actually *see* on the screen.

### Step 5: Forcing the Icons
**What happened:** When you compile Firefox, it sometimes ignores custom icons and builds symlinks (shortcuts) to standard default icons.
**What we did:** After installing the browser to `/usr/lib`, we manually smashed our actual Gorilla Unleashed `.png` and `.jpg` image files straight into the `browser/chrome/icons/default/` folder, replacing the standard shortcuts.

---

## 💻 The Developer's Track

For the technically inclined, here is the architectural breakdown of the deployment failure and the subsequent surgical fixes required to enforce total UI dominance.

### 1. Process Desync (The "No Window" Bug)
When Firefox 154 experienced a fatal parsing error due to malformed UI nodes (broken Fluent strings), the main window failed to render. However, the parent `firefox-bin` process did not properly terminate, leaving `firefox --no-remote` running headless in the background. Because Firefox utilizes a single-instance architecture (communicating via IPC to existing processes), subsequent launch commands just sent an IPC ping to the headless ghost and exited immediately. 
**The Fix:** 
```bash
killall firefox-bin || true
pkill -f firefox
```

### 2. The Fluent HTML Interpolation Bug
Mozilla's `Fluent` localization framework (`.ftl` files) supports HTML element mapping via `data-l10n-name`. 
**Example Source:**
```fluent
bookmarks-toolbar-empty-message = For quick access, place your bookmarks here. <a data-l10n-name="manage-bookmarks">Manage bookmarks…</a>
```
The naive Regex implementation in `bulk_rebrander.py` was mutating the attribute values, resulting in `data-l10n-name="manage-Gorilla bookmarks"`. During the DOM hydration phase, the XUL/HTML renderer searches for the ID `manage-bookmarks`. Upon failing to find it, the promise rejects, blocking the instantiation of the entire UI panel.
**The Fix:** 
The rebrander script was updated to implement negative lookbehinds or strict parsing to exclude `<...>` HTML tags from string replacement logic.

### 3. Localization Blast Radius
Standard `brand.ftl` and `brand.properties` only cover high-level application name variables (`{ -brand-short-name }`). Hardcoded UI strings exist in component-specific files. To achieve total "Gorilla" dominance, we had to recurse through the entire `locales` tree.
**The Command:**
```bash
python3 firefox_localizer/cli.py extract --source firefox-source/browser/locales/en-US --format json --output browser_strings.json
```
This extracted thousands of strings. We applied the Rebrander regex across the entire JSON dictionary, touching critical files like:
- `browser/appmenu.ftl` (The Hamburger Menu)
- `browser/newtab/newtab.ftl` (The about:home page)
- `toolkit/about/aboutAddons.ftl` (The extensions manager)
- `browser/tabContextMenu.ftl` (Right click menus on tabs)

### 4. Re-packing `omni.ja` Equivalent
Because this is an unpacked developer build (`--disable-official-branding`), the raw `.ftl` files must be processed by the build backend to update the `dist/bin/browser` symlinks and configurations.
**The Command:**
```bash
./mach build faster
```
This performs a lightweight re-scan of the source tree and syncs the changes to `obj-x86_64-pc-linux-gnu/dist/bin/`.

### 5. Final Installation Orchestration
To prevent mixing old 153 binaries with 154, the `/usr/lib/gorilla-unleashed` dir must be nuked prior to copying. Finally, the startup cache must be purged to force XUL cache invalidation.
**The Automation Script:**
An automation script `rebrand_locales_automator.py` has been provided in this directory which encapsulates this entire pipeline programmatically.

```bash
# Clear startup cache to force UI re-render
rm -rf ~/.cache/mozilla/firefox/*/startupCache
```
