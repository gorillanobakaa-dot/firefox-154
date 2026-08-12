#!/usr/bin/env python3
"""Assert-once surgical fix batch 2026-08-03 (ledger RUN 2 items #7,#9,#10,#12,#13)."""
import hashlib, subprocess, sys, os, tempfile, shutil, datetime

VAN="/home/gorilla/Documents/FIREFOX.WORK/Firefox.Scripts.Vault.Docs/SafetyVault.Firefox/firefox-main"
LIVE="/home/gorilla/firefox-main"
NP="/home/gorilla/Documents/FIREFOX.WORK/FIrefox.154.Work/patches/new.patches"
LOOK="/home/gorilla/Documents/FIREFOX.WORK/FIrefox.154.Work/patches/FIrefox.154.Look"

def sub1(path, old, new, label):
    s=open(path,encoding="utf-8").read()
    n=s.count(old)
    assert n==1, f"FATAL {label}: expected exactly 1 occurrence, found {n} in {path}"
    open(path,"w",encoding="utf-8").write(s.replace(old,new,1))
    print(f"  OK  {label}")

# ---- #12 menubar.ftl: restore the 5 accesskeys under branded labels ----
MB=f"{LIVE}/browser/locales/en-US/browser/menubar.ftl"
for ctx,key in [("menu-file-new-tab =\n    .label = New Gorilla Tab\n","T"),
                ("menu-file-new-window =\n    .label = New Gorilla Window\n","N"),
                ("menu-file-new-private-window =\n    .label = New Private Gorilla Window\n","W"),
                ("menu-file-save-page =\n    .label = Save Gorilla Page As…\n","A"),
                ("menu-file-print =\n    .label = Print Gorilla…\n","P")]:
    sub1(MB, ctx, ctx+f"    .accesskey = {key}\n", f"accesskey {key} ({ctx.splitlines()[0]})")

# ---- #13 browser.ftl: restore the eaten placeable ----
sub1(f"{LIVE}/browser/locales/en-US/browser/browser.ftl",
     "urlbar-result-search-with = Search with Gorilla\n",
     "urlbar-result-search-with = Search with { $engine }\n", "placeable $engine")

# ---- #7 global-shared.css: restore the [hidden] safety net (live + Look master) ----
HIDDEN_BLOCK = '''
/* GORILLA OVERRIDE: restore FF154's upstream hidden-element safety net (vanilla
   toolkit/themes/shared/global-shared.css:118) — anything carrying the `hidden`
   attribute must not render; `:where()` keeps it at zero specificity so a
   deliberate `!important` show-rule can still win. The pre-154 master template
   this file derives from predates the rule; found missing 2026-08-03. */
:where([hidden]) {
  display: none !important;
}
'''
ANCHOR='@namespace html url("http://www.w3.org/1999/xhtml");\n'
for p in [f"{LIVE}/toolkit/themes/shared/global-shared.css", f"{LOOK}/global-shared.css"]:
    sub1(p, ANCHOR, ANCHOR+HIDDEN_BLOCK, f"[hidden] rule -> {os.path.basename(os.path.dirname(p))}/global-shared.css")

# ---- #9 PDMFactory.cpp: correct the stale provenance comments ----
PDM=f"{LIVE}/dom/media/platforms/PDMFactory.cpp"
sub1(PDM,
 "// SYNCHRONIZED WITH PDMFactory_upstream.cpp - AgnosticDecoderModule removed\n// Last sync: 2026-06-22\n",
 "// GORILLA OVERRIDE: AgnosticDecoderModule excised (software-fallback ban — see\n"
 "// MEDIA_CODEC_LESSONS Bugs B/D). Vanilla reference = the vault tree; no\n"
 "// PDMFactory_upstream.cpp exists (stale comment corrected 2026-08-03).\n",
 "PDMFactory header comment")
sub1(PDM,
 '// #include "AgnosticDecoderModule.h"  // REMOVED: Module never instantiated (Phase 0 cleanup)\n',
 '// #include "AgnosticDecoderModule.h"  // REMOVED: all instantiation sites excised by this patch (software-fallback ban)\n',
 "PDMFactory include comment")

# ---- #10 VideoConduit.cpp: add the missing provenance marker ----
sub1(f"{LIVE}/dom/media/webrtc/libwebrtcglue/VideoConduit.cpp",
 "bool WebrtcVideoConduit::HasAv1() {\n  return !StaticPrefs::media_gorilla_hardware_only_mode();\n",
 "// GORILLA OVERRIDE: AV1 answered as unsupported in hardware-only mode — H.264-only\n"
 "// policy, no AV1 ASIC on Intel HD 4000 (MEDIA_CODEC_LESSONS 6-layer gate).\n"
 "bool WebrtcVideoConduit::HasAv1() {\n  return !StaticPrefs::media_gorilla_hardware_only_mode();\n",
 "VideoConduit marker")

