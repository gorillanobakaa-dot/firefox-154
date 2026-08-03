#!/usr/bin/env python3
"""Tier-1 AI Window seam removal ("Mozambique pass").

Reverses the exact grafts Mozilla added to window-chrome files so each
consumer stops ASKING the AI module anything. Every replacement asserts
exactly-one match; any drift aborts loudly before writing.
"""
import sys

FM = "/home/gorilla/firefox-main/"
edits_done = []


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
    edits_done.append(f"{path} :: {label}")


# ---------- browser-sets.js ----------
rep("browser/base/content/browser-sets.js",
    '''      TranslationsParent: "resource://gre/actors/TranslationsParent.sys.mjs",
      AIWindowUI:
        "moz-src:///browser/components/aiwindow/ui/modules/AIWindowUI.sys.mjs",
''',
    '''      TranslationsParent: "resource://gre/actors/TranslationsParent.sys.mjs",
''',
    "drop AIWindowUI lazy getter")

rep("browser/base/content/browser-sets.js",
    '''          case "cmd_newNavigator":
            if (AIWindow.isDefaultWindow) {
              AIWindow.launchWindow(
                gBrowser?.selectedBrowser,
                true,
                "keyboard_shortcut"
              );
            } else {
              OpenBrowserWindow();
            }
            break;
''',
    '''          case "cmd_newNavigator":
            // GORILLA OVERRIDE: pre-AI behavior restored — Ctrl+N always
            // opens a normal browser window, never an AI window.
            OpenBrowserWindow();
            break;
''',
    "Ctrl+N hijack removed")

rep("browser/base/content/browser-sets.js",
    '''          case "Tools:ClassicWindow":
            OpenBrowserWindow({ aiWindow: false });
            break;
          case "Tools:AIWindow":
            AIWindow.launchWindow(gBrowser?.selectedBrowser, true, "menu");
            break;
          case "Tools:ChatsHistory":
            FirefoxViewHandler.openTab("chats");
            break;
''',
    '''          // GORILLA OVERRIDE: Tools:AIWindow / Tools:ClassicWindow /
          // Tools:ChatsHistory command cases removed with the AI Window
          // excision (their <command> elements are gone from browser-sets.inc.xhtml).
''',
    "AI window/classic/chats commands removed")

rep("browser/base/content/browser-sets.js",
    '''        case "viewGenaiChatSidebarKb": {
          const currentURI = window.gBrowser.selectedBrowser.currentURI;
          const isSmartWindowFullPageMode =
            AIWindow.isAIWindowContentPage(currentURI);
          if (AIWindow.isAIWindowActive(window) && !isSmartWindowFullPageMode) {
            lazy.AIWindowUI.toggleSidebar(window);
            break;
          }

          const pref = "browser.ml.chat.enabled";
''',
    '''        case "viewGenaiChatSidebarKb": {
          // GORILLA OVERRIDE: AI Window sidebar branch removed.
          const pref = "browser.ml.chat.enabled";
''',
    "genai-shortcut AI branch removed")

# ---------- browser-main.js ----------
rep("browser/base/content/browser-main.js",
    '''  if (AIWindow.isOpeningAIWindow(window)) {
    ChromeUtils.importESModule("chrome://browser/content/urlbar/SmartbarInput.mjs", { global: "current" });
  }
''',
    "",
    "Smartbar conditional import removed")

# ---------- browser-menubar.js ----------
rep("browser/base/content/browser-menubar.js",
    '''          if (!event.target.parentNode._placesView) {
            new HistoryMenu(event);
          }

          AIWindow.appMenu(event, window);
          break;
''',
    '''          if (!event.target.parentNode._placesView) {
            new HistoryMenu(event);
          }
          break;
''',
    "history-menu AI hook removed")

# ---------- navigator-toolbox.js ----------
rep("browser/base/content/navigator-toolbox.js",
    '''ChromeUtils.defineESModuleGetters(this, {
  AIWindowUI:
    "moz-src:///browser/components/aiwindow/ui/modules/AIWindowUI.sys.mjs",
});

''',
    "",
    "drop AIWindowUI getter")

