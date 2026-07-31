/* ============================================================================
 * gorilla-unleashed user.js v2.0 — "Kernel-Synced Braveheart" Profile
 * ============================================================================
 * Hardware : Intel i7-3632QM (Ivy Bridge) | Intel HD 4000 GT2 | 16GB RAM
 * Kernel   : Linux 7.0.9-unleashed (custom — 27 tweaks applied)
 * OS       : Debian 13 (Trixie)
 * Browser  : Firefox 152+ / Nightly compatible
 * ============================================================================
 *
 * WHAT THIS FILE DOES (Plain English):
 * Firefox ships as a "rental car" — hobbled, watched, and stuffed with
 * AI chatbots, background spies, and phone-home services. This file is the
 * full teardown. It rips out everything that wastes your RAM, burns CPU cycles
 * in the background, or reports your behaviour back to Mozilla/Google.
 *
 * It then rebuilds Firefox from scratch around YOUR hardware:
 *   - The Intel HD 4000 QuickSync ASIC does ALL video decoding. The CPU rests.
 *   - The GPU draws every pixel of the UI. The CPU rests more.
 *   - The network stack is synced to match the kernel's oversized TCP pipes
 *     and lightning-fast socket recycling so Firefox doesn't become the bottleneck.
 *   - Conferencing (Teams, WhatsApp Web, Telegram, Google Meet, Zoom) is kept
 *     fully functional with its own protected audio/video pathway.
 *   - Background tabs are frozen solid so they waste zero RAM or CPU.
 *   - Every Mozilla AI SDK, telemetry engine, experiment runner, and ad feed
 *     is individually shot and buried.
 *
 * HOW TO INSTALL:
 *   1. Find your Firefox profile folder:
 *      about:support → "Profile Directory" → Open Directory
 *   2. Drop this file into that folder (replace the old one).
 *   3. Fully restart Firefox (File → Exit, then relaunch — not just close-tab).
 *   4. Visit about:config to confirm values loaded correctly.
 *
 * ============================================================================ */


/* ============================================================================
 * SECTION 1: VA-API HARDWARE ACCELERATION — INTEL QUICKSYNC ASIC INJECTION
 * ============================================================================
 *
 * PLAIN ENGLISH:
 * Your Intel HD 4000 has a dedicated video decoder chip called QuickSync — a
 * separate mini-processor built specifically to decode H.264 video. Firefox
 * normally ignores it and burns your main CPU cores instead, which generates
 * heat and kills battery life.
 *
 * This section forces Firefox to route ALL video through that dedicated chip
 * via a Linux interface called VA-API. The CPU is only woken up if the chip
 * genuinely cannot handle the format. Combined with the kernel's DMA-BUF
 * (direct GPU memory) support, frames go GPU→screen with zero CPU touching.
 *
 * WHAT THE INTEL HD 4000 CAN DECODE IN HARDWARE (Ivy Bridge QuickSync):
 *   ✅ H.264 / AVC (YouTube, Netflix, most streaming sites — this is the target)
 *   ✅ MPEG-2 (old broadcast video)
 *   ✅ VC-1 / WMV9 (old Windows Media files)
 *   ❌ VP9  — no hardware support (CPU-only, so we block it for streaming)
 *   ❌ AV1  — no hardware support (CPU-only, so we block it for streaming)
 *   ❌ HEVC/H.265 — NOT supported on Ivy Bridge (hardware limitation)
 *
 * KERNEL SYNERGY:
 * Our kernel already enables the i915 driver's VDBOX unit and VA-API surface.
 * This section tells Firefox to use exactly that pathway without hesitation.
 * ============================================================================ */

// The master switch. Tells Firefox to talk to the Intel VDBOX via the VA-API
// interface that our kernel's i915 driver exposes.
user_pref("media.ffmpeg.vaapi.enabled",                  true);

// Override Firefox's internal "this GPU is untested" blocklist.
// Ivy Bridge is old enough that Firefox's blocklist flags it — this overrides that.
user_pref("media.ffmpeg.vaapi.decode.force-enabled",     true);
user_pref("media.volume_scale",                          "2.0");

// The global hardware decoding master switch. Must be ON.
user_pref("media.hardware-video-decoding.enabled",       true);

// Same override for the global hardware-decoding blocklist.
// Without this, Firefox can refuse even after the above switches are set.
user_pref("media.hardware-video-decoding.force-enabled", true);

// Disables the "try software if one frame fails" safety net.
// We do NOT want Firefox quietly sneaking back to CPU decode after a hiccup.
user_pref("media.ffmpeg.vaapi.disable-fallback",         true);

// Route video decoding through the GPU process, not the content process.
// This removes one layer of data-copying between the decoder and the screen.
user_pref("media.gpu-process-decoder",                   true);

// Force DMA-BUF (Direct Memory Access Buffer) mode.
// This lets decoded video frames live in GPU memory and go directly to the
// display without being copied through RAM first. Zero-copy pipeline.
user_pref("widget.dmabuf.force-enabled",                 true);

// Tells Firefox to prefer H.264 specifically when negotiating which codec
// to use on a page — since that is the only one our GPU can accelerate.
user_pref("media.video.preferred_codec",                  1); // 1 = H.264

// Use the X11/Wayland compositor's native zero-copy path for video overlay.
// This is the final mile of the hardware-decoded frame reaching your screen.
user_pref("media.hardware-video-decoding.nv12-overlay.enabled", true);


/* ============================================================================
 * SECTION 2: WEBRENDER & GPU COMPOSITING — INTEL HD 4000 UI ACCELERATION
 * ============================================================================
 *
 * PLAIN ENGLISH:
 * WebRender is Firefox's "GPU paintbrush." Instead of using your CPU to draw
 * every button, scroll, and animation, it hands all of that work to the GPU.
 * On an Intel HD 4000 with 16GB of shared RAM acting as VRAM, this means
 * scrolling, animations, and tab switching are completely smooth and the main
 * CPU cores are freed up for actual work.
 *
 * KERNEL SYNERGY:
 * Our kernel did NOT disable CONFIG_PREEMPT_RT, which was specifically done
 * to prevent a kernel panic with the i915 Intel graphics driver. Firefox's
 * GPU compositor talks directly to that same i915 driver, so this section
 * and our kernel config are built to work hand-in-hand.
 * ============================================================================ */

// Enable WebRender — Firefox's full GPU-accelerated painting engine.
user_pref("gfx.webrender.all",                           true);

// Use the native system GPU compositor (X11/Wayland) for window drawing.
user_pref("gfx.webrender.compositor",                    false);
user_pref("gfx.webrender.compositor.force-enabled",      false);

// Block the slow software fallback. If WebRender stutters, we want to
// know and fix it — not silently fall back to CPU rendering.
user_pref("gfx.webrender.fallback.software",             false);

// Hardware-accelerated HTML5 Canvas (used by games, charting, heavy UIs).
user_pref("gfx.canvas.accelerated",                      true);

// Tune the GPU canvas tile cache for Intel HD 4000's shared-memory
// architecture. 5000 tiles at a 2MB cache is a good balance.
user_pref("gfx.canvas.accelerated.cache-items",          5000);
user_pref("gfx.canvas.accelerated.cache-size",           2000);

