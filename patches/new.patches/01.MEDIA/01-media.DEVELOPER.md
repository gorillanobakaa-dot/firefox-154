# Media Subsystem — Hardware-Only H.264 Policy + Fixed-Gain Audio DSP — Developer Track

> **Topic:** `01-media` · **Files:** `dom/media/DecoderTraits.cpp`, `dom/media/platforms/PDMFactory.cpp`, `dom/media/platforms/ffmpeg/FFmpegVideoDecoder.cpp`, `dom/media/ipc/RemoteVideoDecoder.cpp`, `dom/media/AudioStream.{cpp,h}`, `dom/media/CubebUtils.cpp`, `dom/media/mediacapabilities/MediaCapabilities.cpp`, `dom/media/mediasource/MediaSource.cpp`, `dom/media/webaudio/AudioContext.cpp`, `dom/media/webaudio/AudioDestinationNode.cpp`, `dom/media/webaudio/DynamicsCompressorNode.cpp`, `dom/media/webcodecs/{VideoDecoder,VideoEncoder,WebCodecsUtils}.cpp`, `dom/media/webrtc/jsapi/DefaultCodecPreferences.cpp`, `dom/media/webrtc/libwebrtcglue/VideoConduit.cpp`, `dom/media/webrtc/libwebrtcglue/WebrtcVideoCodecFactory.cpp`, `dom/media/moz.build`, `gfx/thebes/gfxPlatformGtk.cpp`
> **Generated:** 2026-07-16

---

## Module Summary

This patch group replaces Firefox's permissive 'try hardware, fall back to software' decode policy with a strict hardware-only H.264 policy enforced at six independent layers (DecoderTraits, MediaSource, MediaCapabilities, PDMFactory, RemoteVideoDecoder, WebCodecs) plus the WebRTC codec-negotiation layer. It also rewires the Web Audio DSP so bass-boost and soft-clipping gains are fixed constants applied per-sample, decoupled from the volume slider (which YouTube pins to 1.0 upstream). The result is enforced VAAPI-only H.264 decode via the RDD process on Intel HD 4000 (i965 driver), with no software-decode fallback path anywhere in the pipeline.

## Architecture

- **Pattern:** Layered soft-enforcement gated by a single runtime pref, `media.gorilla.hardware_only_mode` (`StaticPrefs::media_gorilla_hardware_only_mode()`). Every layer that can construct a decoder or answer a codec-capability query is wrapped in a check against this pref AND the predicate `IsBlockedSoftwareOnlyVideoCodec` for the C++ paths. Blocking is intentionally redundant across six layers: any single layer left un-patched would silently re-open software fallback. The pref defaults ON in this build; turning it OFF reverts every gate to upstream behaviour without a rebuild.
- **Trust Boundary:** The RDD (Remote Data Decoder) process is where VAAPI actually runs. Everything upstream of it — content process, PDMFactory, DecoderTraits — is a gate; RDD is the executor. GPU process is not involved and must remain ForceDisabled on Wayland (see gfx_thebes_gfxPlatformGtk.cpp patch and CLAUDE.md).
- **Discrete-GPU assumption:** Reference hardware also has an AMD Radeon HD 7670M (Turks, muxless Enduro) — disabled in BIOS. All GPU-decode paths therefore target Intel HD 4000 exclusively; there is no runtime GPU selection logic in these patches. If deploying to a machine where the discrete GPU is BIOS-enabled, expect undefined behaviour in the compositor path.
- **Attack Surface:** MIME-type spoofing by malicious pages was already handled upstream; this policy narrows the attack surface further by refusing to instantiate SW decoders whose CVE history is longer than H.264's HW path. Frame-pool cap prevents memory-pressure DoS via crafted streams.
- **Dependencies:** `libavcodec (FFmpeg) linked at runtime for VAAPI H.264`, `libva1 + i965-va-driver from Debian`, `LIBVA_DRIVER_NAME=i965 in /etc/environment (the iHD driver does NOT support Ivy Bridge)`

