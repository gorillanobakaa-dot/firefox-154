# Classification of the 88 ABSENT prefs — 2026-08-01
Input: audit-lists/absent.txt (durable re-run). Anchors: PREF_AUDIT_FINAL_2026-08-01.md.
Mechanical columns computed; **verdict column is AUTHORED judgment** (HIGH = anchored,
MED = unanchored) — review before step 2 applies it. FIX targets were verified against
live searchfox pools; unverifiable FIXes were demoted to DROP, never applied on faith.

| verdict | count | action in config/firefox.js |
|---|---|---|
| KEEP_LOCAL | 23 | keep line (works in OUR build; note rebase risk) |
| FIX | 10 | rewrite line to the verified real name (recheck value semantics) |
| DROP | 32 | delete line (was real, removed everywhere we run) |
| FABRICATED | 23 | delete line + log as poison evidence |
| **total** | **88** | |

## Full table

| pref | verdict | conf | value in config | fix target / note |
|---|---|---|---|---|
| `permissions.desktop-notification.notNow.enabled` | KEEP_LOCAL | HIGH | `false` | in OUR build (3-channel check); absent only at the moving tip — rebase-risk note |
| `permissions.desktop-notification.telemetry.siteCategories` | KEEP_LOCAL | HIGH | `'{"facebook.com":"social","instagram.com":"social","twitter.com":"social","x.com":"social","tiktok.com":"social","linkedin.com":"social","reddit.com":"social","pinterest.com":"social","snapchat.com":"social","tumblr.com":"social","slack.com":"chat_communication","discord.com":"chat_communication","teams.microsoft.com":"chat_communication","zoom.us":"chat_communication","whatsapp.com":"chat_communication","telegram.org":"chat_communication","messenger.com":"chat_communication","skype.com":"chat_communication","signal.org":"chat_communication","viber.com":"chat_communication","mail.google.com":"email","gmail.com":"email","outlook.com":"email","outlook.live.com":"email","mail.yahoo.com":"email","yahoo.com":"email","protonmail.com":"email","aol.com":"email","icloud.com":"email","zoho.com":"email","youtube.com":"media_streaming","netflix.com":"media_streaming","twitch.tv":"media_streaming","hulu.com":"media_streaming","disneyplus.com":"media_streaming","hbomax.com":"media_streaming","primevideo.com":"media_streaming","crunchyroll.com":"media_streaming","paramountplus.com":"media_streaming","spotify.com":"media_streaming","soundcloud.com":"media_streaming","pandora.com":"media_streaming","tv.apple.com":"media_streaming","steampowered.com":"gaming","steamcommunity.com":"gaming","store.epicgames.com":"gaming","roblox.com":"gaming","playstation.com":"gaming","xbox.com":"gaming","nintendo.com":"gaming","battle.net":"gaming","itch.io":"gaming","chess.com":"gaming","calendar.google.com":"calendar","outlook.live.com":"calendar","calendar.yahoo.com":"calendar","calendar.com":"calendar","drive.google.com":"productivity_collaboration","docs.google.com":"productivity_collaboration","sheets.google.com":"productivity_collaboration","office.com":"productivity_collaboration","onedrive.live.com":"productivity_collaboration","dropbox.com":"productivity_collaboration","box.com":"productivity_collaboration","notion.so":"productivity_collaboration","trello.com":"productivity_collaboration","asana.com":"productivity_collaboration","monday.com":"productivity_collaboration","atlassian.com":"productivity_collaboration","gitlab.com":"productivity_collaboration","bitbucket.org":"productivity_collaboration","miro.com":"productivity_collaboration","figma.com":"productivity_collaboration","cnn.com":"news_publishers","nytimes.com":"news_publishers","bbc.com":"news_publishers","theguardian.com":"news_publishers","washingtonpost.com":"news_publishers","foxnews.com":"news_publishers","reuters.com":"news_publishers","apnews.com":"news_publishers","bloomberg.com":"news_publishers","wsj.com":"news_publishers","usatoday.com":"news_publishers","nbcnews.com":"news_publishers","abcnews.go.com":"news_publishers","cbsnews.com":"news_publishers","npr.org":"news_publishers","time.com":"news_publishers","newsweek.com":"news_publishers","politico.com":"news_publishers","huffpost.com":"news_publishers","buzzfeednews.com":"news_publishers"}'` | in OUR build (3-channel check); absent only at the moving tip — rebase-risk note |
| `browser.newtabpage.activity-stream.discoverystream.thumbsUpDown.locale-thumbs-config` | KEEP_LOCAL | HIGH | `"en-US, en-GB, en-CA"` | in OUR build (3-channel check); absent only at the moving tip — rebase-risk note |
| `browser.newtabpage.activity-stream.discoverystream.thumbsUpDown.region-thumbs-config` | KEEP_LOCAL | HIGH | `"US, CA"` | in OUR build (3-channel check); absent only at the moving tip — rebase-risk note |
| `browser.newtabpage.activity-stream.discoverystream.thumbsUpDown.searchTopsitesCompact` | KEEP_LOCAL | HIGH | `true` | in OUR build (3-channel check); absent only at the moving tip — rebase-risk note |
| `browser.smartwindow.preferences.endpoint` | KEEP_LOCAL | HIGH | `""` | in OUR build (3-channel check); absent only at the moving tip — rebase-risk note |
| `browser.smartwindow.allowTables` | KEEP_LOCAL | HIGH | `true` | in OUR build (3-channel check); absent only at the moving tip — rebase-risk note |
| `browser.smartwindow.userFeedbackCollection` | KEEP_LOCAL | HIGH | `false` | in OUR build (3-channel check); absent only at the moving tip — rebase-risk note |
| `browser.translation.neverForLanguages` | KEEP_LOCAL | HIGH | `""` | in OUR build (3-channel check); absent only at the moving tip — rebase-risk note |
| `browser.contentblocking.report.proxy.enabled` | KEEP_LOCAL | HIGH | `false` | in OUR build (3-channel check); absent only at the moving tip — rebase-risk note |
| `browser.promo.focus.disallowed_regions` | KEEP_LOCAL | HIGH | `"cn"` | in OUR build (3-channel check); absent only at the moving tip — rebase-risk note |
| `browser.promo.focus.enabled` | KEEP_LOCAL | HIGH | `true` | in OUR build (3-channel check); absent only at the moving tip — rebase-risk note |
| `browser.contentblocking.report.proxy_extension.url` | KEEP_LOCAL | HIGH | `"https://fpn.firefox.com/browser?utm_source=firefox-desktop&utm_medium=referral&utm_campaign=about-protections&utm_content=about-protections"` | in OUR build (3-channel check); absent only at the moving tip — rebase-risk note |
| `browser.privatebrowsing.felt-privacy-v1` | KEEP_LOCAL | HIGH | `true` | in OUR build (3-channel check); absent only at the moving tip — rebase-risk note |
| `ui.new-webcompat-reporter.reason-dropdown.randomized` | KEEP_LOCAL | HIGH | `true` | in OUR build (3-channel check); absent only at the moving tip — rebase-risk note |
| `browser.ipProtection.fxa.useActivateFlow` | KEEP_LOCAL | HIGH | `true` | in OUR build (3-channel check); absent only at the moving tip — rebase-risk note |
| `browser.contentsharing.newBadge.enabled` | KEEP_LOCAL | HIGH | `true` | in OUR build (3-channel check); absent only at the moving tip — rebase-risk note |
| `media.ffmpeg.vaapi.enabled` | KEEP_LOCAL | HIGH | `true` | in OUR build (3-channel check); absent only at the moving tip — rebase-risk note |
| `media.ffmpeg.vaapi.decode.force-enabled` | KEEP_LOCAL | HIGH | `true` | in OUR build (3-channel check); absent only at the moving tip — rebase-risk note |
| `media.vp9.enabled` | KEEP_LOCAL | HIGH | `false` | in OUR build (3-channel check); absent only at the moving tip — rebase-risk note |
| `datareporting.glean.uploadEnabled` | KEEP_LOCAL | HIGH | `false` | in OUR build (3-channel check); absent only at the moving tip — rebase-risk note |
| `toolkit.glean.uploadEnabled` | KEEP_LOCAL | HIGH | `false` | in OUR build (3-channel check); absent only at the moving tip — rebase-risk note |
| `extensions.pocket.enabled` | KEEP_LOCAL | HIGH | `false` | in OUR build (3-channel check); absent only at the moving tip — rebase-risk note |
| `gfx.webrender.scissored-cache-tiles.enabled` | FIX | MED | `true` | → `gfx.webrender.scissored-cache-clears.enabled` — name-mutation of the real scissored-cache pref; check value vs default before adopting [target VERIFIED in searchfox pool] |
| `network.http.pacing.requests.min-number-to-pace` | FIX | MED | `20` | → `network.http.pacing.requests.min-parallelism` — mangled form of the real pacing knob [target VERIFIED in searchfox pool] |
| `media.navigator.video.max_width` | FIX | MED | `1920` | → `media.navigator.video.max_fs` — real cap is max_fs — UNIT DIFFERS (macroblocks, not px): value must be recomputed, not copied [target VERIFIED in searchfox pool] |
| `media.navigator.video.max_height` | FIX | MED | `1080` | → `media.navigator.video.max_fs` — same target as max_width — one real pref caps frame SIZE; do not copy px value [target VERIFIED in searchfox pool] |
| `media.navigator.video.max_framerate` | FIX | MED | `30` | → `media.navigator.video.max_fr` — real cap is max_fr (fps) [target VERIFIED in searchfox pool] |
| `media.getusermedia.aec_enabled` | FIX | HIGH | `true` | → `media.getusermedia.audio.processing.aec.enabled` — prior audit list B [target VERIFIED in searchfox pool] |
| `media.getusermedia.noise_enabled` | FIX | HIGH | `true` | → `media.getusermedia.audio.processing.noise.enabled` — prior audit list B [target VERIFIED in searchfox pool] |
| `media.getusermedia.agc_enabled` | FIX | HIGH | `true` | → `media.getusermedia.audio.processing.agc.enabled` — prior audit list B [target VERIFIED in searchfox pool] |
| `identity.fxaccounts.telemetry.clientAssertionJwt` | FIX | HIGH | `""` | → `identity.fxaccounts.telemetry.clientAssociationPing.enabled` — prior audit list B [target VERIFIED in searchfox pool] |
| `javascript.options.mem.gc_high_frequency_heap_growth_max` | FIX | MED | `128` | → `javascript.options.mem.gc_high_frequency_large_heap_growth` — closest real GC growth knob; demote to DROP if absent [target VERIFIED in searchfox pool] |
| `media.ffvpx.enabled` | DROP | HIGH | `false` | prior audit list A |
| `media.libvpx.enabled` | DROP | HIGH | `false` | prior audit list A; VP8/VP9 already blocked by compiled codec policy |
| `media.h264.enabled` | DROP | HIGH | `true` | prior audit list A; ancient OpenH264-era gate — H.264 policy lives in our compiled DecoderTraits patch |
| `media.mp3.enabled` | DROP | HIGH | `true` | prior audit list A |
| `network.http.pipelining.max-optimistic-requests` | DROP | HIGH | `8` | HTTP pipelining ripped out of browsers; LEGACY standard (RFC9112 s9.3.2) |
| `network.predictor.enabled` | DROP | HIGH | `false` | prior audit list A; the 1436-GitHub-refs poster child |
| `network.predictor.enable-prefetch` | DROP | HIGH | `false` | prior audit list A |
| `network.preload` | DROP | HIGH | `false` | prior audit list A [FAMILY_ALIVE: 41 real sibling(s) in config — check intent coverage in step 3] |
| `media.ffmpeg.vaapi-drm-display.enabled` | DROP | MED | `true` | was real, gone at tip AND from our build (3-channel check) — ALSO remove the inert line in 10.OVERRIDES/NEW_FILES/user.js |
| `dom.indexedDB.enabled` | DROP | HIGH | `true` | prior audit list A; IndexedDB no longer disableable |
| `network.websocket.enabled` | DROP | HIGH | `true` | prior audit list A; WS no longer pref-gated [FAMILY_ALIVE: 1 real sibling(s) in config — check intent coverage in step 3] |
| `dom.events.asyncClipboard.readText` | DROP | HIGH | `true` | prior audit list A; API graduated, gate removed |
| `dom.events.asyncClipboard.clipboardItem` | DROP | HIGH | `true` | prior audit list A; 2136 GitHub refs, removed |
| `browser.ml.chat.hideFromLabs` | DROP | MED | `true` | existed in the FF130s chat rollout, gone at tip (pool shows hideLocalhost but not this) [FAMILY_ALIVE: 18 real sibling(s) in config — check intent coverage in step 3] |
| `browser.urlbar.merino.enabled` | DROP | HIGH | `false` | CORRECTED after owner review: the .enabled gate is not real at tip, but the Merino FAMILY IS ALIVE (8 real prefs; config carries live Mozilla endpoint URLs). This line is inert — delete it; the INTENT (no Merino server contact) must be enforced at VALUE level in step 3: endpointURL/weather.*URL -> "" and/or the quicksuggest gates. EVIDENCE the empty-URL method is upstream-sanctioned: Mozilla's own testing/profiles/unittest-required/user.js:48-50 empties endpointURL/ohttpConfigURL/ohttpRelayURL to kill Merino in tests. Service docs (the 'Merino book', alive): mozilla-services.github.io/merino-py — providers include adMarketplace ads, AccuWeather, Polygon finance, geolocation [FAMILY_ALIVE: 8 real sibling(s) in config — check intent coverage in step 3] |
| `browser.newtabpage.activity-stream.feeds.telemetry` | DROP | MED | `false` | old activity-stream telemetry feed pref; telemetry gated elsewhere in our build [FAMILY_ALIVE: 2 real sibling(s) in config — check intent coverage in step 3] |
| `browser.newtabpage.activity-stream.telemetry.structuredIngestion.endpoint` | DROP | MED | `""` | companion of the above |
| `browser.pocket.enabled` | DROP | HIGH | `false` | prior audit list A; real gate = extensions.pocket.enabled (KEEP_LOCAL) |
| `browser.pocket.api` | DROP | HIGH | `""` | prior audit list A |
| `identity.sync.tokenserver.logRequests` | DROP | MED | `false` | uncertain provenance; real logging family is services.sync.log.* — either way dead here [FAMILY_ALIVE: 1 real sibling(s) in config — check intent coverage in step 3] |
| `javascript.options.mem.gc_high_frequency_low_limit` | DROP | MED | `32` | _mb-suffixed real name [DEMOTED: proposed target javascript.options.mem.gc_high_frequency_low_limit_mb NOT found at tip] [FAMILY_ALIVE: 4 real sibling(s) in config — check intent coverage in step 3] |
| `browser.lowMemoryResponseMB` | DROP | MED | `400` | invented name; real low-memory threshold pref [DEMOTED: proposed target browser.low_commit_space_threshold_mb NOT found at tip] [FAMILY_ALIVE: 743 real sibling(s) in config — check intent coverage in step 3] |
| `dom.wakelock.enabled` | DROP | HIGH | `false` | prior audit list A |
| `dom.page_visibility.enabled` | DROP | HIGH | `true` | prior audit list A |
| `browser.cache.offline.enable` | DROP | HIGH | `true` | AppCache removed years ago; LEGACY |
| `browser.cache.offline.insecure.enable` | DROP | HIGH | `false` | AppCache removed; LEGACY |
| `browser.translations.autoTranslate` | DROP | MED | `false` | early translations-era name; current family is alwaysTranslateLanguages/automaticallyPopup [FAMILY_ALIVE: 3 real sibling(s) in config — check intent coverage in step 3] |
| `browser.translations.panelShown` | DROP | HIGH | `true` | prior audit list A [FAMILY_ALIVE: 3 real sibling(s) in config — check intent coverage in step 3] |
| `browser.tabs.firefox-view-next` | DROP | HIGH | `false` | prior audit list A (older-form firefox-view pref) [FAMILY_ALIVE: 60 real sibling(s) in config — check intent coverage in step 3] |
| `browser.shopping.experience2023.enabled` | DROP | MED | `false` | Fakespot shopping was real (FF119+), sunset upstream |
| `browser.shopping.experience2023.autoOpen.enabled` | DROP | MED | `false` | same sunset |
| `gfx.layerscope.enabled` | DROP | HIGH | `false` | LayerScope debug tool died with the old layers system |
| `media.ffmpeg.vaapi.disable-fallback` | FABRICATED | MED | `true` | no upstream history; the intent (no SW fallback) is already served by decode.force-enabled + the compiled hardware-only policy |
| `media.video.preferred_codec` | FABRICATED | HIGH | `1` | prior audit list C |
| `media.hardware-video-decoding.nv12-overlay.enabled` | FABRICATED | HIGH | `true` | prior audit list C |
| `gfx.canvas.accelerated.async-tiling.enabled` | FABRICATED | MED | `true` | no such pref in canvas-accel family history |
| `gfx.webrender.display-lists.enabled` | FABRICATED | MED | `true` | display lists were never pref-gated under this name |
| `media.peerconnection.video.vp8_enabled` | FABRICATED | HIGH | `true` | prior audit list C + POR tango #3: value=true CONTRADICTS the H.264-only policy — POISON [FAMILY_ALIVE: 1 real sibling(s) in config — check intent coverage in step 3] |
| `network.http.http2.default-hpack-buffer-size` | FABRICATED | HIGH | `65536` | prior audit list C [FAMILY_ALIVE: 2 real sibling(s) in config — check intent coverage in step 3] |
| `network.http.http2.default-concurrent-streams` | FABRICATED | HIGH | `100` | prior audit list C; plausible-looking HTTP/2 tuning trio invented wholesale [FAMILY_ALIVE: 2 real sibling(s) in config — check intent coverage in step 3] |
| `network.http.http2.initial-window-size` | FABRICATED | HIGH | `131072` | prior audit list C [FAMILY_ALIVE: 2 real sibling(s) in config — check intent coverage in step 3] |
| `media.navigator.video.preferred_codec` | FABRICATED | MED | `1` | same invention pattern in the navigator namespace [FAMILY_ALIVE: 1 real sibling(s) in config — check intent coverage in step 3] |
| `datareporting.glean.enabled` | FABRICATED | MED | `false` | invented sibling of the real datareporting.glean.uploadEnabled (which is KEEP_LOCAL) |
| `nimbus.enabled` | FABRICATED | MED | `false` | Nimbus has no master nimbus.enabled; real kill switches are app.normandy.* (locked) + app.shield.optoutstudies.enabled [FAMILY_ALIVE: 10 real sibling(s) in config — check intent coverage in step 3] |
| `messaging-system.rssnews.enabled` | FABRICATED | HIGH | `false` | prior audit list C |
| `ai.inference.enabled` | FABRICATED | MED | `false` | no ai.* pref namespace exists in Firefox |
| `browser.urlbar.suggest.merilytics` | FABRICATED | HIGH | `false` | prior audit list C; flagship invention ('merilytics' is not a word Mozilla ever used) [FAMILY_ALIVE: 26 real sibling(s) in config — check intent coverage in step 3] |
| `browser.low_commit_space_notification_interval_ms` | FABRICATED | MED | `10000` | invented sibling of the real low_commit_space threshold prefs [FAMILY_ALIVE: 743 real sibling(s) in config — check intent coverage in step 3] |
| `browser.ml.backend.onnx.enabled` | FABRICATED | HIGH | `false` | prior audit list C (browser.ml quartet) |
| `browser.ml.textRecognition.enabled` | FABRICATED | HIGH | `false` | prior audit list C; real pref is dom.text-recognition.enabled |
| `browser.ml.textTranslation.enabled` | FABRICATED | HIGH | `false` | prior audit list C |
| `browser.ml.audioTranscription.enabled` | FABRICATED | HIGH | `false` | prior audit list C |
| `browser.monitor.feature` | FABRICATED | MED | `false` | malformed name (no leaf); real family is browser.contentblocking.report.monitor.* |
| `cookiebanners.reportingSite.telemetry.enabled` | FABRICATED | MED | `false` | no history in the real cookiebanners.* family |
| `media.rdd-ffmpeg.vaapi.enabled` | FABRICATED | HIGH | `true` | prior audit list C; real prefs are media.rdd-ffmpeg.enabled + media.ffmpeg.vaapi.enabled — also referenced in a stale comment in 10.OVERRIDES user.js |
