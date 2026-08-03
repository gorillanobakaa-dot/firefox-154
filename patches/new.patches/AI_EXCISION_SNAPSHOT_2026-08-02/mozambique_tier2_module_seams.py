#!/usr/bin/env python3
"""Tier-2 AI Window seam removal: module-side (.sys.mjs) consumers,
messaging system, theme engine, firefoxview chats pane, Smartbar files.

Same discipline as tier 1: every replacement asserts exactly-one match and
aborts loudly before writing anything on drift. Promo-message objects are
removed by brace matching anchored on their unique id strings.
Deleted feature files are backed up to aiwindow-originals/tier2/ first.
"""
import os
import shutil
import sys

FM = "/home/gorilla/firefox-main/"
SNAP = os.path.dirname(os.path.abspath(__file__)) + "/aiwindow-originals/tier2/"
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


def remove_object(path, anchor, label, max_len=20000):
    """Remove a JS object literal (array element) enclosing `anchor`."""
    p = FM + path
    with open(p, encoding="utf-8") as f:
        text = f.read()
    if text.count(anchor) != 1:
        print(f"FAIL [{label}] {path}: anchor count != 1")
        sys.exit(1)
    idx = text.index(anchor)
    # walk back to the opening brace of the enclosing object
    depth = 0
    i = idx
    while i >= 0:
        c = text[i]
        if c == "}":
            depth += 1
        elif c == "{":
            if depth == 0:
                break
            depth -= 1
        i -= 1
    start = i
    # consume preceding whitespace back to line start
    ls = text.rfind("\n", 0, start)
    if text[ls + 1:start].strip() == "":
        start = ls + 1
    # forward brace-match
    depth = 0
    j = i
    while j < len(text):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                break
        j += 1
    end = j + 1
    if text[end:end + 1] == ",":
        end += 1
    if text[end:end + 1] == "\n":
        end += 1
    removed = text[start:end]
    if anchor not in removed or len(removed) > max_len:
        print(f"FAIL [{label}] {path}: bad extraction ({len(removed)} chars)")
        sys.exit(1)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text[:start] + text[end:])
    done.append(f"{path} :: {label} ({len(removed)} chars)")


def delete_file(path, label):
    p = FM + path
    os.makedirs(SNAP, exist_ok=True)
    shutil.copy2(p, SNAP + os.path.basename(path))
    os.remove(p)
    done.append(f"DELETED {path} :: {label} (backup in tier2/)")


AIW_GETTER = ('  AIWindow:\n'
              '    "moz-src:///browser/components/aiwindow/ui/modules/'
              'AIWindow.sys.mjs",\n')

# ========== SessionStore.sys.mjs ==========
rep("browser/components/sessionstore/SessionStore.sys.mjs", AIW_GETTER, "",
    "drop AIWindow getter")

rep("browser/components/sessionstore/SessionStore.sys.mjs",
    '''    if (lazy.AIWindow.isAIWindowActiveAndEnabled(aWindow)) {
      this._windows[aWindow.__SSi].isAIWindow = true;
    }

''',
    "",
    "window-tracking AI flag removed")

rep("browser/components/sessionstore/SessionStore.sys.mjs",
    '''      let windowToUse = windows[lastSessionWindowID];
      let lastWindowIsAIWindow =
        lastWindow && lazy.AIWindow.isAIWindowActive(lastWindow);
      let thisWindowIsAIWindow =
        !!winState.isAIWindow && lazy.AIWindow.isAIWindowEnabled();
      if (
        !windowToUse &&
        canUseLastWindow &&
        lastWindowIsAIWindow == thisWindowIsAIWindow
      ) {
''',
    '''      let windowToUse = windows[lastSessionWindowID];
      if (!windowToUse && canUseLastWindow) {
''',
    "restore window-matching de-AI'd (pre-AI shape)")

rep("browser/components/sessionstore/SessionStore.sys.mjs",
    '''    }

    winData.isAIWindow = lazy.AIWindow.isAIWindowActive(aWindow);
  },
''',
    '''    }
  },
''',
    "window-data AI flag save removed")

