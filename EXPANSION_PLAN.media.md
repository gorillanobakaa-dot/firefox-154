# Firefox Media Stack Expansion Plan
## Phased Implementation Roadmap

**Generated:** 2026-07-07  
**Target:** Sony VAIO SVE14A3AJ (Intel HD 4000, ALC269)  
**Current Status:** Phase 1 Complete (01_MEDIA core patches)

---

## Overview

This document outlines a systematic, phased approach to expanding Firefox media stack patches beyond the core 01_MEDIA folder. The plan addresses 11 expansion areas identified through blast radius analysis, prioritized by risk and impact.

**Total Estimated Effort:** 20-25 hours across 4 phases

---

## Phase 1: Core Mission ✅ COMPLETE

**Status:** Shipped and verified  
**Effort:** ~15 hours (completed)

### Deliverables
- ✅ DecoderTraits.cpp - Codec gatekeeper (H.264-only)
- ✅ PDMFactory.cpp - Hardware-only enforcement
- ✅ FFmpegVideoDecoder.cpp - VA-API implementation
- ✅ AudioStream.cpp - Psychoacoustic DSP
- ✅ CubebUtils.cpp - Audio interface
- ✅ DefaultCodecPreferences.cpp - WebRTC codec list
- ✅ RemoteVideoDecoder.cpp - Zero-copy GPU pipeline

### Verification
- All 7 files pass philosophy consistency audit
- No contradictions found
- Hardware-only H.264 policy enforced at 3 layers
- Psychoacoustic DSP properly implemented

---

## Phase 2: High-Priority Expansion (P1)

**Status:** Planned  
**Estimated Effort:** 9-13 hours  
**Risk Level:** HIGH - These areas could bypass core mission

### 2.1 WebRTC Pipeline (4-6 hours)

**Objective:** Ensure video conferencing respects hardware-only H.264 policy

**Files to Audit/Patch:**
1. `dom/media/webrtc/jsapi/PeerConnectionImpl.cpp` (~3000 lines)
   - Audit SDP offer/answer generation
   - Verify codec negotiation only offers H.264
   - Block VP8/VP9/AV1 in SDP

2. `dom/media/webrtc/libwebrtcglue/VideoConduit.cpp` (~2000 lines)
   - Verify VA-API H.264 encode/decode usage
   - Check for software fallback paths
   - Ensure hardware encoder selection

3. `dom/media/webrtc/libwebrtcglue/AudioConduit.cpp` (~1500 lines)
   - Verify DSP integration consistency
   - Check audio processing chain
   - Ensure no conflicts with AudioStream.cpp

4. `dom/media/webrtc/libwebrtcglue/WebrtcVideoCodecFactory.cpp`
   - Audit codec factory instantiation
   - Verify VP8/VP9 codecs not created
   - Ensure H.264 hardware codec selection

5. `dom/media/webrtc/CodecInfo.cpp`
   - Verify codec capability reporting
   - Ensure VP8/VP9/AV1 reported as unsupported

**Success Criteria:**
- [ ] WebRTC video calls only negotiate H.264
- [ ] VA-API used for encode/decode in video calls
- [ ] No software codec fallback in WebRTC path
- [ ] Audio DSP consistent with AudioStream.cpp

**Verification Commands:**
```bash
# Test WebRTC codec negotiation
# In browser console during video call:
pc = RTCPeerConnection.getStats()
pc.getTransceivers()[0].sender.getParameters().codecs
# Expected: Only H.264 codecs listed

# Verify hardware encode/decode
intel_gpu_top
# Expected: Video engine utilization during call
```

**Dependencies:**
- Requires DefaultCodecPreferences.cpp (already patched)
- May need preference additions in StaticPrefList.yaml

---

### 2.2 Build System Verification (2-3 hours)

**Objective:** Ensure VP8/VP9/AV1 libraries excluded from build

**Files to Audit:**
1. `dom/media/moz.build`
   - Check media subsystem build configuration
   - Verify codec library exclusions

