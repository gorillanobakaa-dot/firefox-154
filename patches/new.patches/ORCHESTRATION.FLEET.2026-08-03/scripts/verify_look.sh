#!/usr/bin/env bash
# Room-clearing verification for 08.Look: vanilla + patch == live, byte-exact.
set -u
V=/home/gorilla/Documents/FIREFOX.WORK/Firefox.Scripts.Vault.Docs/SafetyVault.Firefox/firefox-main
L=/home/gorilla/firefox-main
DIR=/home/gorilla/Documents/FIREFOX.WORK/FIrefox.154.Work/patches/new.patches/08.Look
WORK=$(mktemp -d)
pass=0; fail=0; empty=0; vmiss=0; lmiss=0; other=0
FAILLOG=""
EMPTYLOG=""
for f in "$DIR"/*.patch; do
  base=$(basename "$f")
  # empty patch?
  if [ ! -s "$f" ]; then
    empty=$((empty+1)); EMPTYLOG+="EMPTY  $base"$'\n'; continue
  fi
  rel=$(grep -m1 '^+++ ' "$f" | sed 's/^+++ //; s/\t.*//')
  rel=${rel#b/}
  rel=${rel#/home/gorilla/firefox-main/}
  vfile="$V/$rel"
  lfile="$L/$rel"
  if [ ! -f "$vfile" ]; then vmiss=$((vmiss+1)); FAILLOG+="VMISS  $base  ($rel)"$'\n'; continue; fi
  if [ ! -f "$lfile" ]; then lmiss=$((lmiss+1)); FAILLOG+="LMISS  $base  ($rel)"$'\n'; continue; fi
  tgt="$WORK/target"
  cp "$vfile" "$tgt"
  # Apply patch to the explicit target file, ignoring header pathnames.
  if patch --silent -f "$tgt" < "$f" >/dev/null 2>&1; then
    if cmp -s "$tgt" "$lfile"; then
      pass=$((pass+1))
    else
      fail=$((fail+1)); FAILLOG+="MISMATCH  $base  ($rel)"$'\n'
    fi
  else
    other=$((other+1)); FAILLOG+="APPLYFAIL $base  ($rel)"$'\n'
  fi
  rm -f "$tgt" "$tgt".orig "$tgt".rej 2>/dev/null
done
echo "=== RESULTS ==="
echo "PASS (vanilla+patch==live, byte-exact): $pass"
echo "MISMATCH (applied but != live):         $fail"
echo "APPLYFAIL (patch did not apply clean):  $other"
echo "VANILLA-missing:                        $vmiss"
echo "LIVE-missing:                           $lmiss"
echo "EMPTY patch files (0 bytes):            $empty"
echo
echo "=== EMPTY LIST ==="
printf '%s' "$EMPTYLOG"
echo "=== FAIL/ANOMALY LIST ==="
printf '%s' "$FAILLOG"
rm -rf "$WORK"
