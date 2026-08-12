#!/bin/bash
PATCHDIR="/home/gorilla/Documents/FIREFOX.WORK/FIrefox.154.Work/patches/new.patches/01.MEDIA"
VAULT="/home/gorilla/Documents/FIREFOX.WORK/Firefox.Scripts.Vault.Docs/SafetyVault.Firefox/firefox-main"
LIVE="/home/gorilla/firefox-main"
WORK="/tmp/claude-1000/-home-gorilla-Documents-FIREFOX-WORK-FIrefox-154-Work--claude-worktrees-bold-lamport-02c654/ad78c415-8eb2-43bc-9218-8109ac3e8373/scratchpad/work"
rm -rf "$WORK"; mkdir -p "$WORK"
printf "%-52s %-8s %-8s %-8s %s\n" "PATCH" "VAULT" "LIVE" "APPLY" "RESULT"
for p in "$PATCHDIR"/*.patch; do
  bn=$(basename "$p")
  tgt=$(grep -m1 '^+++ ' "$p" | sed -E 's|^\+\+\+ b/||; s/[[:space:]].*$//')
  vfile="$VAULT/$tgt"
  lfile="$LIVE/$tgt"
  vok="no"; lok="no"; applyres="-"; result="-"
  [ -f "$vfile" ] && vok="yes"
  [ -f "$lfile" ] && lok="yes"
  if [ "$vok" = "yes" ]; then
    mkdir -p "$WORK/$(dirname "$tgt")"
    cp "$vfile" "$WORK/$tgt"
    if ( cd "$WORK" && patch -p1 --no-backup-if-mismatch -s < "$p" ) 2>/tmp/perr; then
      applyres="OK"
      if [ "$lok" = "yes" ]; then
        if cmp -s "$WORK/$tgt" "$lfile"; then result="MATCH"; else result="DIFFER"; fi
      else result="NOLIVE"; fi
    else
      applyres="FAIL"; result="$(head -1 /tmp/perr | cut -c1-30)"
    fi
  else
    result="NOVAULT"
  fi
  printf "%-52s %-8s %-8s %-8s %s\n" "$bn" "$vok" "$lok" "$applyres" "$result"
done
