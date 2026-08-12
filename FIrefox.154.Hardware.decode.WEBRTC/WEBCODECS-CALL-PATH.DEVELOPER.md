# WebCodecs Call Path — Why Hardware-Only Blocks WhatsApp Calls

> *Gorilla Unleashed Firefox 154 · Developer track · 2026-08-11*
> *Companion: `WEBCODECS-CALL-PATH.LAYMAN.md` · Evidence: `evidence-2026-08-11/`*
> *Supersedes the codec-negotiation theory in `FINAL-DIAGNOSIS.md` (2026-07-24)*

---

## A. Finding

WhatsApp Web calls hang at "Connecting…" in this build because **WhatsApp does
not use WebRTC media sections at all**. It encodes and decodes call video
**in-page via the WebCodecs API** (`VideoEncoder` / `VideoDecoder`) and
transports the compressed frames over an **`m=application` DataChannel**.

WebCodecs codec instantiation routes through `PDMFactory`. In this build,
`AgnosticDecoderModule` — which provides the software VP8/VP9/Theora/Vorbis
decoders — is **excised, not gated** (`PDMFactory.cpp:5,12`). Therefore
`VideoDecoder.isConfigSupported({codec:'vp8'})` **rejects** rather than resolving
`{supported:false}`, WhatsApp's call setup throws, and the call never progresses.

The build's SDP codec policy (`DefaultCodecPreferences.cpp`, H.264-only) is
**never reached** and is **not** the cause. It was the prime suspect for three
weeks and is exonerated.

## B. Why this was hard to find (WHY before HOW)

