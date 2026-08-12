# WebCodecs-only Software VP8 Gate — audit-grade record

**Date:** 2026-08-11/12 · **Sequel to:** WEBCODECS-CALL-PATH.DEVELOPER.md
**Builds:** full `./mach build` (yaml) 2026-08-11 18:42 + `build binaries`
19:02 / 19:51 / 20:10 (all MACH_REAL_EXIT=0 via PIPESTATUS, libxul mtime
verified each time). All edits carry `// GORILLA OVERRIDE 2026-08-11:` markers.

## WHY

WhatsApp Web calls hard-require VP8 through WebCodecs over a DataChannel (see
prequel). HD 4000 has no VP8/VP9 ASIC — the call is software in any browser
(Chromium measured: ~130% of one core, ~18 W, Video engine 0.0%). The fortress
excision of `AgnosticDecoderModule` therefore denied a call that could never
be accelerated. Requirement: re-admit software VP8 **for WebCodecs only**,
default-off, with `<video>`/MSE/WebRTC factories untouched.

Rejected alternative: `media.gorilla.hardware_only_mode=false` per profile
(handover §3 option A) — profile-global, reopens software VP9 to all web
content in that profile.

## Design

**Seam:** `DecoderAgent` (WebCodecs-private; zero references outside
`dom/media/webcodecs/`) constructs its own `PDMFactory`
([DecoderAgent.cpp:52]). That constructor is the entire attack surface.

| Change | File | Effect |
|---|---|---|
| pref `media.gorilla.webcodecs_software_vp8` (RelaxedAtomicBool, **false**, mirror always) | `StaticPrefList.yaml` (after `hardware_only_mode`) | opt-in, off for downloaders |
| `enum class Purpose { Default, WebCodecs }`; `explicit PDMFactory(Purpose = Purpose::Default)`; `const bool mForWebCodecs` | `PDMFactory.h` | purpose flag, default-compatible with all existing callers |
| `IsBlockedVideoCodec(mime)` member = static block minus (`mForWebCodecs && pref && VPXDecoder::IsVP8`) ; replaces static call at the 3 sites (CreateDecoderWithPDM / SupportsMimeType / Supports) | `PDMFactory.cpp` | VP8-only exemption, this factory only |
| `StartupPDM(AgnosticDecoderModule::Create(), /*aInsertAtBeginning*/ true)` under `mForWebCodecs && pref`, **outside** the allow-audio-non-utility block | `PDMFactory.cpp` CreateContentPDMs | software VP8 provider, wins selection |
| `MakeRefPtr<PDMFactory>(PDMFactory::Purpose::WebCodecs)` | `DecoderAgent.cpp` | sole WebCodecs caller |
| under `hardware_only_mode`: `"vp8"` → true iff pref | `WebCodecsUtils.cpp` IsSupportedVideoCodec | support answer (resolves, never throws — prequel rule) |
| vp8+pref short-circuit before the container fallback | `VideoDecoder.cpp` CanDecode | blocker 1 fix (below) |

Per-profile companions (`~/.mozilla/ff154-main/user.js` only):
`media.gorilla.webcodecs_software_vp8=true`, `media.webm.enabled=true`.

## The four stacked blockers (chronological; do not rediscover)

1. **Layer-1 leak in `CanDecode`** (`VideoDecoder.cpp:193`): after
   `IsSupportedVideoCodec()` passes, upstream falls through to
   `DecoderTraits::CanHandleContainerType()` — the HTMLMediaElement gate,
   which is `CANPLAY_NO` for VP8 by fortress design. Upstream marks this
   wiring wrong (TODO bug 1880326). Symptom: `isConfigSupported → false`
   despite pref. Fix: `return true` for vp8+pref at that point;
   `DecoderAgent`'s factory decides real decodability.

2. **`media.webm.enabled=false`** (`all.js:553`, fortress flip): kills
   `WebMDecoder::IsSupportedType` → `DecoderTraits::GetTracksInfo` dispatch
   never reaches `WebMDecoder::GetTracksInfo` → `VideoDecoderTraits::
   CreateTrackInfo` gets 0 tracks → `NS_ERROR_ILLEGAL_VALUE` →
   JS `NotSupportedError` at `configure()`. MOZ_LOG line that names it:
   `E/WebCodecs ... CreateTrackInfo failed: NS_ERROR_ILLEGAL_VALUE`.
   Fix: pref true per-profile. **Safety proof:** the DecoderTraits hard lock
   is `hardware_only_mode && WebMDecoder::IsSupportedType(...)` → the flip
   *arms* the explicit lock instead of relying on fallthrough. Probe in the
   same profile: `canPlayType('video/webm; codecs="vp8"')=""`,
   `MediaSource.isTypeSupported(webm/vp9)=false`.

