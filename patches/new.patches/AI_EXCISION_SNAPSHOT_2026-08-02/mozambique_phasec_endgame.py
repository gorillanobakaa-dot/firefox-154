#!/usr/bin/env python3
"""Phase C endgame: cut the remaining genai seams (two of which are LIVE
crash paths in the current build: LinkPreview.teardown on every window
close, GenAI.buildTabMenu on every tab right-click — both import modules
the earlier genai excision unpackaged), then move the aiwindow and genai
directories plus the two AI theme dirs OUT of the tree and drop the
aiwindow DIRS entry. After this, the permanent-off stubs cease to exist —
nothing in the tree asks about AI windows at all.
"""
import os
import shutil
import sys

FM = "/home/gorilla/firefox-main/"
OUT = "/home/gorilla/firefox-main.excised-ai-aiwindow-genai.2026-08-02/"
done = []


def rep(path, old, new, label):
    p = FM + path
    with open(p, encoding="utf-8") as f:
        text = f.read()
    n = text.count(old)
    if n != 1:
        print(f"FAIL [{label}] {path}: pattern found {n} times (want 1)")
        sys.exit(1)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text.replace(old, new))
    done.append(f"{path} :: {label}")


# ===== browser-init.js: LIVE crash on every window close =====
rep("browser/base/content/browser-init.js",
    '''    // Bug 1952900 to allow switching to unload category without leaking
    ChromeUtils.importESModule(
      "moz-src:///browser/components/genai/LinkPreview.sys.mjs"
    ).LinkPreview.teardown(window);

''',
    "",
    "window-unload LinkPreview teardown removed (was a live crash)")

# ===== tab-context-menu.js: LIVE crash on every tab right-click =====
rep("browser/components/tabbrowser/content/tab-context-menu.js",
    '''    // Build Ask Chat items. The classic layout shows the full ask-chat submenu
    // (#context_askChat); the alt layout shows only a flat "Summarize Page" item
    // (#context_askChatSummarize). Hide whichever one this layout doesn't use so
    // a pref toggle reverses cleanly.
    if (!this._altTabContextMenu) {
      document.getElementById("context_askChatSummarize").hidden = true;
      TabContextMenu.GenAI.buildTabMenu(
        document.getElementById("context_askChat"),
        this
      );
    } else {
      document.getElementById("context_askChat").hidden = true;
      // In the alt layout #context_aiSeparator is reused as the divider after
      // the open-and-organize group, so keep it shown (the classic ask-chat
      // path would otherwise hide it together with #context_askChat).
      document.getElementById("context_aiSeparator").hidden = false;
      TabContextMenu.GenAI.buildTabSummarizeItem(
        document.getElementById("context_askChatSummarize"),
        this
      );
    }
''',
    '''    // GORILLA OVERRIDE: genai excised — no ask-chat items in either layout.
    // (Was a live crash: GenAI.sys.mjs is unpackaged, and buildTabMenu ran on
    // every tab right-click.)
    document.getElementById("context_askChatSummarize").hidden = true;
    document.getElementById("context_askChat").hidden = true;
    if (this._altTabContextMenu) {
      // #context_aiSeparator doubles as the divider after the open-and-organize
      // group in the alt layout, so keep it shown there.
      document.getElementById("context_aiSeparator").hidden = false;
    }
''',
    "ask-chat tab menu build removed (was a live crash)")

rep("browser/components/tabbrowser/content/tab-context-menu.js",
    '''ChromeUtils.defineESModuleGetters(TabContextMenu, {
  GenAI: "resource:///modules/GenAI.sys.mjs",
  MenuSectionLayout: "resource:///modules/MenuSectionLayout.sys.mjs",
''',
    '''ChromeUtils.defineESModuleGetters(TabContextMenu, {
  MenuSectionLayout: "resource:///modules/MenuSectionLayout.sys.mjs",
''',
    "drop GenAI getter")

# ===== nsContextMenu.sys.mjs =====
rep("browser/base/content/nsContextMenu.sys.mjs",
    '''  GenAI: "resource:///modules/GenAI.sys.mjs",
  LinkPreview: "moz-src:///browser/components/genai/LinkPreview.sys.mjs",
''',
    "",
    "drop GenAI + LinkPreview getters")

rep("browser/base/content/nsContextMenu.sys.mjs",
    '''    this.showItem(
      "context-previewlink",
      lazy.LinkPreview.shouldShowContextMenu(this)
    );
''',
    '''    this.showItem("context-previewlink", false);
''',
    "link-preview item never shows (was a live crash on link right-click)")

rep("browser/base/content/nsContextMenu.sys.mjs",
    '''  previewLink(url = this.linkURL) {
    // If we're in a view-source tab, remove the view-source: prefix
    url = url.replace(/^view-source:/, "");
    lazy.LinkPreview.handleContextMenuClick(url, this);
  }
''',
    '''  previewLink() {
    // GORILLA OVERRIDE: genai excised — the preview item never shows.
  }
''',
    "previewLink no-op'd")

rep("browser/base/content/nsContextMenu.sys.mjs",
    '''    // GORILLA: EXCISED — no GenAI ask-chat item (AI strip). Re-applied
    // 2026-07-31 on the current FF154 base after the old-base file broke the
    // whole context menu (stale resource://gre ContextualIdentityService
    // import threw during initItems -> every section shown).
    /*
    lazy.GenAI.buildAskChatMenu(document.getElementById("context-ask-chat"), {
      browser: this.browser,
      selectionInfo: this.selectionInfo,
      showItem: this.showItem.bind(this),
      source: "page",
    });
    */
''',
    '''    // GORILLA: EXCISED — no GenAI ask-chat item (genai module removed).
''',
    "stale commented ask-chat block cleaned")

