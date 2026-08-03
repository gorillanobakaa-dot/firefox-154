#!/usr/bin/env python3
"""classify_absent.py — triage the 88 ABSENT prefs into KEEP_LOCAL / FIX / DROP / FABRICATED.

MECHANICAL (computed): IN_LOCAL_BUILD flag (absent.txt), the value each pref carries in
config/firefox.js (the intent evidence), and verification of every proposed FIX target
against the live searchfox namespace pools (cache-warm; a FIX whose target is not found
is DEMOTED to DROP with a note — never applied on faith).
AUTHORED (judgment, reviewable row by row): the DROP-vs-FABRICATED provenance call and
the FIX target proposals. Anchors: PREF_AUDIT_FINAL_2026-08-01.md lists A (DROP),
B (FIX), C (FABRICATED). Confidence: HIGH = anchored there / well-known history;
MED = my judgment, no anchor. Anything not covered -> REVIEW, never silently guessed.

Outputs: CLASSIFICATION_2026-08-01.md (human review table) + classification.tsv (for
the step-2 apply script)."""
import sys, re, os, datetime
TOOLS = "/home/gorilla/Documents/Scripts.For.Work/searchfox-tools"
sys.path.insert(0, TOOLS)
import sfpref

OUTDIR = os.path.dirname(os.path.abspath(__file__))
CONFIG = "/home/gorilla/Documents/FIREFOX.WORK/FIrefox.154.Work/config/firefox.js"

