# Step 3 — value pass report (20260801-185140)
Baseline: objdir greprefs.js (1507 compiled defaults). config feeds nothing at runtime.

| bucket | count |
|---|---|
| Merino endpoints emptied | 6 |
| REDUNDANT_DEFAULT dropped (safe noise) | 47 |
| REDUNDANT_DEFAULT kept+flagged (pinned/sensitive) | 22 |
| real overrides (differ from compiled default) | 69 |
| app prefs w/ no compiled default (kept) | 1406 |
| **prefs after step 3** | **1509** |

## Merino emptied
- `browser.urlbar.merino.endpointURL` (was "https://merino.services.mozilla.com/api/v1/suggest")
- `browser.urlbar.merino.ohttpConfigURL` (was "https://ohttp-gateway-merino.services.mozilla.com/ohttp-configs")
- `browser.urlbar.merino.ohttpRelayURL` (was "https://ohttp-merino.mozilla.fastly-edge.com")
- `browser.urlbar.merino.weather.reportEndpointURL` (was "https://merino.services.mozilla.com/api/v1/suggest")
- `browser.urlbar.merino.weather.hourlyEndpointURL` (was "https://merino.services.mozilla.com/api/v1/weather/hourly-forecasts")
- `browser.newtabpage.activity-stream.discoverystream.merino-provider.endpoint` (was "merino.services.mozilla.com")

## Redundant defaults DROPPED (47) — value==compiled default, non-sensitive, unpinned
- `browser.newtabpage.activity-stream.discoverystream.merino-provider.ohttp.enabled` = false
- `browser.newtabpage.activity-stream.feeds.section.topstories` = false
- `browser.newtabpage.activity-stream.feeds.topsites` = false
- `browser.newtabpage.activity-stream.showSponsored` = false
- `browser.newtabpage.activity-stream.showSponsoredTopSites` = false
- `browser.search.separatePrivateDefault.ui.enabled` = false
- `browser.send_pings` = false
- `browser.translations.enable` = false
- `cookiebanners.bannerClicking.enabled` = true
- `devtools.defaultColorUnit` = "authored"
- `dom.disable_window_move_resize` = false
- `dom.ipc.processCount.extension` = 1
- `dom.ipc.processCount.file` = 1
- `extensions.recommendations.themeRecommendationUrl` = ""
- `extensions.webcompat.smartblockEmbeds.enabled` = true
- `gfx.webrender.all` = true
- `intl.regional_prefs.use_os_locales` = false
- `javascript.options.mem.gc_compacting` = true
- `javascript.options.mem.gc_generational` = true
- `javascript.options.mem.gc_incremental` = true
- `javascript.options.shared_memory` = true
- `javascript.options.wasm` = true
- `layers.acceleration.force-enabled` = true
- `media.av1.enabled` = false
- `media.ffmpeg.vaapi.decode.force-enabled` = true
- `media.ffmpeg.vaapi.enabled` = true
- `media.getusermedia.screensharing.enabled` = true
- `media.hardware-video-decoding.force-enabled` = true
- `media.navigator.permission.disabled` = false
- `media.peerconnection.ice.no_host` = false
- `media.peerconnection.ice.tcp` = true
- `media.videocontrols.picture-in-picture.display-text-tracks.enabled` = true
- `media.vp9.enabled` = false
- `media.webm.enabled` = false
- `mousewheel.with_alt.action` = 2
- `mousewheel.with_meta.action` = 1
- `mousewheel.with_shift.action` = 4
- `network.http.keep-alive.timeout` = 115
- `network.http.pacing.requests.enabled` = true
- `network.http.tcp_keepalive.long_lived_connections` = true
- `network.http.tcp_keepalive.short_lived_connections` = true
- `network.manage-offline-status` = true
- `network.protocol-handler.expose-all` = true
- `network.websocket.max-connections` = 200
- `signon.relatedRealms.enabled` = false
- `toolkit.glean.uploadEnabled` = false
- `widget.dmabuf.force-enabled` = true

## Redundant defaults KEPT + flagged for step-4 lock (22)
- `app.shield.optoutstudies.enabled` = false  [sensitive-ns]
- `browser.ml.chat.enabled` = false  [sensitive-ns]
- `browser.ml.checkForMemory` = false  [sensitive-ns]
- `browser.ml.enable` = false  [sensitive-ns]
- `browser.urlbar.suggest.quicksuggest.nonsponsored` = false  [pinned]
- `browser.urlbar.suggest.quicksuggest.sponsored` = false  [pinned]
- `datareporting.glean.uploadEnabled` = false  [sensitive-ns]
- `datareporting.healthreport.uploadEnabled` = false  [sensitive-ns]
- `datareporting.policy.dataSubmissionEnabled` = false  [sensitive-ns]
- `extensions.pocket.enabled` = false  [sensitive-ns]
- `media.getusermedia.audio.processing.aec.enabled` = true  [pinned]
- `media.getusermedia.audio.processing.agc.enabled` = true  [pinned]
- `media.getusermedia.audio.processing.noise.enabled` = true  [pinned]
- `toolkit.telemetry.archive.enabled` = false  [sensitive-ns]
- `toolkit.telemetry.bhrPing.enabled` = false  [sensitive-ns]
- `toolkit.telemetry.enabled` = false  [sensitive-ns]
- `toolkit.telemetry.firstShutdownPing.enabled` = false  [sensitive-ns]
- `toolkit.telemetry.newProfilePing.enabled` = false  [sensitive-ns]
- `toolkit.telemetry.server` = ""  [sensitive-ns]
- `toolkit.telemetry.shutdownPingSender.enabled` = false  [sensitive-ns]
- `toolkit.telemetry.unified` = false  [sensitive-ns]
- `toolkit.telemetry.updatePing.enabled` = false  [sensitive-ns]

## Verification
- duplicate pref lines: NONE
- merino URLs still non-empty: NONE
- **INVARIANTS PASS**

## Post-verification (5-sample audit of the redundant-drop logic)
Confirmed each is a REAL compiled default in greprefs.js (not a parse false-positive), so
dropping falls back to the identical value:
- browser.translations.enable  -> greprefs false (this build compiles translations OFF)
- browser.send_pings           -> greprefs false
- gfx.webrender.all            -> greprefs true (WebRender stays on via compiled default)
- browser.newtabpage.activity-stream.showSponsored -> greprefs false
- dom.disable_window_move_resize -> greprefs false (padded-whitespace value; norm() handled)
Method sound: value-comparison against compiled defaults, whitespace-normalized.

## Carried step-4 actions
- LOCK the 22 kept-redundant (telemetry/glean/datareporting/pocket/shield/ml + the 2 sticky
  quicksuggest + 3 getusermedia) via pref(...,locked) and/or policies.json — a default-valued
  line is worthless UNLESS locked; that is the whole baked-in-locked-defaults point.
- REVIEW flags (unchanged from step 2b): security.sandbox.content.level=3 (compiled default 4;
  LOWER = weaker sandbox, kept as an Ivy-Bridge perf tradeoff — confirm intent);
  dom.ipc.processPrelaunch.enabled=false (memory-saving); gc_high_frequency_large_heap_growth=128.
