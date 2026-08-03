# APPLY LOG — step 2 (20260801-184333)
Backups: firefox.js.pre-step2.20260801-184333.bak · overrides-user.js.pre-step2.20260801-184333.bak

## Deleted (55) — DROP+FABRICATED
- `media.ffmpeg.vaapi.disable-fallback` (was true)
- `media.video.preferred_codec` (was 1)
- `media.hardware-video-decoding.nv12-overlay.enabled` (was true)
- `gfx.canvas.accelerated.async-tiling.enabled` (was true)
- `gfx.webrender.display-lists.enabled` (was true)
- `media.ffvpx.enabled` (was false)
- `media.libvpx.enabled` (was false)
- `media.peerconnection.video.vp8_enabled` (was true)
- `media.h264.enabled` (was true)
- `media.mp3.enabled` (was true)
- `network.http.pipelining.max-optimistic-requests` (was 8)
- `network.http.http2.default-hpack-buffer-size` (was 65536)
- `network.http.http2.default-concurrent-streams` (was 100)
- `network.http.http2.initial-window-size` (was 131072)
- `network.predictor.enabled` (was false)
- `network.predictor.enable-prefetch` (was false)
- `network.preload` (was false)
- `media.ffmpeg.vaapi-drm-display.enabled` (was true)
- `media.navigator.video.preferred_codec` (was 1)
- `dom.indexedDB.enabled` (was true)
- `network.websocket.enabled` (was true)
- `dom.events.asyncClipboard.readText` (was true)
- `dom.events.asyncClipboard.clipboardItem` (was true)
- `datareporting.glean.enabled` (was false)
- `nimbus.enabled` (was false)
- `messaging-system.rssnews.enabled` (was false)
- `browser.ml.chat.hideFromLabs` (was true)
- `ai.inference.enabled` (was false)
- `browser.urlbar.suggest.merilytics` (was false)
- `browser.urlbar.merino.enabled` (was false)
- `browser.newtabpage.activity-stream.feeds.telemetry` (was false)
- `browser.newtabpage.activity-stream.telemetry.structuredIngestion.endpoint` (was "")
- `browser.pocket.enabled` (was false)
- `browser.pocket.api` (was "")
- `identity.sync.tokenserver.logRequests` (was false)
- `javascript.options.mem.gc_high_frequency_low_limit` (was 32)
- `browser.lowMemoryResponseMB` (was 400)
- `dom.wakelock.enabled` (was false)
- `browser.low_commit_space_notification_interval_ms` (was 10000)
- `dom.page_visibility.enabled` (was true)
- `browser.cache.offline.enable` (was true)
- `browser.cache.offline.insecure.enable` (was false)
- `browser.translations.autoTranslate` (was false)
- `browser.translations.panelShown` (was true)
- `browser.ml.backend.onnx.enabled` (was false)
- `browser.ml.textRecognition.enabled` (was false)
- `browser.ml.textTranslation.enabled` (was false)
- `browser.ml.audioTranscription.enabled` (was false)
- `browser.tabs.firefox-view-next` (was false)
- `browser.monitor.feature` (was false)
- `browser.shopping.experience2023.enabled` (was false)
- `browser.shopping.experience2023.autoOpen.enabled` (was false)
- `cookiebanners.reportingSite.telemetry.enabled` (was false)
- `gfx.layerscope.enabled` (was false)
- `media.rdd-ffmpeg.vaapi.enabled` (was true)