rep("browser/base/content/navigator-toolbox.js",
    '''
        case "smartwindow-ask-button":
          if (isLeftClick) {
            AIWindowUI.toggleSidebar(window);
          }
          break;
''',
    "",
    "ask-button click case removed")

rep("browser/base/content/navigator-toolbox.js",
    '''
        case "smartwindow-ask-button":
          if (isLikeLeftClick) {
            AIWindowUI.toggleSidebar(window);
          }
          break;
''',
    "",
    "ask-button keynav case removed")

# ---------- places-commands.js ----------
rep("browser/components/places/content/places-commands.js",
    '''    case "Browser:ShowAllHistory":
      if (AIWindow.isAIWindowActive(window)) {
        FirefoxViewHandler.openTab("history");
      } else {
        PlacesCommandHook.showPlacesOrganizer("History");
      }
      break;
''',
    '''    case "Browser:ShowAllHistory":
      PlacesCommandHook.showPlacesOrganizer("History");
      break;
''',
    "history command pre-AI behavior restored")

# ---------- utilityOverlay.js ----------
rep("browser/base/content/utilityOverlay.js",
    '''  AboutNewTab: "resource:///modules/AboutNewTab.sys.mjs",
  AIWindow:
    "moz-src:///browser/components/aiwindow/ui/modules/AIWindow.sys.mjs",
''',
    '''  AboutNewTab: "resource:///modules/AboutNewTab.sys.mjs",
''',
    "drop AIWindow getter")

rep("browser/base/content/utilityOverlay.js",
    '''    if (AIWindow.isAIWindowActive(window)) {
      return AIWindow.newTabURL;
    }
    return AboutNewTab.newTabURL;
''',
    '''    return AboutNewTab.newTabURL;
''',
    "new-tab URL override removed")

# ---------- browser.js ----------
rep("browser/base/content/browser.js",
    '''ChromeUtils.defineESModuleGetters(this, {
  AIWindow:
    "moz-src:///browser/components/aiwindow/ui/modules/AIWindow.sys.mjs",
  AMTelemetry: "resource://gre/modules/AddonManager.sys.mjs",
''',
    '''ChromeUtils.defineESModuleGetters(this, {
  AMTelemetry: "resource://gre/modules/AddonManager.sys.mjs",
''',
    "drop AIWindow getter")

rep("browser/base/content/browser.js",
    '''
    const aiWindowMenu = event.target.querySelector("#menu_newAIWindow");
    const classicWindowMenu = event.target.querySelector(
      "#menu_newClassicWindow"
    );

    aiWindowMenu.hidden =
      !AIWindow.isAIWindowEnabled() || AIWindow.isAIWindowActive(window);
    classicWindowMenu.hidden =
      !AIWindow.isAIWindowEnabled() || !AIWindow.isAIWindowActive(window);
  },
''',
    '''
  },
''',
    "file-menu AI item toggling removed")

rep("browser/base/content/browser.js",
    '''      updateBookmarkToolbarVisibility();
      AIWindow.updateImmersiveView(gBrowser.currentURI, window);
''',
    '''      updateBookmarkToolbarVisibility();
''',
    "immersive-view hook removed")

# ---------- browser-sync.js ----------
rep("browser/base/content/browser-sync.js",
    '''ChromeUtils.defineESModuleGetters(this, {
  AIWindow:
    "moz-src:///browser/components/aiwindow/ui/modules/AIWindow.sys.mjs",
  ASRouter: "resource:///modules/asrouter/ASRouter.sys.mjs",
''',
    '''ChromeUtils.defineESModuleGetters(this, {
  ASRouter: "resource:///modules/asrouter/ASRouter.sys.mjs",
''',
    "drop AIWindow getter")

rep("browser/base/content/browser-sync.js",
    '''    const bodyId = AIWindow.hasActiveAIWindows()
      ? "fxa-signout-dialog-body-aiwindow"
      : "fxa-signout-dialog-body";
''',
    '''    const bodyId = "fxa-signout-dialog-body";
''',
    "signout dialog AI variant removed")

