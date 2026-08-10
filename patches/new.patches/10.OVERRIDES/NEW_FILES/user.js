// Gorilla Unleashed — Wayland runtime overrides
// Keeps GPU process off on Wayland: the compositor widget in the GPU process
// has no wl_egl_window (GtkCompositorWidgetInitData carries no Wayland handle),
// so EGL surface creation fails and the window stays black.
// VA-API decode still works via the RDD process (media.rdd-ffmpeg.vaapi.enabled).
user_pref("layers.gpu-process.enabled", false);
user_pref("layers.gpu-process.force-enabled", false);
user_pref("media.gpu-process-decoder", false);

// gfx.x11-egl.force-enabled has no effect in a cairo-gtk3-wayland build
// (the #ifdef MOZ_X11 guard skips the entire InitX11EGLConfig body), but
// remove it to keep prefs clean and avoid confusion.
user_pref("gfx.x11-egl.force-enabled", false);

// ── VA-API hardware video decode (H.264 via i965 in RDD process) ──────────
// The Gorilla hardware-only policy (PDMFactory.cpp) rejects ALL video unless
// the decoder reports DecodeSupport::HardwareDecode. These prefs ensure VA-API
// is initialised in the RDD process and that H.264 never silently falls back
// to software decode (which the C++ policy would reject anyway).
// LIBVA_DRIVER_NAME=i965 must be set in /etc/environment (it is).
user_pref("media.ffmpeg.vaapi.enabled", true);
user_pref("media.ffmpeg.vaapi.decode.force-enabled", true);
user_pref("media.ffmpeg.vaapi-drm-display.enabled", true);

// ── VA-API surface zero-copy: bypass gfxInfo blocklist ────────────────────
// media.ffmpeg.vaapi.force-surface-zero-copy defaults to 2 (gfxInfo-controlled).
// State 1 skips the gfxInfo GetFeatureStatus call entirely, so FEATURE_ALLOW_ALWAYS
// vs FEATURE_STATUS_OK ambiguity cannot block zero-copy. Without this, gfxInfo
// returning anything other than FEATURE_ALLOW_ALWAYS sets mEnvironment=Blocklisted,
// and the Gorilla UserEnable() at gfxPlatformGtk.cpp:282 is overridden (UserEnable
// ranks below Environment). Belt-and-suspenders with the C++ UserForceEnable fix.
user_pref("media.ffmpeg.vaapi.force-surface-zero-copy", 1);

// ── WebRender native Wayland compositor (hardware overlay, low memory BW) ─
// gfx.webrender.compositor defaults to false on Linux, so CompositorType()
// returns DRAW instead of WAYLAND. Without native compositor, VA-API decoded
// NV12 DMABuf frames go through WebRender's full GL pipeline (YUV→RGB shader
// → RGBA framebuffer → Mutter reads), burning ~4× extra GPU memory bandwidth
// on UMA (Ivy Bridge). force-enabled bypasses the gfxInfo blocklist and
// activates the Wayland native compositor so VA-API NV12 surfaces are
// submitted directly as KMS hardware plane overlays, cutting IMC bandwidth
// from ~2500 MiB/s to ~500 MiB/s.
// Side-effect: UploadSWDecodeToDMABuf() also becomes true (GetWebRenderCompositorType()
// == WAYLAND) so if SW decode ever runs it also takes the zero-copy DMABuf path.
// GORILLA TEST 2026-08-09: disabled to A/B the page-ghosting/flicker artifacts.
// This forces WebRender's NATIVE compositor (NativeLayerRootWayland -> one
// wl_subsurface per layer, composited by Mutter). It defaults to FALSE on
// Linux. Revert by uncommenting if it turns out not to be the cause.
// user_pref("gfx.webrender.compositor.force-enabled", true);

// ── Codec policy: H.264-only ──────────────────────────────────────────────
// Belt-and-suspenders with the compiled-in Gorilla DecoderTraits patch that
// returns CANPLAY_NO for VP9/AV1/WebM. Setting these prefs also makes
// YouTube's isTypeSupported() calls return false at the JS level so YouTube
// negotiates H.264 MP4 without attempting any VP9/AV1 MSE SourceBuffer.
user_pref("media.av1.enabled", false);
user_pref("media.vp9.enabled", false);
user_pref("media.mediasource.vp9.enabled", false);