# ── authored verdicts: pref -> (verdict, fix_target|None, confidence, note) ──
A = {
  # FIX — wrong name, proposed real successor (verified below before acceptance)
  "media.getusermedia.aec_enabled":   ("FIX","media.getusermedia.audio.processing.aec.enabled","HIGH","prior audit list B"),
  "media.getusermedia.agc_enabled":   ("FIX","media.getusermedia.audio.processing.agc.enabled","HIGH","prior audit list B"),
  "media.getusermedia.noise_enabled": ("FIX","media.getusermedia.audio.processing.noise.enabled","HIGH","prior audit list B"),
  "identity.fxaccounts.telemetry.clientAssertionJwt": ("FIX","identity.fxaccounts.telemetry.clientAssociationPing.enabled","HIGH","prior audit list B"),
  "network.http.pacing.requests.min-number-to-pace": ("FIX","network.http.pacing.requests.min-parallelism","MED","mangled form of the real pacing knob"),
  "media.navigator.video.max_width":  ("FIX","media.navigator.video.max_fs","MED","real cap is max_fs — UNIT DIFFERS (macroblocks, not px): value must be recomputed, not copied"),
  "media.navigator.video.max_height": ("FIX","media.navigator.video.max_fs","MED","same target as max_width — one real pref caps frame SIZE; do not copy px value"),
  "media.navigator.video.max_framerate": ("FIX","media.navigator.video.max_fr","MED","real cap is max_fr (fps)"),
  "gfx.webrender.scissored-cache-tiles.enabled": ("FIX","gfx.webrender.scissored-cache-clears.enabled","MED","name-mutation of the real scissored-cache pref; check value vs default before adopting"),
  "browser.lowMemoryResponseMB": ("FIX","browser.low_commit_space_threshold_mb","MED","invented name; real low-memory threshold pref"),
  "javascript.options.mem.gc_high_frequency_low_limit": ("FIX","javascript.options.mem.gc_high_frequency_low_limit_mb","MED","_mb-suffixed real name"),
  "javascript.options.mem.gc_high_frequency_heap_growth_max": ("FIX","javascript.options.mem.gc_high_frequency_large_heap_growth","MED","closest real GC growth knob; demote to DROP if absent"),
  # DROP — real once, removed upstream (line is dead everywhere for us)
  "network.predictor.enabled":          ("DROP",None,"HIGH","prior audit list A; the 1436-GitHub-refs poster child"),
  "network.predictor.enable-prefetch":  ("DROP",None,"HIGH","prior audit list A"),
  "network.preload":                    ("DROP",None,"HIGH","prior audit list A"),
  "dom.events.asyncClipboard.clipboardItem": ("DROP",None,"HIGH","prior audit list A; 2136 GitHub refs, removed"),
  "dom.events.asyncClipboard.readText": ("DROP",None,"HIGH","prior audit list A; API graduated, gate removed"),
  "dom.indexedDB.enabled":              ("DROP",None,"HIGH","prior audit list A; IndexedDB no longer disableable"),
  "dom.page_visibility.enabled":        ("DROP",None,"HIGH","prior audit list A"),
  "dom.wakelock.enabled":               ("DROP",None,"HIGH","prior audit list A"),
  "media.h264.enabled":                 ("DROP",None,"HIGH","prior audit list A; ancient OpenH264-era gate — H.264 policy lives in our compiled DecoderTraits patch"),
  "media.mp3.enabled":                  ("DROP",None,"HIGH","prior audit list A"),
  "media.libvpx.enabled":               ("DROP",None,"HIGH","prior audit list A; VP8/VP9 already blocked by compiled codec policy"),
  "media.ffvpx.enabled":                ("DROP",None,"HIGH","prior audit list A"),
  "network.websocket.enabled":          ("DROP",None,"HIGH","prior audit list A; WS no longer pref-gated"),
  "browser.pocket.enabled":             ("DROP",None,"HIGH","prior audit list A; real gate = extensions.pocket.enabled (KEEP_LOCAL)"),
  "browser.pocket.api":                 ("DROP",None,"HIGH","prior audit list A"),
  "browser.translations.panelShown":    ("DROP",None,"HIGH","prior audit list A"),
  "browser.tabs.firefox-view-next":     ("DROP",None,"HIGH","prior audit list A (older-form firefox-view pref)"),
  "network.http.pipelining.max-optimistic-requests": ("DROP",None,"HIGH","HTTP pipelining ripped out of browsers; LEGACY standard (RFC9112 s9.3.2)"),
  "browser.cache.offline.enable":       ("DROP",None,"HIGH","AppCache removed years ago; LEGACY"),
  "browser.cache.offline.insecure.enable": ("DROP",None,"HIGH","AppCache removed; LEGACY"),
  "gfx.layerscope.enabled":             ("DROP",None,"HIGH","LayerScope debug tool died with the old layers system"),
  "browser.shopping.experience2023.enabled": ("DROP",None,"MED","Fakespot shopping was real (FF119+), sunset upstream"),
  "browser.shopping.experience2023.autoOpen.enabled": ("DROP",None,"MED","same sunset"),
  "media.ffmpeg.vaapi-drm-display.enabled": ("DROP",None,"MED","was real, gone at tip AND from our build (3-channel check) — ALSO remove the inert line in 10.OVERRIDES/NEW_FILES/user.js"),
  "browser.newtabpage.activity-stream.feeds.telemetry": ("DROP",None,"MED","old activity-stream telemetry feed pref; telemetry gated elsewhere in our build"),
  "browser.newtabpage.activity-stream.telemetry.structuredIngestion.endpoint": ("DROP",None,"MED","companion of the above"),
  "browser.translations.autoTranslate": ("DROP",None,"MED","early translations-era name; current family is alwaysTranslateLanguages/automaticallyPopup"),
  "browser.ml.chat.hideFromLabs":       ("DROP",None,"MED","existed in the FF130s chat rollout, gone at tip (pool shows hideLocalhost but not this)"),
  "browser.urlbar.merino.enabled":      ("DROP",None,"HIGH","CORRECTED after owner review: the .enabled gate is not real at tip, but the Merino FAMILY IS ALIVE (8 real prefs; config carries live Mozilla endpoint URLs). This line is inert — delete it; the INTENT (no Merino server contact) must be enforced at VALUE level in step 3: endpointURL/weather.*URL -> \"\" and/or the quicksuggest gates. EVIDENCE the empty-URL method is upstream-sanctioned: Mozilla's own testing/profiles/unittest-required/user.js:48-50 empties endpointURL/ohttpConfigURL/ohttpRelayURL to kill Merino in tests. Service docs (the 'Merino book', alive): mozilla-services.github.io/merino-py — providers include adMarketplace ads, AccuWeather, Polygon finance, geolocation"),
  "identity.sync.tokenserver.logRequests": ("DROP",None,"MED","uncertain provenance; real logging family is services.sync.log.* — either way dead here"),
  # FABRICATED — never existed; AI invention (poison evidence)
  "browser.urlbar.suggest.merilytics":  ("FABRICATED",None,"HIGH","prior audit list C; flagship invention ('merilytics' is not a word Mozilla ever used)"),
  "messaging-system.rssnews.enabled":   ("FABRICATED",None,"HIGH","prior audit list C"),
  "network.http.http2.default-concurrent-streams": ("FABRICATED",None,"HIGH","prior audit list C; plausible-looking HTTP/2 tuning trio invented wholesale"),
  "network.http.http2.default-hpack-buffer-size":  ("FABRICATED",None,"HIGH","prior audit list C"),
  "network.http.http2.initial-window-size":        ("FABRICATED",None,"HIGH","prior audit list C"),
  "media.video.preferred_codec":        ("FABRICATED",None,"HIGH","prior audit list C"),
  "media.navigator.video.preferred_codec": ("FABRICATED",None,"MED","same invention pattern in the navigator namespace"),
  "media.peerconnection.video.vp8_enabled": ("FABRICATED",None,"HIGH","prior audit list C + POR tango #3: value=true CONTRADICTS the H.264-only policy — POISON"),
  "media.rdd-ffmpeg.vaapi.enabled":     ("FABRICATED",None,"HIGH","prior audit list C; real prefs are media.rdd-ffmpeg.enabled + media.ffmpeg.vaapi.enabled — also referenced in a stale comment in 10.OVERRIDES user.js"),
  "media.hardware-video-decoding.nv12-overlay.enabled": ("FABRICATED",None,"HIGH","prior audit list C"),
  "browser.ml.backend.onnx.enabled":    ("FABRICATED",None,"HIGH","prior audit list C (browser.ml quartet)"),
  "browser.ml.textRecognition.enabled": ("FABRICATED",None,"HIGH","prior audit list C; real pref is dom.text-recognition.enabled"),
  "browser.ml.textTranslation.enabled": ("FABRICATED",None,"HIGH","prior audit list C"),
  "browser.ml.audioTranscription.enabled": ("FABRICATED",None,"HIGH","prior audit list C"),
  "media.ffmpeg.vaapi.disable-fallback": ("FABRICATED",None,"MED","no upstream history; the intent (no SW fallback) is already served by decode.force-enabled + the compiled hardware-only policy"),
  "gfx.canvas.accelerated.async-tiling.enabled": ("FABRICATED",None,"MED","no such pref in canvas-accel family history"),
  "gfx.webrender.display-lists.enabled": ("FABRICATED",None,"MED","display lists were never pref-gated under this name"),
  "ai.inference.enabled":               ("FABRICATED",None,"MED","no ai.* pref namespace exists in Firefox"),
  "nimbus.enabled":                     ("FABRICATED",None,"MED","Nimbus has no master nimbus.enabled; real kill switches are app.normandy.* (locked) + app.shield.optoutstudies.enabled"),
  "datareporting.glean.enabled":        ("FABRICATED",None,"MED","invented sibling of the real datareporting.glean.uploadEnabled (which is KEEP_LOCAL)"),
  "browser.monitor.feature":            ("FABRICATED",None,"MED","malformed name (no leaf); real family is browser.contentblocking.report.monitor.*"),
  "cookiebanners.reportingSite.telemetry.enabled": ("FABRICATED",None,"MED","no history in the real cookiebanners.* family"),
  "browser.low_commit_space_notification_interval_ms": ("FABRICATED",None,"MED","invented sibling of the real low_commit_space threshold prefs"),
}