rep("browser/components/sessionstore/SessionStore.sys.mjs",
    '''    const isNewDefaultStartupWindow =
      aOptions.firstWindow &&
      !lazy.SessionStartup.willRestore() &&
      lazy.AIWindow.shouldOpenAsSmartWindow();
    const shouldBeAIWindow =
      isNewDefaultStartupWindow ||
      (!!aWinData.isAIWindow && lazy.AIWindow.isAIWindowEnabled());

    const trigger = aOptions.trigger ?? "open_browser";

    if (lazy.AIWindow.isAIWindowActive(aWindow) !== shouldBeAIWindow) {
      lazy.AIWindow.toggleAIWindow(aWindow, shouldBeAIWindow, trigger);
    } else if (shouldBeAIWindow) {
      lazy.AIWindow.recordOpenWindowTelemetry(trigger);
    }

''',
    "",
    "restore-time AI window toggling removed")

rep("browser/components/sessionstore/SessionStore.sys.mjs",
    '''    // A window CANNOT be both a Private Window and an AI Window
    if (winState.isPrivate) {
      features.push("private");
    } else if (winState.isAIWindow) {
      let tab = winState.tabs[winState.selected - 1];
      let restoreSessionURL = "";
      if (tab.entries.length) {
        // tab.index is 1-based in the session store format (0/falsy means unset).
        let activeIndex = (tab.index || tab.entries.length) - 1;
        restoreSessionURL = tab.entries[activeIndex].url;
      }
      argString = lazy.AIWindow.handleAIWindowOptions({
        openerWindow: null,
        args: argString,
        aiWindow: winState.isAIWindow,
        restoreSessionURL,
      });
    }
''',
    '''    if (winState.isPrivate) {
      features.push("private");
    }
''',
    "restore-args AI options removed")

rep("browser/components/sessionstore/session.schema.json",
    '''        "isAIWindow": {
          "type": "boolean"
        },
''',
    "",
    "schema isAIWindow removed")

# ========== NewTabPagePreloading ==========
rep("browser/components/tabbrowser/NewTabPagePreloading.sys.mjs",
    '  AboutNewTab: "resource:///modules/AboutNewTab.sys.mjs",\n' + AIW_GETTER,
    '  AboutNewTab: "resource:///modules/AboutNewTab.sys.mjs",\n',
    "drop AIWindow getter")

rep("browser/components/tabbrowser/NewTabPagePreloading.sys.mjs",
    '''    let winPrivate = lazy.PrivateBrowsingUtils.isWindowPrivate(window);
    let winAIWindow = lazy.AIWindow.isAIWindowActive(window);
    // Grab the least-recently-focused window with a preloaded browser:
    let oldWin = lazy.BrowserWindowTracker.orderedWindows
      .filter(w => {
        return (
          winPrivate == lazy.PrivateBrowsingUtils.isWindowPrivate(w) &&
          winAIWindow == lazy.AIWindow.isAIWindowActive(w) &&
''',
    '''    let winPrivate = lazy.PrivateBrowsingUtils.isWindowPrivate(window);
    // Grab the least-recently-focused window with a preloaded browser:
    let oldWin = lazy.BrowserWindowTracker.orderedWindows
      .filter(w => {
        return (
          winPrivate == lazy.PrivateBrowsingUtils.isWindowPrivate(w) &&
''',
    "adopt-browser AI matching removed")

rep("browser/components/tabbrowser/NewTabPagePreloading.sys.mjs",
    '''    let windowPrivate = lazy.PrivateBrowsingUtils.isWindowPrivate(window);
    let windowAIWindow = lazy.AIWindow.isAIWindowActive(window);
    let countKey = windowPrivate ? "private" : "normal";
    let topWindows = lazy.BrowserWindowTracker.orderedWindows.filter(
      w =>
        lazy.PrivateBrowsingUtils.isWindowPrivate(w) == windowPrivate &&
        lazy.AIWindow.isAIWindowActive(w) == windowAIWindow
    );
''',
    '''    let windowPrivate = lazy.PrivateBrowsingUtils.isWindowPrivate(window);
    let countKey = windowPrivate ? "private" : "normal";
    let topWindows = lazy.BrowserWindowTracker.orderedWindows.filter(
      w => lazy.PrivateBrowsingUtils.isWindowPrivate(w) == windowPrivate
    );
''',
    "preload window-count AI matching removed")

