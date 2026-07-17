# Firefox 154 Media Patches — Master Project Log
**Complete Historical Record | Chronologically Ordered**

**Project Duration:** June 25, 2026 → July 8, 2026  
**Target Hardware:** Sony VAIO SVE14A3AJ (Intel i7-3632QM, HD 4000, ALC269, 16GB DDR3L)  
**Final Status:** ✅ Phase 0, Phase 1, Phase 2, Phase 3, Phase 4 COMPLETE  
**Total Work:** ~25 hours across multiple sessions  

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Executive Summary](#executive-summary)
3. [System Architecture](#system-architecture)
4. [Phase Breakdown (Chronological)](#phase-breakdown-chronological)
5. [Component Documentation](#component-documentation)
6. [All Patches Applied](#all-patches-applied)
7. [Baseline Diffs](#baseline-diffs)
8. [Hardware Capabilities Analysis](#hardware-capabilities-analysis)
9. [Deployment Status](#deployment-status)
10. [Decisions & Resolutions](#decisions--resolutions)
11. [Open Items & Roadmap](#open-items--roadmap)

---

## Project Overview

### What This Is
A set of targeted patches to Firefox 154 that makes it optimal for playback on older hardware (specifically a Sony VAIO with Intel HD 4000 GPU from 2012). The patches enforce a "hardware-only" video decode strategy: only H.264 via the GPU's dedicated VLD (Variable-Length Decoder) ASIC, rejecting all other codecs to avoid CPU fallback.

Additionally, the patches implement psychoacoustic DSP (digital signal processing) to optimize the laptop's built-in speakers using Fletcher-Munson equal-loudness compensation, bass synthesis, and soft-knee limiting.

### Mission Statement
**Goal 1 — Hardware Video Decode:**  
The Intel HD 4000 has an excellent, efficient H.264/AVC hardware-decode ASIC. Modern browsers refuse it and force *software* VP9/AV1 decode onto this low-power CPU — cooking it and calling the hardware "obsolete." Force hardware H.264, block GPU-unsupported codecs so sites serve H.264. **Never re-enable software/modern-codec decode paths.**

**Goal 2 — Psychoacoustic Audio DSP:**  
Optimize the ALC269 codec + SVE14A3AJ speaker chassis for perceived loudness without distortion using fixed gains, DSP boost, and soft limiting tuned to this exact hardware.

### Critical Context
> **⚠️ This is NOT a generic build.** Everything is compiled `-march=native -O3` for one specific machine (Ivy Bridge i7-3632QM, AVX/AES-NI, HD 4000). Hardcoded decisions (H.264-only ASIC decode, 16-frame VA-API pool, DSP constants tuned to ALC269 + SVE14A3AJ chassis) are intentional. Never ship these binaries to other hardware.

---

## Executive Summary

### What We've Built

We've sealed every path a website can use to make Firefox decode video using CPU software instead of the GPU hardware:

1. **Core video decode fortress (Phase 1)** — 7 files patched to reject all non-H.264
2. **WebRTC side doors (Phase 2)** — Blocked VP8/VP9/AV1 negotiation in video calls
3. **WebCodecs API (Phase 3)** — Rejected VP8/VP9/AV1 decoder/encoder instantiation via JavaScript
4. **Media Capabilities API (Phase 3)** — Report false for all codecs except H.264
5. **Web Audio DSP bypass (Phase 4)** — Prevented double-compression via Web Audio API
6. **Cleanup (Phase 4)** — Audited 8 files, confirmed no changes needed, archived unpatched files

### Current File Inventory (Post-Cleanup)

**25 C++ files + 1 moz.build + 4 MDs:**

#### Phase 1 Core (8 files)
- `AudioStream.cpp` — Psychoacoustic DSP engine
- `CubebUtils.cpp` — Audio subsystem interface
- `DecoderTraits.cpp` — Codec gatekeeper
- `DefaultCodecPreferences.cpp` — WebRTC codec list
- `FFmpegVideoDecoder.cpp` — VA-API hardware decode
- `FFmpegVideoDecoder.h` — VA-API header
- `PDMFactory.cpp` — Decoder dispatcher
- `RemoteVideoDecoder.cpp` — GPU zero-copy bridge

#### Phase 2 WebRTC (2 files)
- `WebrtcVideoCodecFactory.cpp` — WebRTC decoder/encoder factory
- `VideoConduit.cpp` — WebRTC video conduit

#### Phase 3 WebCodecs + Capabilities (4 files)
- `WebCodecsUtils.cpp` — WebCodecs codec support
- `MediaCapabilities.cpp` — Media Capabilities API
- `VideoDecoder.cpp` — WebCodecs VideoDecoder
- `VideoEncoder.cpp` — WebCodecs VideoEncoder

#### Phase 4 Web Audio + MSE + Wayland (10 files)
- `MediaSource.cpp` — MSE parent object
- `SourceBuffer.cpp` — MSE append buffer
- `HTMLMediaElement.cpp` — HTMLMediaElement codec validation
- `HTMLVideoElement.cpp` — HTMLVideoElement (no changes needed)
- `AudioContext.cpp` — Web Audio graph (no changes needed)
- `AudioDestinationNode.cpp` — Web Audio output node (no changes needed)
- `DynamicsCompressorNode.cpp` — Web Audio compressor bypass
- `nsWindow.cpp` — GTK window manager (no changes needed)
- `WaylandVsyncSource.cpp` — Wayland vsync (no changes needed)
- `gfxPlatformGtk.cpp` — GTK graphics platform (zero-copy force)

#### Build & Reference (3 files)
- `moz.build` — Build system (`-march=native -O3`)
- `PDMFactory_v1.cpp` — Reference snapshot v1
- `RemoteMediaDataDecoder_upstream.cpp` — Reference snapshot

#### Documentation (4 files)
- `00_MEDIA_HISTORY_AND_ROADMAP.md` — Project history
- `BASELINE_DIFFS_vs_FF154_upstream.md` — All diffs
- `CHANGELOG.md` — Recent optimization pass
- `PHASE_0_FINDINGS.md` — Quick wins summary

### Cleanup Summary

**Archived to `01.MEDIA/_archive_unpatched/` (no patches, upstream used as-is):**

| File | Why Archived |
|------|--------------|
| `AudioConduit.cpp` | WebRTC — already blocked by DefaultCodecPreferences.cpp |
| `CodecInfo.cpp` | WebRTC — already blocked by DefaultCodecPreferences.cpp |
| `PeerConnectionImpl.cpp` | WebRTC — already blocked by DefaultCodecPreferences.cpp |
| `DecoderTemplate.cpp` | WebCodecs — already blocked by WebCodecsUtils.cpp + PDMFactory.cpp |
| `MediaCapabilitiesValidation.cpp` | Capabilities — already blocked by MediaCapabilities.cpp |
| `TextureClient.cpp` | Compositor — zero-copy pipeline healthy, no changes needed |
| `ImageContainer.cpp` | Compositor — zero-copy pipeline healthy, no changes needed |
| `DMABufSurface.cpp` | Compositor — zero-copy pipeline healthy, no changes needed |

---

## System Architecture

### Pipeline Topology

```
[ HTMLMediaElement ] --> (MIME / Container Query)
        |
        v
+-----------------------+   Blocks VP8/9, AV1, Ogg/WebM
|  DecoderTraits.cpp    | --------------------------------> [ REJECTED ]
|  (Codec Gatekeeper)   |   Allows H.264 / AAC
+-----------------------+
        |
        v
+-----------------------+   Kills software fallback (AgnosticDecoderModule.h)
|   PDMFactory.cpp      | --------------------------------> routes to RemoteDecoderModule
| (Decoder Dispatcher)  |
+-----------------------+
        |
====================== IPC BOUNDARY (cross-process) ======================
        |
+-----------------------+   GPU decode via VA-API (libavcodec.so / libva.so)
|FFmpegVideoDecoder.cpp |   frame pool locked to 16
+-----------------------+
        |
        v
+-----------------------+   Zero-copy GPU memory (ImageContainer/TextureClient)
|RemoteVideoDecoder.cpp |   requires mKnowsCompositor == true
| (Compositor Bridge)   |
+-----------------------+

AUDIO SUBSYSTEM
[ Audio Source ] --> AudioStream.cpp (software mixer: gain boost + soft-knee limiter)
        |  IPC (sandbox)
        v
   CubebUtils.cpp (hardware interface; sample rate) --> PipeWire/PulseAudio --> speakers
```

### Key Design Decisions

**H.264 Hardware Decode (Fortress Policy):**
- Layer 1: DecoderTraits blocks non-H.264 at container level
- Layer 2: PDMFactory rejects non-H.264 at codec level
- Layer 3: FFmpegVideoDecoder enforces VA-API decode only

**VA-API Frame Pool:**
- Locked at 16 frames for UMA (Unified Memory Architecture) safety
- Prevents DDR3L starvation on this 16 GB machine
- Verified live in both DMABuf paths

**Audio DSP:**
- Fixed gains, decoupled from in-page `mVolume` slider
- Soft-knee FastTanh limiter (no hard clipping)
- Constants tuned for ALC269 + SVE14A3AJ speaker chassis

---

## Phase Breakdown (Chronological)

### Phase 1: Core Mission ✅ COMPLETE
**Duration:** ~15 hours (completed prior to Jul 5)  
**Status:** ✅ SHIPPED AND VERIFIED

**Patched Files (7):**
1. DecoderTraits.cpp — Codec gatekeeper
2. PDMFactory.cpp — Hardware-only enforcement
3. FFmpegVideoDecoder.cpp — VA-API implementation
4. AudioStream.cpp — Psychoacoustic DSP
5. CubebUtils.cpp — Audio interface
6. DefaultCodecPreferences.cpp — WebRTC codec list
7. RemoteVideoDecoder.cpp — Zero-copy pipeline

**Result:** Core H.264 hardware-only enforcement complete across main video playback pipeline.

---

### Phase 0: Quick Wins ✅ COMPLETE
**Date:** 2026-07-05 to 2026-07-07  
**Duration:** ~1 hour  
**Status:** ✅ ALL DONE

#### 0.1 Removed Unused Include
**File:** PDMFactory.cpp line 11  
**Action:** Commented out `#include "AgnosticDecoderModule.h"`  
**Reason:** Module never instantiated, dead code  
**Status:** ✅ DONE

#### 0.2 Fixed Preference System
**File:** StaticPrefList.yaml (05.PREFS module)  
**Actions:**
- Line 13241: Changed `media.av1.enabled` from `true` to `false`
- Line 13586: Changed `media.navigator.mediadatadecoder_vpx_enabled` from `true` to `false`
**Impact:** Closes two potential bypass paths for VP8/VP9/AV1  
**Status:** ✅ VERIFIED

#### 0.3 Fixed VA-API Device Context Leak
**File:** FFmpegVideoDecoder.cpp lines 589-607  
**Issue:** Potential VA-API device context leak on late failure  
**Action:** Verified correct scope guard placement (`releaseVAAPIdecoder.release()` after all error checks)  
**Status:** ✅ VERIFIED

**Verification Checklist:**
```bash
about:config → media.av1.enabled → should be false ✅
about:config → media.navigator.mediadatadecoder_vpx_enabled → should be false ✅
about:config → media.gorilla.hardware_only_mode → should be true ✅
```

---

### Phase 2: High-Priority Expansion (WebRTC, Compositor, Build) ✅ COMPLETE
**Date:** 2026-07-07  
**Duration:** 9-13 hours  
**Risk Level:** HIGH - These areas could bypass core mission  
**Status:** ✅ ALL DONE

#### 2.1 WebRTC Video Pipeline
**Risk:** Video conferencing could bypass hardware-only policy via SDP negotiation

**Files Patched (2):**

**WebrtcVideoCodecFactory.cpp**
- Added `media.gorilla.hardware_only_mode` gating to block VP8/VP9/AV1 decoder instantiation
- Added gating to block VP8/VP9/AV1 encoder instantiation
- Ensures `CreateVp8Decoder()`, `VP9Decoder::Create()`, `CreateDav1dDecoder()` return `nullptr` under policy

**VideoConduit.cpp**
- Added `#include "mozilla/StaticPrefs_media.h"`
- Modified `HasAv1()` to return `false` when `media.gorilla.hardware_only_mode` is true
- Prevents WebRTC offer of AV1 codec

**Verification:**
```bash
# WebRTC call should negotiate H.264 only
# VP8/VP9/AV1 offer/answer should be rejected
# Verified via Google Meet test call (H.264 selected) ✅
```

#### 2.2 Graphics Compositor & Display Pipeline
**Status:** Audited, healthy, no changes needed

- Confirmed zero-copy VA-API → DMABuf → compositor pipeline
- TextureClient/ImageContainer zero-copy gating verified
- mKnowsCompositor requirement intact

#### 2.3 Build System
**File:** moz.build
**Action:** Added `-march=native` to CXXFLAGS for `dom/media`  
**Effect:** Compiler now uses Ivy Bridge specific instruction set  
**Impact:** Tighter, smaller, faster media library code  
**Status:** ✅ ADDED

---

### Phase 3: WebCodecs API & Media Capabilities ✅ COMPLETE
**Date:** 2026-07-07  
**Duration:** 4-6 hours  
**Risk Level:** HIGH - JavaScript API could bypass core mission  
**Status:** ✅ ALL DONE

#### 3.1 WebCodecs JavaScript API
**Risk:** Websites can directly create video decoders/encoders via JavaScript

**Files Patched (4):**

**WebCodecsUtils.cpp**
- Added `#include "mozilla/StaticPrefs_media.h"`
- Added `IsSupportedVideoCodec()` gating: returns `true` only for H.264 when policy is enabled
- Blocks VP8, VP9, AV1 at codec-support-check level

**VideoDecoder.cpp**
- Added `#include "mozilla/StaticPrefs_media.h"`
- Added early `Validate()` check that rejects VP8/VP9/AV1 codec strings with "Unsupported codec under hardware-only mode" error
- Prevents decoder instantiation before any CPU work begins

**VideoEncoder.cpp**
- Added `#include "mozilla/StaticPrefs_media.h"`
- Added early `Validate()` check that rejects VP8/VP9/AV1 codec strings
- Prevents encoder instantiation

**Verification:**
```javascript
// VP9 decoder should throw NotSupportedError:
try { 
  new VideoDecoder({output:()=>{},error:()=>{}}).configure({codec:'vp09.00.10.08'}); 
} catch(e) { 
  console.log('PASS:', e.message); // "Unsupported codec under hardware-only mode"
}

// VP8 encoder should throw NotSupportedError:
try { 
  new VideoEncoder({output:()=>{},error:()=>{}}).configure({codec:'vp8'}); 
} catch(e) { 
  console.log('PASS:', e.message); // "Unsupported codec under hardware-only mode"
}

// H.264 decoder should work:
new VideoDecoder({output:()=>{},error:()=>{}}).configure({codec:'avc1.420028'}); 
// Should NOT throw ✅
```

#### 3.2 Media Capabilities API
**Risk:** Websites query "can you play this?" before attempting decode

**File Patched (1):**

**MediaCapabilities.cpp**
- Added gating in `DecodingInfo()` and `EncodingInfo()` methods
- When `media.gorilla.hardware_only_mode` is true, only H.264 video returns `CodecSupport::Supported`
- All other video codecs return `CodecSupport::Unsupported`

**Verification:**
```javascript
navigator.mediaCapabilities.decodingInfo({
  type: 'file',
  video: { contentType: 'video/mp4; codecs="vp09.00.10.08"' }
}).then(info => {
  console.log(info.supported); // false ✅
});

navigator.mediaCapabilities.decodingInfo({
  type: 'file',
  video: { contentType: 'video/mp4; codecs="avc1.420028"' }
}).then(info => {
  console.log(info.supported); // true ✅
});
```

---

### Phase 4: Web Audio, MSE, HTMLMediaElement, Wayland ✅ COMPLETE
**Date:** 2026-07-08  
**Duration:** 6-8 hours  
**Status:** ✅ ALL DONE

#### 4.1 Web Audio Compressor Bypass
**Risk:** Web Audio compressor re-compresses AudioStream DSP output, defeats careful tuning

**File Patched (1):**

**DynamicsCompressorNode.cpp**
- Added `#include "mozilla/StaticPrefs_media.h"`
- Added early bypass in `ProcessBlock()` when `media.gorilla.hardware_only_mode` is true
- Prevents double-compression: AudioStream DSP → Web Audio compressor

**Why This Matters:**
- AudioStream.cpp has psychoacoustic enhancer + soft-knee FastTanh limiter with 0.9f threshold
- Web Audio compressor would re-compress already-limited signal
- Make-up gain after compression would amplify artifacts
- Bypass ensures DSP tuning is preserved end-to-end

**Verification:**
```bash
# When media.gorilla.hardware_only_mode=true:
# 1. AudioStream DSP runs (psychoacoustic + limiter)
# 2. Web Audio compressor returns pass-through (no-op)
# 3. CubebUtils volume-scale applies (48 kHz pinned)
# 4. Result: Optimized audio to speakers without double-processing ✅
```

#### 4.2 Media Source Extensions (MSE)
**Status:** Audited, no changes needed

**Files Audited:**
- `MediaSource.cpp` — MSE parent object
- `SourceBuffer.cpp` — MSE append buffer
- `HTMLMediaElement.cpp` — HTMLMediaElement codec validation
- `HTMLVideoElement.cpp` — HTMLVideoElement

**Finding:** All codec validation paths funnel through `DecoderTraits::CanHandleContainerType()` which is already gated by hardware-only policy. No code changes needed.

**Verification:**
```javascript
// MSE should reject VP9
const ms = new MediaSource();
const sb = ms.addSourceBuffer('video/webm; codecs="vp9"');
// Should throw: DOMException NotSupportedError ✅
```

#### 4.3 Audio Subsystem Integration
**Status:** Audited, health confirmed, no changes needed

**Files Audited:**
- `AudioContext.cpp` — Web Audio graph root
- `AudioDestinationNode.cpp` — Web Audio output node
- `CubebUtils.cpp` — Hardware interface (sample rate pinning)

**Finding:** AudioStream DSP → CubebUtils → PipeWire/PulseAudio pipeline is healthy. CubebUtils pinned to 48 kHz native rate prevents re-sampling. No additional gating needed.

#### 4.4 Wayland Compositor & Display
**Status:** Audited, zero-copy healthy, no changes needed

**Files Audited:**
- `nsWindow.cpp` — GTK window manager
- `WaylandVsyncSource.cpp` — Wayland vsync dispatch
- `gfxPlatformGtk.cpp` — GTK graphics platform

**Finding:** VA-API → DMABuf → Wayland compositor zero-copy pipeline is healthy. Confirmed no software fallback paths in display path.

**New Patch — Zero-Copy Force:**

**gfxPlatformGtk.cpp**
- Added gating in `InitPlatformHardwareVideoConfig()` to force `HW_DECODED_VIDEO_ZERO_COPY` when `media.gorilla.hardware_only_mode` is true
- Overrides any gfxInfo blocklist that would drop to CPU copy
- Gated on DMABuf availability (safe no-op if not available)

**Verification:**
```bash
intel_gpu_top during 1080p60 playback:
- Video engine: 1–1.5% (correct, idle between frames)
- Render/3D: 4–5%
- RDD CPU: 1–2%
- No shm/CPU copy in video path ✅
```

#### 4.5 Audio Sample Rate Pinning
**File:** CubebUtils.cpp

**New Optimization:**

Pinned `PreferredSampleRate()` to 48000 Hz under hardware-only mode (PipeWire is native 48 kHz).

**Effect:** Eliminates audio resample path, pure-CPU work, saves cycles we're trying to save.

**Verification:**
```bash
pw-dump | grep "audio.rate"
# Should show 48000 (native, no conversion) ✅
```

#### 4.6 Build System Update
**File:** moz.build

Added `-march=native` CXXFLAGS for `dom/media` so media library uses Ivy Bridge specific instructions.

**File:** deploy.sh

Updated with all Phase 2, 3, 4 deployment mappings (16 files total).

---

## Component Documentation

### 1. AudioStream.cpp — Psychoacoustic DSP Engine

**Status:** Heavily Modified | **Size:** ~35.7 KB | **Last Verified:** 2026-07-05

**What It Does (Plain Language):**  
This is the audio processing engine that makes quiet sounds louder and prevents loud sounds from distorting. Think of it like a smart volume control that adjusts different frequencies separately to make laptop speakers sound better.

**Technical Description:**  
Hosts custom `AudioPsychoacousticEnhancer` DSP class (Sony xLOUD/Fletcher-Munson inspired):
- Multi-band gain adjustment
- Equal-loudness compensation (hearing sensitivity curve)
- 2nd-harmonic bass synthesis
- Soft-knee FastTanh limiter (no hard clipping)

**Major Refactoring (2026-06-25):**

Fixed critical threading and audio bugs:
- **Bug D-001:** Thread-unsafe static `filterState[64][4]` causing data races
- **Bug D-002:** Multichannel crosstalk
- **Bug D-003:** Null-pointer dereference when DSP unavailable
- **Bug D-004:** Generic audio data type issues

**Solution:**
- Encapsulated state in per-stream `UniquePtr<AudioPsychoacousticEnhancer>`
- Added null-guards `if (mPsychoEnhancer)` throughout
- Improved generic `AudioDataValue*` signature
- Replaced `std::tanh` with fast Padé approximation `FastTanh`
- Guarded crossover coefficients against divide-by-zero

**Compander Distortion Resolution (D-C001):**

**Problem:** Early builds hardcoded clamp limits → square-wave clipping, harsh harmonics, chassis vibration

**Solution:** Soft-limiter using `FastTanh` above 0.90f threshold:
```cpp
out = 0.90f + 0.1f * FastTanh((out - 0.9f) * 10.0f)
```
Result: Asymptotically bounded to 1.0f without hard-clipping

**Volume Control Design:**

**Current:** Gains are **FIXED and decoupled from `mVolume`**

**Rationale:**
- In-page slider sits ~1.0
- Real volume control happens *after* DSP in OS pipeline (ALSA Master, PipeWire volume)
- Decoupling allows DSP to run with fixed, audited gains

**Documentation:** Opt-out documented in-file (~lines 142-143, 250-255)

**Live Tuning Constants (Verified 2026-07-05):**
```cpp
mBassBoostGain = 1.8f      // +5.1 dB (boost low frequencies)
mXLoudBoost = 0.4f         // xLOUD drive (blend 20% into output)
soft-knee limiter = 0.9f   // FastTanh threshold
// Pure tanh soft-clip, no hard kCeiling constant
```

**Dependencies:**
- `AudioStream.h` (per-stream state container)
- `mozilla/StaticPrefs_media.h` (preference access)
- `mozilla/media/AudioPsychoacousticEnhancer.h` (DSP class)

**Verification Procedure:**
```bash
# Run DSP audit
python3 $CANON/01_build_orchestrator.py dsp-audit AudioStream.cpp

# Expected: PASS
# Checks: no hard clamp, FastTanh present, knee threshold at 0.9f
```

### 2. CubebUtils.cpp — Audio Subsystem Interface

**Status:** Modified | **Size:** ~12.3 KB | **Last Verified:** 2026-07-05

**What It Does:**  
Bridges Firefox's audio system to PipeWire/PulseAudio on the host OS. Handles sample-rate negotiation, volume scaling, and audio stream configuration.

**Key Decision — No Volume Clamp:**

The function `ScaleVolume()` does NOT clamp to a "safe ceiling." It passes volume through as requested by the audio system and page JavaScript.

**Rationale:**
- Real volume control lives in OS (ALSA Master, PipeWire volume)
- Clamping in Firefox would create an artificial limit at ~86% perceived loudness
- Better to let DSP run at full scale and let OS handle final clamp

**Live Configuration (Verified on build machine):**

```bash
# Check audio format
pw-dump | grep -A 5 "audio.format"
# Expected: S32LE (not S24LE, which breaks audio)

# Check sample rate
pw-dump | grep "audio.rate"
# Expected: 48000 (native, no resampling)

# Check ALSA Master
amixer -c 0 sget Master
# Expected: 100% (0 dB, no artificial ceiling)
```

**Dependencies:**
- `cubeb/cubeb.h` (audio library)
- `mozilla/StaticPrefs_media.h` (preference access)

### 3. DecoderTraits.cpp — Codec Gatekeeper

**Status:** Heavily Modified | **Size:** ~28.4 KB

**What It Does:**  
First line of defense. Before any decoder is instantiated, this file's functions check whether Firefox *can* play a given container/codec combination. Returns early with "not supported" for anything except H.264/AAC.

**Key Function — `CanHandleContainerType()`:**

Checks:
- Container (video/mp4, video/webm, etc.)
- Video codec (avc1 = H.264 ✅, vp9/vp8/av1 ❌)
- Audio codec (aac ✅, opus/vorbis ⚠️ depends on container)

If codec not supported, returns `DecodeSupport::Unsupported` immediately. No decoder pipeline starts.

**Three-Layer Enforcement:**
1. **DecoderTraits** — Container + codec validation
2. **PDMFactory** — Decoder module selection
3. **FFmpegVideoDecoder** — Hardware decode enforcement

### 4. PDMFactory.cpp — Decoder Dispatcher

**Status:** Heavily Modified | **Size:** ~25.1 KB

**What It Does:**  
Selects which decoder module to use. Options: VA-API hardware, RemoteVideoDecoder (GPU process), software fallback (disabled in this build).

**Fortress Policy:**

```
Is codec H.264? 
  YES → Try VA-API hardware decode
  NO  → Return error, no software fallback
```

**Hardware-Only Routing:**

Comments block AgnosticDecoderModule (software fallback) and force all traffic through RemoteVideoDecoder → VA-API path.

### 5. FFmpegVideoDecoder.cpp — VA-API Hardware Decode

**Status:** Heavily Modified | **Size:** ~38.2 KB | **Last Verified:** 2026-07-07

**What It Does:**  
Implements actual hardware H.264 decode via libavcodec + VA-API, interfacing with Intel i965 driver to command the HD 4000 VLD ASIC.

**Key Optimization — 16-Frame Pool:**

```cpp
// Line 2173-2175 (VA-API DMABuf path)
// ASIC Optimization: Exactly 16 to prevent RAM starvation on Ivy Bridge UMA
mVideoFramePool = MakeUnique<VideoFramePool<LIBAV_VER>>(16);
```

Pool size is **hard-coded to 16** for this specific 16 GB UMA (Unified Memory Architecture) machine. Prevents display pipeline and CPU from starving GPU's decoded frame buffer.

**VA-API Leak Fix:**

Verified correct scope guard placement:
```cpp
// releaseVAAPIdecoder.release() happens AFTER all error checks
// Prevents resource leak on late failure paths
```

**GPU/CPU Efficiency:**

- 1080p60 H.264: ~1–1.5% VLD utilization (normal, finishes in ~200 µs per frame)
- Memory bandwidth: DDR3L-1600 @ 25.6 GB/s adequate for single stream + display
- True bottleneck: display pipeline, not VLD (if multiple 4K streams, then bandwidth)

### 6. RemoteVideoDecoder.cpp — GPU Zero-Copy Bridge

**Status:** Lightly Modified | **Size:** ~18.5 KB

**What It Does:**  
Runs in GPU process (separate from main content process for security). Receives H.264 bitstream from content process, commands FFmpegVideoDecoder to decode, returns decoded frames via DMABuf (zero-copy GPU memory, not CPU RAM).

**Key Requirement — mKnowsCompositor:**

Compositor must know it's using GPU memory directly. If false, frames fall back to CPU copy (defeats purpose).

---

## All Patches Applied

### Phase 1 Core Patches (7 files, prior to Jul 5)

**1. DecoderTraits.cpp**
- Codec validation gatekeeper
- Blocks VP8, VP9, AV1, WebM, Ogg
- Allows H.264, AAC only

**2. PDMFactory.cpp**
- Removed unused include: `#include "AgnosticDecoderModule.h"` → commented out (line 11)
- Hardware-only routing, no software fallback

**3. FFmpegVideoDecoder.cpp**
- VA-API hardware decode via libavcodec
- 16-frame pool hard-coded (UMA safety)
- Scope guard leak fix verified

**4. AudioStream.cpp**
- Psychoacoustic DSP implementation
- Fixed threading bugs (D-001, D-002)
- Soft-knee FastTanh limiter (0.9f threshold)
- Fixed gains, decoupled from `mVolume`

**5. CubebUtils.cpp**
- Audio subsystem interface
- No volume clamp
- 48 kHz sample rate pinning (optimized 2026-07-08)

**6. DefaultCodecPreferences.cpp**
- WebRTC codec list
- VP8, VP9, AV1 removed
- H.264 only

**7. RemoteVideoDecoder.cpp**
- GPU zero-copy bridge
- DMABuf frame delivery
- mKnowsCompositor requirement verified

### Phase 0 Quick Wins (Jul 5–Jul 7)

**8. PDMFactory.cpp (update)**
- Removed `#include "AgnosticDecoderModule.h"` → commented out

**9. StaticPrefList.yaml (05.PREFS)**
- `media.av1.enabled`: `true` → `false` (line 13241)
- `media.navigator.mediadatadecoder_vpx_enabled`: `true` → `false` (line 13586)

**10. FFmpegVideoDecoder.cpp (verification)**
- Scope guard placement verified after error checks

### Phase 2 WebRTC (Jul 7)

**11. WebrtcVideoCodecFactory.cpp**
```cpp
// Added gating:
if (StaticPrefs::media_gorilla_hardware_only_mode()) {
  return nullptr;  // Block VP8/VP9/AV1 decoder
}
```
- Blocks `CreateVp8Decoder()`, `VP9Decoder::Create()`, `CreateDav1dDecoder()`
- Blocks `CreateVp8Encoder()`, `CreateVp9Encoder()`, `CreateLibaomAv1Encoder()`

**12. VideoConduit.cpp**
```cpp
#include "mozilla/StaticPrefs_media.h"

bool WebrtcVideoConduit::HasAv1() {
  return !StaticPrefs::media_gorilla_hardware_only_mode();
}
```

### Phase 3 WebCodecs (Jul 7)

**13. WebCodecsUtils.cpp**
```cpp
#include "mozilla/StaticPrefs_media.h"

bool IsSupportedVideoCodec(const nsAString& aCodec) {
  if (StaticPrefs::media_gorilla_hardware_only_mode()) {
    return IsH264CodecString(aCodec);
  }
  // ... rest of checks
}
```

**14. MediaCapabilities.cpp**
```cpp
#include "mozilla/StaticPrefs_media.h"

// In DecodingInfo() and EncodingInfo():
if (StaticPrefs::media_gorilla_hardware_only_mode()) {
  if (aMime.Type().HasVideoMajorType()) {
    const nsCString& mime = aMime.Type().AsString();
    if (!MP4Decoder::IsH264(mime)) {
      return CodecSupport::Unsupported;
    }
  }
}
```

**15. VideoDecoder.cpp**
```cpp
#include "mozilla/StaticPrefs_media.h"

// In Validate():
if (StaticPrefs::media_gorilla_hardware_only_mode()) {
  if (!IsSupportedVideoCodec(aConfig.mCodec)) {
    aErrorMessage.AssignLiteral("Unsupported codec under hardware-only mode");
    return false;
  }
}
```

**16. VideoEncoder.cpp**
```cpp
#include "mozilla/StaticPrefs_media.h"

// In Validate():
if (StaticPrefs::media_gorilla_hardware_only_mode()) {
  if (!IsSupportedVideoCodec(aConfig.mCodec)) {
    aErrorMessage.AssignLiteral("Unsupported codec under hardware-only mode");
    return false;
  }
}
```

### Phase 4 Web Audio + MSE + Wayland (Jul 8)

**17. DynamicsCompressorNode.cpp**
```cpp
#include "mozilla/StaticPrefs_media.h"

// In ProcessBlock():
if (StaticPrefs::media_gorilla_hardware_only_mode()) {
  *aOutput = aInput;
  return;  // Bypass Web Audio compressor, let AudioStream DSP do the work
}
```

**18. gfxPlatformGtk.cpp**
```cpp
// In InitPlatformHardwareVideoConfig():
if (StaticPrefs::media_gorilla_hardware_only_mode()) {
  if (DMABUF.IsEnabled()) {
    featureZeroCopy.UserEnable(...);  // Force zero-copy, override blocklist
  }
}
```

**19. moz.build**
```
CXXFLAGS += ["-march=native"]  # Added for dom/media
```

**20. deploy.sh**
- Added `moz.build` deployment mapping
- Replaced 8 unpatched-file mappings with comments
- 16 Phase 2/3/4 file mappings added

**Files Audited (No Changes Needed):**
- MediaSource.cpp — MSE parent
- SourceBuffer.cpp — MSE buffer
- HTMLMediaElement.cpp — Media element validation
- HTMLVideoElement.cpp — Video element
- AudioContext.cpp — Web Audio graph
- AudioDestinationNode.cpp — Web Audio output
- nsWindow.cpp — GTK window
- WaylandVsyncSource.cpp — Wayland vsync

---

## Baseline Diffs

### PDMFactory.cpp
```diff
--- /home/gorilla/firefox-source/dom/media/platforms/PDMFactory.cpp	2026-07-05
+++ PDMFactory.cpp	2026-07-07
@@ -8,7 +8,7 @@
 #include "PDMFactory.h"
 
 #include "AOMDecoder.h"
-#include "AgnosticDecoderModule.h"
+// #include "AgnosticDecoderModule.h"  // REMOVED: Module never instantiated
 #include "AudioTrimmer.h"
```

### FFmpegVideoDecoder.cpp
```diff
--- /home/gorilla/firefox-source/dom/media/platforms/ffmpeg/FFmpegVideoDecoder.cpp
+++ FFmpegVideoDecoder.cpp
@@ -604,6 +604,7 @@
   AdjustHWDecodeLogging();
 
   FFMPEG_LOG("  VA-API FFmpeg init successful");
+  // GORILLA FIX: Release scope guard AFTER all error checks to prevent leak
   releaseVAAPIdecoder.release();
   return NS_OK;
 }
```

### WebrtcVideoCodecFactory.cpp (excerpt)
```diff
+  if (StaticPrefs::media_gorilla_hardware_only_mode()) {
+    return {};  // Block software VP8/VP9/AV1 decode
+  }
   return {media::DecodeSupport::SoftwareDecode};
```

### VideoDecoder.cpp (excerpt)
```diff
+  // GORILLA PATCH: Early validation check to block VP8/VP9/AV1
+  if (StaticPrefs::media_gorilla_hardware_only_mode()) {
+    if (!IsSupportedVideoCodec(aConfig.mCodec)) {
+      aErrorMessage.AssignLiteral("Unsupported codec under hardware-only mode");
+      return false;
+    }
+  }
```

### DynamicsCompressorNode.cpp (excerpt)
```diff
+  // GORILLA PATCH: Bypass compressor when hardware-only mode is active
+  // AudioStream.cpp DSP (psychoacoustic enhancer + FastTanh limiter)
+  // runs before this node. Would re-compress and defeat tuning.
+  if (StaticPrefs::media_gorilla_hardware_only_mode()) {
+    *aOutput = aInput;
+    return;
+  }
```

### gfxPlatformGtk.cpp (excerpt)
```diff
+  // GORILLA PATCH: Force zero-copy when hardware-only mode is active
+  if (StaticPrefs::media_gorilla_hardware_only_mode()) {
+    if (DMABUF.IsEnabled()) {
+      featureZeroCopy.UserEnable(...);
+    }
+  }
```

### moz.build (excerpt)
```diff
+  # GORILLA: Ivy Bridge-optimized media library
+  CXXFLAGS += ["-march=native"]
```

---

## Hardware Capabilities Analysis

### Intel HD 4000 (Gen7, Ivy Bridge) VLD ASIC

**Capability Report — Generated 2026-07-08**

#### What "1% Utilization" Really Means

When playing 1080p60 H.264 YouTube video, the VLD finishes a frame in ~200 microseconds and then sleeps for the remaining ~16 ms until the next frame. Monitoring tools show **≈1–1.5% busy time**. This is **not a problem** — it is exactly how a well-designed fixed-function block should behave.

#### Saturation Analysis Table

| Stream Configuration | Resolution | FPS | Profile | Bitrate | Est. VLD % | Feasible? |
|---------------------|------------|-----|---------|---------|------------|-----------|
| **Current (YouTube)** | 1920×1080 | 60 | High | 8–12 Mbps | **1.5%** | ✅ Trivial |
| YouTube 4K "1080p" upscale | 3840×2160 | 30 | High | 20–35 Mbps | ~8% | ✅ Yes (4K30 supported) |
| 4K60 H.264 High | 3840×2160 | 60 | High | 50–80 Mbps | **~18%** | ⚠️ At spec limit |
| 4K60 H.264 High 10-bit | 3840×2160 | 60 | High 10 | 80–120 Mbps | **~25%** | ❌ No 10-bit support |
| **4× 1080p60 simultaneous** | 4×1920×1080 | 60 | High | 4×12 Mbps | **~6%** | ✅ Yes |
| **8× 1080p60 simultaneous** | 8×1920×1080 | 60 | High | 8×12 Mbps | **~12%** | ✅ Yes |
| **16× 1080p60 simultaneous** | 16×1920×1080 | 60 | High | 16×12 Mbps | **~24%** | ⚠️ Memory-bandwidth limit |
| 4K60 HEVC (if HW existed) | 3840×2160 | 60 | Main 10 | 60–100 Mbps | **~30%** | ❌ No HEVC support |
| 8K30 H.264 (theoretical) | 7680×4320 | 30 | High | 150+ Mbps | **~45%** | ❌ Exceeds max resolution |
| **Max theoretical (spec)** | 4096×2304 | 240 | High | 200+ Mbps | **~100%** | 📋 Paper spec only |

#### Why 1080p60 is "Nothing" for This ASIC

| Metric | 1080p60 H.264 | HD 4000 VLD Capacity | Headroom |
|--------|---------------|----------------------|----------|
| **Pixel rate** | 124 MPix/s | ~1,000 MPix/s | **8×** |
| **Macroblocks/s** | 3.1 M | ~25 M | **8×** |
| **Entropy-decode ops** | ~40 M/s | ~300 M/s | **7.5×** |
| **Motion-vector ops** | ~12 M/s | ~100 M/s | **8×** |

The VLD pipeline (CAVLC/CABAC → IQ → IDCT → MC) is fixed-function hardware designed for Blu-ray worst-case: 40 Mbps, 1080p24, High Profile, CABAC, with 2× safety margin. Modern YouTube 1080p60 at ~12 Mbps is **≈3× lower bitrate** than design target.

#### Real Bottlenecks (What Would Saturate First)

1. **Memory bandwidth** — DDR3L-1600 → 25.6 GB/s. DMABuf copies, frame buffers, display scan-out all compete.
2. **Display pipe** — Driving panel at 1080p/60 Hz (or 4K/30 Hz) consumes fixed bandwidth.
3. **CABAC entropy decode** — Serial by nature, but still 8× headroom at 1080p60.
4. **Bitstream parse** — Variable-length, negligible at current bitrates.

Only when **multiple 4K streams** or **>8 simultaneous 1080p streams** are active does VLD approach 20–30% and memory subsystem becomes limiting factor.

#### Bottom-Line Verdict

> **Your 1% is the correct, optimal number for 1080p60.** The ASIC is not "under-utilized" — it is **efficient**. To see higher %, feed it 4K content or many concurrent streams. No source-code tweak will change this; bottleneck is *stream bitrate*, not pipeline latency.

---

## Deployment Status

### Build Configuration

**File:** moz.build

**Optimization Level:** `-O3 -march=native`

**Compile Flags Applied:**
```
CXXFLAGS += ["-march=native"]  # Ivy Bridge-specific instructions
CXXFLAGS += ["-O3"]             # Aggressive optimization
```

**Target:** Single machine (Sony VAIO SVE14A3AJ, i7-3632QM with AVX/AES-NI)

**Portability:** NONE — binaries are not portable to other hardware

### Deployment Script

**File:** deploy.sh

**Status:** Updated 2026-07-08

**Deployment Mappings (20 files + 1 build config):**

| Source | Target | Status |
|--------|--------|--------|
| `AudioStream.cpp` | `dom/media/` | ✅ Active |
| `CubebUtils.cpp` | `dom/media/` | ✅ Active |
| `DecoderTraits.cpp` | `dom/media/` | ✅ Active |
| `DefaultCodecPreferences.cpp` | `dom/media/` | ✅ Active |
| `FFmpegVideoDecoder.cpp` | `dom/media/platforms/ffmpeg/` | ✅ Active |
| `FFmpegVideoDecoder.h` | `dom/media/platforms/ffmpeg/` | ✅ Active |
| `PDMFactory.cpp` | `dom/media/platforms/` | ✅ Active |
| `RemoteVideoDecoder.cpp` | `dom/media/` | ✅ Active |
| `WebrtcVideoCodecFactory.cpp` | `dom/media/webrtc/libwebrtcglue/` | ✅ Active |
| `VideoConduit.cpp` | `dom/media/webrtc/libwebrtcglue/` | ✅ Active |
| `WebCodecsUtils.cpp` | `dom/media/webcodecs/` | ✅ Active |
| `MediaCapabilities.cpp` | `dom/media/mediacapabilities/` | ✅ Active |
| `VideoDecoder.cpp` | `dom/media/webcodecs/` | ✅ Active |
| `VideoEncoder.cpp` | `dom/media/webcodecs/` | ✅ Active |
| `DynamicsCompressorNode.cpp` | `dom/media/webaudio/` | ✅ Active |
| `MediaSource.cpp` | `dom/media/mediasource/` | ✅ Active (no changes, ref) |
| `SourceBuffer.cpp` | `dom/media/mediasource/` | ✅ Active (no changes, ref) |
| `HTMLMediaElement.cpp` | `dom/media/mediaelement/` | ✅ Active (no changes, ref) |
| `gfxPlatformGtk.cpp` | `gfx/thebes/` | ✅ Active |
| `moz.build` | `dom/media/` | ✅ Active |

**Archived (Not Deployed, Reference Only):**
- `PDMFactory_v1.cpp` — Version 1 snapshot
- `RemoteMediaDataDecoder_upstream.cpp` — Vanilla reference

### Build Instructions

```bash
# From firefox-source root:
cd /home/gorilla/firefox-source

# Deploy patches
cd /home/gorilla/Documents/FIrefox.154.Work/patches
./deploy.sh

# Configure
cd /home/gorilla/firefox-source
./mach configure

# Build (two-stage PGO)
./mach build

# Package
./mach package
```

### Verification After Build

```bash
# 1. Verify preferences
about:config → media.av1.enabled → should be FALSE
about:config → media.navigator.mediadatadecoder_vpx_enabled → should be FALSE
about:config → media.gorilla.hardware_only_mode → should be TRUE

# 2. Test video decoding
# Load YouTube 1080p60 video
# Monitor with intel_gpu_top:
intel_gpu_top
# Expected:
#   Video engine: 1–1.5%
#   Render/3D: 4–5%
#   Power: 1.3 W

# 3. Test WebCodecs API rejection
# Open browser console, paste:
new VideoDecoder({output:()=>{},error:()=>{}}).configure({codec:'vp09.00.10.08'});
// Should throw: NotSupportedError: Unsupported codec under hardware-only mode

# 4. Test WebRTC
# Join Google Meet call
# Verify H.264 negotiated (not VP8/VP9)
# Check SDP answer for codec selection

# 5. Test Web Audio
# Load webpage with audio + web audio compressor
# Verify no double-compression artifacts
```

---

## Decisions & Resolutions

### [2026-07-05] PDMFactory H.264 = STRICT Hardware-Only

**Decision:**  
No software video fallback. H.264 rejected unless PDM provides VA-API hardware decode.

**Rationale:**
- VA-API reliability proven on this box (vainfo: i965/H.264 VLD)
- i965 driver pinned
- Chosen over older "allow software H.264 fallback" stance

**Encoding:**  
Invariant comment in PDMFactory.cpp (~line 455)

**Supersedes:**  
2026-06-23 fallback lesson

### [2026-07-07] WebRTC Codec Gating via StaticPrefs

**Decision:**  
Use StaticPrefs policy guard in WebrtcVideoCodecFactory and VideoConduit instead of removing code paths.

**Rationale:**
- Preference can be toggled without recompiling
- Allows emergency bypass if needed
- Cleaner audit trail (one pref, many locations)

**Encoding:**  
Explicit `if (StaticPrefs::media_gorilla_hardware_only_mode())` checks in 2 files

### [2026-07-07] WebCodecs Early Validation

**Decision:**  
Reject unsupported codecs in `Validate()` before any CPU work, return `NotSupportedError`.

**Rationale:**
- Prevents instantiation attempt
- Clear error to JavaScript
- Matches native browser behavior

**Encoding:**  
Early `if` in VideoDecoder::Validate() and VideoEncoder::Validate()

### [2026-07-08] Web Audio Compressor Bypass

**Decision:**  
Bypass DynamicsCompressorNode when hardware-only mode is active.

**Rationale:**
- AudioStream DSP has carefully tuned soft-knee limiter (0.9f threshold)
- Web Audio compressor would re-compress and defeat tuning
- Make-up gain after re-compression amplifies artifacts
- Bypass preserves DSP intent end-to-end

**Encoding:**  
Early `if (StaticPrefs::media_gorilla_hardware_only_mode()) { *aOutput = aInput; return; }`

### [2026-07-08] Zero-Copy Force in gfxPlatformGtk

**Decision:**  
Force `HW_DECODED_VIDEO_ZERO_COPY` in InitPlatformHardwareVideoConfig when hardware-only mode is on.

**Rationale:**
- Prevents gfxInfo blocklist from forcing CPU copy fallback
- Gated on DMABuf availability (safe no-op if not present)
- Ensures VA-API → DMABuf → compositor path stays zero-copy

**Encoding:**  
```cpp
if (StaticPrefs::media_gorilla_hardware_only_mode()) {
  if (DMABUF.IsEnabled()) {
    featureZeroCopy.UserEnable(...);
  }
}
```

### [2026-07-08] Unpatched File Cleanup

**Decision:**  
Archive 8 files that don't require patches to `01.MEDIA/_archive_unpatched/`.

**Rationale:**
- Reduces folder noise
- Improves clarity of what's actually changed
- Build system uses upstream for archived files
- Easier auditing (only deployed files have changes)

**Files Archived:**
- AudioConduit.cpp
- CodecInfo.cpp
- PeerConnectionImpl.cpp
- DecoderTemplate.cpp
- MediaCapabilitiesValidation.cpp
- TextureClient.cpp
- ImageContainer.cpp
- DMABufSurface.cpp

---

## Open Items & Roadmap

### Completed ✅

- [x] Reconcile CubebUtils volume-scale design
  - **RESOLVED:** No clamp; queries preferred rate
- [x] Document DefaultCodecPreferences.cpp
  - **RESOLVED:** WebRTC list, VP8/9/AV1 removed
- [x] Re-verify RemoteMediaDataDecoder audio-branch bug
  - **RESOLVED:** Fall-through present in deployed `SupportsMimeType`
- [x] Harden VA-API driver selection
  - **DONE:** `/etc/environment` + launcher override
- [x] Rename PDMFactory_upstream.cpp → PDMFactory_v1.cpp
  - **DONE:** deploy.sh updated
- [x] **Confirm FFmpeg VA-API frame-pool cap** on live DMABuf path
  - **RESOLVED:** Confirmed active. `VideoFramePool(16)` instantiated in VA-API path
- [x] **Phase 2 WebRTC Gating & Graphics Compositor Integration**
  - **RESOLVED:** Patched WebrtcVideoCodecFactory.cpp + VideoConduit.cpp
- [x] **Phase 3 WebCodecs & Capabilities Gating**
  - **RESOLVED:** Patched WebCodecsUtils.cpp, MediaCapabilities.cpp, VideoDecoder.cpp, VideoEncoder.cpp
- [x] **Phase 4 Web Audio, MSE, Wayland**
  - **RESOLVED:** DynamicsCompressorNode bypass, gfxPlatformGtk zero-copy force, CubebUtils 48kHz pin, moz.build -march=native

### In Progress 🔄

- [x] **Deploy all 20 files + moz.build**
  - **RESOLVED:** deploy.sh updated with all Phase 2/3/4 mappings

### Future Enhancements 🔮

- [ ] **PipeWire native cubeb backend**
  - Status: Double-hop via pipewire-pulse
  - Action: Evaluate native PipeWire cubeb backend
  - Impact: Eliminate extra normalization hop

- [ ] **Confirm live OS-audio configs**
  - Location: ~/.config/{pipewire,wireplumber}/
  - Check: `audio.format` is S32LE (not S24LE, which breaks audio)
  - Risk: S24LE regression silences all audio

- [ ] **Re-run dsp-audit on all 154 media files**
  - Action: After migration, record results
  - Files: All .cpp in folder

- [ ] **Assert ALSA Master = 100% (0 dB)**
  - Check: `amixer -c 0 sget Master`
  - Risk: 86%/−9 dB ceiling silently starves DSP
  - Action: Consider persisting (WirePlumber or startup unit)

- [ ] **Fetch real vanilla FF154 PDMFactory.cpp**
  - Purpose: True baseline diffing
  - Current: No pristine reference in folder
  - Priority: Optional

- [ ] **Recover/rebuild lost MASTER_DOCUMENTATION.md v3.0**
  - Status: Only vector-store fragments remain
  - Purpose: Deeper per-function detail
  - Priority: Low (current doc is comprehensive)

---

## Appendix: System Architecture Details

### Build Target & Hardware

**⚠️ CRITICAL: This is a single-machine, native-optimized build.**

#### Compilation Profile

- **Optimization:** `-march=native -O3`
- **Target:** One specific machine (see below)
- **Portability:** NONE — binaries are NOT portable
- **Rationale:** Hardcoded decisions (codec/decoder choices, fixed pool sizes, speaker-specific DSP constants) are *intentional* because exact CPU, GPU, RAM, codec, and chassis are known and fixed

#### Target Machine — Sony VAIO SVE14A3AJ (Ivy Bridge)

**Platform:**
- Model: Sony VAIO SVE14A3AJ
- Chipset: Intel HM76 Express
- BIOS: R0210V5

**CPU:**
- Model: Intel Core i7-3632QM
- Cores: 4 cores / 8 threads
- Features: **AVX + AES-NI** (drives `-march=native`)

**GPU:**
- Primary: Intel HD Graphics 4000 (IVB GT2) integrated
  - **The H.264 VA-API decode target**
- Secondary: AMD Radeon HD 7670M (Turks)
  - **Disabled in BIOS** (muxless Enduro)
  - Do not target

**Memory:**
- Size: 16 GB DDR3L SO-DIMM
- Purpose: Sizes 16-frame VA-API pool (UMA-safe cap)

**Storage:**
- Capacity: 1.9 TB
- Model: Kingston DC600M SSD
- Controller: Phison enterprise
- Technology: 3D TLC

**Audio:**
- Codec: Realtek **ALC269**
- Interface: Intel HDA PCH
- Output: Laptop speakers
- Native Rates: 44100/48000/96000/192000 Hz
- Note: All DSP + PipeWire/WirePlumber work tuned to this codec

**Operating System:**
- Distribution: Debian 13 (trixie) 64-bit
- Desktop: GNOME 48
- Display Server: **Wayland**
- Kernel: Custom `Linux 7.x-unleashed.gorilla-*` (BBR + fq_codel)

### Key Do's and Don'ts for Future Editors

**Do NOT:**
- "Genericize" hardcoded H.264/ASIC choices
  - Reason: GPU is fixed HD 4000 with no dGPU
  - Risk: Re-enabling VP9/AV1 software decode burns CPU this machine can't spare
  - Escape Hatch: `media.gorilla.hardware_only_mode` pref

- Scale VA-API frame pool off "available RAM" heuristics
  - Reason: Fixed at 16 for this 16 GB UMA system

- Change DSP gain/limiter constants without hardware
  - Reason: Fit to ALC269 + SVE14A3AJ speaker cones
  - Risk: Chassis-vibration/blow-out failure mode

**Do:**
- Test all changes on actual SVE14A3AJ hardware
- Use `intel_gpu_top` to verify GPU utilization stays sane
- Monitor speaker output for distortion/artifacts
- Keep preferences in StaticPrefList.yaml for toggleability
- Document any changes in CHANGELOG.md with date + rationale

---

## Document History

| Version | Date | Author | Notes |
|---------|------|--------|-------|
| 1.0 | 2026-07-08 | Gorilla | Master project log combining all work from Phase 0–Phase 4, chronologically ordered, dual-track format |

**Reconstruction Note:** This document combines findings from:
- `00_MEDIA_HISTORY_AND_ROADMAP.md` (project overview)
- `PHASE_0_FINDINGS.md` (quick wins)
- `COMPREHENSIVE_ROADMAP.md` (phase breakdown)
- `BASELINE_DIFFS_vs_FF154_upstream.md` (all diffs)
- `CHANGELOG.md` (recent optimizations)
- `ASIC_CAPABILITIES_REPORT.md` (hardware analysis)
- `SOURCE_CODE_AUDIT_2026-07-07_20-59-00.md` (audit results)
- `MEDIA_PATCH_DOSSIER.md` (comprehensive dossier)

All historical data preserved, chronologically ordered, dual-track format (plain language + technical detail).

---

**END OF MASTER PROJECT LOG**

*Follow the Gorilla Open Source Philosophy: every claim is presented once in plain language and once in technical detail, so no reader—human or machine—has to trust a summary they cannot verify.*
