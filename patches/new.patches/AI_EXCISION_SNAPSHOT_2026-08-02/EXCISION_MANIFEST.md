# AI/ML CLUSTER STRUCTURAL EXCISION — 2026-08-02

**Goal:** actually REMOVE the AI/ML subsystem from source (not just pref-gate), per owner
("structural removal was attempted with a shit gemini... it's worth a try").
**Method:** [[Structural_Excision_Discipline]] — map static+dynamic, cut the coherent set,
build=oracle, resolve orphans INWARD never shim, stop-and-gate if an innocent load-bearing
consumer is hit. Snapshot of all pre-edit files in this dir (reversal source).

## REMOVED (dropped from build / binary)
- `toolkit/components/ml` (13 MB, ONNX engine+models) — DIRS entry commented in toolkit/components/moz.build
- `browser/components/aiwindow` (4.3 MB) — DIRS entry in browser/components/moz.build
- `browser/components/genai` (692 KB) — DIRS entry in browser/components/moz.build
- `toolkit/components/aboutinference` (about:inference, NIGHTLY-gated) — DIRS + C++ redirector + CSP + l10n

## SEAM EDITS (registrations / consumers de-wired)
| File | Edit |
|---|---|
| toolkit/modules/ActorManagerParent.sys.mjs | removed MLEngine actor registration |
| browser/components/DesktopActorRegistry.sys.mjs | removed AIChatContent + AISmartBar actors; dropped genai/chat.html + about:aichatcontent from matches |
| browser/components/urlbar/UrlbarProvidersManager.sys.mjs | removed UrlbarProviderAiChat provider |
| browser/components/urlbar/moz.build | dropped UrlbarProviderAiChat.sys.mjs + private/MLSuggest.sys.mjs |
| docshell/base/nsAboutRedirector.cpp | removed about:inference entry (C++) |
| dom/security/nsContentSecurityUtils.cpp | removed about:inference from CSP allowlist (C++) |
| browser/themes/addons/jar.mn + moz.build | removed aiwindow + aiwindow-nova builtin themes + GeneratedFile blocks |
| toolkit/locales/jar.mn | removed aboutInference.ftl l10n |
| browser/components/tabbrowser/content/tabbrowser.js | removed SmartTabGroupingManager lazy import |
| browser/components/BrowserContentHandler.sys.mjs | canOpenAsSmartWindow() -> false (normal startup preserved) |
| toolkit/components/extensions/ext-toolkit.json | neutralized trial_ml WebExtension API |
| browser/components/preferences/jar.mn | dropped OnDeviceModelManager.mjs + aiFeatures.mjs |

## GATED (load-bearing consumer satisfied by lock, not surgery)
- `browser.preferences.aiControls=false, locked` — hides the AI-features prefs pane (its module removed)
- `browser.smartwindow.enabled=false, locked` — smart-window actors gated off
- (all AI features already false+locked from the earlier pref sweep — belt)

## VALIDATION
- `./mach configure` — PASS (2413 moz.build files read clean; DIRS/GeneratedFile edits valid).
- `./mach build` — RUNNING (the oracle). Log: scratchpad/ai_excision_build.log. Errors = remaining
  edges; resolve INWARD (delete caller), never shim. If an INNOCENT load-bearing consumer is hit,
  STOP and gate instead.

## REVERSAL
Restore the 11 snapshot files here + un-comment the DIRS entries + `git checkout` the C++/JS, OR
restore firefox-main from vault per [[tree-restore-procedure]].

## ROUND 2 (2026-08-02, build-oracle iteration — owner: "every complainer gets removed")
Build run 1 failed at: `LlamaRunnerBinding.cpp: 'LlamaRunner.h' file not found` (WebIDL whose C++
impl was in excised ml). Fixed INWARD: deregistered LlamaRunner.webidl (dom/webidl/moz.build).
Then the JS consumer cascade was traced — ml is imported by urlbar Firefox-Suggest infra
(MLSuggest→SuggestBackendMl→QuickSuggest), tab UI (SmartTabGrouping), prefs (aiFeatures/
OnDeviceModelManager). All consumer refs are SHALLOW (lazy getters / one string branch /
comments) — removable without bricking the address bar.