# ========== UrlbarUtils ==========
rep("browser/components/urlbar/UrlbarUtils.sys.mjs",
    'const lazy = XPCOMUtils.declareLazy({\n' + AIW_GETTER,
    'const lazy = XPCOMUtils.declareLazy({\n',
    "drop AIWindow getter")

rep("browser/components/urlbar/UrlbarUtils.sys.mjs",
    ' * @import {SmartbarInput} from "chrome://browser/content/urlbar/SmartbarInput.mjs"\n',
    "",
    "SmartbarInput JSDoc import removed")

rep("browser/components/urlbar/UrlbarUtils.sys.mjs",
    "* @returns {UrlbarInput | SmartbarInput }",
    "* @returns {UrlbarInput}",
    "return type de-AI'd")

rep("browser/components/urlbar/UrlbarUtils.sys.mjs",
    '''    /** @type {UrlbarInput | SmartbarInput} */
    let urlbar = window.gURLBar;
    // Check if we're in an AI window with immersive view (no address bar visible)
    if (
      lazy.AIWindow.isAIWindowActive(window) &&
      lazy.AIWindow.shouldUseImmersiveView(window.gBrowser.currentURI)
    ) {
      let smartbar = lazy.AIWindow.getSmartbarForWindow(window);
      if (smartbar) {
        urlbar = smartbar;
      }
    }
    return urlbar;
''',
    '''    return window.gURLBar;
''',
    "smartbar substitution removed (pre-AI shape)")

# ========== UrlbarInput ==========
rep("browser/components/urlbar/content/UrlbarInput.mjs",
    'const lazy = XPCOMUtils.declareLazy({\n' + AIW_GETTER,
    'const lazy = XPCOMUtils.declareLazy({\n',
    "drop AIWindow getter")

rep("browser/components/urlbar/content/UrlbarInput.mjs",
    '''    return lazy.AIWindow.isAIWindowActive(this.window)
      ? "smartwindow"
      : "classic";
''',
    '''    return "classic";
''',
    "windowMode always classic")

# ========== Smartbar file deletions + jar.mn ==========
rep("browser/components/urlbar/jar.mn",
    '''        content/browser/urlbar/SmartbarInput.mjs           (content/SmartbarInput.mjs)
        content/browser/urlbar/SmartbarInputController.mjs (content/SmartbarInputController.mjs)
        content/browser/urlbar/SmartbarInputUtils.mjs      (content/SmartbarInputUtils.mjs)
''',
    "",
    "Smartbar jar entries removed")

rep("browser/components/urlbar/UrlbarParentController.sys.mjs",
    ' * @import {SapLocation, SmartbarInput} from "moz-src:///browser/components/urlbar/content/SmartbarInput.mjs"\n',
    "",
    "SmartbarInput JSDoc import removed")

rep("browser/components/urlbar/content/UrlbarChildController.mjs",
    ' * @import {SmartbarInput} from "moz-src:///browser/components/urlbar/content/SmartbarInput.mjs"\n',
    "",
    "SmartbarInput JSDoc import removed")

delete_file("browser/components/urlbar/content/SmartbarInput.mjs",
            "AI smartbar (unloadable: its chrome://aiwindow imports are gone)")
delete_file("browser/components/urlbar/content/SmartbarInputController.mjs",
            "AI smartbar controller (only SmartbarInput imported it)")
delete_file("browser/components/urlbar/content/SmartbarInputUtils.mjs",
            "AI smartbar utils (only SmartbarInput imported it)")

# ========== firefoxview chats pane ==========
rep("browser/components/firefoxview/firefoxview.mjs",
    'const lazy = {};\nChromeUtils.defineESModuleGetters(lazy, {\n'
    + AIW_GETTER + '});\n\n',
    "",
    "drop AIWindow getter block")