2. `dom/media/platforms/moz.build`
   - Check platform decoder build config
   - Verify hardware acceleration flags

3. `dom/media/platforms/ffmpeg/moz.build`
   - Verify FFmpeg/VA-API integration
   - Check hardware decode flags

4. `media/libvpx/moz.build`
   - Verify VP8/VP9 library excluded or disabled

5. `media/libaom/moz.build`
   - Verify AV1 library excluded or disabled

6. `toolkit/moz.configure`
   - Check global build configuration
   - Verify -march=native propagation

**Success Criteria:**
- [ ] libvpx (VP8/VP9) excluded from build
- [ ] libaom/libdav1d (AV1) excluded from build
- [ ] VA-API support compiled in
- [ ] -march=native propagates to media subsystem
- [ ] Binary size reduced (no unused codec libraries)

**Verification Commands:**
```bash
# Check linked libraries
ldd firefox-bin | grep -E "vpx|aom|dav1d"
# Expected: No matches (libraries not linked)

# Check binary size
ls -lh firefox-bin
# Expected: Smaller than upstream build

# Verify VA-API support
ldd firefox-bin | grep va
# Expected: libva.so present
```

---

### 2.3 Graphics Compositor Integration (3-4 hours)

**Objective:** Verify zero-copy DMA-BUF path and prevent VRAM leaks

**Files to Audit:**
1. `gfx/layers/client/TextureClient.cpp`
   - Verify VA-API DMA-BUF surface support
   - Check texture lifecycle management
   - Ensure VRAM leak prevention

2. `gfx/layers/ImageContainer.cpp`
   - Verify zero-copy frame handling
   - Check frame pool management
   - Ensure proper cleanup on errors

3. `widget/gtk/DMABufSurface.cpp`
   - Verify Wayland DMA-BUF integration
   - Check surface creation/destruction
   - Ensure proper error handling

4. `dom/media/platforms/ffmpeg/FFmpegVideoFramePool.cpp`
   - Verify 16-frame pool limit
   - Check UMA memory safety
   - Ensure proper frame recycling

**Success Criteria:**
- [ ] DMA-BUF surfaces used for VA-API frames
- [ ] Zero-copy path working on Wayland
- [ ] No VRAM leaks on compositor crashes
- [ ] 16-frame pool limit enforced
- [ ] Proper cleanup on decode errors

**Verification Commands:**
```bash
# Check DMA-BUF usage
cat /proc/$(pgrep firefox)/maps | grep dmabuf
# Expected: DMA-BUF mappings present during video playback

# Monitor VRAM usage
intel_gpu_top
# Expected: Stable VRAM usage, no leaks

# Check for memory leaks
valgrind --leak-check=full firefox
# Expected: No VA-API/DMA-BUF related leaks
```

**Dependencies:**
- Requires RemoteVideoDecoder.cpp (already patched)
- May need Wayland-specific configuration

---

## Phase 3: Medium-Priority Expansion (P2)

**Status:** Planned  
**Estimated Effort:** 5-6 hours  
**Risk Level:** MEDIUM - Could bypass policy but less commonly used

### 3.1 WebCodecs API (3-4 hours)

**Objective:** Block VP8/VP9/AV1 in modern encode/decode API

**Files to Audit/Patch:**
1. `dom/media/webcodecs/VideoDecoder.cpp`
   - Audit VideoDecoder.configure() codec validation
   - Block VP8/VP9/AV1 codec strings
   - Ensure H.264 uses VA-API

2. `dom/media/webcodecs/VideoEncoder.cpp`
   - Audit VideoEncoder.configure() codec validation
   - Block VP8/VP9/AV1 encoding
   - Ensure H.264 uses VA-API encoder

3. `dom/media/webcodecs/DecoderTemplate.cpp`
   - Verify generic decoder template
   - Check for software fallback paths
   - Ensure PDMFactory integration