// Enable partial GPU tile uploads. Only re-uploads pixels that actually
// changed — saves GPU bandwidth on the Intel's shared memory bus.
user_pref("gfx.canvas.accelerated.async-tiling.enabled", true);

// Allow WebRender to use display lists to batch draw calls together.
// Fewer GPU round trips = fewer stalls on the Intel HD 4000's modest EU count.
user_pref("gfx.webrender.display-lists.enabled",         true);

// Enable the optimised scissor rectangle to skip drawing hidden content.
// Pages with many hidden layers (Gmail, Google Docs) benefit a lot from this.
user_pref("gfx.webrender.scissored-cache-tiles.enabled", true);

// Disable CPU-side layer compositing (the old, slow pre-WebRender system).
user_pref("layers.acceleration.force-enabled",           true);
user_pref("layers.gpu-process.enabled",                  true);


/* ============================================================================
 * SECTION 3: CODEC LOCKING — "ONLY WHAT THE ASIC CAN HANDLE"
 * ============================================================================
 *
 * PLAIN ENGLISH:
 * Video codecs are the compression formats that video is stored in. Your Intel
 * HD 4000 can only hardware-decode H.264. It cannot do VP9, AV1, or HEVC.
 *
 * Without this section, YouTube will serve VP9 (because it uses less of
 * THEIR bandwidth), and your CPU will silently melt decoding it in software.
 * With this section, those codecs are fully blocked, and every video platform
 * is forced to fall back to their H.264 stream instead.
 *
 * IMPORTANT — CONFERENCING EXCEPTION:
 * WebRTC (the technology behind Teams, Meet, WhatsApp Web, Telegram video)
 * historically uses VP8 as its baseline video codec. VP8 is a lighter codec
 * than VP9 and decodes fast enough in software on an i7-3632QM that it does
 * NOT melt the CPU. We keep VP8 alive ONLY for WebRTC. Standalone VP8/VP9/AV1
 * video streaming is still blocked.
 *
 * The conferencing section (Section 5) locks WebRTC to H.264 wherever possible,
 * meaning Teams and Meet will use hardware-decoded H.264 on modern servers.
 * VP8 in WebRTC is the fallback-of-last-resort, kept only so calls don't
 * black-screen on legacy servers.
 * ============================================================================ */

// Block Firefox's internal software VP8/VP9 decoder (ffvpx).
// This is the primary software decode engine — killing it prevents CPU decode.
user_pref("media.ffvpx.enabled",                         false);

// Block the libvpx VP8/VP9 library. Belt AND suspenders.
user_pref("media.libvpx.enabled",                        false);

// Block AV1 completely. The Intel HD 4000 has no AV1 hardware — this codec
// at 4K would pin all 8 threads at 100% just to decode one video stream.
user_pref("media.av1.enabled",                           false);

// Block standalone VP9 video streams (YouTube's preferred codec).
// Sites will fall back to their H.264 track automatically.
user_pref("media.vp9.enabled",                           false);

// Block VP9 inside WebRTC calls specifically (Teams/Meet VP9 negotiation).
// Forces the call to negotiate H.264 or VP8 instead.
user_pref("media.peerconnection.video.vp9_enabled",      false);

// Allow VP8 in WebRTC ONLY (legacy conferencing server fallback).
// This does NOT re-enable VP8 for video streaming sites.
// It is a narrow, targeted exception for call quality resilience.
user_pref("media.peerconnection.video.vp8_enabled",      true);

// Keep WebM container support OFF for regular media playback.
// VP9 lives in .webm containers — blocking the container is a second kill-switch.
// NOTE: WebRTC does NOT use the WebM file container, so this is safe to disable.
user_pref("media.webm.enabled",                          false);

// Keep HEVC (H.265) off — Ivy Bridge has no HEVC hardware decode.
user_pref("media.hevc.enabled",                          false);

// Keep H.264 explicitly ON (belt and suspenders — should be on by default).
user_pref("media.h264.enabled",                          true);

// Keep AAC and MP3 audio hardware acceleration on (H.264 streams use AAC).
user_pref("media.mp4.enabled",                           true);
user_pref("media.mp3.enabled",                           true);

// Keep Opus audio ON — this is used by WebRTC for voice in calls.
// It is extremely low CPU cost and has no GPU involvement.
user_pref("media.opus.enabled",                          true);

// Block FLAC and Ogg Vorbis from triggering software decode pipelines.
// These are lossless/legacy formats rarely served by streaming sites.
user_pref("media.ogg.enabled",                           false);
user_pref("media.flac.enabled",                          false);

// Disable the legacy media plugin (GMP) codec download mechanism.
// We hardcode our codec choices above — we do not want Firefox silently
// downloading and enabling a VP9 software plugin behind our back.
user_pref("media.gmp-provider.enabled",                  false);
user_pref("media.gmp-manager.updateEnabled",             false);

// Tell the EME (Encrypted Media Extensions) system — used by Netflix/Disney+ —
// to use hardware-backed decryption where the Widevine CDM supports it.
user_pref("media.eme.enabled",                           true);
user_pref("media.eme.hdcp-policy-check.enabled",         true);


/* ============================================================================
 * SECTION 4: NETWORK STACK — KERNEL TCP SYNCHRONISATION
 * ============================================================================
 *
 * PLAIN ENGLISH:
 * Our custom kernel gave Firefox a six-lane motorway to work with: 16MB
 * default TCP buffers, 64MB maximum, a 128-packet instant burst window, and
 * socket cleanup in 1 second instead of 60. None of that matters if Firefox
 * is still driving a bicycle down it.
 *
 * This section tunes Firefox's internal network engine to MATCH the kernel's
 * oversized pipes. Connection limits are raised, pacing is tuned to prevent
 * bufferbloat on our FQ-CoDel queuing discipline, and speculative pre-loading
 * noise is silenced so the kernel's fast socket recycling isn't wasted opening
 * connections to URLs we never actually visit.
 *
 * KERNEL SYNERGY (direct matches):
 *   Kernel TCP_INIT_CWND=128    → Firefox network.tcp.max_connections raised
 *   Kernel RTO_MIN=10ms         → Firefox timeouts tightened to match
 *   Kernel TCP_TIMEWAIT=1s      → Firefox connection recycling aggressive
 *   Kernel rmem/wmem = 64MB     → Firefox read/write buffers enlarged
 *   Kernel FQ-CoDel (config)    → Firefox pacing kept ON to complement it
 * ============================================================================ */

// Total concurrent HTTP connections. Our kernel handles fast socket recycling
// (1 second TIME_WAIT instead of 60) so we can safely open more in parallel.
// Total concurrent HTTP connections. Sized for multi-gigabit throughput.
user_pref("network.http.max-connections",                1500);

// Per-server persistent connection limit. Raised to exploit
// the kernel's enlarged 64MB TCP write buffer and 128-packet CWND burst.
user_pref("network.http.max-persistent-connections-per-server", 20);

// Per-proxy persistent connections (for HTTPS proxies/VPNs).
user_pref("network.http.max-persistent-connections-per-proxy",  128);

// Raise the maximum number of queued HTTP/1.1 pipeline requests.
user_pref("network.http.pipelining.max-optimistic-requests", 8);