rep("browser/components/firefoxview/firefoxview.mjs",
    '    { id: "firefoxview-search-text-box-chats" },\n',
    "",
    "chats searchbox l10n entry removed")

rep("browser/components/firefoxview/firefoxview.mjs",
    '''  if (isAIWindow()) {
    await import("chrome://browser/content/firefoxview/chats.mjs");
    document.getElementById("firefoxview-chats-nav").hidden = false;
    document.querySelector("view-chats").hidden = false;
  }

''',
    "",
    "chats pane loader removed")

rep("browser/components/firefoxview/firefoxview.mjs",
    '''
function isAIWindow() {
  return lazy.AIWindow.isAIWindowActiveAndEnabled(topChromeWindow);
}
''',
    "\n",
    "isAIWindow helper removed")

rep("browser/components/firefoxview/firefoxview.html",
    '''      <moz-page-nav-button
        view="chats"
        id="firefoxview-chats-nav"
        data-l10n-id="firefoxview-chats-nav"
        iconSrc="chrome://browser/content/firefoxview/view-chats.svg"
        hidden
      >
      </moz-page-nav-button>
''',
    "",
    "chats nav button removed")

rep("browser/components/firefoxview/firefoxview.html",
    '          <view-chats name="chats" type="page" hidden></view-chats>\n',
    "",
    "chats view element removed")

rep("browser/components/firefoxview/jar.mn",
    '''    content/browser/firefoxview/chats.mjs
    content/browser/firefoxview/chats-tab-list.css
    content/browser/firefoxview/chats-tab-list.mjs
''',
    "",
    "chats jar entries removed")

rep("browser/components/firefoxview/jar.mn",
    '    content/browser/firefoxview/view-chats.svg (content/view-chats.svg)\n',
    "",
    "chats icon jar entry removed")

delete_file("browser/components/firefoxview/chats.mjs", "AI chats pane")
delete_file("browser/components/firefoxview/chats-tab-list.mjs", "AI chats list")
delete_file("browser/components/firefoxview/chats-tab-list.css", "AI chats css")
delete_file("browser/components/firefoxview/ChatsController.sys.mjs",
            "AI chats controller")
delete_file("browser/components/firefoxview/content/view-chats.svg",
            "AI chats icon")

# ========== UITour ==========
rep("browser/components/uitour/UITour.sys.mjs",
    '  AboutReaderParent: "resource:///actors/AboutReaderParent.sys.mjs",\n'
    + AIW_GETTER,
    '  AboutReaderParent: "resource:///actors/AboutReaderParent.sys.mjs",\n',
    "drop AIWindow getter")

rep("browser/components/uitour/UITour.sys.mjs",
    '''      case "showFirefoxAccountsForAIWindow": {
        // if user "Blocked" Smart Window feature from AI Control or global AI Control default
        // override Smart Window feature to "available"
        if (lazy.AIWindow.isBlocked) {
          Services.prefs.setStringPref(
            "browser.ai.control.smartWindow",
            "available"
          );
        }

        lazy.AIWindow.launchWindow(browser).then(success => {
          if (!success) {
            lazy.log.warn(
              "showFirefoxAccountsForAIWindow: Failed to launch Smart Window"
            );
          }
        });
        break;
      }

''',
    "",
    "AI sign-in action removed")

rep("browser/components/uitour/UITour-lib.js",
    '''
  /**
   * Trigger the Firefox Accounts sign-in flow for the AI Window feature.
   *
   * This will prompt the user to sign in and then open the AI Window
   * upon successful authentication.
   *
   * @example
   * Mozilla.UITour.showFirefoxAccountsForAIWindow();
   */
  Mozilla.UITour.showFirefoxAccountsForAIWindow = function () {
    _sendEvent("showFirefoxAccountsForAIWindow");
  };
''',
    "",
    "web-facing AI sign-in API removed")

# ========== browser-sidebar ==========
rep("browser/components/sidebar/browser-sidebar.js",
    '''      get: () =>
        sidebar._prefVisible && !(config.hideInAIWindow && this.isAIWindow()),
''',
    '''      get: () => sidebar._prefVisible,
''',
    "sidebar visibility de-AI'd")

