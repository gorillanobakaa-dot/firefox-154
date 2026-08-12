#!/bin/bash
VAULT=/home/gorilla/Documents/FIREFOX.WORK/Firefox.Scripts.Vault.Docs/SafetyVault.Firefox/firefox-main
LIVE=/home/gorilla/firefox-main
DIR=/home/gorilla/Documents/FIREFOX.WORK/FIrefox.154.Work/patches/new.patches/07.TOOLKIT
WORK=$(mktemp -d)
declare -A M=(
  [browser_base_content_nsContextMenu.sys.mjs.patch]=browser/base/content/nsContextMenu.sys.mjs
  [browser_components_urlbar_QuickSuggest.sys.mjs.patch]=browser/components/urlbar/QuickSuggest.sys.mjs
  [toolkit_components_translations_actors_TranslationsParent.sys.mjs.patch]=toolkit/components/translations/actors/TranslationsParent.sys.mjs
  [toolkit_mozapps_extensions_LightweightThemeManager.sys.mjs.patch]=toolkit/mozapps/extensions/LightweightThemeManager.sys.mjs
)
for f in "${!M[@]}"; do
  rel="${M[$f]}"
  tgt="$WORK/$(basename "$rel")"
  cp "$VAULT/$rel" "$tgt"
  patch --no-backup-if-mismatch -s "$tgt" < "$DIR/$f" 2>&1
  echo "############### $f"
  echo "--- diff: (vanilla+patch)  vs  LIVE  [< = patched-result, > = live] ---"
  diff "$tgt" "$LIVE/$rel"
  echo "=== reject/fuzz check: also verbose apply ==="
  cp "$VAULT/$rel" "$tgt.2"
  patch --no-backup-if-mismatch "$tgt.2" < "$DIR/$f" 2>&1 | grep -iE 'fuzz|hunk|offset|FAILED|succeed' | head
  echo
done