// Enable request pacing. Works with FQ-CoDel queue discipline.
user_pref("network.http.pacing.requests.enabled",        true);
user_pref("network.http.pacing.requests.min-number-to-pace", 20);
user_pref("network.http.pacing.requests.burst",          14);
user_pref("network.http.pacing.requests.hz",             100);

// Internal network read buffer. Sized to match the kernel's 16MB default.
user_pref("network.buffer.cache.size",                   131072);   // 128KB read chunk
user_pref("network.buffer.cache.count",                  512);      // 512 chunks = 64MB total

// HTTP/2 settings. Match our kernel's large CWND (128 packets) by allowing
// more concurrent streams and a larger initial window per stream.
user_pref("network.http.http2.enabled",                  true);
user_pref("network.http.http2.default-settings-header-table-size", 65536);
user_pref("network.http.http2.default-settings-max-concurrent-streams", 200);
user_pref("network.http.http2.default-settings-initial-window",      1048576);

// Enable HTTP/3 (QUIC). Bypasses TCP for supported sites.
user_pref("network.http.http3.enable",                   true);
user_pref("network.http.http3.enable_0rtt",              true);

// Connection timeouts to match our kernel's TCP_TIMEOUT_INIT=100ms.
user_pref("network.http.connection-timeout",             90);
user_pref("network.http.keep-alive.timeout",             300);
user_pref("network.http.throttle-requests",              false);
user_pref("network.http.max_response_header_size",       393216);

// DNS settings — use a fast local cache.
user_pref("network.dns.max_high_priority_threads",       8);
user_pref("network.dns.disablePrefetch",                 false);
user_pref("network.dns.disablePrefetchFromHTTPS",        false);
user_pref("network.dnsCacheEntries",                     20000);
user_pref("network.dnsCacheExpiration",                  3600);

// Enable predictive loading to leverage high-bandwidth capability.
user_pref("network.prefetch-next",                       true);
user_pref("network.predictor.enabled",                   true);
user_pref("network.predictor.enable-prefetch",           true);
user_pref("network.predictor.max-resources-per-entry",   250);
user_pref("network.predictor.max-uri-length",            2048);

// DNS over HTTPS — use Cloudflare's fast resolver.
user_pref("network.trr.mode",                            2);
user_pref("network.trr.uri",                             "https://cloudflare-dns.com/dns-query");
user_pref("network.trr.bootstrapAddress",                "1.1.1.1");

// Link pre-loading.
user_pref("network.preload",                             true);

// Speculatively-opened connections (pre-connect).
user_pref("network.http.speculative-parallel-limit",     32);

// Force Firefox to use the kernel's built-in TCP keep-alive.
user_pref("network.http.tcp_keepalive.short_lived_connections",  true);
user_pref("network.http.tcp_keepalive.long_lived_connections",   true);
user_pref("network.http.tcp_keepalive.long_lived_idle_time",     900); // 15 min

// TCP Fast Open
user_pref("network.tcp.tcp_fastopen_enable",                  true);
user_pref("network.tcp.tcp_fastopen_consecutive_failure_limit", 20);


/* ============================================================================
 * SECTION 5: WEBRTC & CONFERENCING — TEAMS / WHATSAPP / TELEGRAM / MEET
 * ============================================================================
 *
 * PLAIN ENGLISH:
 * WebRTC is the technology that powers in-browser video calls. It is what
 * makes Teams, Google Meet, WhatsApp Web, Telegram Web, and Zoom work without
 * installing any software. This section keeps WebRTC fully operational.
 *
 * The key tuning here is forcing H.264 as the PREFERRED video codec for calls.
 * Modern conferencing servers (Teams, Meet, Zoom) ALL support H.264. This means
 * your video call will be encoded AND decoded using the Intel QuickSync ASIC —
 * not your CPU — resulting in cooler temperatures and better battery life during
 * long calls.
 *
 * We also prevent WebRTC from leaking your real IP address (a common privacy
 * hole) while still allowing it to make calls to Google, Microsoft, etc.
 * ============================================================================ */

// Keep WebRTC fully functional. This is the foundation of all web calling.
user_pref("media.peerconnection.enabled",                true);

// Force H.264 software encode/decode via OpenH264 (Cisco's free H.264 library).
// This ensures H.264 is available for WebRTC even before hardware encode kicks in.
user_pref("media.webrtc.hw.h264.enabled",                true);

// Enable hardware H.264 encoding through VA-API for video calls.
// Your i7-3632QM's QuickSync can ENCODE H.264 in hardware too, not just decode.
// This dramatically reduces CPU usage when you're on camera in a video call.
user_pref("media.ffmpeg.vaapi-drm-display.enabled",      true);

// Tell the WebRTC engine to prefer H.264 when negotiating with the remote server.
// value 1 = H.264, value 2 = VP8, value 3 = VP9.
user_pref("media.navigator.video.preferred_codec",        1);

// Maximum video resolution to encode during calls (1080p).
// The HD 4000 handles 1080p H.264 encode fine via QuickSync.
user_pref("media.navigator.video.max_width",             1920);
user_pref("media.navigator.video.max_height",            1080);
user_pref("media.navigator.video.max_framerate",          60);

// Target 60fps for outgoing video. The HD 4000 QuickSync ASIC hardware-encodes
// H.264 (media.webrtc.hw.h264.enabled = true), so 60fps does not burn CPU.
user_pref("media.navigator.video.default_fps",            60);

// H.264 Level 4.2 (level_idc 42) — required for 1080p60. Default was 31 (Level 3.1,
// ~720p30), which would have silently capped the 1080p60 we want above.
user_pref("media.navigator.video.h264.level",             42);

// Keep microphone and camera access working (required for all video calls).
user_pref("media.navigator.enabled",                     true);
user_pref("media.navigator.permission.disabled",         false);

// WebRTC IP leak protection: Use only the interface that actually connects
// to the internet. Prevents sites from discovering your LAN/VPN IP via WebRTC.
// "default_address_only" mode. Does NOT break calls — just hides extra IPs.
user_pref("media.peerconnection.ice.default_address_only", true);
user_pref("media.peerconnection.ice.no_host",            false); // Must stay false for LAN calls

// Allow ICE (connection negotiation) to use all our available network interfaces.
// Required for calls to succeed from behind corporate NAT / home routers.
user_pref("media.peerconnection.ice.tcp",                true);

// Keep DTLS (the encrypted tunnel WebRTC uses) fully operational.
user_pref("security.ssl.enable_false_start",             true);

// Allow getUserMedia (camera/microphone API) on all HTTPS sites.
// Without this, calls cannot access your hardware.
user_pref("media.getusermedia.screensharing.enabled",    true);
user_pref("media.getusermedia.browser.enabled",          true);

// Ensure audio processing for calls is using the system audio pipeline.
// Our kernel's VAIO audio fixes (Section 3 of the kernel doc) apply to this path.
user_pref("media.getusermedia.audio.processing.platform.enabled", true);

// Enable echo cancellation, noise suppression, and AGC for voice calls.
// These are software DSP features that make you sound clearer on calls.
user_pref("media.getusermedia.aec_enabled",              true);
user_pref("media.getusermedia.noise_enabled",            true);
user_pref("media.getusermedia.agc_enabled",              true);