rep("browser/components/sidebar/browser-sidebar.js",
    '''
  isAIWindow() {
    return this.AIWindow.isAIWindowActive(window);
  },
''',
    "",
    "isAIWindow helper removed")

rep("browser/components/sidebar/browser-sidebar.js",
    '        hideInAIWindow: true,\n',
    "",
    "hideInAIWindow config removed")

rep("browser/components/sidebar/browser-sidebar.js",
    'ChromeUtils.defineESModuleGetters(SidebarController, {\n' + AIW_GETTER,
    'ChromeUtils.defineESModuleGetters(SidebarController, {\n',
    "drop AIWindow getter")

# ========== ASRouter / targeting / messages ==========
rep("browser/components/asrouter/modules/ASRouter.sys.mjs",
    '  ToolbarBadgeHub: "resource:///modules/asrouter/ToolbarBadgeHub.sys.mjs",\n'
    + AIW_GETTER + '});',
    '  ToolbarBadgeHub: "resource:///modules/asrouter/ToolbarBadgeHub.sys.mjs",\n});',
    "drop AIWindow getter")

rep("browser/components/asrouter/modules/ASRouter.sys.mjs",
    '''        trigger.context.isAIWindow = !!lazy.AIWindow?.isAIWindowActive?.(
          browser.documentGlobal
        );
''',
    "",
    "trigger-context AI flag removed")

rep("browser/components/asrouter/modules/ASRouterTargeting.sys.mjs",
    '''
function addAIWindowTargeting(targeting) {
  if (!targeting || targeting === "true") {
    // Default behavior: Classic-only if no targeting is specified
    return `!isAIWindow`;
  }

  if (/\\bisAIWindow\\b/.test(targeting)) {
    return targeting;
  }

  return `((${targeting}) && !isAIWindow)`;
}
''',
    "",
    "addAIWindowTargeting removed (every-message AI ask)")

rep("browser/components/asrouter/modules/ASRouterTargeting.sys.mjs",
    '''    let { targeting } = message;
    targeting = addAIWindowTargeting(targeting);
''',
    '''    let { targeting } = message;
''',
    "targeting rewrite call removed")

remove_object("browser/components/asrouter/modules/OnboardingMessageProvider.sys.mjs",
              'id: "SMARTWINDOW_DEFAULT_PROMO",',
              "SMARTWINDOW_DEFAULT_PROMO message removed")
remove_object("browser/components/asrouter/modules/OnboardingMessageProvider.sys.mjs",
              'id: "SMARTWINDOW_FEEDBACK_MODAL_POSITIVE",',
              "feedback-positive message removed")
remove_object("browser/components/asrouter/modules/OnboardingMessageProvider.sys.mjs",
              'id: "SMARTWINDOW_FEEDBACK_MODAL_NEGATIVE",',
              "feedback-negative message removed")
remove_object("browser/components/asrouter/modules/FeatureCalloutMessages.sys.mjs",
              'id: "SMARTWINDOW_NEWTAB_CALLOUT",',
              "newtab callout removed")
remove_object("browser/components/asrouter/modules/FeatureCalloutMessages.sys.mjs",
              'id: "SMARTWINDOW_CLOSE_CURRENT_TAB",',
              "close-tab callout removed")
remove_object("browser/components/asrouter/modules/FeatureCalloutMessages.sys.mjs",
              'id: "SMARTWINDOW_SIDEBAR_AUTO_OPEN_PROMPT",',
              "sidebar auto-open prompt removed")
remove_object("browser/components/asrouter/modules/PanelTestProvider.sys.mjs",
              'id: "TEST_CONTENT_ANCHOR",',
              "AI-anchored test message removed")

rep("browser/components/asrouter/modules/PanelTestProvider.sys.mjs",
    '''      MESSAGES().map(message => ({
        ...message,
        targeting:
          typeof message.targeting === "string" &&
          message.targeting?.includes("isAIWindow")
            ? `isAIWindow && providerCohorts.panel_local_testing == "SHOW_TEST"`
            : `providerCohorts.panel_local_testing == "SHOW_TEST"`,
      }))
''',
    '''      MESSAGES().map(message => ({
        ...message,
        targeting: `providerCohorts.panel_local_testing == "SHOW_TEST"`,
      }))
''',
    "test-provider targeting de-AI'd")

