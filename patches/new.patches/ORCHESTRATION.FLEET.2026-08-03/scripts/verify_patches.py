#!/usr/bin/env python3
"""verify_patches.py — tamper/drift check for all patch groups.
Per patch: parse target path; confirm ADDED (+) lines are present in the LIVE tree
(intent actually applied), and REMOVED (-) lines are present in VANILLA (patch was
authored against the real baseline). Flags divergence = tampering / drift / never-applied."""
import os, re, sys, glob

BASE="/home/gorilla/Documents/FIREFOX.WORK/FIrefox.154.Work/patches/new.patches"
VAN="/home/gorilla/Documents/FIREFOX.WORK/Firefox.Scripts.Vault.Docs/SafetyVault.Firefox/firefox-main"
LIVE="/home/gorilla/firefox-main"
GROUPS=sys.argv[1:] or ["01.MEDIA","02.GPU","03.NETWORKING","04.PERFORMANCE","05.PREFS",
 "06.QUOTA","07.TOOLKIT","08.Look","09.REMOTE","12.MOZAMBIQUE.DRILL","13.TELEMETRY.KILL"]

def _rel(p):
    for pre in (LIVE+"/", VAN+"/"):
        if p.startswith(pre): return p[len(pre):]
    m=re.match(r'^[ab]/(.+)$', p)
    if m: return m.group(1)
    # absolute path containing firefox-main/
    if "firefox-main/" in p: return p.split("firefox-main/",1)[1]
    return p if not p.startswith("/") else None

def target_path(patch_lines, patchfile):
    for pref in ("+++ ","--- "):
        for l in patch_lines:
            if l.startswith(pref):
                raw=l[len(pref):].split("\t")[0].strip()
                if raw in ("/dev/null",""): continue
                r=_rel(raw)
                if r: return r
    return None

def norm(s): return re.sub(r'\s+',' ',s.strip())

def read(path):
    try: return open(path,encoding="utf-8",errors="replace").read()
    except: return None

results=[]
for g in GROUPS:
    for pf in sorted(glob.glob(f"{BASE}/{g}/**/*.patch",recursive=True)):
        pl=open(pf,encoding="utf-8",errors="replace").read().split("\n")
        tgt=target_path(pl,pf)
        rel=os.path.relpath(pf,BASE)
        if not tgt:
            results.append((g,rel,"NO_TARGET","could not parse target path",0,0)); continue
        live_txt=read(f"{LIVE}/{tgt}"); van_txt=read(f"{VAN}/{tgt}")
        if live_txt is None:
            results.append((g,rel,"LIVE_MISSING",tgt,0,0)); continue
        live_n=norm(live_txt); van_n=norm(van_txt) if van_txt else ""
        # collect + and - content lines (skip +++/--- headers and empty)
        adds=[l[1:] for l in pl if l.startswith("+") and not l.startswith("+++")]
        rems=[l[1:] for l in pl if l.startswith("-") and not l.startswith("---")]
        adds=[a for a in adds if a.strip()]
        rems=[r for r in rems if r.strip()]
        add_present=sum(1 for a in adds if norm(a) in live_n)
        add_total=len(adds)
        rem_in_van=sum(1 for r in rems if van_txt and norm(r) in van_n)
        rem_total=len(rems)
        # verdict
        add_ratio=add_present/add_total if add_total else 1.0
        if add_total==0 and rem_total==0:
            v="EMPTY"
        elif add_ratio>=0.90:
            v="APPLIED"
        elif add_ratio>=0.5:
            v="PARTIAL"
        else:
            v="NOT_APPLIED"
        results.append((g,rel,v,tgt,f"{add_present}/{add_total}",f"{rem_in_van}/{rem_total}"))

# report
from collections import Counter
c=Counter(r[2] for r in results)
print("="*90)
print(f"PATCH VERIFICATION — {len(results)} patches across {len(GROUPS)} groups")
print(f"verdicts: {dict(c)}")
print("="*90)
# show everything that is NOT cleanly APPLIED first (the signal)
print("\n### FLAGGED (not cleanly applied — inspect) ###")
flagged=[r for r in results if r[2] not in ("APPLIED",)]
if not flagged: print("   none — all patches' + lines present in live tree")
for g,rel,v,tgt,a,rm in flagged:
    print(f"  [{v:12}] {rel}")
    print(f"                 target={tgt}  +present={a}  -in_vanilla={rm}")
# per-group APPLIED summary
print("\n### per-group APPLIED counts ###")
for g in GROUPS:
    gr=[r for r in results if r[0]==g]
    ap=sum(1 for r in gr if r[2]=="APPLIED")
    print(f"  {g:22} {ap}/{len(gr)} applied")