4. `dom/media/webcodecs/WebCodecsUtils.cpp`
   - Audit utility functions
   - Verify codec string validation
   - Check capability reporting

**Success Criteria:**
- [ ] `new VideoDecoder({codec: 'vp09'})` throws error
- [ ] `new VideoDecoder({codec: 'av01'})` throws error
- [ ] `new VideoDecoder({codec: 'avc1.42E01E'})` uses VA-API
- [ ] `new VideoEncoder({codec: 'avc1'})` uses VA-API encoder
- [ ] No software fallback in WebCodecs path

**Verification Commands:**
```javascript
// Test in browser console
try {
  const decoder = new VideoDecoder({
    output: () => {},
    error: () => {}
  });
  decoder.configure({codec: 'vp09.00.10.08'});
  console.log('FAIL: VP9 not blocked');
} catch (e) {
  console.log('PASS: VP9 blocked');
}

// Test H.264 hardware decode
const decoder = new VideoDecoder({
  output: () => {},
  error: () => {}
});
decoder.configure({codec: 'avc1.42E01E', hardwareAcceleration: 'prefer-hardware'});
// Check intel_gpu_top for video engine usage
```

---

### 3.2 Media Capabilities API (2 hours)

**Objective:** Report VP8/VP9/AV1 as unsupported, H.264 as hardware

**Files to Audit/Patch:**
1. `dom/media/mediacapabilities/MediaCapabilities.cpp`
   - Audit decodingInfo() implementation
   - Ensure VP8/VP9/AV1 reported as unsupported
   - Ensure H.264 reported as smooth/powerEfficient

2. `dom/media/mediacapabilities/MediaCapabilitiesValidation.cpp`
   - Audit codec validation logic
   - Verify integration with DecoderTraits
   - Check hardware capability detection

**Success Criteria:**
- [ ] `navigator.mediaCapabilities.decodingInfo({type: 'file', video: {contentType: 'video/webm; codecs=vp9'}})` returns `supported: false`
- [ ] `navigator.mediaCapabilities.decodingInfo({type: 'file', video: {contentType: 'video/mp4; codecs=avc1.42E01E'}})` returns `supported: true, smooth: true, powerEfficient: true`
- [ ] Respects media.gorilla.hardware_only_mode preference

**Verification Commands:**
```javascript
// Test in browser console
navigator.mediaCapabilities.decodingInfo({
  type: 'file',
  video: {
    contentType: 'video/webm; codecs=vp9',
    width: 1920,
    height: 1080,
    bitrate: 5000000,
    framerate: 30
  }
}).then(result => {
  console.log('VP9:', result.supported ? 'FAIL' : 'PASS');
});

navigator.mediaCapabilities.decodingInfo({
  type: 'file',
  video: {
    contentType: 'video/mp4; codecs=avc1.42E01E',
    width: 1920,
    height: 1080,
    bitrate: 5000000,
    framerate: 30
  }
}).then(result => {
  console.log('H.264:', result.supported && result.powerEfficient ? 'PASS' : 'FAIL');
});
```

---

## Phase 4: Low-Priority Expansion (P3)

**Status:** Future Work  
**Estimated Effort:** 6-7 hours  
**Risk Level:** LOW - Nice-to-have improvements

### 4.1 Media Source Extensions (2 hours)
- Verify MSE respects codec blocking
- Audit SourceBuffer.addSourceBuffer() validation

### 4.2 HTMLMediaElement Integration (2 hours)
- Verify canPlayType() respects DecoderTraits
- Improve error messages for blocked codecs

### 4.3 Web Audio API Integration (2 hours)
- Verify no conflicts with psychoacoustic DSP
- Check DynamicsCompressorNode interaction

### 4.4 Platform-Specific (Wayland) (1 hour)
- Verify Wayland zero-copy working
- Check vsync timing

---

## Phase 0: Immediate Quick Wins (P0)

