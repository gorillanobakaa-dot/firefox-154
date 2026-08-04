#!/usr/bin/env python3
"""apply_step2.py — apply CLASSIFICATION_2026-08-01 verdicts to config/firefox.js.

Actions: DROP/FABRICATED -> delete the pref line (55 expected). FIX -> rewrite to the
verified real name with a GORILLA FIX provenance marker (10 originals -> 9 targets;
max_width+max_height collapse into one max_fs). KEEP_LOCAL/REAL -> untouched.
Safety: timestamped backup first; a FIX whose target ALREADY exists in config becomes a
plain delete (intent already covered — never create a duplicate line); full log to
APPLY_LOG_STEP2.md; post-apply verification re-extracts and checks invariants.
Rider: removes the confirmed-inert media.ffmpeg.vaapi-drm-display.enabled line + fixes the
stale media.rdd-ffmpeg.vaapi.enabled comment in 10.OVERRIDES/NEW_FILES/user.js."""
import re, os, shutil, datetime

OUT = os.path.dirname(os.path.abspath(__file__))
WORK = "<repo>"
CONFIG = f"{WORK}/config/firefox.js"
UJS = f"{WORK}/patches/new.patches/10.OVERRIDES/NEW_FILES/user.js"
STAMP = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

# authored value surgery for FIX rows (old -> forced new value + reason); others copy value
VALX = {
  "identity.fxaccounts.telemetry.clientAssertionJwt":
      ("false", 'type surgery: old value "" on a wrong-name pref; real pref is boolean; hardening intent = disable'),
}
MAXFS_PAIR = {"media.navigator.video.max_width", "media.navigator.video.max_height"}
MAXFS_LINE = 'pref("media.navigator.video.max_fs", 8160); // GORILLA FIX 2026-08-01: replaces invented max_width/max_height — real cap is macroblocks: 1920x1080px = 120x68 = 8160'

# ── load classification ──────────────────────────────────────────────────────
drops, fixes = set(), {}
for i, line in enumerate(open(f"{OUT}/classification.tsv")):
    if i == 0: continue
    pref, verdict, target, conf, val = (line.rstrip("\n").split("\t") + [""])[:5]
    if verdict in ("DROP", "FABRICATED"): drops.add(pref)
    elif verdict == "FIX": fixes[pref] = target
in_config = set(open(f"{OUT}/all_prefs.txt").read().split())

# ── backups ──────────────────────────────────────────────────────────────────
shutil.copy2(CONFIG, f"{OUT}/firefox.js.pre-step2.{STAMP}.bak")
shutil.copy2(UJS, f"{OUT}/overrides-user.js.pre-step2.{STAMP}.bak")

# ── apply to config/firefox.js ───────────────────────────────────────────────
src = open(CONFIG, encoding="utf-8").read().split("\n")
out, dropped, renamed, covered = [], [], [], []
maxfs_done = False
for line in src:
    m = re.match(r'(\s*)(?:sticky_)?pref\(\s*"([^"]+)"\s*,\s*(.+?)\)\s*;', line)
    if not m: out.append(line); continue
    ind, key, val = m.groups()
    if key in drops:
        dropped.append((key, val.strip())); continue
    if key in MAXFS_PAIR:
        if not maxfs_done:
            maxfs_done = True
            if "media.navigator.video.max_fs" in in_config:
                covered.append((key, "media.navigator.video.max_fs already in config"))
            else:
                out.append(ind + MAXFS_LINE)
        renamed.append((key, "media.navigator.video.max_fs", "8160 (macroblocks)"))
        continue
    if key in fixes:
        tgt = fixes[key]
        if tgt in in_config:
            covered.append((key, f"{tgt} already in config — old line deleted only")); continue
        if key in VALX:
            nv, why = VALX[key]
        else:
            nv, why = val.strip(), "value carried over"
        out.append(f'{ind}pref("{tgt}", {nv}); // GORILLA FIX 2026-08-01: renamed from {key} ({why})')
        renamed.append((key, tgt, nv)); continue
    out.append(line)