## Renamed (10)
- `gfx.webrender.scissored-cache-tiles.enabled` -> `gfx.webrender.scissored-cache-clears.enabled` = true
- `network.http.pacing.requests.min-number-to-pace` -> `network.http.pacing.requests.min-parallelism` = 20
- `media.navigator.video.max_width` -> `media.navigator.video.max_fs` = 8160 (macroblocks)
- `media.navigator.video.max_height` -> `media.navigator.video.max_fs` = 8160 (macroblocks)
- `media.navigator.video.max_framerate` -> `media.navigator.video.max_fr` = 30
- `media.getusermedia.aec_enabled` -> `media.getusermedia.audio.processing.aec.enabled` = true
- `media.getusermedia.noise_enabled` -> `media.getusermedia.audio.processing.noise.enabled` = true
- `media.getusermedia.agc_enabled` -> `media.getusermedia.audio.processing.agc.enabled` = true
- `javascript.options.mem.gc_high_frequency_heap_growth_max` -> `javascript.options.mem.gc_high_frequency_large_heap_growth` = 128
- `javascript.options.mem.gc_high_frequency_heap_growth_max` -> `javascript.options.mem.gc_high_frequency_large_heap_growth` = 300

## Covered-by-existing (1) — old line deleted, target already present
- `identity.fxaccounts.telemetry.clientAssertionJwt`: identity.fxaccounts.telemetry.clientAssociationPing.enabled already in config — old line deleted only

## Rider (10.OVERRIDES/NEW_FILES/user.js)
- removed inert media.ffmpeg.vaapi-drm-display.enabled line (absent from build, 3-channel check)
- fixed stale comment: media.rdd-ffmpeg.vaapi.enabled (fabricated) -> media.rdd-ffmpeg.enabled (real)

## Verification
- pref count: 1613 -> 1556 unique (1666 lines)
- dropped prefs still present: NONE
- fix targets missing: NONE
- duplicate pref lines: ['app.normandy.api_url', 'app.normandy.enabled', 'app.normandy.shieldLearnMoreUrl', 'app.shield.optoutstudies.enabled', 'app.update.auto', 'app.update.staging.enabled', 'breakpad.reportURL', 'browser.aboutwelcome.enabled', 'browser.contentblocking.report.privacy_metrics.enabled', 'browser.crashReports.unsubmittedCheck.autoSubmit2', 'browser.crashReports.unsubmittedCheck.enabled', 'browser.eme.ui.enabled', 'browser.firefox-view.feature-tour', 'browser.fullscreen.autohide', 'browser.gesture.pinch.in', 'browser.gesture.pinch.in.shift', 'browser.gesture.pinch.out', 'browser.gesture.pinch.out.shift', 'browser.gesture.tap', 'browser.link.open_newwindow.disabled_in_fullscreen', 'browser.lowMemoryResponseMask', 'browser.menu.showViewImageInfo', 'browser.ml.chat.enabled', 'browser.newtabpage.activity-stream.discoverystream.locale-list-config', 'browser.newtabpage.activity-stream.discoverystream.thumbsUpDown.region-thumbs-config', 'browser.profiles.enabled', 'browser.sessionstore.interval.idle', 'browser.sessionstore.log.appender.file.logOnSuccess', 'browser.sessionstore.loglevel', 'browser.sessionstore.max_tabs_undo', 'browser.sessionstore.privacy_level', 'browser.shareqrcode.enabled', 'browser.swipe.navigation-icon-end-position', 'browser.swipe.navigation-icon-max-radius', 'browser.swipe.navigation-icon-min-radius', 'browser.swipe.navigation-icon-start-position', 'browser.tabs.groups.enabled', 'browser.tabs.min_inactive_duration_before_unload', 'browser.tabs.searchclipboardfor.middleclick', 'browser.tabs.tooltipsShowPidAndActiveness', 'browser.tabs.unloadOnLowMemory', 'browser.taskbarTabs.enabled', 'browser.translations.enable', 'browser.uitour.enabled', 'browser.uitour.url', 'browser.urlbar.addons.featureGate', 'browser.urlbar.autoFill.adaptiveHistory.enabled', 'browser.urlbar.clipboard.featureGate', 'browser.urlbar.mdn.featureGate', 'browser.urlbar.quicksuggest.enabled', 'browser.urlbar.richSuggestions.featureGate', 'browser.urlbar.suggest.quicksuggest.nonsponsored', 'browser.urlbar.suggest.quicksuggest.sponsored', 'browser.urlbar.trending.featureGate', 'browser.urlbar.weather.featureGate', 'browser.warnOnQuitShortcut', 'devtools.aboutdebugging.local-tab-debugging', 'devtools.aboutdebugging.showHiddenAddons', 'devtools.high-contrast-mode-support', 'devtools.layout.boxmodel.highlightProperty', 'devtools.webconsole.sidebarToggle', 'dom.ipc.processPrelaunch.enabled', 'extensions.recommendations.themeRecommendationUrl', 'general.autoScroll', 'intl.multilingual.aboutWelcome.languageMismatchEnabled', 'intl.multilingual.downloadEnabled', 'intl.multilingual.enabled', 'intl.multilingual.liveReload', 'intl.multilingual.liveReloadBidirectional', 'javascript.options.mem.gc_high_frequency_large_heap_growth', 'javascript.options.shared_memory', 'media.av1.enabled', 'media.contextmenu.video-overlay-detection', 'media.getusermedia.screensharing.enabled', 'media.gmp-provider.enabled', 'media.gmp-widevinecdm-l1.enabled', 'media.gmp-widevinecdm-l1.visible', 'media.videocontrols.picture-in-picture.enabled', 'media.videocontrols.picture-in-picture.video-toggle.enabled', 'mousewheel.with_alt.action', 'mousewheel.with_shift.action', 'network.prefetch-next', 'nimbus.telemetry.targetingContextEnabled', 'places.semanticHistory.featureGate', 'privacy.trackingprotection.cryptomining.enabled', 'privacy.trackingprotection.fingerprinting.enabled', 'privacy.userContext.enabled', 'privacy.userContext.ui.enabled', 'security.mixed_content.block_active_content', 'security.sandbox.content.level', 'security.sandbox.logging.enabled', 'sidebar.revamp', 'sidebar.verticalTabs', 'signon.firefoxRelay.feature', 'termsofuse.bypassNotification', 'toolkit.telemetry.archive.enabled', 'toolkit.telemetry.bhrPing.enabled', 'toolkit.telemetry.firstShutdownPing.enabled', 'toolkit.telemetry.newProfilePing.enabled', 'toolkit.telemetry.shutdownPingSender.enabled', 'toolkit.telemetry.updatePing.enabled', 'ui.new-webcompat-reporter.send-more-info-link']
- **INVARIANTS FAIL**

