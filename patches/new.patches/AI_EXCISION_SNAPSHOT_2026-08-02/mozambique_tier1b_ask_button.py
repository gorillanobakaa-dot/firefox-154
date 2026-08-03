#!/usr/bin/env python3
"""Tier-1b: remove the smartwindow-ask-button toolbar markup and its two
click-routing selector entries (missed by tier 1, caught by the leftover
sweep). Companion to mozambique_tier1_seam_removal.py."""
import sys

FM = "/home/gorilla/firefox-main/"


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
    print(f"OK  {path} :: {label}")


rep("browser/base/content/navigator-toolbox.inc.xhtml",
    '''    <toolbaritem id="smartwindow-ask-button"
                 class="chromeclass-toolbar-additional"
                 hidden="true"
                 overflows="false"
                 removable="false">
      <toolbarbutton id="smartwindow-ask-button-inner"
                      class="toolbarbutton-1"
                      aria-expanded="false"
                      data-l10n-id="smartwindow-ask-button">
      </toolbarbutton>
    </toolbaritem>

''',
    "",
    "ask-button toolbar markup removed")

rep("browser/base/content/navigator-toolbox.js",
    '''        #split-view-button,
        #smartwindow-ask-button
        `''',
    '''        #split-view-button
        `''',
    "click-routing selector list cleaned")

rep("browser/base/content/navigator-toolbox.js",
    '''        #split-view-button,
        #smartwindow-ask-button
      `''',
    '''        #split-view-button
      `''',
    "keynav selector list cleaned")

print("ALL TIER-1B EDITS OK")