# ---------- sanitizeDialog.js ----------
rep("browser/base/content/sanitizeDialog.js",
    '''ChromeUtils.defineESModuleGetters(lazy, {
  AIWindow:
    "moz-src:///browser/components/aiwindow/ui/modules/AIWindow.sys.mjs",
  DownloadUtils: "resource://gre/modules/DownloadUtils.sys.mjs",
''',
    '''ChromeUtils.defineESModuleGetters(lazy, {
  DownloadUtils: "resource://gre/modules/DownloadUtils.sys.mjs",
''',
    "drop AIWindow getter")

# brace-matched removal of the isEnabled label-swap block
p = FM + "browser/base/content/sanitizeDialog.js"
with open(p, encoding="utf-8") as f:
    text = f.read()
marker = ("    // Update history labels to include chat conversations if "
          "Smart Window is enabled.\n    if (lazy.AIWindow.isEnabled) {")
start = text.find(marker)
if start < 0:
    print("FAIL [sanitize label block] marker not found")
    sys.exit(1)
brace_open = text.index("{", start + marker.index("if ("))
depth = 0
i = brace_open
while i < len(text):
    if text[i] == "{":
        depth += 1
    elif text[i] == "}":
        depth -= 1
        if depth == 0:
            break
    i += 1
end = text.index("\n", i) + 1
if text.count(marker) != 1:
    print("FAIL [sanitize label block] marker not unique")
    sys.exit(1)
with open(p, "w", encoding="utf-8") as f:
    f.write(text[:start] + text[end:])
edits_done.append("sanitizeDialog.js :: chat-label block removed (brace-matched)")

# ---------- nsContextMenu.sys.mjs ----------
rep("browser/base/content/nsContextMenu.sys.mjs",
    '''ChromeUtils.defineESModuleGetters(lazy, {
  AIWindow:
    "moz-src:///browser/components/aiwindow/ui/modules/AIWindow.sys.mjs",
  BrowserSearchTelemetry:
''',
    '''ChromeUtils.defineESModuleGetters(lazy, {
  BrowserSearchTelemetry:
''',
    "drop AIWindow getter")

rep("browser/base/content/nsContextMenu.sys.mjs",
    '''    let showSmartWindow = lazy.AIWindow.isAIWindowEnabled();
''',
    '''    // GORILLA OVERRIDE: AI Window excised — smart-window link item never shows.
    let showSmartWindow = false;
''',
    "context-menu smart-window item disabled")

# ---------- panelUI.js ----------
p = FM + "browser/components/customizableui/content/panelUI.js"
with open(p, encoding="utf-8") as f:
    text = f.read()
start_anchor = "  _showAIMenuItem() {"
end_anchor = "  _showTabGroupsMenuItem() {"
s = text.find(start_anchor)
e = text.find(end_anchor)
if s < 0 or e < 0 or e <= s:
    print("FAIL [panelUI] anchors not found")
    sys.exit(1)
replacement = (
    "  _showAIMenuItem() {\n"
    "    // GORILLA OVERRIDE: AI Window excised; the app-menu AI/classic/chat\n"
    "    // items were removed from appmenu-viewcache.inc.xhtml, so there is\n"
    "    // nothing to toggle.\n"
    "  },\n\n"
)
with open(p, "w", encoding="utf-8") as f:
    f.write(text[:s] + replacement + text[e:])
edits_done.append("panelUI.js :: _showAIMenuItem no-op'd")

# ---------- XHTML: command set ----------
rep("browser/base/content/browser-sets.inc.xhtml",
    '''    <command id="Tools:AIWindow" />
    <command id="Tools:ChatsHistory" />
    <command id="Tools:ClassicWindow" />
''',
    "",
    "AI command elements removed")

# ---------- XHTML: menubar ----------
rep("browser/base/content/browser-menubar.inc.xhtml",
    '''                <menuitem id="menu_newAIWindow"
                          command="Tools:AIWindow"
                          data-l10n-id="menu-file-new-ai-window"/>
                <menuitem id="menu_newClassicWindow"
                          command="Tools:ClassicWindow"
                          data-l10n-id="menu-file-new-classic-window"/>
''',
    "",
    "File-menu AI items removed")