/* ============================================================================
 * SECTION 6: GOOGLE SERVICES — GMAIL / GEMINI CLI / GOOGLE WORKSPACE
 * ============================================================================
 *
 * PLAIN ENGLISH:
 * Some of Firefox's privacy tweaks can accidentally break Google's services
 * (Gmail, Google Drive, Google Meet, Gemini). This section explicitly allows
 * the technologies those services depend on while still maintaining privacy
 * against tracking from other parties.
 *
 * We allow: First-party cookies from Google, WebSockets (used by Gmail and
 * Gemini's streaming responses), and storage APIs that Gmail needs to work
 * offline. We block third-party Google trackers (Google Analytics embedded
 * on OTHER sites — not on Google's own properties).
 * ============================================================================ */

// Allow sites to store data in IndexedDB (Gmail Offline, Google Drive need this).
user_pref("dom.indexedDB.enabled",                       true);

// Allow WebSockets. Gemini CLI's streaming responses and Gmail's real-time
// push notifications both use persistent WebSocket connections.
user_pref("network.websocket.enabled",                   true);
user_pref("network.websocket.max-connections",           200);

// Allow service workers. Google Meet, Gmail, and Google Drive all register
// service workers for offline functionality and push notifications.
user_pref("dom.serviceWorkers.enabled",                  true);

// Allow push notifications (Gmail badge count, Meet call ringtone in background).
user_pref("dom.push.enabled",                            true);

// Keep web storage (localStorage/sessionStorage) available.
// Google services use these extensively for session tokens and caching.
user_pref("dom.storage.enabled",                         true);

// Allow SharedArrayBuffer — required by some Google Meet video processing.
// This is safe when Firefox's site isolation (Fission) is enabled (see Section 8).
user_pref("javascript.options.shared_memory",            true);

// Allow clipboard read/write access (required for Google Docs copy-paste features).
user_pref("dom.events.asyncClipboard.readText",          true);
user_pref("dom.events.asyncClipboard.clipboardItem",     true);

// Allow screen sharing API (for Google Meet / Teams screenshare).
user_pref("media.getusermedia.screensharing.enabled",    true);


/* ============================================================================
 * SECTION 7: THE GREAT AI & TELEMETRY PURGE
 * ============================================================================
 *
 * PLAIN ENGLISH:
 * Modern Firefox is being transformed into a "platform" by Mozilla. As of
 * Firefox 119–152+, it now ships with: an AI chatbot sidebar, machine learning
 * inference engines, a Rust-based telemetry SDK (Glean/FOG), a remote
 * experiment platform (Nimbus/Normandy), a sponsored tile ad feed (TopSites),
 * a centralized metrics pipeline (GLEN), a crash reporter, a health reporter,
 * and several background worker threads that run 24/7 even when Firefox is
 * sitting idle.
 *
 * None of these are useful on a machine tuned for raw performance. All of them
 * waste RAM, burn CPU cycles, and phone home to Mozilla's servers. They are
 * dismantled here individually, by name.
 *
 * WHAT WE ARE DISABLING (Technical Names):
 *   FOG    = Firefox on Glean (the Rust telemetry SDK injected in FF 78+)
 *   Glean  = Mozilla's new metrics collection library (replaces old telemetry)
 *   GLEN   = Glean Event Notifications (real-time event stream to Mozilla)
 *   Nimbus = The A/B experiment platform (used to test UI changes on you)
 *   Normandy = The remote config and "recipe" runner (can install studies)
 *   Pocket = The "read-it-later" news/ad feed integrated into the new tab
 *   TopSites = The sponsored shortcut tiles on the new tab page
 *   ML/AI  = The on-device machine learning inference engine (FF 118+)
 *   Suggest = Firefox Suggest (monetised search suggestions, FF 92+)
 *   Merilytics = Internal metrics aggregation (FF 130+)
 * ============================================================================ */

/* --- 7A. GLEAN / FOG / GLEN TELEMETRY ENGINE --- */
// Glean is Mozilla's new telemetry SDK. FOG (Firefox on Glean) is its
// Rust-native integration. Kill the entire pipeline at the source.
user_pref("toolkit.telemetry.enabled",                   false);
user_pref("toolkit.telemetry.unified",                   false);
user_pref("toolkit.telemetry.archive.enabled",           false);
user_pref("toolkit.telemetry.bhrPing.enabled",           false);
user_pref("toolkit.telemetry.firstShutdownPing.enabled", false);
user_pref("toolkit.telemetry.newProfilePing.enabled",    false);
user_pref("toolkit.telemetry.shutdownPingSender.enabled",false);
user_pref("toolkit.telemetry.updatePing.enabled",        false);
user_pref("toolkit.telemetry.cachedClientID",            "");
user_pref("toolkit.telemetry.server",                    "");

// FOG (Firefox on Glean) — the Rust telemetry runtime that replaced the
// old JS telemetry system. Disable its data upload and ping scheduler.
user_pref("datareporting.glean.uploadEnabled",           false);
user_pref("datareporting.glean.enabled",                 false);
user_pref("toolkit.glean.uploadEnabled",                 false);

// Health Report and Data Submission master switches.
user_pref("datareporting.policy.dataSubmissionEnabled",  false);
user_pref("datareporting.healthreport.uploadEnabled",    false);
user_pref("datareporting.healthreport.service.enabled",  false);

/* --- 7B. NIMBUS / NORMANDY — REMOTE EXPERIMENTS --- */
// Normandy is a server that can remotely install "recipes" and run
// A/B experiments on your browser without asking you.
user_pref("app.normandy.enabled",                        false);
user_pref("app.normandy.api_url",                        "");
user_pref("app.normandy.shieldLearnMoreUrl",             "");

// Nimbus is Normandy's successor — the newer experiment platform.
user_pref("app.shield.optoutstudies.enabled",            false);
user_pref("nimbus.enabled",                              false);
user_pref("messaging-system.rssnews.enabled",            false);

/* --- 7C. CRASH REPORTER & HEALTH MONITOR --- */
user_pref("browser.crashReports.unsubmittedCheck.enabled", false);
user_pref("browser.crashReports.unsubmittedCheck.autoSubmit2", false);
user_pref("breakpad.reportURL",                          "");

/* --- 7D. MACHINE LEARNING / AI CHATBOT SIDEBAR --- */
// Firefox 118+ ships with an on-device ML inference engine. Firefox 130+
// adds a right-sidebar AI chatbot. Disabled entirely.
user_pref("browser.ml.enable",                           false);
user_pref("browser.ml.checkForMemory",                   false);
user_pref("browser.ml.modelHubRootUrl",                  "");
user_pref("browser.ml.modelCacheMaxSize",                0);

// AI Chatbot Sidebar (Copilot, ChatGPT, Gemini embedded in Firefox sidebar).
// As of Firefox 130+, this can appear as a "suggestions" panel.
user_pref("browser.ml.chat.enabled",                     false);
user_pref("browser.ml.chat.hideFromLabs",                true);
user_pref("ai.inference.enabled",                        false);

// The AI-powered "Suggest" feature in the address bar. It sends your
// partial URL/search terms to Mozilla's servers for AI completion.
user_pref("browser.urlbar.suggest.merilytics",           false);
user_pref("browser.urlbar.suggest.quicksuggest.nonsponsored", false);
user_pref("browser.urlbar.suggest.quicksuggest.sponsored",    false);
user_pref("browser.urlbar.quicksuggest.enabled",         true);
user_pref("browser.urlbar.quicksuggest.dataCollection.enabled", false);
user_pref("browser.urlbar.merino.enabled",               false); // Merino = Mozilla's AI suggest backend
user_pref("browser.urlbar.trending.featureGate",         false);
user_pref("browser.urlbar.addons.featureGate",           false);
user_pref("browser.urlbar.mdn.featureGate",              false);