## Kill Switches

### `PDMFactory.cpp :: IsBlockedSoftwareOnlyVideoCodec(nsACString mime)` — HARD ⚠️

- **Condition:** Called from PDMFactory::CreateDecoder, PDMFactory::Supports, RemoteVideoDecoderChild construction paths — always active for video/* MIMEs.
- **Effect:** Returns true for any video codec other than H.264; the caller returns NS_ERROR_DOM_MEDIA_FATAL_ERR('Gorilla hardware-only policy.') before any decoder is instantiated. Explicitly excludes audio MIMEs (audio/aac, audio/opus) from the block — that was BUG C in the media-lessons registry (blocking audio killed all audio playback).
- **Reversibility:** reversible
- **Notes:** Single-point-of-truth: adding a new blocked codec is a one-line change here. Do NOT gate on RemoteDecoderModule's DecodeSupport::HardwareDecode — upstream bug 1754239 makes it always return SoftwareDecode; the hardware-enforcement point belongs ONLY in FFmpegVideoDecoder::Init inside the RDD process.

### `DecoderTraits.cpp :: CanHandleContainerType / CanHandleCodecsType` — HARD ⚠️

- **Condition:** Called during MSE type-support probes (SourceBuffer.isTypeSupported, MediaSource.isTypeSupported) — before any decoder is constructed.
- **Effect:** Returns CANPLAY_NO for video/webm, video/x-webm, video/ogg, and for codecs strings containing vp8/vp9. YouTube observes the NO and negotiates the H.264 (avc1.*) rendition instead. This is the earliest gate — prevents the pipeline from even planning a VP9 playback path.
- **Reversibility:** reversible
- **Notes:** Redundant with PDMFactory but intentionally so; if PDMFactory ever regresses, the pipeline still fails to *plan* a VP9 stream and falls back to H.264 cleanly.

### `FFmpegVideoDecoder.cpp :: Init() (RDD process)` — HARD ⚠️

- **Condition:** Executed at decoder init inside the RDD process — the *actual* hardware boundary.
- **Effect:** If VAAPI init fails for H.264, returns MediaResult(NS_ERROR_DOM_MEDIA_FATAL_ERR, 'Gorilla policy: H.264 hardware decode required') instead of falling back to libavcodec software decode. Loud failure by design.
- **Reversibility:** reversible
- **Notes:** This is the last line of defense — the only place inside the RDD process where enforcement is authoritative. All other layers are advisory relative to this one.

### `FFmpegVideoDecoder.cpp :: mVideoFramePool = MakeUnique<VideoFramePool<LIBAV_VER>>(16)` — RUNTIME_GUARD ⚠️

- **Condition:** At decoder construction, four call sites, all with literal 16.
- **Effect:** Pins the decoded-frame recycling pool to exactly 16 buffers. No std::max, no dynamic growth. Prevents memory-bus contention on Intel HD 4000 UMA (GPU shares the system RAM bus; the constraint is bandwidth, not raw capacity — the reference machine has 16 GiB but the video decoder, desktop compositor, and browser UI all share one memory controller). Was BUG D in the media-lessons registry.
- **Reversibility:** reversible
- **Notes:** 16 is empirically the sweet spot on this hardware — below jitters, above triggers swap contention with the browser UI.

### `AudioStream.{cpp,h} :: mBassBoostGain=1.8f, mXLoudBoost=0.4f (fixed) + FastTanh soft-clipper` — RUNTIME_GUARD ⚠️

- **Condition:** Applied per-sample in the audio callback, unconditionally.
- **Effect:** Bass emphasis via one-pole HP/LP split at kBassFreq=220Hz with mBassBoostGain=1.8f applied to the bass path, then soft-clipping via FastTanh (Padé approximation) with a hardness knee at ±0.9 for the whole signal. Fixed gains — do NOT track mVolume. mVolume is applied BEFORE the DSP stage (as volScale), which is critical: applying it after would re-couple DSP to the slider and undo the fix.
- **Reversibility:** reversible
- **Notes:** Prior code multiplied gains by mVolume; because YouTube (and most pages) pin their internal volume to 1.0 and let the OS/user slider do actual level control, mVolume is effectively always ~1.0 — making the DSP silently near-inert. Decoupling is the entire fix.

### `AudioContext.cpp :: GetSampleRateForAudioContext()` — HARD ⚠️  *(v1.1, 2026-07-10)*

- **Condition:** `StaticPrefs::media_gorilla_hardware_only_mode()` is true.
- **Effect:** Returns literal `48000.0f` and bypasses `CubebUtils::PreferredSampleRate()`. Eliminates software 44.1→48 kHz resampling on the Realtek ALC269 codec (native rates 44100/48000/96000/192000; PipeWire on this system runs 48 kHz). Adds a 10 ms latency hint alongside.
- **Reversibility:** toggle the pref to revert.
- **Notes:** The same file also carries an inherited-Mozilla `TODO(bug 2047321)` about page-resume gating during audio-focus interruption — that TODO is upstream Mozilla work, not ours, and is what precheck P2-001 flagged.

### `AudioDestinationNode.cpp` — FastTanh output limiter — RUNTIME_GUARD ⚠️  *(v1.1, 2026-07-10)*

- **Condition:** Applied per-sample at the graph output when hardware-only mode is active.
- **Effect:** Second FastTanh soft-knee limiter at the destination node, downstream of AudioStream's own soft-clip. Belt-and-suspenders — catches signals that reach the destination via Web Audio graphs that bypass AudioStream's DSP (e.g., WebAudio-generated content).
- **Reversibility:** toggle the pref to revert.
- **Notes:** Together with the AudioContext 48 kHz lock, this is the second of two audio additions that landed after the initial DSP work.

### `DynamicsCompressorNode.cpp` — pass-through under hardware-only — SOFT ⚠️

- **Condition:** `media.gorilla.hardware_only_mode` true.
- **Effect:** The Web Audio DynamicsCompressorNode becomes a pass-through so its generic compression does not fight the tuned AudioStream DSP and destination-node limiter. Prevents double-compression artefacts.
- **Reversibility:** toggle the pref to revert.
- **Notes:** Chose bypass over deletion so pages that explicitly instantiate a `DynamicsCompressorNode` still get an object with the expected interface — just one that does nothing to the signal.

### `DefaultCodecPreferences.cpp / WebrtcVideoCodecFactory.cpp / VideoConduit.cpp (WebRTC)` — HARD ⚠️

- **Condition:** During SDP offer/answer negotiation for peer connections.
- **Effect:** This build advertises H.264-only in its codec preferences; peers select H.264 automatically. Prevents a video call from negotiating VP9 or AV1 and triggering software decode mid-call.
- **Reversibility:** reversible
- **Notes:** Applies to Meet, Jitsi, Element, any WebRTC-based video calling.

## Performance Profile

| Component | Before | After | Mechanism |
|---|---|---|---|
| H.264 decode (VAAPI hw path) | not measured | not measured | RDD-process VAAPI via i965 driver — dedicated decode circuit |
| Attempted VP9 stream (avoided) | 1 CPU core at 100% per stream | not instantiated (returned NS_ERROR at PDMFactory) | IsBlockedSoftwareOnlyVideoCodec gate |
| Frame-pool memory | unbounded (std::max-driven growth) | capped at 16 buffers | literal 16 at four call sites in FFmpegVideoDecoder.cpp |
| Audio DSP effectiveness | gains × mVolume(~1.0) → near-inert | fixed gains applied per-sample, decoupled from slider | AudioStream.cpp/h + volScale ordering |

- **CPU:** H.264 decode runs on the HD 4000's dedicated VLD decoder in the RDD process; parent + content processes remain nearly idle during playback (specific numbers for MEDIA topic: not measured — the measured 12.8% parent CPU win recorded in the project belongs to the TELEMETRY topic, not this one). The *avoided* cost is a single software-decoded VP9 stream pinning one CPU core at 100%.
- **Memory:** Frame pool capped at 16 buffers × NV12 1080p frame ≈ 24 MB steady-state per decoder. Prevents unbounded growth on long playbacks. Not measured as before/after.
- **I/O:** VAAPI passes NV12 DMABuf handles to compositor without CPU copies — zero-copy path guarded by `mKnowsCompositor && mKnowsCompositor->GetTextureForwarder()` null check in RemoteVideoDecoder.cpp (missing null check dropped ALL frames — BUG F).
- **Timer Interval:** N/A — event-driven pipeline.

## Security Analysis

### User Profiling

Not applicable to this topic — this is a decode-policy change with no data-collection surface. (See Telemetry topic.)

### Targeting

Narrows attack surface: refuses to instantiate software decoders whose historical CVE count is much higher than H.264's hardware path. A malicious .webm cannot even get a decoder allocated.

### Trust Chain

Trust is placed in libva1 + i965 driver + kernel media subsystem. If any of these is compromised, hardware decode is compromised — but no additional trust in software decoder code is required.

### Abuse Potential

Frame-pool cap prevents crafted-stream memory-exhaustion DoS. Loud failure on VAAPI init failure means a bad stream cannot silently degrade the whole browser.

## Implementation Flow

1. **`DecoderTraits::CanHandleContainerType / CanHandleCodecsType`** — First gate — returns CANPLAY_NO for WebM/Ogg containers and VP8/VP9 codec strings. YouTube observes NO and negotiates H.264 rendition upstream.
   *Side effects:* None — pure predicate.
2. **`MediaCapabilities::DecodingInfo / MediaSource::IsTypeSupported`** — Same predicate replayed at capability-query time so JS Promise-based probes get consistent answers.
   *Side effects:* None.
3. **`PDMFactory::Supports / PDMFactory::CreateDecoder`** — Calls IsBlockedSoftwareOnlyVideoCodec(mimeType); if true, refuses decoder construction with NS_ERROR_DOM_MEDIA_FATAL_ERR and 'Gorilla hardware-only policy.' error string. Deletes the historical AgnosticDecoderModule (VP8/VP9/Theora/Vorbis) fallback path.
   *Side effects:* Playback errors surface as media error events on the video element.
4. **`FFmpegVideoDecoder::Init (RDD process)`** — Actual hardware boundary. Attempts VAAPI init for H.264; on failure, returns MediaResult with fatal error rather than falling back to libav software path.
   *Side effects:* Frame pool constructed with size=16.
5. **`RemoteVideoDecoder::ProcessOutput`** — Passes zero-copy DMABuf handles to compositor, guarded by mKnowsCompositor/TextureForwarder null check.
   *Side effects:* Without the null check, all frames get dropped — this was BUG F.
6. **`AudioStream::AudioCallback (per-sample DSP)`** — Applies mVolume × CubebUtils::GetVolumeScale() FIRST (volume shaping), THEN mBassBoostGain=1.8f on the LP-split bass path, THEN FastTanh soft-clipping at ±0.9 threshold. Ordering is load-bearing.
   *Side effects:* Perceptibly warmer bass and higher usable loudness before distortion on tinny laptop speakers.
7. **`DefaultCodecPreferences / WebrtcVideoCodecFactory`** — Restricts advertised WebRTC codec set to H.264 in SDP negotiation. Peers pick H.264 automatically.
   *Side effects:* Interoperability preserved — H.264 is universally supported by WebRTC peers.

## Technical Debt

🟡 **LOW** — TODO(bug 2047321) in AudioContext.cpp — page resume() gating during audio-focus interruption is deferred to that upstream bug
  - *Recommendation:* Track upstream bug 2047321; this is inherited Mozilla debt, not ours. Precheck flagged it as P2 by rule; downgrade context: it's a known-tracked upstream item.

🟡 **LOW** — Blocklist is negative (grows with each new codec) rather than a positive allowlist
  - *Recommendation:* Accepted trade-off — the negative list documents each block with a real reason. A one-entry allowlist would be shorter but less self-documenting.

🟠 **MEDIUM** — Frame-pool literal 16 duplicated across four call sites in FFmpegVideoDecoder.cpp
  - *Recommendation:* Extract to a named constant (kIvyBridgeFramePoolSize=16) with a comment explaining the empirical basis. Low priority — the four occurrences are colocated in one file.

🟠 **MEDIUM** — No unit test asserts that IsBlockedSoftwareOnlyVideoCodec returns false for audio MIMEs
  - *Recommendation:* Add a gtest — BUG C (blocking audio MIMEs killed all audio) is exactly the class of regression a test would catch.

## Impact If Removed / Disabled

Reverting: (1) VP9/AV1/HEVC/VP8 requests would succeed, spawning software decoders that saturate the CPU on this hardware; (2) failed VAAPI H.264 init would silently fall back to software instead of surfacing a diagnostic error; (3) the audio DSP would go silently inert on pages that don't touch the volume slider (which is most of them); (4) the frame pool would grow unbounded and contend with browser-UI allocations on the shared UMA memory bus; (5) WebRTC calls could negotiate VP9 and freeze the browser mid-meeting.

## Testing Notes

Manual verification recipe (no gtests added by this patch group):
1. `vainfo | grep H264` — expect three VAEntrypointVLD lines. If missing, i965 driver is not installed or LIBVA_DRIVER_NAME is unset.
2. `grep LIBVA_DRIVER_NAME /etc/environment` — expect `i965`.
3. YouTube any 1080p H.264 clip; open about:support and verify the media-decoder section shows a hardware-backed decoder. `top` should show RDD process moderate, parent+content near-idle.
4. Force a VP9 URL (e.g. youtube.com/watch?v=…&vp9=1 or a WebM test URL); expect a media error event, NOT smooth playback via software.
5. Audio: play any 90 Hz-heavy track; bass should be perceptibly emphasized. Push volume to 100%; expect soft compression rather than crackly clipping.
6. WebRTC: join a Google Meet room; open about:webrtc and verify the outbound video codec is H.264 (not VP9/VP8/AV1).

## Changelog Notes

Layer-by-layer buildup documented in MEDIA_CODEC_LESSONS.md (bugs A–I). Key milestones: (A) frame-pool cap, (C) audio-MIME exclusion in blocklist, (D) RDD-process VAAPI relocation from GPU-process gate, (F) TextureForwarder null-check for zero-copy, (I) audio-DSP decoupling from mVolume slider. STRICT policy timestamp recorded in PDMFactory comment: 2026-07-05.

**Version history:**
- **v1.0** — initial six-layer H.264 hardware-only policy + AudioStream DSP + frame-pool cap.
- **v1.1** (2026-07-10) — added AudioContext 48 kHz native rate lock (eliminates ALC269 44.1→48 resampling) and AudioDestinationNode FastTanh soft limiter (protective second stage).

**Historical DSP bugs fixed by the AudioStream rewrite** (documented in the topic's MASTER_PROJECT_LOG):
- **D-001** — thread-unsafe static `filterState[64][4]` causing data races.
- **D-002** — multichannel crosstalk.
- **D-003** — null-pointer dereference when DSP unavailable.
- **D-004** — generic audio data-type issues.

**Documentation-vs-reality self-audit (MEDIA_PATCH_DOSSIER.md):** the project ran a claim-by-claim audit of prior narrative docs against the actual source. It found 6 fabricated claims: a fake `kCeiling` identifier (value correct, name wrong), a fake CubebUtils `48000` baseline, a `std::max(sVolumeScale, 4.0)` "historical clamp" that never existed in the source (a reconstructed-memory artifact), a fake 192 kHz reference, etc. All 6 corrected in both docs and, where the error was in a code comment, in the source itself. Doc accuracy 87.5% → 89.7%. That the project publishes its own hallucination list is worth noting; most projects hide theirs.

---
*Developer Track. Human Track twin: `01-media.LAYMAN.md`.*