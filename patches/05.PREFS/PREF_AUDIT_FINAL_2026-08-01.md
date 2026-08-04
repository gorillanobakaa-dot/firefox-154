# FINAL Pref Audit — config/firefox.js vs current mozilla-central (Nightly)
**2026-08-01. Authority: searchfox `text:` (exact) — the real source, per-pref.**
**GitHub code-search count = DISCARDED: it certifies DEAD prefs as real via cargo-cult
(e.g. network.predictor.enabled = 1436 GitHub refs but REMOVED from Firefox; searchfox=0).**

## Result (of 1613 config prefs)
- **~1522 REAL** — confirmed in current mozilla-central (1504 batch + 18 rescued by per-pref text: that the batch-enumerate false-negatived).
- **~82 NOT in current Firefox** — for a Nightly user (your build = mozilla-central) these are inert. Three sub-types:

### (A) DROP — removed upstream, now dead in your build (were real once; cargo-culted in old user.js)
network.predictor.enabled, network.predictor.enable-prefetch, network.preload,
dom.events.asyncClipboard.clipboardItem, dom.events.asyncClipboard.readText,
dom.indexedDB.enabled, dom.page_visibility.enabled, dom.wakelock.enabled,
media.h264.enabled, media.mp3.enabled, media.libvpx.enabled, media.ffvpx.enabled,
network.websocket.enabled, browser.pocket.enabled, browser.pocket.api,
browser.tabs.firefox-view (older form), browser.translations.panelShown, etc.

### (B) FIX — wrong name, real equivalent exists (change to the real pref)
media.getusermedia.aec_enabled     -> media.getusermedia.audio.processing.aec.enabled
media.getusermedia.agc_enabled     -> media.getusermedia.audio.processing.agc.enabled
media.getusermedia.noise_enabled   -> media.getusermedia.audio.processing.noise.enabled
identity.fxaccounts.telemetry.clientAssertionJwt -> identity.fxaccounts.telemetry.clientAssociationPing.enabled
(others: run `sfpref enumerate <namespace>` to find the real neighbour)

### (C) FABRICATED — never existed, pure Gemini invention
browser.urlbar.suggest.merilytics, messaging-system.rssnews.enabled,
network.http.http2.default-concurrent-streams, network.http.http2.default-hpack-buffer-size,
network.http.http2.initial-window-size, media.navigator.video.max_framerate/height/width,
media.video.preferred_codec, media.peerconnection.video.vp8_enabled, media.rdd-ffmpeg.vaapi.enabled,
media.hardware-video-decoding.nv12-overlay.enabled, browser.ml.audioTranscription/backend.onnx/textRecognition/textTranslation.enabled, etc.

## Method note
searchfox `text:` per-pref is the authority. The batch namespace-enumerate is a fast
first pass but false-negatives on big/capped namespaces (missed 18 real prefs the
per-pref text: rescued). GitHub count is NOT used — it is polluted by cargo-culted dead prefs.
Full lists: nf_absent.txt (the 82), nf_inbuild.txt (9 build-defined). Nightly = searchfox
version-matched, no release cross-check needed.

---
## ADDENDUM (2026-08-01, later): durable lists regenerated
The transient lists this audit referenced (nf_absent.txt, nf_inbuild.txt, full_audit.log)
were lost to scratchpad. Regenerated durably in `audit-lists/` (run_audit.py + outputs).
Exact counts from the durable re-run: **1525 REAL (1504 batch + 21 rescued) · 88 ABSENT,
of which 23 are IN_LOCAL_BUILD** (present in OUR objdir greprefs.js / local firefox.js —
i.e. they DO work in our 154 build even though gone at the mozilla-central tip; version
skew + our own custom prefs). These supersede the approximate ~1522/~82/9 above.