**Status:** Can be done now  
**Estimated Effort:** 1 hour  
**Risk Level:** NONE - Cleanup only

### 0.1 Remove Unused Include (5 minutes)
**File:** `PDMFactory.cpp` line 11  
**Action:** Remove `#include "AgnosticDecoderModule.h"`  
**Reason:** Module never instantiated, include is dead code

### 0.2 Verify Preference System (30 minutes)
**Files:** `modules/libpref/init/StaticPrefList.yaml`  
**Actions:**
- [ ] Verify media.gorilla.hardware_only_mode defined (default: true)
- [ ] Verify media.ffmpeg.vaapi.enabled = true
- [ ] Verify media.hardware-video-decoding.enabled = true
- [ ] Verify media.navigator.mediadatadecoder_vpx_enabled = false
- [ ] Verify media.av1.enabled = false
- [ ] Document all codec-related preferences

### 0.3 Document Expansion Roadmap (25 minutes)
**File:** Create `EXPANSION_PLAN.md` in patches folder  
**Action:** Document this phased plan for future reference

---

## Implementation Strategy

### Session-Based Approach

**Session 1 (Phase 0 + Start Phase 2.1):**
- Remove unused include
- Verify preferences
- Copy PeerConnectionImpl.cpp
- Initial audit of SDP negotiation

**Session 2 (Continue Phase 2.1):**
- Implement WebRTC patches
- Test video call codec negotiation
- Document findings

**Session 3 (Phase 2.2 + 2.3):**
- Build system verification
- Graphics compositor audit
- Document requirements

**Session 4 (Phase 3):**
- WebCodecs patches
- Media Capabilities patches
- Integration testing

**Session 5 (Phase 4 - Optional):**
- MSE/HTMLMediaElement improvements
- Web Audio verification
- Platform-specific tuning

---

## Risk Mitigation

### Backup Strategy
- Keep pristine upstream files for diffing
- Document all changes in patch headers
- Maintain rollback capability via git

### Testing Strategy
- Test each phase independently
- Verify no regressions in Phase 1 functionality
- Use verification commands after each change

### Documentation Strategy
- Update 00_MEDIA_HISTORY_AND_ROADMAP.md after each phase
- Document decision rationale in code comments
- Maintain audit trail in reports/

---

## Success Metrics

### Phase 1 (Complete)
- ✅ 7 files patched
- ✅ 0 critical issues
- ✅ Hardware-only policy enforced
- ✅ Psychoacoustic DSP working

### Phase 2 (Target)
- [ ] WebRTC H.264-only verified
- [ ] Build excludes VP8/VP9/AV1 libraries
- [ ] Zero-copy DMA-BUF working
- [ ] No VRAM leaks

### Phase 3 (Target)
- [ ] WebCodecs blocks VP8/VP9/AV1
- [ ] Media Capabilities reports correctly

### Phase 4 (Target)
- [ ] MSE validates codecs
- [ ] Error messages improved
- [ ] Web Audio verified

---

## Maintenance Plan

### After Each Firefox Update
1. Re-run audit on Phase 1 files (01_MEDIA)
2. Check for upstream changes in expansion files
3. Re-apply patches if needed
4. Update documentation

### Quarterly Review
- Review new Firefox media features
- Identify new expansion opportunities
- Update phased plan

---

## Contact & Support

**Primary Maintainer:** Gorilla  
**Documentation:** `/home/gorilla/Documents/FIrefox.154.Work/patches/`  
**Audit System:** `/home/gorilla/Documents/FIrefox.154.Work/patches/LLM.Prompts/Audit.Scripts/`

For questions or issues, refer to:
- `01_MEDIA/00_MEDIA_HISTORY_AND_ROADMAP.md` - Core mission documentation
- `reports/01_MEDIA_AUDIT_REPORT.md` - Latest audit findings
- `01_MEDIA/prompt.txt` - Audit methodology

---

**Last Updated:** 2026-07-07  
**Next Review:** After Phase 2 completion