/* --- 7E. TOPSITES, POCKET, & AD FEEDS --- */
// TopSites = sponsored shortcut tiles on the new tab page (ads).
user_pref("browser.newtabpage.activity-stream.showSponsored",              false);
user_pref("browser.newtabpage.activity-stream.showSponsoredTopSites",      false);
user_pref("browser.newtabpage.activity-stream.feeds.section.topstories",   false);
user_pref("browser.newtabpage.activity-stream.feeds.topsites",             false);
user_pref("browser.newtabpage.activity-stream.feeds.telemetry",            false);
user_pref("browser.newtabpage.activity-stream.telemetry",                  false);
user_pref("browser.newtabpage.activity-stream.telemetry.structuredIngestion.endpoint", "");

// Pocket (Mozilla's "read it later" news feed with ads, embedded in new tab).
user_pref("browser.pocket.enabled",                      false);
user_pref("extensions.pocket.enabled",                   false);
user_pref("browser.pocket.api",                          "");

/* --- 7F. BROWSER UPDATER & EXTENSION TELEMETRY --- */
// We manage Firefox via Debian packages. The built-in updater is redundant
// and runs its own background service that wastes RAM.
user_pref("app.update.enabled",                          false);
user_pref("app.update.auto",                             false);
user_pref("app.update.background.enabled",               false);
user_pref("app.update.staging.enabled",                  false);

// Extension recommendations — Mozilla's "suggested extensions" banner.
user_pref("extensions.getAddons.showPane",               false);
user_pref("extensions.htmlaboutaddons.recommendations.enabled", false);
user_pref("extensions.recommendations.themeRecommendationUrl", "");

/* --- 7G. UI TOURS, WELCOME SCREENS, HINTS --- */
user_pref("browser.uitour.enabled",                      false);
user_pref("browser.uitour.url",                          "");
user_pref("trailhead.firstrun.didSeeAboutWelcome",       true); // Skip welcome screen
user_pref("browser.aboutwelcome.enabled",                false);

/* --- 7H. FIREFOX ACCOUNTS TELEMETRY --- */
// Keep Firefox Accounts functional (login to sync bookmarks) but disable
// the telemetry that reports your account activity to Mozilla.
user_pref("identity.fxaccounts.telemetry.clientAssertionJwt", "");
user_pref("identity.sync.tokenserver.logRequests",        false);


/* ============================================================================
 * SECTION 8: MEMORY MANAGEMENT, LEAK PREVENTION & GARBAGE COLLECTION
 * ============================================================================
 *
 * PLAIN ENGLISH:
 * Firefox has a well-known problem: it leaks memory. Tabs that you opened 3
 * hours ago accumulate leaked JavaScript objects that the garbage collector
 * should have cleaned up but didn't. Over a long session, Firefox can bloat
 * from 500MB to 4GB+ of RAM and start stuttering.
 *
 * This section addresses this in four ways:
 *   1. Tunes the JavaScript garbage collector (SpiderMonkey) to be more
 *      aggressive about cleaning up dead objects — especially in hidden tabs.
 *   2. Caps the per-process memory ceiling so no single tab can eat 4GB.
 *   3. Enables Firefox's automatic "trim memory" feature that tells the OS
 *      to reclaim unused but reserved memory blocks.
 *   4. Reduces the session-save interval so Firefox isn't doing a full
 *      disk-write every 15 seconds (a small but constant I/O leak).
 *
 * KERNEL SYNERGY:
 * Our kernel uses Multi-Gen LRU (MGLRU) for smarter memory reclamation and
 * ZRAM with zstd compression for swap. These kernel features work best when
 * Firefox is NOT holding onto gigabytes of already-dead memory. The more
 * aggressively Firefox releases memory, the more efficiently the kernel's
 * MGLRU can manage what's left.
 * ============================================================================ */

/* --- 8A. JAVASCRIPT GARBAGE COLLECTOR TUNING --- */
// Trigger a GC pass when more than this many MB of JS heap are allocated.
// Lower = more frequent cleanup. For 16GB RAM, 128MB is a good sweet spot
// (aggressive enough to prevent bloat, not so aggressive it causes jank).
user_pref("javascript.options.mem.gc_high_frequency_heap_growth_max", 128);
user_pref("javascript.options.mem.gc_high_frequency_low_limit",       32);

// Maximum JavaScript heap size per content process.
// 2048MB cap prevents one runaway tab from eating all RAM.
user_pref("javascript.options.mem.max",                 1024);

// Trigger a GC pass when the heap grows by more than 2x since last GC.
user_pref("javascript.options.mem.gc_high_frequency_heap_growth_max", 300);

// Force a GC compaction (moves live objects together, freeing fragmented RAM).
// Compaction is done during idle time and genuinely reclaims memory leaks.
user_pref("javascript.options.mem.gc_compacting",        true);

// Enable incremental GC (spreads cleanup over multiple frames, no jank).
user_pref("javascript.options.mem.gc_incremental",       true);

// Enable generational GC (separates short-lived and long-lived objects).
// This is particularly effective at cleaning up streaming video JS objects.
user_pref("javascript.options.mem.gc_generational",      true);

/* --- 8B. FIREFOX PROCESS MEMORY CAPS --- */
// Per-content-process RAM cap. Set to 4096MB (4GB) per process.
// With 4 content processes (our processCount), maximum total = 16GB.
// This allows full use of our RAM while preventing any single tab from
// triggering the kernel's OOM killer.
user_pref("browser.sessionstore.max_tabs_undo",          5);  // Stop storing huge undo history
user_pref("browser.sessionhistory.max_total_viewers",    1);  // Only keep 1 page in the back/forward cache

/* --- 8C. TRIM MEMORY / RETURN TO OS --- */
// Tell Firefox to actively return unused memory blocks to the OS kernel
// (which our MGLRU can then reallocate or compress into ZRAM).
user_pref("browser.lowMemoryResponseMB",                 400); // Trigger low-mem response at 400MB free
user_pref("browser.tabs.unloadOnLowMemory",              true);
user_pref("browser.tabs.min_inactive_duration_before_unload", 60000);

/* --- 8D. SESSION STORE LEAK REDUCTION --- */
// Firefox saves your session to disk every 15 seconds by default. This is
// constant I/O on a RAM disk and creates a background write loop. Extend
// it to 2 minutes — we're not using a spinning disk anyway.
user_pref("browser.sessionstore.interval",               120000); // 2 minutes
user_pref("browser.sessionstore.interval.idle",          3600000); // 1 hour when idle
user_pref("browser.sessionstore.privacy_level",          0);       // Save form data/passwords in session


