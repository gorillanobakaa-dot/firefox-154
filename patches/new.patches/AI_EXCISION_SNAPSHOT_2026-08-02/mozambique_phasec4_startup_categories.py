#!/usr/bin/env python3
"""Phase C4: startup-category and provider registrations — the string-based
couplings the static map can't see. GenAI.init and LinkPreview.init were
registered as startup-category hooks in BrowserComponents.manifest;
ModelHubProvider (about:addons local-AI-models section) as an addon-provider
category; TranslationsParent.AIFeature chained into the excised ml layer
(restored to the pre-AI plain-pref semantic); and the aichat sidebar
registration (dead pref, missing l10n) is retired."""
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

rep("browser/components/BrowserComponents.manifest",
    "category browser-window-delayed-startup moz-src:///browser/components/genai/LinkPreview.sys.mjs LinkPreview.init\n",
    "",
    "LinkPreview.init startup category removed")

rep("browser/components/BrowserComponents.manifest",
    "category browser-idle-startup resource:///modules/GenAI.sys.mjs GenAI.init\n",
    "",
    "GenAI.init startup category removed")

rep("toolkit/mozapps/extensions/extensions.manifest",
    "category addon-provider-module ModelHubProvider resource://gre/modules/addons/ModelHubProvider.sys.mjs\n",
    "",
    "ModelHubProvider addon-provider registration removed (ml excised)")

rep("toolkit/components/translations/actors/TranslationsParent.sys.mjs",
    '''  TranslationsFeature:
    "chrome://global/content/translations/TranslationsFeature.sys.mjs",
''',
    "",
    "drop TranslationsFeature lazy getter (imports excised ml AIFeature)")

rep("toolkit/components/translations/actors/TranslationsParent.sys.mjs",
    '''  /**
   * Translations AIFeature implementation.
   *
   * @returns {typeof TranslationsFeature}
   */
  static get AIFeature() {
    return lazy.TranslationsFeature;
  }
''',
    '''  /**
   * GORILLA OVERRIDE: the ml AIFeature layer is excised. Pre-AI behavior
   * restored — Translations enabled-ness is the plain pref check it always
   * was before the AI-controls wrapper existed. All in-tree callers use
   * only `.isEnabled` (verified 2026-08-02).
   */
  static get AIFeature() {
    return {
      get isEnabled() {
        return Services.prefs.getBoolPref("browser.translations.enable", false);
      },
    };
  }
''',
    "AIFeature seam reverted to plain pref semantic")

rep("browser/components/sidebar/browser-sidebar.js",
    '''    this.registerPrefSidebar(
      "browser.ml.chat.enabled",
      "viewGenaiChatSidebar",
      {
        name: "aichat",
        elementId: "sidebar-switcher-genai-chat",
        url: "chrome://browser/content/genai/chat.html",
        keyId: "viewGenaiChatSidebarKb",
        menuId: "menu_genaiChatSidebar",
        menuL10nId: "menu-view-genai-chat",
        // Bug 1900915 to expose as conditional tool
        revampL10nId: "sidebar-menu-genai-chat-label",
        iconUrl: "chrome://global/skin/icons/highlights.svg",
        gleanClickEvent: Glean.sidebar.chatbotIconClick,
        toolContextMenuId: "aichat",
        permissions: true,
      }
    );

''',
    "",
    "aichat sidebar registration removed")

rep("browser/components/sidebar/browser-sidebar.js",
    '  viewGenaiChatSidebar: "aichat",\n',
    "",
    "toolsNameMap aichat entry removed")

rep("browser/components/sidebar/sidebar-customize.mjs",
    '  ["viewGenaiChatSidebar", "sidebar-menu-genai-chat-label"],\n',
    "",
    "customize l10n map aichat entry removed")

print("ALL PHASE-C4 EDITS OK")

import subprocess
r = subprocess.run(["grep", "-rn", "viewGenaiChatSidebar\\|TranslationsFeature",
                    FM + "browser", FM + "toolkit",
                    "--include=*.mjs", "--include=*.js"],
                   capture_output=True, text=True)
left = [l for l in r.stdout.splitlines()
        if "test" not in l and "TranslationsFeature.sys.mjs:" not in l
        and "@import" not in l and "typedef" not in l]
print("remaining refs (informational):")
print("\n".join(left[:6]) if left else "  NONE")
