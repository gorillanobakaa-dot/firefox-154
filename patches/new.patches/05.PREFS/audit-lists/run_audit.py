#!/usr/bin/env python3
"""run_audit.py — durable re-run of the config/firefox.js pref audit vs mozilla-central.

Regenerates the full lists the 2026-08-01 audit lost to scratchpad:
  all_prefs.txt     every unique pref extracted from config/firefox.js
  real.txt          confirmed in current mozilla-central (BATCH enumerate | RESCUED per-pref text:)
  absent.txt        NOT in current mozilla-central (annotated: in-local-build? nearest real names?)
  audit_summary.md  counts + method + timestamp

Method per PREF_AUDIT_FINAL_2026-08-01.md: searchfox is the authority; batch
namespace-enumerate first (fast), then per-pref `text:` rescue for EVERY miss
(the batch pass false-negatives on big/capped namespaces — it missed 18 last run).
GitHub count NOT used (anti-signal). Politeness: inherits searchfox_tools 24h cache
+ 1s live throttle; cache hits are instant and hit no network."""
import sys, re, os, datetime
TOOLS = "/home/gorilla/Documents/Scripts.For.Work/searchfox-tools"
sys.path.insert(0, TOOLS)
import searchfox_tools as sf
import sfpref

CONFIG = "/home/gorilla/Documents/FIREFOX.WORK/FIrefox.154.Work/config/firefox.js"
OUTDIR = os.path.dirname(os.path.abspath(__file__))
GREPREFS = "/home/gorilla/firefox-main/obj-x86_64-pc-linux-gnu/dist/bin/greprefs.js"
LOCAL_FFJS = "/home/gorilla/firefox-main/browser/app/profile/firefox.js"

def log(msg):
    print(f"[{datetime.datetime.now():%H:%M:%S}] {msg}", flush=True)

# ── 1. extract every unique pref from the blueprint ──────────────────────────
text = open(CONFIG, encoding="utf-8", errors="replace").read()
prefs, seen = [], set()
for m in re.finditer(r'^\s*(?:sticky_)?pref\(\s*"([^"]+)"', text, re.M):
    k = m.group(1)
    if k not in seen:
        seen.add(k); prefs.append(k)
log(f"extracted {len(prefs)} unique prefs from {CONFIG}")
open(f"{OUTDIR}/all_prefs.txt", "w").write("\n".join(prefs) + "\n")

# ── 2. batch namespace enumeration (reuses sfpref query strings → cache-warm) ─
def ns_of(p): return ".".join(p.split(".")[:2])
namespaces = sorted({ns_of(p) for p in prefs})
log(f"{len(namespaces)} namespaces to enumerate")
ns_real = {}
for i, ns in enumerate(namespaces, 1):
    try:
        ns_real[ns] = set(sfpref.enumerate_ns(ns)[2])
    except Exception as e:
        ns_real[ns] = set(); log(f"  ! enumerate failed for {ns}: {e}")
    if i % 25 == 0: log(f"  ...{i}/{len(namespaces)} namespaces")

real_batch = [p for p in prefs if p in ns_real[ns_of(p)]]
misses = [p for p in prefs if p not in ns_real[ns_of(p)]]
log(f"batch pass: REAL={len(real_batch)}  misses={len(misses)} -> per-pref text: rescue")

# ── 3. per-pref text: rescue on every miss ───────────────────────────────────
rescued, absent = [], []
for i, p in enumerate(misses, 1):
    try:
        hits = sf.search(f"text:{p}", use_cache=True, limit=50)
    except Exception as e:
        hits = []; log(f"  ! text: query failed for {p}: {e}")
    if hits:
        rescued.append((p, f"{hits[0][0]}:{hits[0][1]}"))
    else:
        absent.append(p)
    if i % 20 == 0: log(f"  ...{i}/{len(misses)} rescue checks")

# ── 4. annotate the absent: in OUR local build? nearest real name? ──────────
grep_txt = open(GREPREFS, encoding="utf-8", errors="replace").read() if os.path.exists(GREPREFS) else ""
ffjs_txt = open(LOCAL_FFJS, encoding="utf-8", errors="replace").read()
if not grep_txt:
    log(f"  ! {GREPREFS} missing — in-build check limited to browser/app/profile/firefox.js")

def nearest(p):
    pool = ns_real.get(ns_of(p), set())
    last, parent = p.split(".")[-1], p.rsplit(".", 1)[0]
    return [k for k in sorted(pool) if k.split(".")[-1] == last or k.rsplit(".", 1)[0] == parent][:3]

with open(f"{OUTDIR}/real.txt", "w") as f:
    for p in real_batch:   f.write(f"{p}\tBATCH\n")
    for p, ex in rescued:  f.write(f"{p}\tRESCUED\t{ex}\n")

inbuild = []
with open(f"{OUTDIR}/absent.txt", "w") as f:
    f.write("# prefs from config/firefox.js NOT found in current mozilla-central (searchfox)\n")
    f.write("# columns: pref <TAB> IN_LOCAL_BUILD|- <TAB> nearest-real-names|-\n")
    for p in absent:
        q = f'"{p}"'
        ib = "IN_LOCAL_BUILD" if (q in grep_txt or q in ffjs_txt) else "-"
        if ib != "-": inbuild.append(p)
        nr = nearest(p)
        f.write(f"{p}\t{ib}\t{';'.join(nr) if nr else '-'}\n")

total_real = len(real_batch) + len(rescued)
open(f"{OUTDIR}/audit_summary.md", "w").write(f"""# Audit lists — regenerated {datetime.date.today()} (durable re-run)
Source: config/firefox.js ({len(prefs)} unique prefs) vs searchfox firefox-main (Nightly).
Method: batch namespace-enumerate ({len(namespaces)} namespaces) + per-pref `text:` rescue on {len(misses)} misses.
Authority: searchfox. GitHub count NOT used (anti-signal — see PREF_AUDIT_FINAL_2026-08-01.md).

| bucket | count |
|---|---|
| REAL (batch enumerate) | {len(real_batch)} |
| REAL (rescued by per-pref text:) | {len(rescued)} |
| **REAL total** | **{total_real}** |
| ABSENT from mozilla-central | {len(absent)} |
| ...of which present in OUR local build | {len(inbuild)} |

Files: all_prefs.txt · real.txt · absent.txt (annotated: in-local-build + nearest real names).
Prior (lost, scratchpad) run for comparison: 1504 batch + 18 rescued = 1522 REAL, ~82 absent, 9 in-build.
Next: classify absent.txt into DROP / FIX(rename) / FABRICATED, apply to config/firefox.js.
""")
log(f"DONE: REAL={total_real} ({len(real_batch)} batch + {len(rescued)} rescued)  ABSENT={len(absent)} (in-local-build: {len(inbuild)})")