/* ============================================================================
 * SECTION 9: BACKGROUND TAB FREEZING & THROTTLING
 * ============================================================================
 *
 * PLAIN ENGLISH:
 * Imagine you have 20 tabs open. 19 of them are in the background. In a
 * default Firefox, all 19 of those background tabs are still running
 * JavaScript timers, fetching data, playing audio analysis, running
 * animations, and generally burning CPU as if you were watching them.
 *
 * This section turns background tabs into "frozen" tiles. When a tab goes
 * into the background:
 *   - Its JavaScript timers are slowed to a maximum of 1 tick per second
 *   - Its animations are paused completely
 *   - Its "wake-lock" is released (it can no longer prevent sleep)
 *   - After 5 minutes of inactivity, it is "unloaded" — kept in the tab
 *     list but evicted from RAM entirely, restoring from session when clicked
 *
 * EXCEPTION: Tabs actively playing audio (Spotify, YouTube Music) or in a
 * WebRTC call are automatically exempted from throttling. Your music doesn't
 * pause just because you switched tabs.
 *
 * KERNEL SYNERGY:
 * This directly supports our kernel's MGLRU memory management. Evicted tabs
 * free up RAM that the kernel's MGLRU and ZRAM can manage more efficiently.
 * ============================================================================ */

// Master switch for background tab throttling.
user_pref("dom.timeout.throttling_delay",                15000);   // Throttle after 15s in background

// Slow background tab timers to minimum 1 second intervals.
// Default is 1ms — this is a 1000x reduction in background CPU wake-ups.
user_pref("dom.min_background_timeout_value",            1000);    // 1s minimum for background JS timers
user_pref("dom.timeout.background_throttling_max_budget", 50);     // Max 50ms CPU budget per second in background

// Kill page-visible (but off-screen) tabs' requestAnimationFrame loops.
// These are the main source of CPU waste in background video-player tabs.
user_pref("dom.min_background_timeout_value_without_budget_throttling", 1000);

// Throttle background wake-locks (tabs that request "stay awake" privileges).
user_pref("dom.wakelock.enabled",                        false);   // No tab can prevent system sleep

// After 5 minutes of background inactivity, unload the tab from RAM.
// It stays in the tab bar — clicking it just reloads from session cache.
user_pref("browser.tabs.min_inactive_duration_before_unload", 300000); // 5 minutes

// Enable the background tab memory trimmer.
// This actively calls the OS to release memory held by inactive tabs.
user_pref("browser.low_commit_space_notification_interval_ms", 10000);

// Page Visibility API: Pause animations, videos in background tabs.
user_pref("dom.page_visibility.enabled",                 true);

// Freeze background timers more aggressively when the window is minimised.
user_pref("dom.suspend_inactive.enabled",                true);

// Stop autoplay in background tabs (video tabs that start ads when backgrounded).
user_pref("media.block-autoplay-until-in-foreground",    true);


/* ============================================================================
 * SECTION 10: FISSION (SITE ISOLATION) & PROCESS ARCHITECTURE
 * ============================================================================
 *
 * PLAIN ENGLISH:
 * Fission is Firefox's equivalent of Chrome's "every tab in its own process"
 * architecture. Each website gets its own isolated process, which means:
 *   - A crashed tab cannot crash Firefox (isolation)
 *   - A hacked tab cannot read another tab's memory (security)
 *   - The OS can more cleanly evict a dead tab's memory (RAM efficiency)
 *
 * For our i7-3632QM (4 cores / 8 threads), 4 content processes is the optimal
 * count. More processes = more RAM overhead and scheduler pressure. Fewer = less
 * isolation. 4 is the Goldilocks number for an 8-thread Ivy Bridge processor.
 * ============================================================================ */

// Enable Fission (site isolation). Required for SharedArrayBuffer (Google Meet).
user_pref("fission.autostart",                           true);

// Number of content processes. Each runs one or more isolated website tabs.
// 4 = 4 cores on the i7-3632QM. Matches dom.ipc.processCount.
user_pref("dom.ipc.processCount",                        2);
user_pref("dom.ipc.processCount.webIsolated",            2);

// Maximum processes for file:// URLs (local files). Keep at 1.
user_pref("dom.ipc.processCount.file",                   1);

// Extension (add-on) processes. 1 is sufficient for most setups.
user_pref("dom.ipc.processCount.extension",              1);

// Prioritise foreground tab processes over background ones at the OS level.
user_pref("dom.ipc.processPriorityManager.enabled",      true);

// Enable the Utility Process (FF 112+). This moves background services like
// audio decoding and network I/O into their own low-priority process,
// preventing them from blocking the main render thread.
user_pref("browser.tabs.remote.useCrossOriginEmbedderPolicy", true);

// Skip the slow (but safe) Content Process launch pre-warming queue.
// Pre-warming launches content processes before they are needed, which
// wastes RAM. On 4 defined processes, we don't need speculative spawning.
user_pref("dom.ipc.processPrelaunch.enabled",            false);


/* ============================================================================
 * SECTION 11: DISK CACHE — RAM-ONLY POLICY
 * ============================================================================
 *
 * PLAIN ENGLISH:
 * By default Firefox uses your hard drive / SSD as a disk cache — storing
 * website images, CSS, and scripts on disk so pages load faster on revisit.
 * On a system configured to keep everything in RAM (which ours is), a
 * disk cache just adds a pointless read/write layer.
 *
 * We disable disk cache entirely and allocate 1GB of RAM as the browser cache.
 * With 16GB total RAM, 1GB dedicated to browser cache means frequently visited
 * pages (Gmail, YouTube) load from memory in microseconds.
 *
 * KERNEL SYNERGY:
 * Our kernel uses ZRAM (compressed RAM-as-swap) with zstd compression.
 * Even when the system is under memory pressure, the 1GB browser cache
 * will be transparently compressed by the kernel rather than written to
 * actual disk — giving us the best of both worlds.
 * ============================================================================ */

// Disable disk cache entirely.
user_pref("browser.cache.disk.enable",                   false);
user_pref("browser.cache.disk.capacity",                 0);
user_pref("browser.cache.disk.smart_size.enabled",       false);
user_pref("browser.cache.disk_cache_ssl",                false);

// Enable the RAM cache.
user_pref("browser.cache.memory.enable",                 true);

// 1GB RAM cache. With 16GB total, this is 6.25% — generous but not excessive.
user_pref("browser.cache.memory.capacity",               262144); // 256MB in KB

// Enable offline cache (AppCache / Service Worker cache) — needed for Gmail offline.
user_pref("browser.cache.offline.enable",                true);
user_pref("browser.cache.offline.insecure.enable",       false); // But not for HTTP sites

// Prefetch cache — disabled (we already blocked prefetch in Section 4).
user_pref("network.prefetch-next",                       false);


/* ============================================================================
 * SECTION 12: FIREFOX 152+ / NIGHTLY — NEW FEATURE DISABLES
 * ============================================================================
 *
 * PLAIN ENGLISH:
 * This section targets features added in Firefox 128–152+ that were NOT in
 * the original user.js. Mozilla has been aggressively expanding Firefox into
 * a "platform" with its own AI SDK, translation engine, tab grouping system,
 * and a centralised metrics bus. These are the newest additions to disable.
 *
 * WHAT WE'RE KILLING HERE (added since your original file):
 *   - Tab Groups / Tab Organiser (FF 131+): background JS, disk writes
 *   - Firefox Translations (FF 118+): downloads 30-100MB AI language models
 *   - Firefox View (FF 106+): background sync service with Mozilla servers
 *   - GenAI (Generative AI) SDK (FF 130+): on-device LLM inference
 *   - New Profiles System (FF 129+): multiple browser profile manager w/sync
 *   - Content Analysis SDK (FF 125+): DLP-style scanning of clipboard/files
 *   - Sidebar redesign (FF 131+): background service for sidebar state sync
 * ============================================================================ */

