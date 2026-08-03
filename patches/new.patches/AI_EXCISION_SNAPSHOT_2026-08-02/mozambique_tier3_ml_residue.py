#!/usr/bin/env python3
"""Tier-3: ml-residue landmines flushed out by real GUI use (2026-08-03).
1. TranslationsFeature extended the excised ml AIFeature base -> module load
   failed for the translations panel + about:translations (all members are
   self-contained; the base added nothing they use).
2. PlacesSemanticHistoryManager's constructor unconditionally created an
   EmbeddingsGenerator (excised ml) -> the urlbar semantic provider's lazy
   getter threw on EVERY keystroke.
3. preferences.js still registered three AI panes whose module
   (aiFeatures.mjs) was deleted -> settings search preload errored.
Plus belt prefs: browser.ml.enable + places.semanticHistory.featureGate
locked false."""
import sys

FM = "/home/gorilla/firefox-main/"

def rep(path, old, new, label):
    p = FM + path
    text = open(p, encoding="utf-8").read()
    n = text.count(old)
    if n != 1:
        print(f"FAIL [{label}] {path}: {n} matches (want 1)"); sys.exit(1)
    open(p, "w", encoding="utf-8").write(text.replace(old, new))
    print(f"OK  {path} :: {label}")

# ---- 1. TranslationsFeature: drop the dead base class ----
rep("toolkit/components/translations/TranslationsFeature.sys.mjs",
    'import { AIFeature } from "chrome://global/content/ml/AIFeature.sys.mjs";\n',
    "",
    "dead ml AIFeature import removed")

rep("toolkit/components/translations/TranslationsFeature.sys.mjs",
    '''/**
 * AIFeature implementation for translations.
 */
export class TranslationsFeature extends AIFeature {
''',
    '''/**
 * GORILLA OVERRIDE: formerly extended the excised ml AIFeature base class.
 * Every member below is self-contained (prefs + TranslationsParent), so the
 * class now stands alone. Translations itself is fully preserved.
 */
export class TranslationsFeature {
''',
    "class stands alone (translations preserved)")

# ---- 2. PlacesSemanticHistoryManager: finalize before touching ml ----
rep("toolkit/components/places/PlacesSemanticHistoryManager.sys.mjs",
    '''    this.embedder = lazy.EmbeddingsGenerator.forPlaces();
''',
    '''    // GORILLA OVERRIDE: ml stack excised — the embeddings generator no
    // longer exists. Finalize immediately: every capability getter reports
    // false and the urlbar semantic provider stays inactive (it used to
    // throw on every keystroke).
    this.#finalized = true;
    this.qualifiedForSemanticSearch = false;
    this.semanticDB = null;
    if (true) {
      return;
    }
    this.embedder = lazy.EmbeddingsGenerator.forPlaces();
''',
    "ctor finalizes before ml touch")

# ---- 3. preferences.js: remove the three AI panes ----
rep("browser/components/preferences/preferences.js",
    '''  ai: {
    l10nId: "preferences-ai-controls-header3",
    iconSrc: "chrome://global/skin/icons/highlights.svg",
    groupIds: ["aiControlsDescription", "aiFeatures", "aiStatesDescription"],
    module: "chrome://browser/content/preferences/config/aiFeatures.mjs",
    visible: () =>
      Services.prefs.getBoolPref("browser.preferences.aiControls", false),
  },
''',
    "",
    "AI-controls pane removed")

rep("browser/components/preferences/preferences.js",
    '''  manageMemories: {
    parent: "personalizeSmartWindow",
    l10nId: "ai-window-manage-memories-header",
    groupIds: ["manageMemories"],
    module: "chrome://browser/content/preferences/config/aiFeatures.mjs",
    supportPage: "smart-window-memories",
  },
''',
    "",
    "manage-memories pane removed")

rep("browser/components/preferences/preferences.js",
    '''  personalizeSmartWindow: {
    parent: "ai",
    l10nId: "ai-window-personalize-header",
    iconSrc: "chrome://browser/skin/smart-window-mono.svg",
    badge: "beta",
    groupIds: ["assistantDefaultGroup", "assistantModelGroup", "memoriesGroup"],
    module: "chrome://browser/content/preferences/config/aiFeatures.mjs",
  },
''',
    "",
    "personalize-smart-window pane removed")

# ---- 4. belt prefs ----
rep("browser/app/profile/firefox.js",
    'pref("browser.ml.chat.shortcuts.smartwindow", false, locked);\n',
    '''pref("browser.ml.chat.shortcuts.smartwindow", false, locked);
// GORILLA OVERRIDE: ml excised — master ml switch and semantic-history gate
// locked off so nothing ever tries to reach the removed stack.
pref("browser.ml.enable", false, locked);
pref("places.semanticHistory.featureGate", false, locked);
''',
    "ml master + semantic gate locked off")

print("ALL TIER-3 EDITS OK")