# FIX-target verification pools: namespace prefix -> enumerate once (cache-warm)
def pool(ns, _cache={}):
    if ns not in _cache:
        try: _cache[ns] = set(sfpref.enumerate_ns(ns)[2])
        except Exception as e:
            print(f"  ! enumerate failed for {ns}: {e}"); _cache[ns] = set()
    return _cache[ns]

def target_exists(t):
    return t in pool(".".join(t.split(".")[:2]))

# ── load inputs ──────────────────────────────────────────────────────────────
cfg = open(CONFIG, encoding="utf-8", errors="replace").read()
def cfg_value(p):
    m = re.search(r'^\s*(?:sticky_)?pref\(\s*"' + re.escape(p) + r'"\s*,\s*(.+?)\)\s*;', cfg, re.M)
    return m.group(1).strip() if m else "?"

rows = []
for line in open(f"{OUTDIR}/absent.txt"):
    if line.startswith("#"): continue
    parts = line.rstrip("\n").split("\t")
    if len(parts) < 3: continue
    pref, inbuild, nearest = parts[0], parts[1] == "IN_LOCAL_BUILD", parts[2]
    val = cfg_value(pref)
    if inbuild:
        rows.append((pref, "KEEP_LOCAL", "", "HIGH", "in OUR build (3-channel check); absent only at the moving tip — rebase-risk note", val))
    elif pref in A:
        verdict, target, conf, note = A[pref]
        if verdict == "FIX":
            if target_exists(target):
                note += " [target VERIFIED in searchfox pool]"
            else:
                verdict, note = "DROP", note + f" [DEMOTED: proposed target {target} NOT found at tip]"
                target = ""
        rows.append((pref, verdict, target or "", conf, note, val))
    else:
        rows.append((pref, "REVIEW", "", "-", f"no authored verdict — needs a human call (nearest: {nearest})", val))