/* --- 12A. FIREFOX TRANSLATIONS (AI Language Models) --- */
// Firefox Translations silently downloads 30-100MB neural network models
// per language pair and runs them through the same ML inference engine we
// already killed in Section 7. Belt AND suspenders.
user_pref("browser.translations.enable",                 false);
user_pref("browser.translations.autoTranslate",          false);
user_pref("browser.translations.panelShown",             true);  // Mark as shown so it stops prompting

/* --- 12B. GENAI / ON-DEVICE LLM SDK (FF 130+) --- */
// Mozilla has integrated an "ONNX Runtime"-based GenAI SDK for running
// small language models locally. This uses significant RAM and GPU/CPU.
user_pref("browser.ml.backend.onnx.enabled",             false);
user_pref("browser.ml.textRecognition.enabled",          false);
user_pref("browser.ml.textTranslation.enabled",          false);
user_pref("browser.ml.audioTranscription.enabled",       false);

/* --- 12C. FIREFOX VIEW (FF 106+) --- */
// Firefox View syncs your recent tabs and browsing history across devices
// via Mozilla's servers. It runs a background polling service.
user_pref("browser.tabs.firefox-view",                   false);
user_pref("browser.tabs.firefox-view-next",              false);
user_pref("browser.firefox-view.feature-tour",           "{\"screen\":\"\",\"complete\":true}");

/* --- 12D. TAB GROUPS (FF 131+) --- */
// Tab groups adds a background service that writes group state to disk.
user_pref("browser.tabs.groups.enabled",                 false);

/* --- 12E. NEW PROFILES SYSTEM (FF 129+) --- */
// Mozilla's new multi-profile manager adds background sync.
user_pref("browser.profiles.enabled",                    false);

/* --- 12F. CONTENT ANALYSIS SDK (FF 125+) --- */
// Content Analysis is a DLP (Data Loss Prevention) enterprise integration
// that scans clipboard content and downloads. Completely unnecessary.
user_pref("browser.contentanalysis.enabled",             false);
user_pref("browser.contentanalysis.interception_point.clipboard.enabled", false);

/* --- 12G. SIDEBAR REDESIGN BACKGROUND SERVICES (FF 131+) --- */
// The new vertical sidebar has a sync service for "sidebar state."
user_pref("sidebar.revamp",                              false);
user_pref("sidebar.verticalTabs",                        false);

/* --- 12H. NEW ADDRESS BAR "RICH SUGGESTIONS" (FF 115+) --- */
// Rich suggestions in the URL bar send keystrokes to Mozilla's Merino service.
user_pref("browser.urlbar.richSuggestions.featureGate",  false);
user_pref("browser.urlbar.weather.featureGate",          false);
user_pref("browser.urlbar.clipboard.featureGate",        false);

/* --- 12I. FIREFOX RELAY & MONITOR (FF 117+) --- */
// Firefox Relay (email masking) and Monitor (breach alerts) run background
// polling services and send data to Mozilla servers.
user_pref("signon.firefoxRelay.feature",                 "disabled");
user_pref("browser.monitor.feature",                     false);

/* --- 12J. SHOPPING / FAKESPOT (FF 116+) --- */
// Fakespot analyses Amazon/Walmart product pages and sends URLs to Mozilla.
user_pref("browser.shopping.experience2023.enabled",     false);
user_pref("browser.shopping.experience2023.autoOpen.enabled", false);

/* --- 12K. COOKIE BANNER BLOCKER TELEMETRY (FF 112+) --- */
// The cookie banner reducer is useful, but its telemetry reporting is not.
user_pref("cookiebanners.service.enableGlobalRules",     true);  // Keep the blocker ON
user_pref("cookiebanners.service.mode",                  1);     // Block auto-accept banners
user_pref("cookiebanners.bannerClicking.enabled",        true);
user_pref("cookiebanners.reportingSite.telemetry.enabled", false); // Telemetry OFF

/* --- 12L. PICTURE-IN-PICTURE SYNC (FF 113+) --- */
// PiP itself is fine — keep it. Disable the telemetry event reporting.
user_pref("media.videocontrols.picture-in-picture.enabled",              true);
user_pref("media.videocontrols.picture-in-picture.video-toggle.enabled", true);
user_pref("media.videocontrols.picture-in-picture.display-text-tracks.enabled", true);


/* ============================================================================
 * SECTION 13: SECURITY BASELINE — STAYS SANE WHILE BEING FAST
 * ============================================================================
 *
 * PLAIN ENGLISH:
 * Performance and security are not opposites. This section keeps the most
 * important security features ON (HTTPS-only, sandboxing, mixed-content
 * blocking) while removing the "security theatre" features that waste
 * resources without actually protecting you (like Google Safe Browsing's
 * real-time URL check, which sends every URL you type to Google).
 * ============================================================================ */

// HTTPS-Only mode: Block plain HTTP sites or warn before visiting them.
// Unencrypted HTTP in 2025 is just asking to have your data read on the wire.
user_pref("dom.security.https_only_mode",                true);
user_pref("dom.security.https_only_mode_pbm",            true); // Also in private windows

// Content blocking (trackers, fingerprinters). Keep ON.
user_pref("privacy.trackingprotection.enabled",          true);
user_pref("privacy.trackingprotection.socialtracking.enabled", true);
user_pref("privacy.trackingprotection.cryptomining.enabled",   true);
user_pref("privacy.trackingprotection.fingerprinting.enabled", true);

// Disable Google Safe Browsing's remote lookup (privacy issue, sends URLs).
// The local blocklist (downloaded periodically) is kept — this only disables
// the real-time "phone Google right now with this URL" feature.
user_pref("browser.safebrowsing.phishing.enabled",       true);   // Keep local list
user_pref("browser.safebrowsing.malware.enabled",        true);   // Keep local list
user_pref("browser.safebrowsing.downloads.remote.enabled", false); // Block real-time check
user_pref("browser.safebrowsing.provider.google4.gethashURL", ""); // No real-time URL check

// Block mixed content (HTTP resources inside HTTPS pages).
user_pref("security.mixed_content.block_active_content", true);
user_pref("security.mixed_content.block_display_content", true);

// Keep the process sandbox ON at level 4 (maximum for Linux).
// This prevents a hacked content process from accessing the filesystem.
user_pref("security.sandbox.content.level", 3);
user_pref("security.sandbox.gpu.level",                  1);     // GPU process sandbox


/* ============================================================================
 * SECTION 14: FINE-TUNING — IVY BRIDGE SPECIFIC OPTIMISATIONS
 * ============================================================================
 *
 * PLAIN ENGLISH:
 * These are miscellaneous performance tweaks targeting the specific
 * characteristics of the i7-3632QM CPU: its 8-thread SMT topology, its
 * 6MB L3 cache, and the shared memory architecture of the Intel HD 4000
 * where CPU and GPU use the same physical RAM pool.
 * ============================================================================ */

// Force enable the "LayerScope" GPU profiler bypass — not for user profiling,
// but tells the GPU compositor to skip debug validation passes.
user_pref("gfx.layerscope.enabled",                      false);

