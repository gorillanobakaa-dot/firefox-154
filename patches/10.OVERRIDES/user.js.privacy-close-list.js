
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
