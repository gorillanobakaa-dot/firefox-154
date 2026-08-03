#!/usr/bin/env python3
"""NOT AI-related — nightly customize-in-a-tab bug (2026-08-03): the window's
toolbox palette (a <template>.content DocumentFragment since the recent
refactor) goes null between customize entry and Restore Defaults / window
unload; upstream tip carries the identical unguarded code. Two crash sites:
CustomizableUI.getUnusedWidgets (killed reset -> stuck transition -> Done
button dead) and the XUL widget wrapper at unload. Fix: self-heal by
re-grabbing the palette from the BrowserToolbarPalette template (which
provably stays in the document), with a console breadcrumb; plus an optional
chain at the wrapper site."""
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

rep("browser/components/customizableui/CustomizableUI.sys.mjs",
    '''  getUnusedWidgets(aWindowPalette) {
    let window = aWindowPalette.documentGlobal;
''',
    '''  getUnusedWidgets(aWindowPalette) {
    // GORILLA OVERRIDE (suspected nightly customize-tab bug): the palette
    // fragment can go null mid-session; self-heal from the template rather
    // than crashing reset/populatePalette (which left customize mode stuck).
    if (!aWindowPalette) {
      let win = Services.wm.getMostRecentBrowserWindow();
      aWindowPalette = win?.document.getElementById(
        "BrowserToolbarPalette"
      )?.content;
      if (win?.gNavToolbox && aWindowPalette) {
        win.gNavToolbox.palette = aWindowPalette;
        console.warn("CustomizableUI: window palette was null — re-grabbed from template");
      }
      if (!aWindowPalette) {
        return [];
      }
    }
    let window = aWindowPalette.documentGlobal;
''',
    "getUnusedWidgets self-heals null palette")

rep("browser/components/customizableui/CustomizableUI.sys.mjs",
    '''      instance = aWindow.gNavToolbox.palette.getElementsByAttribute(
        "id",
        aWidgetId
      )[0];
''',
    '''      // GORILLA OVERRIDE: palette can be null (nightly customize-tab bug);
      // a missing instance is already handled by callers.
      instance = aWindow.gNavToolbox.palette?.getElementsByAttribute(
        "id",
        aWidgetId
      )[0];
''',
    "widget-wrapper site null-safe")

print("ALL PALETTE SELF-HEAL EDITS OK")
