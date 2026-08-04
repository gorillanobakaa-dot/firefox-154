# STEP-2 FIX — #ifdef-branch regression repair (20260801-194910)
Root cause: step2b keep-last dedup was #ifdef-UNAWARE; for prefs that appear ONLY in
mutually-exclusive #if/#else branches (no unconditional override), it kept the physically-
last branch — the WRONG branch for this Linux/Nightly build. Surfaced by the sandbox-level
question. Fix target = authoritative preprocessed build output (dist/bin greprefs.js +
browser/defaults/preferences/firefox.js), NOT a simulator.

## FIXED (22) — restored Linux/Nightly-effective value
- `browser.eme.ui.enabled`: false -> true
- `general.autoScroll`: true -> false
- `browser.urlbar.autoFill.adaptiveHistory.enabled`: false -> true
- `browser.tabs.tooltipsShowPidAndActiveness`: false -> true
- `browser.tabs.searchclipboardfor.middleclick`: false -> true
- `browser.gesture.pinch.out`: "" -> "cmd_fullZoomEnlarge"
- `browser.gesture.pinch.in`: "" -> "cmd_fullZoomReduce"
- `browser.gesture.pinch.out.shift`: "" -> "cmd_fullZoomReset"
- `browser.gesture.pinch.in.shift`: "" -> "cmd_fullZoomReset"
- `browser.gesture.tap`: "" -> "cmd_fullZoomReset"
- `browser.sessionstore.log.appender.file.logOnSuccess`: false -> true
- `browser.newtabpage.activity-stream.discoverystream.locale-list-config`: "" -> "en-US,en-CA,en-GB"
- `browser.newtabpage.activity-stream.discoverystream.thumbsUpDown.region-thumbs-config`: "US" -> "US, CA"
- `media.contextmenu.video-overlay-detection`: false -> true
- `browser.contentblocking.report.privacy_metrics.enabled`: false -> true
- `privacy.userContext.enabled`: false -> true
- `privacy.userContext.ui.enabled`: false -> true
- `devtools.layout.boxmodel.highlightProperty`: false -> true
- `devtools.webconsole.sidebarToggle`: false -> true
- `devtools.high-contrast-mode-support`: false -> true
- `browser.shareqrcode.enabled`: false -> true
- `ui.new-webcompat-reporter.send-more-info-link`: false -> true

## DROPPED (4) — absent from this build, falls to compiled default
- `browser.lowMemoryResponseMask`
- `security.sandbox.logging.enabled`
- `media.gmp-widevinecdm-l1.visible`
- `media.gmp-widevinecdm-l1.enabled`

## HELD for owner decision
- `places.semanticHistory.featureGate`: vanilla=true but it is an ML feature; mission gates ML,
  so the accidental `false` is mission-aligned. LEFT false pending your call.
- `security.sandbox.content.level`=3: NOT a dedup bug (deliberate unconditional Gorilla line),
  but flagged: comment says 'level 4', value is 3, vanilla-Linux=6, verified-shipped(atom)=4,
  and content-sandbox is SEPARATE from RDD/VA-API (your '1 for RDD' memory was a conflation).

## NOT TOUCHED: 49 prefs with unconditional Gorilla overrides (keep-last was correct).
Verified: all telemetry/normandy/shield/uitour/prefetch/ml.chat hardening intact.

## Owner decision (2026-08-01, same day)
- `places.semanticHistory.featureGate` = **false CONFIRMED** ("if it is machine learning we do
  not want that — too hard on low processors and low RAM"). GORILLA marker added; the accidental
  false is now a deliberate false. Remaining open decision: security.sandbox.content.level.
