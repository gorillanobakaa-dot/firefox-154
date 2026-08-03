#!/usr/bin/env python3
"""Phase C2: retire genai.ftl (the build-blocker after the genai dir move).
browser/locales/jar.mn packaged preview/genai.ftl out of the moved dir; its
4 strings served only the genai page-assist sidebar, which lost its
implementation (chrome://browser/content/genai/pageAssist.html) with the
move. Remove the registration, the l10n map entry, and the jar line.
"""
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


rep("browser/components/sidebar/browser-sidebar.js",
    '  viewGenaiPageAssistSidebar: "aipageassist",\n',
    "",
    "toolsNameMap page-assist entry removed")

rep("browser/components/sidebar/browser-sidebar.js",
    '''    this.registerPrefSidebar(
      "browser.ml.pageAssist.enabled",
      "viewGenaiPageAssistSidebar",
      {
        name: "aipageassist",
        elementId: "sidebar-switcher-genai-page-assist",
        url: "chrome://browser/content/genai/pageAssist.html",
        menuId: "menu_genaiPageAssistSidebar",
        menuL10nId: "menu-view-genai-page-assist",
        revampL10nId: "sidebar-menu-genai-page-assist-label",
        iconUrl: "chrome://browser/skin/reader-mode.svg",
      }
    );

''',
    "",
    "page-assist sidebar registration removed (impl gone with genai)")

rep("browser/components/sidebar/sidebar-customize.mjs",
    '  ["viewGenaiPageAssistSidebar", "sidebar-menu-genai-page-assist-label"],\n',
    "",
    "customize l10n map entry removed")

rep("browser/locales/jar.mn",
    '  preview/genai.ftl                                (../components/genai/content/genai.ftl)\n',
    "",
    "genai.ftl packaging removed (source dir moved out of tree)")

print(f"ALL PHASE-C2 EDITS OK ({len(done)}):")
for d in done:
    print("  ", d)

# verify nothing else registers or references preview/genai.ftl
import subprocess
r = subprocess.run(
    ["grep", "-rn", "genai.ftl", FM + "browser", FM + "toolkit",
     "--include=*.mjs", "--include=*.js", "--include=*.jsm",
     "--include=jar.mn", "--include=*.list"],
    capture_output=True, text=True)
left = [l for l in r.stdout.splitlines() if "test" not in l]
print("\nremaining genai.ftl references (want NONE):")
print("\n".join(left) if left else "  NONE")

# --- run 2 addendum (applied separately after the survivor scan): ---
# rep("browser/components/sidebar/sidebar-main.mjs",
#     '        ["browser/sidebar.ftl", "preview/genai.ftl"],\n',
#     '        ["browser/sidebar.ftl"],\n',
#     "Localization list de-genai'd")

# --- run 3 addendum (root-cause of scattered fluent failures): browser.xhtml
# still LINKED preview/genai.ftl; one missing linked file degrades the whole
# document's bundle generation (window title, shortcuts, ReportBrokenSite ids
# all failed). Removed the <link rel="localization" href="preview/genai.ftl"/>
# line. Lesson: an FTL has FIVE anchors — jar.mn, Localization() lists, AND
# <link rel="localization"> in every consuming document.