rep("browser/base/content/browser-menubar.inc.xhtml",
    '''
                <menuitem id="chatsHistoryMenu" class="chats-history-menuitem"
                          data-l10n-id="menu-history-chats"
                          disabled="true" hidden="true" command="Tools:ChatsHistory"/>
''',
    "",
    "History-menu chats item removed")

# ---------- XHTML: app menu ----------
rep("browser/base/content/appmenu-viewcache.inc.xhtml",
    '''      <toolbarbutton id="appMenu-new-ai-window-button"
                     class="subviewbutton"
                     command="Tools:AIWindow"
                     aria-describedby="appMenu-new-ai-window-badge">
        <label class="toolbarbutton-text" crop="end"
               data-l10n-id="appmenuitem-new-ai-window"/>
        <html:moz-badge id="appMenu-new-ai-window-badge"
                        type="beta"/>
      </toolbarbutton>
      <toolbarbutton id="appMenu-new-classic-window-button"
                     class="subviewbutton"
                     data-l10n-id="appmenuitem-new-classic-window"
                     command="Tools:ClassicWindow"/>
''',
    "",
    "app-menu AI/classic window buttons removed")

rep("browser/base/content/appmenu-viewcache.inc.xhtml",
    '''      <toolbarbutton id="appMenu-chats-history-button"
                     class="subviewbutton"
                     data-l10n-id="menu-history-chats"
                     command="Tools:ChatsHistory"/>
''',
    "",
    "app-menu chats-history button removed")

# ---------- tabbrowser.js ----------
rep("browser/components/tabbrowser/content/tabbrowser.js",
    '''    "about:privatebrowsing":
      "chrome://browser/skin/privatebrowsing/favicon.svg",
    "chrome://browser/content/aiwindow/aiWindow.html":
      "chrome://browser/skin/smart-window-simplified.svg",
  };
''',
    '''    "about:privatebrowsing":
      "chrome://browser/skin/privatebrowsing/favicon.svg",
  };
''',
    "AI favicon map entry removed")

rep("browser/components/tabbrowser/content/tabbrowser.js",
    '''
      if (AIWindow.isAIWindowActive(window)) {
        let uriToLoad = gBrowserInit.uriToLoadPromise;
        let firstURI = Array.isArray(uriToLoad) ? uriToLoad[0] : uriToLoad;

        if (!this._allowTransparentBrowser) {
          // firstURI may be a Promise (uriToLoadPromise still resolving while
          // SessionStore restores) or empty; only build a URI from a real
          // string, otherwise default to transparent like the no-URI case.
          browser.toggleAttribute(
            "transparent",
            !firstURI ||
              typeof firstURI != "string" ||
              AIWindow.isAIWindowContentPage(Services.io.newURI(firstURI))
          );
        }
      }
''',
    "",
    "transparent-browser AI block removed")

rep("browser/components/tabbrowser/content/tabbrowser.js",
    '''      if (AIWindow.isAIWindowActive(window) || this._allowTransparentBrowser) {
''',
    '''      if (this._allowTransparentBrowser) {
''',
    "createBrowser transparency condition de-AI'd")

rep("browser/components/tabbrowser/content/tabbrowser.js",
    '''
          if (!gBrowser._allowTransparentBrowser) {
            this._browser.toggleAttribute(
              "transparent",
              AIWindow.isAIWindowActive(window) &&
                AIWindow.isAIWindowContentPage(aLocation)
            );
          }
''',
    "",
    "location-change transparency toggle removed")

# ---------- browser-init.js ----------
rep("browser/base/content/browser-init.js",
    '''      if (extraOptions.hasKey("ai-window")) {
        document.documentElement.setAttribute("ai-window", true);
      }
      if (extraOptions.hasKey("aiwindow-immersive-view")) {
        document.documentElement.setAttribute("aiwindow-immersive-view", true);
      }
      if (extraOptions.hasKey("aiwindow-new-window")) {
        document.documentElement.setAttribute("aiwindow-new-window", true);
      }
''',
    "",
    "ai-window attribute plumbing removed")

print(f"ALL EDITS OK ({len(edits_done)}):")
for e in edits_done:
    print("  ", e)