3. **Claim-then-refuse module ordering:** appended-at-end Agnostic never got
   asked; `RemoteDecoderModule(RDD)`/FFVPX claimed VP8 then their
   hardware-only `Init()` refused → `EncodingError "The given encoding is not
   supported"`. Fix: insert Agnostic at the FRONT (`StartupPDM(..., true)` →
   `mCurrentPDMs.InsertElementAt(0,...)`, PDMFactory.cpp:857). Agnostic
   claims only VPX/AV1 (`AgnosticDecoderModule::Supports`), so H.264 still
   routes to the hardware path; VP9 is stopped earlier by
   `IsBlockedVideoCodec`.

4. **Dead-block placement:** first registration sat inside
   `if (StaticPrefs::media_allow_audio_non_utility())` — yaml value
   `@IS_IOS@` → **false on Linux**; the entire block (FFVPX/FFmpeg lines
   included) is dead code on this platform. Tell-tale: MOZ_LOG
   `"Content PDM order:"` with zero entries. Fix: registration moved after
   the `#endif`.

## Verification (all on the real artifact)

Headless probe method (supersedes the window-title trick — Wayland-native
windows are invisible to `xwininfo`, and agent shells lack `XAUTHORITY`):
unique `MOZ_APP_REMOTINGNAME` + `--headless --new-instance` + page `dump()`
to stdout; probe profile sets `browser.dom.window.dump.enabled=true` and
`media.navigator.permission.disabled=true` (probe profile ONLY). UVC camera
is single-consumer — `fuser /dev/video0` before any capture probe.

| Probe | pref-ON profile | shipped defaults |
|---|---|---|
| `isConfigSupported` vp8 dec / enc | true / true | false / false (resolves, no throw) |
| vp9 dec | false | false |
| h264 dec | true | true |
| camera luma (real frames >10) | 37–86 | — |
| encode → decode loopback | **5 chunks → 5 frames** | — |
| `canPlayType` webm / MSE webm | NO / false | NO / false |

Transport baseline (2026-08-12 `/tmp/ice.log*`, WhatsApp page-load probes):
ICE pairs `31.205.107.200 ↔ 157.240.{0,27,225}.133:3478` SUCCEEDED +
nominated; DTLS `SSL handshake completed`; SRTP `SRTP_AEAD_AES_128_GCM`;
consent refreshed; 163 STUN responses / 0 timeouts / 0 send errors; probes
close at their designed ~5 s. **The console "WebRTC: ICE failed" seen on
pre-20:10 binaries was pipeline-teardown collateral, not a transport
defect.** `media.peerconnection.ice.default_address_only=true`: exoneration
now extends from gathering to full connect+DTLS.

Remaining non-transport wedge (own lesson:
`Slow_Script_Watchdog_Wedged_WhatsApp_Call_UI`): WhatsApp JS exceeded even
`dom.max_script_run_time=30` on the i7-3632QM; terminated script = dead call
UI. `=0` in this machine's user.js; shipped 30 unchanged, pending data.

## Patch masters

Regenerated vs pristine vault (backups `.pre-20260811b/c`):
`01.MEDIA/dom_media_{AudioStream,platforms_PDMFactory,webcodecs_{WebCodecsUtils,VideoDecoder,DecoderAgent}}.cpp.patch`,
`01.MEDIA/dom_media_platforms_PDMFactory.h.patch`,
`05.PREFS/modules_libpref_init_StaticPrefList.yaml.patch`.

## Not verified

- A real answered WhatsApp call in the main browser (remote never picked up
  during testing; scheduling constraint).
- Call audio path (Opus over DataChannel) — expected via FFVPX, untested.
- Whether the shipped `dom.max_script_run_time=30` suffices on other
  2012-class CPUs once the rest works.
- Wrapper (`whatsapp-desktop`) profile has none of the per-profile prefs —
  calls there remain off until its launcher's managed block is updated.