The failure mode presents as a *connectivity* problem ("Connecting…", plus
WhatsApp's own "check your internet connection" toast). Every instinct points at
ICE/TURN or codec negotiation. Both are healthy here. The actual failure is a
**JavaScript exception inside the page**, thrown by a Web API that most WebRTC
debugging workflows never inspect, on a code path (`PDMFactory`) that developers
associate with `<video>` playback rather than with calls.

The decisive question turned out not to be *"which codec is being refused?"* but
*"is a media section being created at all?"* — answered by
`chrome://webrtc-internals`, which showed `offer m-lines: ['application']` for
every PeerConnection **in a working Chromium call**.

## C. Evidence chain

All measurements from the reference machine (i7-3632QM / HD 4000 / Debian 13 /
Wayland), 2026-08-11. Artefacts in `evidence-2026-08-11/`.

### C1. Chromium reference call (working) — `webrtc_internals_dump.gz`

```
PC 9-6 / 9-8 / 9-10   (three PeerConnections, all identical in shape)
  rtcConfiguration : {"alwaysNegotiateDataChannels":false}   <- NO iceServers
  offer m-lines    : ['application']                         <- NO audio, NO video
  candidate types  : {'host': 1}                             <- host only
  ICE              : checking -> connected
```

Implications, each fatal to a prior hypothesis:
- No `m=audio` / `m=video` ⇒ **no SDP codec negotiation occurs**; the H.264-only
  offer list cannot be the cause.
- No `iceServers` ⇒ **TURN/STUN configuration is not the differentiator**;
  Chromium connects on host candidates alone.
- Media nonetheless flows (below) ⇒ transport is the DataChannel.

### C2. Packet capture — `whatsapp-chromium-call.pcap` (35 MB, snaplen 128)

```
10.29.142.247:42580 <-> 57.144.63.57:3478   34006/33641 frames   45 MB   289 s
STUN message types: 0x0001 Binding Req (336), 0x0101 Binding Resp (329),
                    0x0003 Allocate Req (21)   <- TURN allocations
Throughput: steady ~1.7 MB / 10 s  ≈ 1.36 Mbit/s
Packet mix: 30877 frames >1000 B, 26253 frames <300 B
```

Media is relayed via Meta TURN on :3478 and is **TURN-encapsulated**, which is
why heuristic RTP dissection yields nothing — there are no bare RTP headers to
match. Do not attempt codec identification from this capture; it cannot work.

### C3. Hardware utilisation during the live Chromium call

```
intel_gpu_top -J:
  engine Render/3D    busy = 2.5% / 0.7%
  engine Blitter      busy = 0.0%
  engine Video        busy = 0.0%      <- ASIC idle for the entire call
  power GPU 0.77 W    power Package 16.20–18.04 W
ps: one Chromium process at 83.4% CPU, ~130% total across processes
gUM constraints requested by WhatsApp: 1280x720 and 640x480 @30, audio 16 kHz mono
```

**A working WhatsApp call performs zero hardware video decode on this platform,
in any browser.** HD 4000 exposes no `VAProfileVP8*` / `VAProfileVP9*` entry
points (per `vainfo`, recorded in `FINAL-DIAGNOSIS.md` §3), so no hardware path
exists for the codec in use.

### C4. WebCodecs capability probe — the root-cause test

Test page: `VideoDecoder.isConfigSupported` / `VideoEncoder.isConfigSupported`
for `vp8`, `vp09.00.10.08`, `avc1.42001f`, 640x480.

| Codec | Gorilla fork | Chromium 151.0.7922.108 |
|---|---|---|
| VP8 decode / encode | **ERR (rejects)** | true / true |
| VP9 decode / encode | **ERR (rejects)** | true / true |
| H.264 decode / encode | true / true | true / true |
| AV1 | — | true / true |

`WEBCODECS=PRESENT` in both. The API exists in the fork; only the codecs fail.

**Re-run with `media.gorilla.hardware_only_mode=false` in the profile:
identical output.** The pref does not restore VP8 — confirming the block is
compile-time excision, not a runtime gate.

### C5. Source confirmation

```
dom/media/platforms/PDMFactory.cpp:5    // GORILLA OVERRIDE: AgnosticDecoderModule excised
                                        //   (software-fallback ban — MEDIA_CODEC_LESSONS Bugs B/D)
dom/media/platforms/PDMFactory.cpp:12   // #include "AgnosticDecoderModule.h"  // REMOVED:
                                        //   all instantiation sites excised by this patch
dom/media/platforms/PDMFactory.cpp:635,673,755
                                        // AgnosticDecoderModule (VP8/VP9/Theora/Vorbis) not allowed
```

`dom/media/platforms/agnostic/AgnosticDecoderModule.cpp` is still present and
still listed in `dom/media/platforms/moz.build:28`, i.e. it **compiles** but is
never instantiated. The object code is in the binary; the call sites are gone.
This matters for the fix: restoring it is a call-site change, not a build-system
change.

## D. Hypotheses tested and disproved

Recorded so they are not re-litigated. Each was disproved by measurement.

| # | Hypothesis | Test | Result |
|---|---|---|---|
| D1 | Debian WebKitGTK lacks WebRTC (original wrapper) | headless probe | **TRUE** — correct, motivated the Firefox switch |
| D2 | ICE/STUN gathering broken in fork | headless PC + Google STUN | host=2 **srflx=1** — works |
| D3 | `media.peerconnection.ice.default_address_only=true` (added 2026-08-10) breaks gathering | same probe, pref true vs false | **identical** (host=2 srflx=1) — **exonerated** |
| D4 | TURN allocation fails in fork | Chromium dump | WhatsApp passes **no iceServers**; Chromium uses host-only too |
| D5 | getUserMedia blocked in wrapper profile | test page | mic + `USB2.0 Camera` allocated — works |
| D6 | H.264-only SDP prevents negotiation | `createOffer` probe; Chromium dump | offer is valid (H264+opus); **no m=video ever created by WhatsApp** |
| D7 | OpenH264 GMP missing in fresh profile | seeded from `~/.mozilla/ff154-main` | did not fix; GMP is irrelevant to WebCodecs |

D3 was published as the likely cause during the investigation and **withdrawn**.
Any doc still asserting it must be corrected.

## E. Defect found in passing — the kill switch does not work

`media.gorilla.hardware_only_mode` is honoured inconsistently:

| File | Gated on pref? |
|---|---|
| `dom/media/webrtc/libwebrtcglue/WebrtcVideoCodecFactory.cpp` | ✅ yes (11 sites) |
| `dom/media/webrtc/libwebrtcglue/VideoConduit.cpp` (`HasAv1()`) | ✅ yes |
| `dom/media/webrtc/jsapi/DefaultCodecPreferences.cpp:127` | ❌ **no — unconditional** |
| `dom/media/platforms/PDMFactory.cpp` (AgnosticDecoderModule) | ❌ **no — excised** |

Verified empirically: with the pref `false`, `createOffer` still yields
H.264-only (`codecs=H264,rtx,ulpfec,red,opus,…`, no VP8). The documented escape
hatch is non-functional; any exception requires a recompile. This contradicts
`00.Open.Source.Philosophy (2).md` Part Seven, which describes the pref as the
"master gate … controlling all codec policy enforcement".

## F. Fix — APPLIED 2026-08-11

The exception is a **`TypeError`**, captured verbatim:

```
vp8_dec : THREW [TypeError | "IsConfigSupported: config is invalid: Un…"]
h264_dec: true
```

That located the true defect precisely, and it is **not** in `PDMFactory`. The
GORILLA WebCodecs patch placed its policy check inside the **config-validation**
functions:

| Site | Effect of returning `false` |
|---|---|
| `WebCodecsUtils.cpp:611` `IsSupportedVideoCodec()` | correct — capability answer, H.264-only under the pref |
| `VideoDecoder.cpp:722` `VideoDecoderTraits::Validate()` | **wrong — "config is malformed" ⇒ `TypeError`** |
| `VideoEncoder.cpp:429` `VideoEncoderTraits::Validate()` | **wrong — same** |

`CanDecode()` (`VideoDecoder.cpp:198`) and `VideoEncoderTraits::IsSupported()`
(`VideoEncoder.cpp:351`) **already** consult `IsSupportedVideoCodec()`, so the
correct `{supported:false}` answer was always reachable. The `Validate()` copies
were redundant *and* converted a clean refusal into a throw.

**Applied fix: delete the check from both `Validate()` functions. Nothing else.**

- `dom/media/webcodecs/VideoDecoder.cpp` — block removed, `GORILLA OVERRIDE
  2026-08-11` comment records why.
- `dom/media/webcodecs/VideoEncoder.cpp` — same.
- `WebCodecsUtils.cpp` — **untouched**; enforcement is unchanged and absolute.
- `#include "mozilla/StaticPrefs_media.h"` retained in both files: removing an
  include from a unified-build bundle risks breaking sibling TUs.

**This restores Layer 1's documented philosophy.** `MEDIA_CODEC_LESSONS.md`
Layer 1 has `canPlayType()` return `CANPLAY_NO` — a *clean* refusal — explicitly
"so YouTube negotiates H.264 MP4 without wasting RTP attempts on VP9/AV1". The
WebCodecs patch was added later, outside the documented 6-layer gate, and broke
that pattern. A capability gate must answer "no"; it must never throw.

**Cost: none.** No software decoder is enabled, no policy is relaxed, VP8/VP9
remain unsupported. The build simply reports it correctly, which lets sites fall
back to H.264 — the codec this platform decodes in hardware.

**Not fixed here (deliberately out of scope, separate build reason required):**
the §E kill-switch inconsistency. `DefaultCodecPreferences.cpp:127` and the
`PDMFactory` excision still ignore the pref. That defect does not affect
WhatsApp (no SDP negotiation occurs) and fixing it would change SDP behaviour
for every WebRTC site, so it is filed rather than bundled.

### F1. Acceptance test (post-build)

1. Re-run the §G probe: expect `vp8_dec:false h264_dec:true` — **`false`, not
   `THREW`**. This alone proves the spec fix.
2. Launch `whatsapp-desktop`, place a video call. Two possible outcomes, both
   informative:
   - **Call connects** ⇒ WhatsApp falls back to H.264; hardware-only policy
     preserved *and* calls work. Best case, no further change.
   - **Call still fails** ⇒ WhatsApp requires VP8 unconditionally. The remaining
     options are the §E route (software VP8, pref-scoped to the wrapper profile,
     ~130% CPU / ~18 W measured) or accepting that calls stay on the phone.

## G. Reproduction

```sh
# 1. WebCodecs capability probe (the root-cause test)
#    page: VideoDecoder/VideoEncoder .isConfigSupported for vp8 / vp9 / avc1.42001f
#    NOTE: headless dump() proved unreliable while other instances ran;
#          write the result into document.title and read it back:
MOZ_APP_REMOTINGNAME=wcprobe firefox --new-instance --name wcprobe \
  -profile /tmp/probe file:///path/wc4.html
xwininfo -root -tree | grep -oE 'WCRESULT[^"]*'

# 2. Chromium control
chromium --user-data-dir=/tmp/cr --no-first-run chrome://webrtc-internals
#    make a call, then: Create Dump -> "Download the PeerConnection updates and stats data"

# 3. Hardware utilisation during a call
sudo intel_gpu_top -J -s 2000     # engine "Video" busy% is the number that matters
```

## H. Platform compatibility — corrected

`FINAL-DIAGNOSIS.md` recommends Zoom for hardware decode. **This is wrong.**
Zoom's web client bypasses WebRTC media and performs WASM software decode; it
cannot reach the ASIC and is among the worst options on this hardware.

| Service | Call video path | Reaches HD 4000 ASIC? |
|---|---|---|
| Microsoft Teams | H.264 primary (AV1 for screen share) | ✅ yes |
| Jitsi Meet | configurable `preferredCodec: H264` | ✅ yes (no simulcast with H.264) |
| Telegram | VP8 **and** H.264 | ⚠️ likely |
| Google Meet | VP9 primary, AV1 experimental | ❌ no |
| Signal | VP8 | ❌ no |
| **WhatsApp Web** | **WebCodecs VP8 over DataChannel** | ❌ no — needs §F patch to work at all |
| **Zoom web** | proprietary WASM, outside WebRTC | ❌ no — software regardless |

## I. Not verified

- Which exact codec WhatsApp selects in-page (VP8 assumed from the WebCodecs
  probe delta; the DataChannel payload is opaque and TURN-encapsulated).
- Whether the §F patch makes WhatsApp calls actually succeed end-to-end — this
  is the primary post-build acceptance test.
- Whether WhatsApp would use H.264 via WebCodecs if VP8 were absent but H.264
  present; the current failure is a *throw*, which may abort before any
  fallback logic runs. If so, §F3 (return `false` instead of throwing) might
  fix calls **without** enabling software VP8 at all. **Test §F3 alone first.**
- Power measurement is package-level (RAPL); no battery-drain test was run.