# ── mechanical FAMILY_ALIVE flag on every deletion verdict ───────────────────
# Lesson (owner caught it on merino): a DROP/FABRICATED verdict on pref X says nothing
# about X's FAMILY. If real siblings of X live in config, the deleted line's INTENT may
# need value-level enforcement on those siblings (step 3) — flag it, never assume.
realset = [l.split("\t")[0] for l in open(f"{OUTDIR}/real.txt") if l.strip()]
for i, (pref, verdict, target, conf, note, val) in enumerate(rows):
    if verdict in ("DROP", "FABRICATED"):
        parent = pref.rsplit(".", 1)[0]
        sibs = sum(1 for r in realset if r.startswith(parent + "."))
        if sibs:
            rows[i] = (pref, verdict, target, conf,
                       note + f" [FAMILY_ALIVE: {sibs} real sibling(s) in config — check intent coverage in step 3]", val)

# ── outputs ──────────────────────────────────────────────────────────────────
counts = {}
for r in rows: counts[r[1]] = counts.get(r[1], 0) + 1

with open(f"{OUTDIR}/classification.tsv", "w") as f:
    f.write("pref\tverdict\tfix_target\tconfidence\tconfig_value\n")
    for pref, verdict, target, conf, note, val in rows:
        f.write(f"{pref}\t{verdict}\t{target}\t{conf}\t{val}\n")

with open(f"{OUTDIR}/CLASSIFICATION_2026-08-01.md", "w") as f:
    f.write(f"""# Classification of the 88 ABSENT prefs — {datetime.date.today()}
Input: audit-lists/absent.txt (durable re-run). Anchors: PREF_AUDIT_FINAL_2026-08-01.md.
Mechanical columns computed; **verdict column is AUTHORED judgment** (HIGH = anchored,
MED = unanchored) — review before step 2 applies it. FIX targets were verified against
live searchfox pools; unverifiable FIXes were demoted to DROP, never applied on faith.

| verdict | count | action in config/firefox.js |
|---|---|---|
""")
    order = ["KEEP_LOCAL", "FIX", "DROP", "FABRICATED", "REVIEW"]
    act = {"KEEP_LOCAL": "keep line (works in OUR build; note rebase risk)",
           "FIX": "rewrite line to the verified real name (recheck value semantics)",
           "DROP": "delete line (was real, removed everywhere we run)",
           "FABRICATED": "delete line + log as poison evidence",
           "REVIEW": "human call required before touching"}
    for v in order:
        if v in counts: f.write(f"| {v} | {counts[v]} | {act[v]} |\n")
    f.write(f"| **total** | **{len(rows)}** | |\n\n## Full table\n\n")
    f.write("| pref | verdict | conf | value in config | fix target / note |\n|---|---|---|---|---|\n")
    for v in order:
        for pref, verdict, target, conf, note, val in rows:
            if verdict != v: continue
            tn = (f"→ `{target}` — " if target else "") + note
            f.write(f"| `{pref}` | {verdict} | {conf} | `{val}` | {tn} |\n")

print("counts:", {k: counts[k] for k in order if k in counts}, "total", len(rows))
