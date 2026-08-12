#!/bin/bash
# Room-clearing patch verifier for 07.TOOLKIT
VAULT=/home/gorilla/Documents/FIREFOX.WORK/Firefox.Scripts.Vault.Docs/SafetyVault.Firefox/firefox-main
LIVE=/home/gorilla/firefox-main
DIR=/home/gorilla/Documents/FIREFOX.WORK/FIrefox.154.Work/patches/new.patches/07.TOOLKIT
WORK=$(mktemp -d)
cd "$DIR" || exit 1

for f in *.patch; do
  # skip zero-delta stub (no @@ hunk)
  if ! grep -q '^@@' "$f"; then
    echo "SKIP(no-hunk): $f"
    continue
  fi
  # extract target relpath from the FIRST +++ header
  plus=$(grep -m1 '^+++ ' "$f" | awk '{print $2}')
  rel=$(echo "$plus" | sed -e 's#^b/##' -e "s#^${LIVE}/##" -e 's#^a/##')
  vfile="$VAULT/$rel"
  lfile="$LIVE/$rel"
  vexist="V-ok"; lexist="L-ok"
  [ -f "$vfile" ] || vexist="V-MISSING"
  [ -f "$lfile" ] || lexist="L-MISSING"
  if [ "$vexist" != "V-ok" ] || [ "$lexist" != "L-ok" ]; then
    echo "PATHFAIL: $f -> $rel [$vexist $lexist]"
    continue
  fi
  # count +++/--- pairs to detect multi-file
  nfiles=$(grep -c '^+++ ' "$f")
  # stage vanilla copy
  tgt="$WORK/$(basename "$rel")"
  cp "$vfile" "$tgt"
  # apply patch to explicit file (ignore header path issues)
  out=$(patch --no-backup-if-mismatch -s "$tgt" < "$f" 2>&1)
  rc=$?
  if [ $rc -ne 0 ]; then
    echo "APPLYFAIL(rc=$rc,nfiles=$nfiles): $f -> $rel :: $out"
    continue
  fi
  if cmp -s "$tgt" "$lfile"; then
    echo "MATCH(nfiles=$nfiles): $f -> $rel"
  else
    d=$(cmp "$tgt" "$lfile" 2>&1)
    echo "MISMATCH(nfiles=$nfiles): $f -> $rel :: $d"
  fi
done
echo "WORKDIR=$WORK"
