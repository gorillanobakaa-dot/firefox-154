#!/usr/bin/env python3
"""step3_values.py — value pass on config/firefox.js.

(1) MERINO egress: empty the endpoint URLs (unittest-sanctioned kill method) + GORILLA marker.
(2) REDUNDANT_DEFAULT: compare every pref against the COMPILED default in objdir greprefs.js.
    Baseline = greprefs ALONE, because config/firefox.js will REPLACE the app firefox.js:
    dropping a line whose value == greprefs value falls back to the IDENTICAL value (safe);
    a line differing from greprefs is a real override (KEEP). Not-in-greprefs = app pref with
    no compiled default = KEEP (our line is authoritative).
    Auto-drop only SAFE noise: redundant AND not sticky/locked AND not GORILLA-marked AND not
    in a sensitive namespace (privacy/security/telemetry/crash/update/experiment/AI). Redundant
    lines in sensitive namespaces are KEPT and FLAGGED as lock-candidates for step 4.
Backup + full log + report + post-verify. Nothing baked (config feeds nothing at runtime)."""
import re, os, shutil, datetime, collections

OUT = os.path.dirname(os.path.abspath(__file__))
WORK = "/home/gorilla/Documents/FIREFOX.WORK/FIrefox.154.Work"
CONFIG = f"{WORK}/config/firefox.js"
GREPREFS = "/home/gorilla/firefox-main/obj-x86_64-pc-linux-gnu/dist/bin/greprefs.js"
STAMP = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

MERINO_EMPTY = {
    "browser.urlbar.merino.endpointURL", "browser.urlbar.merino.ohttpConfigURL",
    "browser.urlbar.merino.ohttpRelayURL", "browser.urlbar.merino.weather.reportEndpointURL",
    "browser.urlbar.merino.weather.hourlyEndpointURL",
    "browser.newtabpage.activity-stream.discoverystream.merino-provider.endpoint",
}
SENSITIVE = ("privacy.", "security.", "datareporting.", "toolkit.telemetry", "app.update",
             "app.shield", "app.normandy", "browser.crashReports", "breakpad.",
             "browser.contentblocking", "network.trr", "dom.security", "nimbus",
             "browser.ml.", "extensions.pocket", "browser.pocket", "dom.private-attribution",
             "browser.safebrowsing", "identity.fxaccounts.telemetry")

def norm(v):  # strip sticky/locked attribute + whitespace for value comparison
    return re.sub(r'\s*,\s*(sticky|locked)\s*$', '', v).strip()

# ── compiled defaults from greprefs.js ───────────────────────────────────────
defaults = {}
for m in re.finditer(r'^\s*pref\(\s*"([^"]+)"\s*,\s*(.+?)\)\s*;', open(GREPREFS).read(), re.M):
    defaults[m.group(1)] = m.group(2).strip()

shutil.copy2(CONFIG, f"{OUT}/firefox.js.pre-step3.{STAMP}.bak")
lines = open(CONFIG, encoding="utf-8").read().split("\n")
PAT = re.compile(r'^(\s*)((?:sticky_)?pref)\(\s*"([^"]+)"\s*,\s*(.+?)\)\s*;(.*)$')

out, merino, redundant_drop, redundant_keep, real_override, no_default = [], [], [], [], [], []
for line in lines:
    m = PAT.match(line)
    if not m:
        out.append(line); continue
    ind, fn, key, val, tail = m.groups()
    # (1) merino egress neutering
    if key in MERINO_EMPTY and norm(val) not in ('""', "''"):
        out.append(f'{ind}pref("{key}", ""); // GORILLA 2026-08-01: Merino endpoint emptied (no-egress; unittest-required/user.js precedent)')
        merino.append((key, norm(val))); continue
    is_pinned = ("sticky" in val or "locked" in val or "GORILLA" in tail or "GORILLA" in line)
    if key not in defaults:
        no_default.append(key); out.append(line); continue
    if norm(val) == defaults[key]:
        sensitive = key.startswith(SENSITIVE)
        if is_pinned or sensitive:
            redundant_keep.append((key, norm(val), "pinned" if is_pinned else "sensitive-ns"))
            out.append(line)
        else:
            redundant_drop.append((key, norm(val))); continue
    else:
        real_override.append((key, norm(val), defaults[key])); out.append(line)

open(CONFIG, "w", encoding="utf-8").write("\n".join(out))

# ── verify ───────────────────────────────────────────────────────────────────
t = open(CONFIG).read()
names = re.findall(r'^\s*(?:sticky_)?pref\(\s*"([^"]+)"', t, re.M)
dupes = sorted({n for n in names if names.count(n) > 1})
merino_bad = [k for k in MERINO_EMPTY if re.search(r'pref\("'+re.escape(k)+r'",\s*"[^"]', t)]
ok = not dupes and not merino_bad

# ── report + log ─────────────────────────────────────────────────────────────
rep = [f"# Step 3 — value pass report ({STAMP})",
       f"Baseline: objdir greprefs.js ({len(defaults)} compiled defaults). config feeds nothing at runtime.",
       f"\n| bucket | count |", "|---|---|",
       f"| Merino endpoints emptied | {len(merino)} |",
       f"| REDUNDANT_DEFAULT dropped (safe noise) | {len(redundant_drop)} |",
       f"| REDUNDANT_DEFAULT kept+flagged (pinned/sensitive) | {len(redundant_keep)} |",
       f"| real overrides (differ from compiled default) | {len(real_override)} |",
       f"| app prefs w/ no compiled default (kept) | {len(no_default)} |",
       f"| **prefs after step 3** | **{len(set(names))}** |",
       f"\n## Merino emptied", *[f"- `{k}` (was {v})" for k, v in merino],
       f"\n## Redundant defaults DROPPED ({len(redundant_drop)}) — value==compiled default, non-sensitive, unpinned",
       *[f"- `{k}` = {v}" for k, v in sorted(redundant_drop)],
       f"\n## Redundant defaults KEPT + flagged for step-4 lock ({len(redundant_keep)})",
       *[f"- `{k}` = {v}  [{why}]" for k, v, why in sorted(redundant_keep)],
       f"\n## Verification",
       f"- duplicate pref lines: {dupes or 'NONE'}",
       f"- merino URLs still non-empty: {merino_bad or 'NONE'}",
       f"- **INVARIANTS {'PASS' if ok else 'FAIL'}**"]
open(f"{OUT}/STEP3_REPORT.md", "w").write("\n".join(rep) + "\n")

print(f"merino_emptied={len(merino)} redundant_dropped={len(redundant_drop)} "
      f"redundant_kept={len(redundant_keep)} real_overrides={len(real_override)} no_default={len(no_default)}")
print(f"prefs now: {len(set(names))} unique / {len(names)} lines; INVARIANTS {'PASS' if ok else 'FAIL'}")
if not ok: print("dupes:", dupes, "merino_bad:", merino_bad)
# sensitive-namespace breakdown of the kept-redundant, for the step-4 lock decision
byns = collections.Counter(k.split(".")[0]+"."+(k.split(".")[1] if "."in k[len(k.split(".")[0])+1:] else "") for k,_,_ in redundant_keep)
print("kept-redundant top namespaces:", dict(byns.most_common(8)))