// GORILLA 2026-07-31: force prefers-color-scheme=dark product-wide. The theme
// is all-black; on a LIGHT GTK theme, in-content dark tokens gated behind
// @media (prefers-color-scheme: dark) never applied -> grey-on-black text in
// shadow components (checkbox labels, sync/home cards, search engine names).
user_pref("ui.systemUsesDarkTheme", 1);

// GORILLA 2026-07-31: about:telemetry showed "collecting pre-release data".
// Kill legacy Telemetry collection outright (the Glean side is already
// lobotomized at compile time — 13.TELEMETRY.KILL).
user_pref("toolkit.telemetry.enabled", false);
user_pref("toolkit.telemetry.unified", false);
user_pref("toolkit.telemetry.archive.enabled", false);
user_pref("datareporting.healthreport.uploadEnabled", false);
user_pref("datareporting.policy.dataSubmissionEnabled", false);

// ==========================================================================
// GORILLA privacy close-list (Column A) — 2026-08-01
// Pure surveillance/experiment doors closed after the forensic egress audit.
// ZERO functional cost; none touch DRM/WebAuthn/WebRTC/PKI/sandbox (the 5 pillars).
// Rationale + audit: patches/new.patches/14.EGRESS.LOCKDOWN/FORENSIC_AUDIT_AND_HARDENING_PLAN_2026-08-01.md
// Independent-transport doors (matter most): discovery (TAAR) + crash reporting.
// Belt-and-suspenders (glean core already dead): ping-centre, activity-stream.
// NOT changed on purpose: enterprise_roots (keep Mozilla independent root store;
//   enable reactively only if a corp/gov portal cert-fails), dom.push + geo
//   (permission-gated real-world features), RemoteSettings/update/captive-portal
//   (security + real-world, see the kept-door ledger).
// ==========================================================================
user_pref("browser.discovery.enabled", false);                        // TAAR addon-recommendation -> services.addons (independent transport)
user_pref("app.shield.optoutstudies.enabled", false);                 // Shield studies (belt over the Mozambique 60y timer)
user_pref("messaging-system.rsexperimentloader.enabled", false);      // Nimbus experiment loader (belt over Mozambique)
user_pref("browser.crashReports.unsubmittedCheck.enabled", false);    // stop unsubmitted-crash probe/nag
user_pref("browser.tabs.crashReporting.sendReport", false);           // tab-crash reports -> crash-stats.mozilla.org (independent transport)
user_pref("browser.ping-centre.telemetry", false);                    // Activity Stream ping-centre
user_pref("browser.newtabpage.activity-stream.telemetry", false);     // newtab telemetry
user_pref("browser.newtabpage.activity-stream.feeds.telemetry", false);// newtab feed telemetry
user_pref("toolkit.telemetry.coverage.opt-out", true);                // disable coverage-ping mechanism
user_pref("browser.attribution.enabled", false);                      // install/attribution reporting

// GORILLA 2026-08-10: kill the "Import your logins from Google Chrome" rows in
// the login autocomplete popup. Two reasons: (1) growth-nag, not a feature;
// (2) it is the popup-clipping bug — these rows are filled by ASYNC Fluent
// l10n, measure 0px/4px at adjustHeight() time, then inflate to 51px/38px
// under the already-locked 25px max-height. Traced live in the Browser
// Toolbox; see THEME_FIX_LOG §39.
user_pref("signon.showAutoCompleteImport", "");

// GORILLA 2026-08-10: kill the Firefox Relay email-mask upsell (same popup as
// the import nag — the "Get a free email mask" doorhanger on email fields).
// It is an ad for a Mozilla subscription service requiring a Mozilla account;
// the rebrand even renamed the ad to "Gorilla Unleashed Relay email mask".
// Gate check is FirefoxRelayUtils.relayIsAvailableOrEnabled(): any value
// outside available/offered/enabled disables integration entirely — no
// autocomplete rows, no doorhanger, no relay.firefox.com traffic.
user_pref("signon.firefoxRelay.feature", "disabled");