# ---- regenerate the 4 affected patches + byte-exact verification ----
REGEN=[("01.MEDIA/dom_media_platforms_PDMFactory.cpp.patch","dom/media/platforms/PDMFactory.cpp"),
       ("01.MEDIA/dom_media_webrtc_libwebrtcglue_VideoConduit.cpp.patch","dom/media/webrtc/libwebrtcglue/VideoConduit.cpp"),
       ("08.Look/browser_locales_en-US_browser_menubar.ftl.patch","browser/locales/en-US/browser/menubar.ftl"),
       ("08.Look/browser_locales_en-US_browser_browser.ftl.patch","browser/locales/en-US/browser/browser.ftl")]
for patchrel, rel in REGEN:
    pf=f"{NP}/{patchrel}"
    assert os.path.isfile(pf), f"FATAL: missing patch {pf}"
    r=subprocess.run(["diff","-u","--label",f"a/{rel}","--label",f"b/{rel}",f"{VAN}/{rel}",f"{LIVE}/{rel}"],capture_output=True,text=True)
    assert r.returncode==1, f"FATAL: diff rc={r.returncode} for {rel}"
    open(pf,"w",encoding="utf-8").write(r.stdout)
    # verify: vanilla + patch == live, byte-exact
    with tempfile.TemporaryDirectory() as td:
        dst=os.path.join(td,rel); os.makedirs(os.path.dirname(dst),exist_ok=True)
        shutil.copy(f"{VAN}/{rel}",dst)
        a=subprocess.run(["patch","-s","-p1","-i",pf],cwd=td)
        assert a.returncode==0, f"FATAL: patch apply failed for {patchrel}"
        c=subprocess.run(["cmp","-s",dst,f"{LIVE}/{rel}"])
        assert c.returncode==0, f"FATAL: NOT byte-exact after patch: {rel}"
    print(f"  OK  regen+verify BYTE-EXACT {patchrel}")

# ---- THEME_FIX_LOG §36 (append-only mandate) ----
def sha(p): return hashlib.sha256(open(p,"rb").read()).hexdigest()
live_css=f"{LIVE}/toolkit/themes/shared/global-shared.css"; look_css=f"{LOOK}/global-shared.css"
entry=f"""
## 36. 2026-08-03 — global-shared.css: FF154 `[hidden]` safety net restored (live + master)

**What:** re-added vanilla FF154's `:where([hidden]) {{ display: none !important; }}` (vanilla
global-shared.css:118) after the `@namespace html` line, with a GORILLA OVERRIDE provenance
comment. The pre-154 master template this file derives from predates the rule, so deploying the
master had silently dropped the chrome-side hidden-element enforcement (§17's bug class).
**Where:** live `toolkit/themes/shared/global-shared.css` + master `FIrefox.154.Look/global-shared.css`
(both edited identically; no per-file patch exists for this file — master copy IS the source).
**Checks:** vanilla rule text verbatim; zero specificity preserved (`:where()`); rebuild owed to
bake into omni.ja. Found by tree-poison-screen RUN 2 (THEME/CSS minion), supervisor-verified
(vanilla=1 hit, live=0 hits pre-fix).
**sha256 after:** live {sha(live_css)}
              master {sha(look_css)}
"""
with open(f"{LOOK}/notes/THEME_FIX_LOG_2026-07-31.md","a",encoding="utf-8") as fh: fh.write(entry)
print("  OK  THEME_FIX_LOG §36 appended")

# ---- ledger: mark items FIXED ----
with open(f"{NP}/ORCHESTRATION.FLEET.2026-08-03/FLEET_FINDINGS_LEDGER_2026-08-03.md","a",encoding="utf-8") as fh:
    fh.write(f"""
## RUN 2 fix batch — APPLIED {datetime.date.today()} (owner-approved)
Items **#7 #9 #10 #12 #13 FIXED** via assert-once script (scratchpad/fix_batch.py):
menubar.ftl 5 accesskeys restored under branded labels; browser.ftl `{{ $engine }}` placeable
restored; global-shared.css `[hidden]` net restored live+master (+THEME_FIX_LOG §36, sha256s
there); PDMFactory.cpp stale upstream-file comment corrected; VideoConduit.cpp HasAv1 gate got
its GORILLA marker. Patches regenerated + verified vanilla+patch==live BYTE-EXACT: PDMFactory,
VideoConduit, menubar.ftl, browser.ftl. Still parked: #8 orphan tokens, #11 AudioContext promise
delta, GPU-pref reconciliation, dead-patch deletion, security-string wording (owner). REBUILD OWED.
""")
print("  OK  ledger updated")
print("ALL FIXES APPLIED AND VERIFIED")
