# Forensic Audit & Hardening Plan — ff154 Privacy Posture

> **Date:** 2026-08-01 · **Author:** gorilla + agent · **Status:** PLAN (nothing changed yet)
> **Scope:** the whole privacy/egress posture of the live build — close surveillance,
> preserve real-world infrastructure, and fix the gaps the audit exposed.
> **Grounding:** every "current state" below is MEASURED (strace/tshark/perf/`/proc`/pref-grep,
> this session), not assumed. Instruments that don't work here (bpftrace/ftrace) are noted —
> the kernel is hardened without them by design (see [[Custom_Kernel_Has_No_eBPF_Ftrace_By_Design]]).

---

## 0. The Doctrine (three rules, non-negotiable)

1. **CLOSE** pure surveillance/experiment doors — telemetry, studies, addon-rec, coverage,
   crash auto-send. These have **zero functional cost**.
2. **PRESERVE & VERIFY** the five real-world infrastructure pillars. A privacy build that
   breaks Netflix, captive-portal wifi, YubiKeys, or gov-portal logins is not a privacy
   build — it's an abandoned one. Compromise is the point.
3. **DOCUMENT EVERY KEPT DOOR.** Each connection left open gets a one-line rationale in
   this file, so a future over-zealous agent does not "harden" the passkey daemon or the
   cert-revocation feed into oblivion thinking it found a leak. An undocumented kept-door
   is a bug waiting to be "fixed."

---

## 1. Measured Current State (2026-08-01)

### Telemetry / experiments — DEAD (confirmed 4 ways: source, threads, wire, perf)
No `incoming.telemetry`, `normandy`, `nimbus`, `glean`, `shield`, `ping-centre`, `contile`
on the wire in any capture (90s idle + 2 cold starts). FOG init skipped, glean dispatcher
thread never spawned (0 across 18 procs AND on a fresh profile), MemoryTelemetry/Glean
recording DCE'd. This part of the build holds.

### The five pillars — measured
| Pillar | State | Gap found |
|---|---|---|
| 1 Media/DRM/EME | `eme` default-on, `widevinecdm`+`gmpopenh264` enabled, VA-API drivers present (i965 for HD4000, iHD) | Widevine CDM not yet on disk (on-demand DL — fine) |
| 2 WebAuthn/FIDO2 | webauthn prefs default-on | **no pcscd daemon** (smartcard/PIV/CAC dead), **no /dev/tpm** (platform passkeys unavailable — 2011 hw), USB keys OK via hidraw |
| 3 WebRTC | peerconnection default-on | stock leak posture — verify mDNS host obfuscation |
| 4 PKI/Identity | OCSP/CRLite default, 151 system CAs in /etc/ssl/certs | **`security.enterprise_roots.enabled` default-false** → system/corp/gov CAs untrusted |
| 5 Sandbox | **HEALTHY** — content procs run `Seccomp:2` (seccomp-bpf active), kernel `CONFIG_SECCOMP_FILTER=y`, build sets `content.level=4`, Fission on, userns=62934 | none — the initial "level 1" alarm was a MEASUREMENT ERROR (grep caught an `#ifdef` branch; Seccomp checked on the parent, which is normally 0). RDD sandbox is the only intentional media compromise (see GAP-1). |

---

## 2. Column A — CLOSE (surveillance doors, no functional cost)

Deploy via `10.OVERRIDES/user.js` (runtime) AND `05.PREFS/firefox.js` (build default);
lock the ones that must never flip. None of these touch the five pillars.