Step-3 value-audit flags carried forward: min-parallelism=20, scissored-cache-clears=true,
gc_high_frequency_large_heap_growth=128 (semantics vs defaults unverified); Merino URL
neutering; quicksuggest.online.enabled sticky; 10 live nimbus.* values.

---
## Step 2b — doubles dedupe (2026-08-01 18:45)
Discovery: the step-2 invariant exposed ~101 PRE-EXISTING doubled prefs (20 identical-value, 81 conflicting).
Pattern: [vanilla base value, hardened override] layered in one file — last-wins had been carrying the intent.
Policy applied: keep LAST occurrence (behavior-preserving); exception: value-identical pairs differing only
by sticky/locked keep the attributed line (2: browser.urlbar.suggest.quicksuggest.nonsponsored, browser.urlbar.suggest.quicksuggest.sponsored).
Removed 109 duplicate lines. Self-created gc double resolved earlier (kept 128, step-3 flag).

### FLAGGED for step-3 review (>=3 occurrences / chaotic):
- `browser.tabs.unloadOnLowMemory`: ['true', 'false', 'true']
- `security.sandbox.content.level`: ['9', '3', '6', '1', '3']
- `sidebar.revamp`: ['true', 'false', 'false']
- `dom.ipc.processPrelaunch.enabled`: ['false', 'true', 'false']
- `browser.crashReports.unsubmittedCheck.enabled`: ['true', 'false', 'false']
- `app.shield.optoutstudies.enabled`: ['true', 'false', 'false']