# ===== sidebar-main.mjs =====
rep("browser/components/sidebar/sidebar-main.mjs",
    '''  ShortcutUtils: "resource://gre/modules/ShortcutUtils.sys.mjs",
  GenAI: "resource:///modules/GenAI.sys.mjs",
''',
    '''  ShortcutUtils: "resource://gre/modules/ShortcutUtils.sys.mjs",
''',
    "drop GenAI getter")

rep("browser/components/sidebar/sidebar-main.mjs",
    '''    const menuBuilders = {
      aichat: async () => {
        if (Services.prefs.getBoolPref("browser.ml.chat.page")) {
          await lazy.GenAI.buildAskChatMenu(this._contextMenu, {
            browser: window.gBrowser.selectedBrowser,
            selectionInfo: null,
            source: "tool",
          });
        }
      },
    };
''',
    '''    const menuBuilders = {};
''',
    "aichat menu builder removed")

rep("browser/components/sidebar/sidebar-main.mjs",
    '''    if (action.view === "viewGenaiChatSidebar") {
      providerInfo = lazy.GenAI.currentChatProviderInfo;
      action.iconUrl = providerInfo.iconUrl;
      // Sets the tooltip text for the action based on the chatbot provider's name.
      // This tooltip text is also used to set the action label
      action.tooltiptext = providerInfo.name;
    }

''',
    "",
    "chatbot entrypoint branch removed")

# ===== SpecialMessageActions =====
rep("toolkit/components/messaging-system/lib/SpecialMessageActions.sys.mjs",
    '  GenAI: "resource:///modules/GenAI.sys.mjs",\n',
    "",
    "drop GenAI getter")

rep("toolkit/components/messaging-system/lib/SpecialMessageActions.sys.mjs",
    '''      case "SUMMARIZE_PAGE": {
        const entry = action.data ?? "message";
        await lazy.GenAI.summarizeCurrentPage(window, entry);
        break;
      }
''',
    "",
    "summarize-page action removed")

# ===== DesktopActorRegistry: LinkPreview actor =====
rep("browser/components/DesktopActorRegistry.sys.mjs",
    '''
  LinkPreview: {
    parent: {
      esModuleURI: "resource:///actors/LinkPreviewParent.sys.mjs",
    },
    child: {
      esModuleURI: "resource:///actors/LinkPreviewChild.sys.mjs",
    },
    includeChrome: true,
    enablePreference: "browser.ml.linkPreview.enabled",
    safeForUntrustedWebProcess: true,
  },
''',
    "",
    "LinkPreview actor registration removed")

# ===== preferences =====
rep("browser/components/preferences/main.js",
    '  LinkPreview: "moz-src:///browser/components/genai/LinkPreview.sys.mjs",\n',
    "",
    "drop LinkPreview getter")

rep("browser/components/preferences/config/tabs-browsing.mjs",
    '  LinkPreview: "moz-src:///browser/components/genai/LinkPreview.sys.mjs",\n',
    "",
    "drop LinkPreview getter")

rep("browser/components/preferences/config/tabs-browsing.mjs",
    '''  deps: ["aiControlDefault", "aiControlLinkPreviews"],
  visible: ({ aiControlDefault, aiControlLinkPreviews }) => {
    return (
      window.canShowAiFeature(aiControlLinkPreviews, aiControlDefault) &&
      // @ts-ignore bug 1996860
      lazy.LinkPreview.canShowPreferences
    );
  },
''',
    '''  deps: ["aiControlDefault", "aiControlLinkPreviews"],
  // GORILLA OVERRIDE: genai excised — link-preview settings never show.
  visible: () => false,
''',
    "link-preview setting hidden")

rep("browser/components/preferences/config/tabs-browsing.mjs",
    '''  pref: "browser.ml.linkPreview.optin",
  // LinkPreview.canShowKeyPoints depends on the global genai pref.
  // @ts-ignore bug 1996860
  visible: () => lazy.LinkPreview.canShowKeyPoints,
''',
    '''  pref: "browser.ml.linkPreview.optin",
  // GORILLA OVERRIDE: genai excised — key-points setting never shows.
  visible: () => false,
''',
    "key-points setting hidden")

# ===== moz.build: aiwindow leaves DIRS forever =====
rep("browser/components/moz.build",
    '''    # GORILLA OVERRIDE: aiwindow dir re-enters DIRS but its moz.build now
    # ships ONLY 5 permanent-off stub modules (AI Window body stays excised).
    "aiwindow",
''',
    '''    # GORILLA excised: "aiwindow" (2026-08-02; dir moved to
    # firefox-main.excised-ai-aiwindow-genai.2026-08-02 — stubs no longer
    # needed, zero consumers remain after the Mozambique passes)
''',
    "aiwindow removed from DIRS (endgame)")

print(f"ALL PHASE-C EDITS OK ({len(done)}):")
for d in done:
    print("  ", d)

# ===== directory moves =====
os.makedirs(OUT, exist_ok=True)
moves = [
    ("browser/components/aiwindow", "aiwindow"),
    ("browser/components/genai", "genai"),
    ("browser/themes/addons/aiwindow", "themes-aiwindow"),
    ("browser/themes/addons/aiwindow-nova", "themes-aiwindow-nova"),
]
for src, dst in moves:
    s = FM + src
    d = OUT + dst
    if os.path.isdir(s):
        shutil.move(s, d)
        print(f"MOVED {src} -> {d}")
    else:
        print(f"SKIP (absent): {src}")