DELETED (pure-AI files): SmartTabGrouping.sys.mjs, private/MLSuggest.sys.mjs,
private/SuggestBackendMl.sys.mjs, UrlbarProviderAiChat.sys.mjs, preferences/OnDeviceModelManager.mjs,
preferences/config/aiFeatures.mjs. (Snapshotted here first.)
DE-WIRED: QuickSuggest (dropped SuggestBackendMl getter + enabledBackends entry); UrlbarView
(dropped the UrlbarProviderAiChat result branch); tabgroup-menu #initSuggestions (return before the
deleted-module import); urlbar/moz.build (dropped SuggestBackendMl); dom/webidl/moz.build (dropped
LlamaRunner.webidl).
GATED (not removed — cascade into load-bearing / already off): the preferences.js `ai` category
module ref (gated by browser.preferences.aiControls=false LOCKED); MLEngine actor already removed;
translations/places-semantic import ml lazily but are pref-gated off.
configure: PASS (both rounds). build run 2: RUNNING (bh1m7fbsj).
DISCIPLINE NOTE: this is the build-oracle loop working exactly as [[Structural_Excision_Discipline]]
prescribes — build complains → remove the complainer INWARD (never shim) → rebuild. The address-bar
core was the stop-and-gate candidate but its AI refs turned out shallow/removable, so no gate needed
there. ml native engine (13 MB) + aiwindow (4.3 MB) + genai + aboutinference all excised from build.

## ROUND 3 (2026-08-02) — mozinference/llama excised; ESR128 diff method (owner-directed)
Build run 2 FAILED at libmozinference.so link (llama_*/ggml_* symbols undefined) — the notification's
"exit 0" was tee's again (caught by binary verify: libxul stale @12:39, LlamaRunner still 59). Removed:
config/external/moz.build mozinference DIRS entry; browser/installer/package-manifest.in libmozinference
line; third_party/moz.build llama.cpp BUG_COMPONENT metadata; moved third_party/llama.cpp (7.3M) ->
/home/gorilla/firefox-main.excised-ai-llama.cpp.2026-08-02 (reversible); intl/locales/moz.build "ml"
l10n dir. configure PASS.

ESR128 DIFF (owner method "diff against versions that didn't ship AI"): confirmed the post-ESR128
recent AI grafts = aiwindow, genai, aboutinference, mozinference, llama.cpp (ALL removed ✓). NUANCE:
`ml`, translations, glean, normandy, nimbus ALREADY existed in ESR128 (ml is older translation/early-ML
infra) — so full ml removal is BEYOND an ESR revert and requires de-wiring ml's ESR-era consumers
(translations/places/urlbar — done via gates + shallow-ref removal).

NEXT-PASS CANDIDATES (in 154 toolkit/components, NOT in ESR128 — verify AI/telemetry then remove):
content-classifier (ML), captchadetection (likely ML), dap (privacy-agg TELEMETRY), pageextractor,
sitecategories. NOT AI (keep): aboutpdf, doh (owner-vetoed), gecko-trace, media, qrcode.
Deferred to a SEPARATE pass AFTER the current excision builds clean (don't pile removals into an
unbuilt tree). See [[Historical_Reversion_Beats_Reactive_Stubbing]].

## ✅ SUCCESS — build run 3 (2026-08-02 17:49) — BINARY-VERIFIED
"Your build was successful!" (real mach msg, CLAUDECODE unset, wall 977s, 0 err / 0 warn).
BINARY PROOF (libxul.so relinked 17:49, was stale 08-01 12:39):
  LlamaRunner 0 (was 59) | MLEngineParent 0 | EngineProcess 0 | AIChatContent 0 | llama_free 0
  libmozinference.so ABSENT from dist/bin.
The recent post-ESR128 AI graft is STRUCTURALLY EXCISED (not pref-gated): ml engine + aiwindow +
genai + aboutinference + mozinference + llama.cpp, ~18MB+ source, gone from the binary.
Method that worked (vs Gemini): static+dynamic map -> build=oracle (found LlamaRunner WebIDL,
libmozinference version-script, llama.cpp FINAL_LIBRARY, ml locales one edge at a time) -> resolve
INWARD never shim -> ESR128 diff for scope -> BINARY verification caught 2 tee-exit-0 false successes.
STILL PENDING: runtime smoke test (does it launch + address bar/tabs work with AI refs gone).
NEXT PASS (deferred): content-classifier, captchadetection, dap, pageextractor, sitecategories.

---


## 2026-08-02 (evening) — aiwindow stub layer + Tier-1 seam removal ("Mozambique pass")