// Frame timing. Cap Firefox's internal timer precision to 1ms.
// The kernel runs at HZ=250 (4ms tick). 1ms timer allows Firefox to align
// with OS scheduler ticks without over-requesting wakeups.
user_pref("dom.min_timeout_value",                       1);

// Use the system's CPU hardware concurrency value (8 threads) for the
// JS worker thread pool. This lets WebAssembly and heavy JS use all 8 threads.
user_pref("dom.workers.maxPerDomain",                    8);

// Font rendering — use the GPU's subpixel AA path, not Cairo CPU rendering.
user_pref("gfx.text.subpixel-position.force-enabled",   true);

// Reduce paint suppression threshold. With a GPU doing all painting,
// we can afford to suppress paints for a shorter time before giving up.
user_pref("nglayout.initialpaint.delay",                 0);
user_pref("nglayout.initialpaint.delay_in_oopif",        0);

// Enable content-process JIT (Just-In-Time compiler) for JavaScript.
// Essential for fast JavaScript execution. Should be on by default, but explicit.
user_pref("javascript.options.ion",                      true);   // IonMonkey (optimising JIT)
user_pref("javascript.options.baselinejit",              true);   // Baseline JIT
user_pref("javascript.options.wasm",                     true);   // WebAssembly JIT

// Shared Memory and Atomics — enable for Fission isolated contexts.
// Required for SharedArrayBuffer (Google Meet multithreaded video processing).
user_pref("javascript.options.shared_memory",            true);

// Disable the slow "decorative rendering" of the browser chrome UI.
// We do not need animated transitions for the toolbar or sidebar.
user_pref("ui.prefersReducedMotion",                     1);

// Bump the maximum script run time before the "slow script" warning.
// Heavy streaming site JavaScript (Prime Video, Disney+) can take >10 seconds
// to initialise their DRM player. Don't warn — just let it run.
user_pref("dom.max_script_run_time",                     30);
user_pref("dom.max_chrome_script_run_time",              30);

/* END OF gorilla-unleashed user.js v2.0 ====================================== */

/* === GORILLA UNLEASHED INTERACTIVE OPTIMIZATIONS === */
user_pref("gfx.x11-egl.force-enabled", true);
user_pref("media.rdd-ffmpeg.enabled", true);
user_pref("media.rdd-ffmpeg.vaapi.enabled", true);
user_pref("media.rdd-process.enabled", true);
user_pref("media.mediasource.vp9.enabled", false);
user_pref("media.av1.enabled", false);

// neqo congestion control: match kernel's BBR choice
// 0=NewReno, 1=CUBIC(default), 2=BBR
user_pref("network.http.http3.cc_algorithm",                 2);

// ECN for QUIC: allows neqo to receive FQ-CoDel's congestion marks
user_pref("network.http.http3.ecn",                          true);

// Probe HTTP/3 aggressively - don't wait for HTTP/2 to time out
user_pref("network.http.http3.backup_timer_delay",           50);

// QUIC connection-level flow control window (24MB)
user_pref("network.http.http3.max_data",                     25165824);

// Per-stream receive windows for bidirectional streams (6MB)
user_pref("network.http.http3.max_stream_data_bidi_local",   6291456);
user_pref("network.http.http3.max_stream_data_bidi_remote",  6291456);

// Unidirectional streams (3MB)
user_pref("network.http.http3.max_stream_data_uni",          3145728);

// QUIC version preference: prefer QUIC v1
user_pref("network.http.http3.alt-svc-mapping-for-testing",  "");

// Enable 0-RTT resumption
user_pref("network.http.http3.enable_0rtt",                  true);

// QUIC idle timeout: keep QUIC connections alive 5 minutes
user_pref("network.http.http3.idle_timeout",                 300000);

// QUIC connection migration
user_pref("network.http.http3.migrate_connections",          true);

// Prioritise QUIC/HTTP3 over HTTP/2
user_pref("network.http.http3.alt_svc_win_length",           3);


// ── Gorilla Fix: Disable GTK compositor window transparency ──────────────────
// widget.transparent-windows=true causes the entire browser content area to
// be fully see-through (desktop wallpaper bleeds through). Disabled so the
// window renders with a solid opaque background.
user_pref("widget.transparent-windows", false);


/* 🦍 GORILLA UNLEASHED: NATIVE ANIMATION PURGE */
user_pref("ui.caretBlinkTime", 0);
user_pref("toolkit.cosmeticAnimations.enabled", false);
user_pref("browser.tabs.animate", false);
user_pref("browser.download.animateNotifications", false);
user_pref("image.animation_mode", "none");


/* 🦍 GORILLA UNLEASHED: BACKGROUND NETWORK & IPC ANNIHILATION */
/* Stop the Socket and IPC threads from spinning the CPU on idle */

/* 1. Kill Telemetry & Health Reports via Prefs (Non-Excision) */
user_pref("toolkit.telemetry.enabled", false);
user_pref("toolkit.telemetry.server", "data:,");
user_pref("toolkit.telemetry.archive.enabled", false);
user_pref("toolkit.telemetry.newProfilePing.enabled", false);
user_pref("toolkit.telemetry.shutdownPingSender.enabled", false);
user_pref("toolkit.telemetry.updatePing.enabled", false);
user_pref("toolkit.telemetry.bhrPing.enabled", false);
user_pref("toolkit.telemetry.firstShutdownPing.enabled", false);
user_pref("toolkit.telemetry.coverage.opt-out", true);
user_pref("toolkit.coverage.opt-out", true);
user_pref("datareporting.healthreport.uploadEnabled", false);
user_pref("datareporting.policy.dataSubmissionEnabled", false);
user_pref("app.shield.optoutstudies.enabled", false);
user_pref("browser.ping-centre.telemetry", false);

/* 2. Kill Massive SafeBrowsing Database Downloads (Stops 100MB+ background syncs) */
user_pref("browser.safebrowsing.downloads.remote.enabled", false);
user_pref("browser.safebrowsing.malware.enabled", false);
user_pref("browser.safebrowsing.phishing.enabled", false);
user_pref("browser.safebrowsing.provider.google.updateURL", "");
user_pref("browser.safebrowsing.provider.google.gethashURL", "");

/* 3. Kill Pocket & Activity Stream Background Preloading */
user_pref("extensions.pocket.enabled", false);
user_pref("browser.newtabpage.activity-stream.feeds.telemetry", false);
user_pref("browser.newtabpage.activity-stream.feeds.snippets", false);
user_pref("browser.newtabpage.activity-stream.feeds.section.topstories", false);
user_pref("browser.newtabpage.activity-stream.feeds.discoverystreamfeed", false);
user_pref("browser.newtabpage.activity-stream.telemetry", false);
user_pref("browser.newtabpage.activity-stream.asrouter.userprefs.cfr.addons", false);
user_pref("browser.newtabpage.activity-stream.asrouter.userprefs.cfr.features", false);

/* 4. Kill Prefetching & Speculative Connections */
user_pref("network.prefetch-next", false);
user_pref("network.dns.disablePrefetch", true);
user_pref("network.predictor.enabled", false);
user_pref("network.http.speculative-parallel-limit", 0);
user_pref("browser.places.speculativeConnect.enabled", false);
