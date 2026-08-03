#!/usr/bin/env python3
"""Phase C3: the build-blocker root — the Glean telemetry registry
(toolkit/components/glean/metrics_index.py) still listed the moved
aiwindow/genai metrics.yaml files. Remove both entries, plus the last
surviving caller of a genai Glean category (the chatbot keyboard-shortcut
case in browser-sets.js) and its <key> element."""
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

rep("toolkit/components/glean/metrics_index.py",
    '    "browser/components/aiwindow/metrics.yaml",\n', "",
    "aiwindow metrics.yaml deregistered from Glean")

rep("toolkit/components/glean/metrics_index.py",
    '    "browser/components/genai/metrics.yaml",\n', "",
    "genai metrics.yaml deregistered from Glean")

rep("browser/base/content/browser-sets.js",
    '''        case "viewGenaiChatSidebarKb": {
          // GORILLA OVERRIDE: AI Window sidebar branch removed.
          const pref = "browser.ml.chat.enabled";
          const enabled = Services.prefs.getBoolPref(pref);
          Glean.genaiChatbot.keyboardShortcut.record({
            enabled,
            sidebar: SidebarController.currentID,
          });
          if (enabled) {
            SidebarController.toggle("viewGenaiChatSidebar");
          }
          break;
        }
''',
    '''        // GORILLA OVERRIDE: viewGenaiChatSidebarKb case removed with genai
        // (its Glean category genai.chatbot left the metrics registry).
''',
    "genai chatbot shortcut case removed")

rep("browser/base/content/browser-sets.inc.xhtml",
    '''    <key id="viewGenaiChatSidebarKb"
         data-l10n-id="ai-chatbot-sidebar-shortcut"
#ifdef XP_MACOSX
         modifiers="control"
#else
         modifiers="accel,alt"
#endif
         />
''',
    "",
    "genai chatbot key element removed")

print("ALL PHASE-C3 EDITS OK")

# --- run 2 addendum (after boot smoke): removed tabgroup-menu.js static import
# of chrome://browser/content/genai/content/model-optin.mjs (boot error), and
# removed orphan SmartbarMentionsPanelSearch.sys.mjs + its urlbar moz.build
# entry (zero importers after SmartbarInput deletion; backup in tier2/).
