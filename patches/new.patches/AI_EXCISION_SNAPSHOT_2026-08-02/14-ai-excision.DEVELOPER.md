# AI Excision — Structural Removal of aiwindow / genai / ml from the Tree — Developer Track

> **Topic:** `14-ai-excision` · **Dirs removed:** `browser/components/aiwindow`, `browser/components/genai`, `toolkit/components/ml` (unpackaged), `config/external/mozinference`, `third_party/llama.cpp`, `browser/themes/addons/aiwindow{,-nova}`
> **Generated:** 2026-08-03 · **Chronology:** `EXCISION_MANIFEST.md` (this directory) · **Scripts:** `mozambique_*.py` (this directory)

---

## Module Summary

Unlike Topic 12 (Normandy/Nimbus: "keep the corpse standing"), the AI stack was young enough to remove outright. Mozilla grafted it post-ESR128 by **inverting the dependency**: ~40 core files were rewired to *ask the AI layer for permission* at their decision points (`Ctrl+N` asks `AIWindow.isDefaultWindow`, session restore asks `handleAIWindowOptions`, every ASRouter message evaluation was rewritten through `addAIWindowTargeting()`, the theme engine watched every window for an `ai-window` attribute). Removal therefore ran in two movements: a **stub tourniquet** (5 permanent-off modules at the old moz-src URIs so 20 lazy importers answer "no" instead of throwing), then **seam reversal** (every graft cut back to its pre-AI shape, verified against ESR — `OpenBrowserWindow()` was always underneath), after which the stubs had zero consumers and left the tree with the directories.

## Phases (all edits assert-exactly-once; scripts are the byte-exact record)

| Phase | Script | Scope |
|---|---|---|
| Stubs | (manifest §evening) | 5 permanent-off modules; `aiwindow/moz.build` gutted to `MOZ_SRC_FILES` ×5 |
| Tier 1 | `mozambique_tier1_seam_removal.py` + `_tier1b` | 35 edits, 15 window-chrome files: Ctrl+N hijack, `Tools:AIWindow/ClassicWindow/ChatsHistory` commands + menu/app-menu markup, ask-button, tabbrowser transparency ×3, new-tab URL, sanitize/sync/context-menu hooks, all 7 window-scope getters |
| Tier 2 | `_tier2_module_seams.py` + `_tier2b` | 75 edits + 8 deletions: SessionStore ×6, urlbar, NewTabPagePreloading, firefoxview chats pane (deleted), Smartbar files (deleted), UITour + web API, sidebar, `addAIWindowTargeting` removed, 7 promo messages removed (brace-matched), BrowserContentHandler plumbing, Sanitizer, theme engine (`_isAIWindow`, MutationObserver, `promiseAIThemeData`) |
| Phase C | `_phasec_endgame.py` | 18 edits (incl. 3 live-crash fixes, below) + dirs moved to `/home/gorilla/firefox-main.excised-ai-aiwindow-genai.2026-08-02/` + DIRS entry dropped |
| C2–C4 | `_phasec2/3/4` | The five hidden anchors (below) + aichat sidebar retirement + `TranslationsParent.AIFeature` reverted to plain `browser.translations.enable` pref check |

## Live crashes inherited from the earlier unpackaging (fixed in Phase C)

1. `tab-context-menu.js` — `GenAI.buildTabMenu()` ran **unconditionally on every tab right-click**; module unpackaged → throw.
2. `browser-init.js` — synchronous `LinkPreview.teardown(window)` **on every window close**.
3. `nsContextMenu` — `LinkPreview.shouldShowContextMenu()` **on every link right-click**.

## The five hidden anchors (what holds a component dir besides `DIRS`)

A symbol xref sees none of these; each one broke the build or the boot:

1. **Glean registry** — `toolkit/components/glean/metrics_index.py` lists every `metrics.yaml` by path; a listed file that moved = fatal `config.status`. Grep surviving JS for the yaml's categories first (`genai.chatbot` → `Glean.genaiChatbot.*` had one live caller).
2. **Startup categories** — `BrowserComponents.manifest`: `category browser-idle-startup … GenAI.init` fired on every boot.
3. **Provider categories** — `extensions.manifest`: ModelHubProvider (about:addons AI-models section).
4. **jar.mn l10n lines + `new Localization([...])` lists** — `preview/genai.ftl`.
5. **`<link rel="localization">` in consuming documents** — the nastiest: browser.xhtml + sidebar-customize.html still linked the unshipped FTL; **one missing linked file degrades the document's whole bundle generation**, so *unrelated* ids scatter-fail (window title, shortcuts, ReportBrokenSite) — masquerading as string corruption. Diagnose with `third_party/python/fluent.syntax` (parse: 196 files, 0 junk ⇒ loading problem), then diff document links against `dist/bin/browser/localization/en-US/`.

## Build-system trap (cost ~2 h)

`mach build faster` **hangs** (parent in `futex_wait`, zombie `config.status` child, empty log) instead of reporting a backend error. The backend was never slow: run it directly —
`cd obj-* && ~/.mozbuild/srcdirs/<hash>/_virtualenvs/build/bin/python config.status` → real traceback in ~11 s (2412 moz.build files). Note `config.status` does **not** regenerate FasterMake by default: `--backend=FasterMake`, then `make -C obj-*/faster -j4` bypasses mach entirely. Atom: `Component_Dir_Four_Hidden_Anchors` (ingested, 215-vector collection).

## Verification (measured, 2026-08-03)

- `config.status` clean; `make -C faster` exit 0, 0 errors.
- `dist/bin`: zero aiwindow/genai/Smartbar/chats/ChatsController/GenAI/LinkPreview artifacts (find-verified).
- Fresh-profile headless boot (direct binary, not mach): **zero** AI references, **zero** `Couldn't find a message`, zero ReportBrokenSite errors.
- Full `./mach build` (libxul relink) launched 2026-08-03 to drop the two dead Glean categories still baked into the previous libxul — the only compiled-code residue.

## Residue (inert, deliberate)

- `browser/locales/en-US/browser/genai.ftl` (standard l10n mirror) ships; orphan strings crash nothing.
- Unreachable `viewGenaiChatSidebar` data branches in `sidebar-main.mjs`; enterprise-policy name strings; smartwindow TOU message (targeting requires a locked-false pref).
- `browser.smartwindow.* / browser.ai.control.* / browser.ml.*` locked-false prefs kept as belt.

## Reversal

Originals: `aiwindow-originals/` (+ `tier2/`) in this directory; whole dirs at `firefox-main.excised-ai-aiwindow-genai.2026-08-02/` and `firefox-main.excised-ai-llama.cpp.2026-08-02/`. Restore dirs, revert the scripts' replacements (each `rep()` is its own inverse), re-add DIRS + `metrics_index.py` + category + link entries, full rebuild.