| Pref | Set to | Why |
|---|---|---|
| `browser.discovery.enabled` | false | TAAR addon-recommendation → services.addons; pure profiling |
| `app.shield.optoutstudies.enabled` | false | Shield studies (belt on top of the Mozambique'd transport) |
| `messaging-system.rsexperimentloader.enabled` | false | Nimbus experiment loader (belt on top of the 60y timer) |
| `browser.crashReports.unsubmittedCheck.enabled` | false | stops the "unsubmitted crash" nag/probe |
| `browser.tabs.crashReporting.sendReport` | false | tab-crash reports → crash-stats.mozilla.org |
| `browser.ping-centre.telemetry` | false | Activity Stream ping-centre |
| `browser.newtabpage.activity-stream.telemetry` | false | newtab telemetry |
| `browser.newtabpage.activity-stream.feeds.telemetry` | false | newtab feed telemetry |
| `toolkit.telemetry.coverage.opt-out` | true | disables the coverage ping mechanism |
| `browser.attribution.enabled` | false | install/attribution reporting |

**Note on redundancy:** several of these (ping-centre, activity-stream) route through the
already-dead glean/FOG core — closing the pref is belt-and-suspenders, not the only line of
defense. Crash reporting and discovery are the ones with an **independent transport**, so
those matter most.

---

## 3. Column B — PRESERVE & VERIFY (the five pillars + kept-door rationale)

**KEEP OPEN — do not "harden" these:**
| Kept door | Pillar | Rationale (the anti-resurrection note) |
|---|---|---|
| `firefox.settings.services.mozilla.com` (RemoteSettings) | 4 PKI | carries OneCRL/CRLite **cert revocation** + intermediate preloading. Killing it silently degrades TLS trust. NOT telemetry. |
| `services.addons.mozilla.org` (blocklist) | 5/sec | malicious-addon blocklist. Security feed, keep. |
| `aus5.mozilla.org` (update) | sec | Firefox security updates. Keep (this is a daily driver). |
| `detectportal.firefox.com` | real-world | captive-portal detection — **without it, hotel/airport wifi login pages don't appear.** Keep. |
| EME / Widevine / OpenH264 / VA-API | 1 | Netflix/Disney+/YouTube HD + hw decode on HD4000. Keep all. |
| WebAuthn prefs + hidraw | 2 | passkeys / YubiKey. Keep. |
| peerconnection / STUN-TURN / codecs | 3 | Zoom/Teams/WhatsApp. Keep. |
| OCSP / CRLite / system CA path | 4 | cert validation. Keep. |
| Fission / content sandbox | 5 | site isolation. Keep AND repair (see §5). |

**JUDGMENT CALLS (real-world tradeoff — author decides, defaults shown):**
| Door | Kill? | Tradeoff |
|---|---|---|
| `location.services.mozilla.com` (`geo.provider.network.url`) | optional | kill → network geolocation degraded (maps/weather less precise); GPS/manual still work |
| `dom.push.enabled` | optional | kill → no Web Push notifications (some chat/PWA); NOT needed for WebAuthn |
| `security.enterprise_roots.enabled` | **enable?** | true → trusts the 151 system CAs (needed for corp/gov portals, pillar 4); also trusts whatever admin/malware put in the store. Recommend **true** for a real-world daily driver. |

---

## 4. GAPS FOUND (need action or an explicit accept-the-risk)

### GAP-1 — RETRACTED (was: "sandbox degraded to level 1"). NO GAP.
**CORRECTION 2026-08-01:** the "content.level=1 / no seccomp" alarm was a MEASUREMENT
ERROR and is withdrawn. Verified ground truth: every content process runs `Seccomp: 2`
(SECCOMP_MODE_FILTER — active seccomp-bpf), kernel has `CONFIG_SECCOMP=y` +
`CONFIG_SECCOMP_FILTER=y`, build sets `security.sandbox.content.level=4` (all.js:4167),
profile persists no override. The two mistakes: (1) the grep matched an `#ifdef` platform
branch (`=1`) in all.js, not the effective value; (2) Seccomp was read on the PARENT
(normally 0) instead of content processes. **Pillar #5 is intact.**

The ONLY intentional sandbox compromise for media is the RDD (data-decoder) process, via
`MOZ_DISABLE_RDD_SANDBOX=1` — documented in the brain (toolchain_preflight,
firefox_graphics_gpu_patches, GOLDEN_RULES "Layer 6") as the VA-API `/dev/dri` workaround.
It is NOT currently in the launcher, i.e. VA-API works WITH the RDD sandbox intact (via the
/dev/dri allowance); the env var is a documented FALLBACK only. Correct, intentional,
KEEP-as-is. Kernel note: the build strips observability (eBPF/ftrace/kprobes) but KEEPS
enforcement (seccomp) — a deliberate split, not crude slimming.

### GAP-2 — WebAuthn system side incomplete (pillar 2)
No `pcscd`, no TPM. USB security keys work; smartcard/PIV/CAC and platform passkeys don't.
- **If smartcard/gov-portal auth is wanted:** `apt install pcscd libccid` + enable the service.
- **TPM:** hardware limit on the 2011 VAIO — document as a known unavailable capability.

### GAP-3 — Enterprise/system CAs not trusted (pillar 4)
`enterprise_roots.enabled=false` → the 151 system CAs are ignored. Corp/gov portals using
system-store certs will fail. See §3 judgment call.

### GAP-4 — Residual telemetry "buzz" (perf-measured)
Unguarded glean metric types (labeled counters, dual-labeled counters, `RecordPowerMetrics`,
legacy `AccumulateTelemetryCallback`) + the FFI entry points of the guarded distributions
still execute (guard sits post-FFI). Small (0.06–0.17%/symbol, idle window) but real on
2–4 GB targets. This is the true scope of "item 14" — see §6 Phase 4.

---

## 5. Phased Execution Plan (steps · techniques · instruments)

### Phase 0 — Baseline & functional-verify the pillars (BEFORE any change)
- Media: load a DRM test (bitmovin EME test page / a Netflix trailer), confirm playback +
  `about:support` shows Widevine active + VA-API in use (`about:support` GPU + `intel_gpu_top`).
- WebAuthn: webauthn.io round-trip with a USB key (if available).
- WebRTC: browserleaks.com/webrtc — confirm it works AND note whether local IP leaks
  (verify `media.peerconnection.ice.obfuscate_host_addresses`=true).
- PKI: visit an OCSP/CRLite-covered site; if a gov/corp portal is in scope, test it.
- Sandbox: `cat /proc/<content-pid>/status | grep Seccomp`; `zgrep CONFIG_SECCOMP /boot/config-$(uname -r)`.
- **Instruments:** functional web tests + `/proc` + `about:support` + `about:webrtc`.
- **Output:** a "pillars-green" baseline so any later breakage is attributable.

### Phase 1 — Deploy Column A (surveillance close-list)
- Write the §2 prefs into `10.OVERRIDES/user.js` + `05.PREFS/firefox.js`.
- Restart; re-run the egress audit (90s idle + cold start).
- **Techniques:** `tshark` DNS+SNI capture, `strace -f -e trace=connect` on a cold start.
- **Pass criteria:** no new breakage in Phase-0 tests; discovery/crash/coverage endpoints
  absent from a cold-start capture; the five pillars still green.

### Phase 2 — Resolve the judgment doors (§3)
- Author decides location/push/enterprise_roots. Apply, re-verify affected pillar.

### Phase 3 — Sandbox (GAP-1 RETRACTED — verification only)
- No repair needed: sandbox verified healthy (content procs `Seccomp:2`, level 4, kernel
  CONFIG_SECCOMP_FILTER=y). Optional belt check: `about:support` → "Effective Content
  Process Sandbox Level" should read 4.
- Leave the RDD `/dev/dri` allowance + the `MOZ_DISABLE_RDD_SANDBOX` fallback exactly as
  documented (pillar-1 media compromise). Do NOT "harden" the RDD sandbox — it breaks VA-API.

### Phase 4 — Source-level residual telemetry (GAP-4 / "item 14")
- Extend the `GORILLA_TELEMETRY_OFF`/gate pattern to the **unguarded metric types**
  (labeled/dual-labeled counters, power metrics) and, where cheap, short-circuit the FFI
  entry points — NOT just the two distributions already done.
- **Technique:** `perf record` before/after to prove the buzz dropped; `strings libxul`
  for metric-string elimination. Follow the soft-gate doctrine ([[Soft_Gate_Not_Excision_Doctrine]]).
- **Scope reminder:** measured 689 `glean::` sites / 65 netwerk files / 6 gated — pick the
  hot ones (Socket Thread counters) first; the core channel files rebase-churn, so weigh cost.

### Phase 5 — Document & preserve
- Dual-track write-up of the whole audit into this topic; DB atoms for each finding
  (sandbox gap, residual doors, connectivity layer, kept-door doctrine).
- Refresh the REPAIRS snapshot with any changed pref files.
- Update `THEME_FIX_LOG`/`PATCH.READINESS` and the memory tier.

---

## 6. Verification Harness (prove no pillar broke)
A single re-runnable script that, after any change, checks: DRM playback flag, WebAuthn
availability, WebRTC connectivity, a TLS handshake to an OCSP site, content-proc Seccomp,
and a fresh egress capture. Green across all = safe to snapshot. This is the regression
gate for every future telemetry/privacy edit.

---

## 7. What Stays Open, Forever, On Purpose (the kept-door ledger)
RemoteSettings (revocation), addon-blocklist, update check, captive-portal detection, EME/
Widevine/VA-API, WebAuthn+hidraw, WebRTC+STUN/TURN, OCSP/CRLite, Fission. Each is load-
bearing for a real-world daily driver. **Do not close these to chase a "zero-connection"
number — that number is not the goal; a usable private browser is.**