open(CONFIG, "w", encoding="utf-8").write("\n".join(out))

# ── rider: 10.OVERRIDES user.js ──────────────────────────────────────────────
u = open(UJS, encoding="utf-8").read()
rider = []
inert = 'user_pref("media.ffmpeg.vaapi-drm-display.enabled", true);\n'
if inert in u:
    u = u.replace(inert, ""); rider.append("removed inert media.ffmpeg.vaapi-drm-display.enabled line (absent from build, 3-channel check)")
if "(media.rdd-ffmpeg.vaapi.enabled)" in u:
    u = u.replace("(media.rdd-ffmpeg.vaapi.enabled)", "(media.rdd-ffmpeg.enabled)")
    rider.append("fixed stale comment: media.rdd-ffmpeg.vaapi.enabled (fabricated) -> media.rdd-ffmpeg.enabled (real)")
open(UJS, "w", encoding="utf-8").write(u)

# ── verify ───────────────────────────────────────────────────────────────────
new = open(CONFIG, encoding="utf-8").read()
newprefs = re.findall(r'^\s*(?:sticky_)?pref\(\s*"([^"]+)"', new, re.M)
newset, dupes = set(), sorted({p for p in newprefs if newprefs.count(p) > 1})
leftovers = sorted(drops & set(newprefs))
tgt_missing = sorted({t for t in fixes.values() if t not in newprefs})
ok = not leftovers and not tgt_missing and not dupes
exp = 1613 - len(dropped) - len(renamed) + (1 if maxfs_done and not any("max_fs already" in c for _, c in covered) else 0) + len([r for r in renamed if r[1] != "media.navigator.video.max_fs"]) - len([k for k, _ in covered if k not in MAXFS_PAIR])

# ── log ──────────────────────────────────────────────────────────────────────
L = [f"# APPLY LOG — step 2 ({STAMP})",
     f"Backups: firefox.js.pre-step2.{STAMP}.bak · overrides-user.js.pre-step2.{STAMP}.bak",
     f"\n## Deleted ({len(dropped)}) — DROP+FABRICATED"]
L += [f"- `{k}` (was {v})" for k, v in dropped]
L += [f"\n## Renamed ({len(renamed)})"] + [f"- `{a}` -> `{b}` = {c}" for a, b, c in renamed]
L += [f"\n## Covered-by-existing ({len(covered)}) — old line deleted, target already present"] + [f"- `{a}`: {b}" for a, b in covered]
L += ["\n## Rider (10.OVERRIDES/NEW_FILES/user.js)"] + [f"- {r}" for r in rider]
L += [f"\n## Verification", f"- pref count: 1613 -> {len(set(newprefs))} unique ({len(newprefs)} lines)",
     f"- dropped prefs still present: {leftovers or 'NONE'}",
     f"- fix targets missing: {tgt_missing or 'NONE'}",
     f"- duplicate pref lines: {dupes or 'NONE'}",
     f"- **INVARIANTS {'PASS' if ok else 'FAIL'}**",
     "\nStep-3 value-audit flags carried forward: min-parallelism=20, scissored-cache-clears=true,",
     "gc_high_frequency_large_heap_growth=128 (semantics vs defaults unverified); Merino URL",
     "neutering; quicksuggest.online.enabled sticky; 10 live nimbus.* values."]
open(f"{OUT}/APPLY_LOG_STEP2.md", "w").write("\n".join(L) + "\n")
print(f"deleted={len(dropped)} renamed={len(renamed)} covered={len(covered)} rider={len(rider)}")
print(f"unique prefs now: {len(set(newprefs))} (lines {len(newprefs)}); INVARIANTS {'PASS' if ok else 'FAIL'}")
if not ok: print("LEFTOVERS:", leftovers, "MISSING:", tgt_missing, "DUPES:", dupes)