# ========== SpecialMessageActions ==========
rep("toolkit/components/messaging-system/lib/SpecialMessageActions.sys.mjs",
    '''  AIWindow:
    // eslint-disable-next-line mozilla/no-browser-refs-in-toolkit
    "moz-src:///browser/components/aiwindow/ui/modules/AIWindow.sys.mjs",
''',
    "",
    "drop AIWindow getter")

rep("toolkit/components/messaging-system/lib/SpecialMessageActions.sys.mjs",
    '''      case "FXA_AIWINDOW_SIGNIN_FLOW":
        /** @returns {Promise<boolean>} */
        return lazy.AIWindow.launchWindow(browser);
''',
    "",
    "AI sign-in action removed")

# ========== BrowserContentHandler ==========
rep("browser/components/BrowserContentHandler.sys.mjs",
    '''ChromeUtils.defineESModuleGetters(lazy, {
  AIWindow:
    "moz-src:///browser/components/aiwindow/ui/modules/AIWindow.sys.mjs",
  AIWindowAccountAuth:
    "moz-src:///browser/components/aiwindow/ui/modules/AIWindowAccountAuth.sys.mjs",
  AsyncShutdown: "resource://gre/modules/AsyncShutdown.sys.mjs",
''',
    '''ChromeUtils.defineESModuleGetters(lazy, {
  AsyncShutdown: "resource://gre/modules/AsyncShutdown.sys.mjs",
''',
    "drop AIWindow + AccountAuth getters")

# remove canOpenAsSmartWindow with its JSDoc (anchored back to the /**)
p = FM + "browser/components/BrowserContentHandler.sys.mjs"
with open(p, encoding="utf-8") as f:
    text = f.read()
fn_anchor = "function canOpenAsSmartWindow(forcePrivate = false) {"
if text.count(fn_anchor) != 1:
    print("FAIL [canOpenAsSmartWindow] anchor count != 1")
    sys.exit(1)
fn_idx = text.index(fn_anchor)
doc_start = text.rfind("/**", 0, fn_idx)
fn_end = text.index("\n}\n", fn_idx) + len("\n}\n")
if doc_start < 0 or fn_idx - doc_start > 2500:
    print("FAIL [canOpenAsSmartWindow] JSDoc anchor sanity")
    sys.exit(1)
chunk = text[doc_start:fn_end]
if "GORILLA excised" not in chunk:
    print("FAIL [canOpenAsSmartWindow] unexpected body")
    sys.exit(1)
with open(p, "w", encoding="utf-8") as f:
    f.write(text[:doc_start] + text[fn_end + 1:])
done.append("BrowserContentHandler.sys.mjs :: canOpenAsSmartWindow + JSDoc removed")

rep("browser/components/BrowserContentHandler.sys.mjs",
    '''  const openAsSmart = canOpenAsSmartWindow(forcePrivate);

  let args;
''',
    '''  let args;
''',
    "openAsSmart computation removed")

rep("browser/components/BrowserContentHandler.sys.mjs",
    '''    // Smart Window needs args as an nsIMutableArray so handleAIWindowOptions can append its attributes
    if (openAsSmart) {
      let array = Cc["@mozilla.org/array;1"].createInstance(Ci.nsIMutableArray);
      array.appendElement(string);
      args = array;
    } else {
      // Single string guaranteed to not contain '|' can simply be wrapped
      // in an nsISupportsString object.
      args = string;
    }
''',
    '''    // Single string guaranteed to not contain '|' can simply be wrapped
    // in an nsISupportsString object.
    args = string;
''',
    "smart-window args wrapping removed (pre-AI shape)")

rep("browser/components/BrowserContentHandler.sys.mjs",
    '''    private: forcePrivate,
    aiWindow: openAsSmart,
  });
''',
    '''    private: forcePrivate,
  });
''',
    "openWindow aiWindow option removed")