### Phase A: permanent-off stubs (the tourniquet)
Problem: 20 surviving files lazy-import 5 deleted aiwindow modules via moz-src URIs
(18x AIWindow.sys.mjs, 2x AIWindowUI.sys.mjs, plus ChatStore/AIWindowAccountAuth/
ChatUtils getters). Lazy getters throw the moment any member is touched.
Fix: overwrote the 5 modules in browser/components/aiwindow/ui/modules/ with
permanent-off stubs (every getter false/"disabled", every method no-op;
handleAIWindowOptions returns args unchanged = the original's own disabled branch).
Gutted browser/components/aiwindow/moz.build to MOZ_SRC_FILES for ONLY those 5 files;
re-added "aiwindow" to browser/components/moz.build DIRS.
Originals preserved: aiwindow-originals/ (this directory).
Verified: mach build faster exit 0; dist/bin/moz-src/.../aiwindow contains exactly
5 stub symlinks and nothing else; headless boot clean.

### Phase B: Tier-1 seam removal (window chrome de-wired)
Scripts (exact record of every edit, assert-once matching):
- mozambique_tier1_seam_removal.py  (32 edits, 13 files)
- mozambique_tier1b_ask_button.py   (3 edits, 2 files)
What was reversed (pre-AI behavior restored):
- Ctrl+N always opens a normal window (browser-sets.js hijack removed)
- Tools:AIWindow / Tools:ClassicWindow / Tools:ChatsHistory commands + their
  File-menu, History-menu and app-menu items removed (browser-sets.inc.xhtml,
  browser-menubar.inc.xhtml, appmenu-viewcache.inc.xhtml, browser.js popup toggling,
  panelUI.js _showAIMenuItem no-op'd)
- smartwindow-ask-button toolbar markup + click/keynav routing removed
- New-tab URL override removed (utilityOverlay.js), Show-All-History redirect
  removed (places-commands.js), history-menu AI hook removed (browser-menubar.js)
- SmartbarInput conditional import removed (browser-main.js)
- tabbrowser.js transparent-browser AI blocks removed (3 sites) + AI favicon map entry
- browser-init.js ai-window attribute plumbing removed
- Sanitize dialog chat-label block, sync signout AI variant, context-menu
  smart-window item (hard false), genai-shortcut AI branch removed
- All 7 window-scope AIWindow/AIWindowUI lazy getters dropped
Verified: zero bare AIWindow references left in window-scope files; mach build
faster exit 0; headless boot, error grep clean (no aiwindow/smartwindow/TypeError).

### Still stub-backed (Tier-2 queue, functionally dead via stubs):
SessionStore (10 sites), NewTabPagePreloading (4), UrlbarUtils/UrlbarInput,
firefoxview trio (chats pane), UITour pair, browser-sidebar.js, ASRouter +
SpecialMessageActions + FeatureCalloutMessages/Onboarding message content,
BrowserContentHandler, Sanitizer.sys.mjs, SmartbarInput/SmartbarInputUtils +
urlbar jar.mn entries, session.schema.json, ProfileDataUpgrader,
LightweightThemeConsumer/Manager aiwindow theme ids, storybook config.
End-state option: once Tier-2 seams are cut, the 5 stubs + DIRS entry can be
deleted outright.

## 2026-08-02 (night) — Tier-2 + Phase C: aiwindow/genai FULLY out of the tree

### Tier-2 (module-side seams; scripts: mozambique_tier2_module_seams.py + _tier2b_continuation.py)
75 exact-string edits + 8 file deletions. Highlights, all reverted to pre-AI shape:
- SessionStore: 6 seams (window AI flag, restore matching, AI window toggling,
  restore-args handleAIWindowOptions) + session.schema.json isAIWindow
- NewTabPagePreloading (AI window matching), UrlbarUtils (smartbar substitution),
  UrlbarInput (windowMode always "classic")
- firefoxview chats pane DELETED (chats.mjs, chats-tab-list.*, ChatsController,
  view-chats.svg, nav button + view element + jar entries)
- Smartbar files DELETED (SmartbarInput/Controller/Utils + urlbar jar entries)
- UITour case + web-facing UITour-lib API removed; browser-sidebar de-AI'd
- ASRouterTargeting.addAIWindowTargeting REMOVED (it injected !isAIWindow into
  EVERY message evaluation); ASRouter trigger-context flag removed
- 7 AI promo/callout messages removed (SMARTWINDOW_DEFAULT_PROMO, 2 feedback
  modals, 3 callouts, TEST_CONTENT_ANCHOR)
- BrowserContentHandler: canOpenAsSmartWindow + all plumbing removed
- Sanitizer: chat-clear function + calls; ProfileDataUpgrader migration; storybook
- Theme engine: LightweightThemeConsumer ai-window MutationObserver + AI theme
  substitution branch removed; LightweightThemeManager promiseAIThemeData removed

### Phase C (endgame; scripts: mozambique_phasec_endgame.py + _phasec2_genai_ftl.py)
- Fixed TWO LIVE CRASHES inherited from the earlier genai unpackaging:
  LinkPreview.teardown on every window close (browser-init.js), and
  GenAI.buildTabMenu on every tab right-click (tab-context-menu.js)
- All genai seams cut: nsContextMenu (link-preview item + previewLink),
  sidebar-main (aichat builder, chatbot entrypoint, genai.ftl l10n list),
  SpecialMessageActions (SUMMARIZE_PAGE), DesktopActorRegistry (LinkPreview
  actor), preferences (LinkPreview getters + settings hidden)
- genai page-assist sidebar registration removed; preview/genai.ftl jar line gone
- DIRS: "aiwindow" removed again — the 5 stubs ceased to exist with the dir
- MOVED OUT OF TREE → /home/gorilla/firefox-main.excised-ai-aiwindow-genai.2026-08-02/:
  browser/components/aiwindow (incl. stubs + original 4.3M body),
  browser/components/genai, browser/themes/addons/aiwindow + aiwindow-nova

### Known residue (inert, documented):
- aichat sidebar registration in browser-sidebar.js (pref browser.ml.chat.enabled
  locked false; url points into moved genai — registration is pref-dead)
- enterprisepolicies LinkPreviews/LinkPreviewKeyPoints policy name strings (data)
- Onboarding smartwindow TOU message variant (targeting requires
  browser.smartwindow.enabled which is locked false)
- browser.smartwindow.* / browser.ai.control.* locked prefs KEPT (belt)
- SmartbarMentionsPanelSearch.sys.mjs spotted in dist/bin moz-src (urlbar) —
  check origin next session

## 2026-08-02 (late night) — Phase C3/C4: the hidden anchors + FINAL CLEAN BOOT

Build broke after the dir moves; root causes were the four STRING-BASED anchors
a directory has besides moz.build DIRS (scripts: mozambique_phasec3_glean_index.py,
mozambique_phasec4_startup_categories.py):
1. GLEAN REGISTRY: toolkit/components/glean/metrics_index.py listed
   aiwindow/genai metrics.yaml → config.status fatal. Both deregistered; last
   surviving Glean caller (genai chatbot shortcut case + its <key>) removed.
2. STARTUP CATEGORIES: BrowserComponents.manifest ran GenAI.init
   (browser-idle-startup) and LinkPreview.init (browser-window-delayed-startup).
   Both removed.
3. ADDON PROVIDER: extensions.manifest registered ModelHubProvider
   (about:addons local-AI-models; loads excised ml ModelHub). Removed.
4. TRANSLATIONS SEAM: TranslationsParent.AIFeature chained to excised ml
   AIFeature. Reverted to pre-AI semantic: plain browser.translations.enable
   pref check (all 5 in-tree callers use only .isEnabled — verified).
Also: aichat sidebar registration retired (dead pref, missing l10n string);
tabgroup-menu.js model-optin static import removed (boot error);
orphan SmartbarMentionsPanelSearch.sys.mjs deleted (zero importers).

MACH LESSON (cost ~2h): mach 'build faster' HANGS (futex wait, zombie child)
instead of showing backend errors — the "slow backend" was never slow. Diagnose
with: cd objdir && <build venv python> config.status  (11s, real traceback).
Bypass wrapper: config.status --backend=FasterMake && make -C objdir/faster.

VERIFIED FINAL STATE (2026-08-02 ~23:59):
- config.status clean (2412 moz.build, 11.6s); make faster exit 0
- dist/bin: zero aiwindow/genai/Smartbar/chats/LinkPreview/GenAI artifacts
  (residue: en-US genai.ftl strings file — inert, kept deliberately)
- headless boot (fresh profile, direct binary): ZERO AI-related errors
- Non-AI residue flagged: ReportBrokenSite.sys.mjs:559 TypeError (classify
  next session); sidebar-main viewGenaiChatSidebar data branches (unreachable)

## 2026-08-03 (post-endgame) — the FIFTH anchor: document l10n links

The "pre-existing" ReportBrokenSite TypeError + scattered fluent failures
(window title, shortcuts, save-login ids) were OURS: browser.xhtml and
sidebar-customize.html still carried <link rel="localization"
href="preview/genai.ftl"/> after Phase C2 unshipped that file. ONE missing
linked FTL degrades the whole document bundle → unrelated ids fail. Both
links removed; fresh-profile boot now shows ZERO ReportBrokenSite errors,
ZERO "Couldn't find a message", ZERO AI references. Source FTLs verified
healthy via third_party/python/fluent.syntax (196 files, 0 junk). Cosmetic
reportBrokenSite.ftl reflow (report-sent-header .title, select-expression
variant indent) restored to upstream shape while investigating.
Brain atom updated: Component_Dir_Four_Hidden_Anchors now documents the
l10n triple (jar.mn + Localization() lists + document <link> registrations).

## 2026-08-03 00:26 — FULL BUILD BAKED & VERIFIED (topic closed)

mach wrapper hung AGAIN on the full build (same futex/zombie signature, caught
by watchdog in 14 min) → build driven directly: full config.status (also fixed
a stale RecursiveMake install manifest for the deleted Smartbar module) then
`make -C obj-x86_64-pc-linux-gnu -j6`. Ran 00:06→00:26 (~20 min, sccache),
MAKE_EXIT=0, zero error lines in 1.2M log.

BINARY VERIFICATION (libxul.so relinked 00:26):
- LlamaRunner / llama_ / ggml_ / mozinference / SmartTabGrouping: all 0
- Dead Glean categories smart_window / genai.chatbot / aiwindow: all 0
  (the last compiled residue named in the 2026-08-02 entry is now GONE)
- Fresh-profile headless boot on the new libxul: zero AI refs, zero fluent
  errors, zero load failures.
Nothing AI remains in source, packaging, or compiled code.

## 2026-08-03 (GUI verification) — runtime bugs found by a human at the keyboard

Headless boots were clean but interactive paths hid real bugs. Live-monitor +
breadcrumb + stack-injection method (atom GUI_Runtime_Forensics...) found:
- Tier-3 ml residue (mozambique_tier3_ml_residue.py): TranslationsFeature extended
  the excised ml AIFeature base (module load fail on translate panel/about:translations)
  -> class stands alone; PlacesSemanticHistoryManager ctor built ml EmbeddingsGenerator
  on EVERY keystroke -> finalize-first guard; 3 preferences AI panes (aiFeatures.mjs
  deleted) removed; browser.ml.enable + places.semanticHistory.featureGate locked false.
- StartupCache trap: fixes were on disk but browser ran cached bytecode (errors at
  old line numbers). SOP now: rebuild -> kill firefox -> rm -rf PROFILE/startupCache
  -> relaunch. Atom: StartupCache_Stale_Bytecode_Invalidates_On_BuildID_Only.
- FTL fifth anchor: unshipped preview/genai.ftl still <link>ed in browser.xhtml +
  sidebar-customize.html degraded the whole document bundle -> unrelated ids
  scatter-failed (looked like scrub damage). Links removed.
- Tab groups locked OFF entirely (browser.tabs.groups.enabled=false locked, owner
  ruling) + 2900 chars of dead post-return smart-grouping UI code removed from
  tabgroup-menu.js.
- PHANTOM CUSTOMIZE PANEL (the capstone): a dead, un-closable "customize toolbar"
  surface appeared on tabstrip right-click. Root: #customization-container{display:flex}
  (ID selector) out-specifies [hidden]; the lazy gCustomizeMode getter clones the
  hidden template on any context-menu popupshowing -> renders a dead panel; its Done
  calls exit() which bails (customizing===false). Fix (customizeMode.css):
  #customization-container[hidden]{display:none!important}. Reproduces on vanilla
  mozilla-central tip (upstream bug). Atom: Phantom_Customize_Panel_ID_Selector_Beats_Hidden.
  customize_palette_selfheal.py also added a defensive null-palette re-grab (separate
  secondary crash in getUnusedWidgets, also unguarded upstream).

FINAL RUNTIME STATE (fresh-profile windowed session, 2026-08-03): Ctrl+N normal,
no AI menu/command/button anywhere, tab + link right-click clean, translations panel
loads, settings clean, phantom gone, Done closes real customize, window unload clean.
Zero AI-related console errors.

## Session chronicle
Full three-day narrative + roadblock ledger + atom/script index:
patches/new.patches/SESSION_CHRONICLE_2026-07-31_to_08-03.md
