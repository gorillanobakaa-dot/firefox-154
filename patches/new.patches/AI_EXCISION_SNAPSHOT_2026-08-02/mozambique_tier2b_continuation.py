#!/usr/bin/env python3
"""Tier-2b continuation: resumes after mozambique_tier2_module_seams.py
aborted (correctly, pre-write) on the promo-message anchor appearing twice
(outer message id + inner dismiss-action id). remove_object now anchors on
the FIRST occurrence and asserts every other occurrence lies inside the
extracted object. Also carries all steps that followed the abort point.
"""
import os
import shutil
import sys

FM = "/home/gorilla/firefox-main/"
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
    p = FM + path
    with open(p, encoding="utf-8") as f:
        text = f.read()
    total = text.count(anchor)
    if total < 1:
        print(f"FAIL [{label}] {path}: anchor not found")
        sys.exit(1)
    idx = text.index(anchor)
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
    ls = text.rfind("\n", 0, start)
    if text[ls + 1:start].strip() == "":
        start = ls + 1
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
    if removed.count(anchor) != total or len(removed) > max_len:
        print(f"FAIL [{label}] {path}: extraction covers "
              f"{removed.count(anchor)}/{total} anchors, {len(removed)} chars")
        sys.exit(1)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text[:start] + text[end:])
    done.append(f"{path} :: {label} ({len(removed)} chars)")


AIW_GETTER = ('  AIWindow:\n'
              '    "moz-src:///browser/components/aiwindow/ui/modules/'
              'AIWindow.sys.mjs",\n')

# ========== promo/callout message objects ==========
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
    "    // Store user's theme before replacing with aiThemeData or privateThemeData.\n",
    "    // Store user's theme before replacing with privateThemeData.\n",
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

print(f"ALL TIER-2B EDITS OK ({len(done)}):")
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