rep("browser/components/BrowserContentHandler.sys.mjs",
    '''    // Substitute about:home with the Smart Window URL when the user has
    // chosen Smart Window as default. Done here (rather than in
    // getFirstWindowArgs) so that BrowserHandler.defaultArgs — which
    // browser-init.js compares against to decide session-restore /
    // crash-recovery overrides — reflects the same URL. A user with
    // browser.startup.page=0 has explicitly chosen blank startup, which we
    // respect — they'll get Smart Window chrome with about:blank content.
    if (startPage === "about:home" && canOpenAsSmartWindow()) {
      startPage = lazy.AIWindow.initialStartupURL;
    }

''',
    "",
    "startup-page AI substitution removed")

# ========== Sanitizer ==========
rep("browser/modules/Sanitizer.sys.mjs",
    '''ChromeUtils.defineESModuleGetters(lazy, {
  AIWindow:
    "moz-src:///browser/components/aiwindow/ui/modules/AIWindow.sys.mjs",
  ChatStore:
    "moz-src:///browser/components/aiwindow/ui/modules/ChatStore.sys.mjs",
  ContextualIdentityService:
''',
    '''ChromeUtils.defineESModuleGetters(lazy, {
  ContextualIdentityService:
''',
    "drop AIWindow + ChatStore getters")

rep("browser/modules/Sanitizer.sys.mjs",
    '''        Glean.browserSanitizer.downloads.stopAndAccumulate(timerId);

        await clearChatConversations(range, progress);
''',
    '''        Glean.browserSanitizer.downloads.stopAndAccumulate(timerId);
''',
    "history-item chat clear call removed")

rep("browser/modules/Sanitizer.sys.mjs",
    '''        Glean.browserSanitizer.cookies.stopAndAccumulate(timerId);

        await clearChatConversations(range, progress);
''',
    '''        Glean.browserSanitizer.cookies.stopAndAccumulate(timerId);
''',
    "cookies-item chat clear call removed")

rep("browser/modules/Sanitizer.sys.mjs",
    '''
// Clear chat conversations if AI Window is enabled.
// (ChatStore uses milliseconds.)
async function clearChatConversations(range, progress) {
  if (!lazy.AIWindow.isEnabled) {
    return;
  }
  progress.step = "clearing Smart Window chat conversations";
  try {
    if (range) {
      let startDate = new Date(range[0] / 1000);
      let endDate = new Date(range[1] / 1000);
      await lazy.ChatStore.deleteConversationsByDateRange(startDate, endDate);
    } else {
      await lazy.ChatStore.deleteAllConversations();
    }
  } catch (ex) {
    log("Failed to clear chat conversations", ex);
  }
}
''',
    "",
    "clearChatConversations removed")

# ========== ProfileDataUpgrader ==========
rep("browser/components/ProfileDataUpgrader.sys.mjs",
    '''
    if (existingDataVersion < 164) {
      const { PREF_BOOL, PREF_INT, PREF_STRING } = Services.prefs;
      const METHODS = {
        [PREF_BOOL]: ["getBoolPref", "setBoolPref"],
        [PREF_INT]: ["getIntPref", "setIntPref"],
        [PREF_STRING]: ["getStringPref", "setStringPref"],
      };
      const OLD_PREFIX = "browser.aiwindow.";
      for (let oldPref of Services.prefs.getChildList(OLD_PREFIX)) {
        let prefType = Services.prefs.getPrefType(oldPref);
        if (
          !Services.prefs.prefHasUserValue(oldPref) ||
          !Object.hasOwn(METHODS, prefType)
        ) {
          continue;
        }
        let newPref =
          "browser.smartwindow." + oldPref.substring(OLD_PREFIX.length);
        let [getter, setter] = METHODS[prefType];
        Services.prefs[setter](newPref, Services.prefs[getter](oldPref));
        Services.prefs.clearUserPref(oldPref);
      }
    }
''',
    "",
    "aiwindow pref migration removed")

# ========== storybook ==========
rep("browser/components/storybook/.storybook/main.js",
    "    `${projectRoot}/browser/components/aiwindow/ui/**/*.stories.mjs`,\n",
    "",
    "storybook glob removed")

# ========== LightweightThemeConsumer ==========
LWTC = "toolkit/modules/LightweightThemeConsumer.sys.mjs"
rep(LWTC,
    '  this._isAIWindow = this._doc.documentElement.hasAttribute("ai-window");\n',
    "",
    "ctor ai-window flag removed")

rep(LWTC,
    '''    2,
    () => {
      if (this._isAIWindow) {
        this._update(this._lastData);
      }
    }
  );
''',
    '''    2,
    () => {}
  );
''',
    "toolbar-theme AI callback no-op'd")

rep(LWTC,
    '''
  this._aiWindowObserver = new this._win.MutationObserver(() => {
    this.toggleAIWindowMode(this._win);
  });
  this._aiWindowObserver.observe(this._doc.documentElement, {
    attributeFilter: ["ai-window"],
  });
''',
    "",
    "ai-window MutationObserver removed")

rep(LWTC,
    '''        Services.ppmm.sharedData.delete(`theme/${this._winId}`);
        this._aiWindowObserver?.disconnect();
        this._aiWindowObserver = null;
''',
    '''        Services.ppmm.sharedData.delete(`theme/${this._winId}`);
''',
    "observer cleanup removed")

rep(LWTC,
    '    // Store user\'s theme before replacing with aiThemeData or privateThemeData.\n',
    '    // Store user\'s theme before replacing with privateThemeData.\n',
    "comment de-AI'd")

rep(LWTC,
    '''    if (this._isAIWindow) {
      const useNova = this.BROWSER_NOVA_ENABLED;
      const cachedData = useNova
        ? manager.aiNovaThemeData
        : manager.aiThemeData;
      if (cachedData) {
        themeData = cachedData;
        isDefaultOrInApp = true;
      } else {
        const promise = useNova
          ? manager.promiseAINovathemeData()
          : manager.promiseAIThemeData();
        promise.then(() => {
          if (this._isAIWindow && this._win && !this._win.closed) {
            this._update(this._lastData);
          }
        });
        return;
      }
    } else if (
''',
    '''    if (
''',
    "AI theme substitution branch removed")

rep(LWTC,
    '''    if (this._isAIWindow || isPrivateThemeActive) {
''',
    '''    if (isPrivateThemeActive) {
''',
    "global-theme-data guard de-AI'd")

rep(LWTC,
    '''
  toggleAIWindowMode(win) {
    this._isAIWindow = win.document.documentElement.hasAttribute("ai-window");
    this._update(lazy.LightweightThemeManager.themeData);
  },
''',
    "",
    "toggleAIWindowMode removed")

# ========== LightweightThemeManager ==========
rep("toolkit/mozapps/extensions/LightweightThemeManager.sys.mjs",
    '''export var LightweightThemeManager = {
  aiThemeData: null,
  _aiThemeDataPromise: null,

  async promiseAIThemeData() {
    if (this.aiThemeData) {
      return this.aiThemeData;
    }

    if (this._aiThemeDataPromise) {
      return this._aiThemeDataPromise;
    }

    this._aiThemeDataPromise = this._fetchThemeDataFromBuiltinManifest(
      "resource://builtin-themes/aiwindow/"
    ).then(data => {
      this.aiThemeData = data;
      this._aiThemeDataPromise = null;
      return data;
    });

    return this._aiThemeDataPromise;
  },
''',
    '''export var LightweightThemeManager = {
''',
    "AI theme data provider removed")

print(f"ALL TIER-2 EDITS OK ({len(done)}):")
for d in done:
    print("  ", d)

# ---------- post-verification ----------
import subprocess
r = subprocess.run(
    ["grep", "-rn", "aiwindow/ui/modules", FM + "browser", FM + "toolkit",
     "--include=*.mjs", "--include=*.js", "-l"],
    capture_output=True, text=True)
survivors = [l for l in r.stdout.splitlines()
             if "/browser/components/aiwindow/" not in l and "test" not in l]
print("\nREMAINING stub consumers (want NONE):")
print("\n".join(survivors) if survivors else "  NONE — stubs are orphaned, Phase C is a go")
