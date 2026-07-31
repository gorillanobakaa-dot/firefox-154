# Gorilla Unleashed — Media Codec Lessons Learned
# Consolidated from: LESSONS_MASTER.md, BUG_FIXES_COMPLETED_ALL_9_BUGS_RESOLVED.xml,
#   Bug_Fixes_Report_Firefox_Unleashed_Zero_CPU_Media_Pipeline.xml,
#   Session_2026_07_05, Media_audio_video_Firefox_154_Gorilla_Media_Stack_*.xml,
#   Compile.errors.fixed.so.far..txt (ERRORs 12, 12b, 12c, 12d, 12e)
# Target: Intel HD 4000 / Ivy Bridge — VA-API i965 — H.264 hardware-only decode

---

## THE MISSION (read this first)

Hardware-only H.264 decode via VA-API i965 on Intel HD Graphics 4000 (Ivy Bridge).
Zero CPU decode. Zero software fallback. Zero VP9/AV1/HEVC. If VA-API can't do it, it fails loud.

Hard system dependency: `LIBVA_DRIVER_NAME=i965` in `/etc/environment`.
The iHD driver is also installed and does NOT support Ivy Bridge.
If this variable is lost or wrong, VA-API fails → ALL video fatal-errors. No silence. No fallback.

---

## ARCHITECTURE: THE 6-LAYER CODEC GATE

Every layer must be intact. A single failure = total video failure (by design).

```
Layer 1 — canPlayType() / isTypeSupported() [content process, JS boundary]
  File:  dom/media/DecoderTraits.cpp
  Guard: media.gorilla.hardware_only_mode (StaticPrefs, default=true)
  Does:  Returns CANPLAY_NO for VP9 (vp9/vp09), AV1 (av01), VP8, HEVC (hev1/hvc1),
         video/webm container, video/ogg container.
  Result: YouTube's JS gets canPlayType("")  for all non-H.264 video.
          YouTube negotiates H.264 MP4 without wasting RTP attempts on VP9/AV1.

Layer 2 — IsBlockedSoftwareOnlyVideoCodec() gate [content process, PDM]
  File:  dom/media/platforms/PDMFactory.cpp
  Func:  IsBlockedSoftwareOnlyVideoCodec(aMimeType) = !MP4Decoder::IsH264(aMimeType)
  Does:  Rejects anything that is NOT H.264 at CreateDecoder time.
  !! TRAPS — see KNOWN BUGS section below !!

Layer 3 — PDM selection / RDD delegation [content process → IPC → RDD]
  File:  dom/media/platforms/PDMFactory.cpp + dom/media/ipc/RemoteDecoderModule.cpp
  Does:  Routes H.264 decode to the RDD process via RemoteDecoderModule.
  !! TRAP: RemoteDecoderModule::Supports() ALWAYS returns SoftwareDecode !!
           Do NOT gate on HardwareDecode from this proxy. See KNOWN BUGS below.

Layer 4 — VA-API hardware init [RDD process]
  File:  dom/media/platforms/ffmpeg/FFmpegVideoDecoder.cpp
  Func:  InitHWDecoderIfAllowed() → InitVAAPIDecoder() → VADisplayHolder::GetSingleton()
  Does:  Opens VA display via DRM (/dev/dri/renderD128), initializes i965 VA-API.
  Guard: FFmpegVideoDecoder::Init() rejects H.264 if IsHardwareAccelerated() == false
         after init attempt. THIS is the real hardware-only enforcement gate.
         IsHardwareAccelerated() = mUsingV4L2 || !!mVAAPIDeviceContext || !!mVulkanDeviceContext

Layer 5 — VA-API driver pin [system environment]
  File:  /etc/environment
  Must:  LIBVA_DRIVER_NAME=i965
  Verify: LIBVA_DRIVER_NAME=i965 vainfo | grep H264
          Must show VAEntrypointVLD for ConstrainedBaseline, Main, High profiles.

Layer 6 — RDD sandbox DRM access [kernel/security]
  File:  security/sandbox/linux/broker/SandboxBrokerPolicyFactory.cpp
  Func:  GetRDDPolicy() → AddGLDependencies() → grants rdwr on /dev/dri/*
  Verify: gorilla user ACL on /dev/dri/renderD128 (rw-)
```

---

## KNOWN BUGS THAT KEEP COMING BACK

These bugs have been fixed, reintroduced during version porting, and fixed again.
Read this before touching PDMFactory.cpp.

---

### BUG A — RemoteDecoderModule HardwareDecode proxy check
**Files:**     dom/media/platforms/PDMFactory.cpp, dom/media/ipc/RemoteDecoderModule.cpp
**Recurred:**  FF153 → FF154 (ERRORs 12b in Compile.errors.fixed.so.far..txt)
**Symptom:**   YouTube "Your browser can't play this video". NS_ERROR_DOM_MEDIA_METADATA_ERR
               fires immediately. All 4 YouTube stream candidates fail. RDD process never
               receives any decode request.
**Root cause:**
  RemoteDecoderModule::Supports() ALWAYS returns SoftwareDecode regardless of what
  the RDD will actually do in hardware (upstream bug mozilla 1754239, unfixed):

    if (supports) {
      // TODO: Note that we do not yet distinguish between SW/HW decode support.
      //       Will be done in bug 1754239.
      return media::DecodeSupport::SoftwareDecode;
    }

  If PDMFactory::CreateDecoderWithPDM() checks this proxy for HardwareDecode,
  it will ALWAYS get SoftwareDecode → ALWAYS reject H.264 → total failure.
  The RDD, VideoBridgeChild, FFmpegVideoDecoder, VA-API: NONE are reached.

**Pattern that triggers it:**
    if (!aPDM->Supports(SupportDecoderParams(config), nullptr)
             .contains(DecodeSupport::HardwareDecode)) {
      return ... reject H.264 ...
    }

**Fix:**   Remove this check entirely. It cannot work with a proxy PDM.
           Hardware enforcement belongs ONLY in FFmpegVideoDecoder::Init() in RDD.

**Rule:**  NEVER gate on DecodeSupport::HardwareDecode from RemoteDecoderModule.
           The correct gate is FFmpegVideoDecoder::Init() → IsHardwareAccelerated().

---

### BUG B — IsBlockedSoftwareOnlyVideoCodec blocks audio MIMEs
**Files:**     dom/media/platforms/PDMFactory.cpp
**Recurred:**  FF153 → FF154 (ERROR 12c in Compile.errors.fixed.so.far..txt)
**Symptom:**   YouTube "Your browser can't play this video" with empty codec list.
               canPlayType() for audio/aac and audio/opus returns "" (empty).
               Audio tracks cannot initialize. Player cannot start.
**Root cause:**
  IsBlockedSoftwareOnlyVideoCodec() is defined as:
    return !MP4Decoder::IsH264(aMimeType);

  This returns true for ANYTHING that isn't H.264 — including audio/aac, audio/opus,
  audio/mpeg, audio/vorbis, audio/flac.

  SupportsMimeType() calls it WITHOUT a video-type guard:
    DecodeSupportSet PDMFactory::SupportsMimeType(const nsACString& aMimeType) const {
      if (IsBlockedSoftwareOnlyVideoCodec(aMimeType)) {   ← no video guard!
        return DecodeSupportSet{};
      }
    }

  → IsBlockedSoftwareOnlyVideoCodec("audio/aac") = !false = true → empty set returned.
  → YouTube isTypeSupported("audio/mp4; codecs=mp4a.40.2") → false → no audio path.

**Pattern that triggers it:**
  Calling IsBlockedSoftwareOnlyVideoCodec() on a raw MIME string without checking
  that the MIME is a video type first.

**Fix:**
    if (StringBeginsWith(aMimeType, "video/"_ns) &&
        IsBlockedSoftwareOnlyVideoCodec(aMimeType)) {
      return DecodeSupportSet{};
    }

**Affected call sites in PDMFactory.cpp:**
  - CreateDecoderWithPDM() line ~474: SAFE — inside `if (config.IsVideo())`
  - Supports() line ~510:            SAFE — inside `if (aParams.mConfig.IsVideo())`
  - SupportsMimeType() line ~496:    DANGEROUS — raw MIME string, needs the guard above

**Rule:**  NEVER call IsBlockedSoftwareOnlyVideoCodec() without a prior video-type
           check. Audio MIMEs must ALWAYS pass through unblocked.

---

### BUG C — kHardwareVideoDecodeOnly / strict HW flag fatal-errors on VA-API failure
**Files:**  dom/media/platforms/PDMFactory.cpp (FF153-era variable name)
**Recurred:** FF152 → FF153 (documented in LESSONS_MASTER.md 2026-06-25)
**Symptom:** Log shows "Strict HW decode mode: software video decoding is forbidden."
             VA-API init fails (wrong driver, missing LIBVA_DRIVER_NAME), fatal error thrown.
**Note:**   In FF154 Gorilla, this flag is replaced by StaticPrefs::media_gorilla_hardware_
            only_mode() and the check lives in FFmpegVideoDecoder::Init() — which is the
            correct place. Do NOT move this check to the content process.
**Rule:**   If VA-API fails, fix the driver/environment. Do NOT disable the hardware-only
            check or add a software fallback. That silently defeats the mission.

---

### BUG D — Frame pool allowed to grow beyond 16 frames (UMA RAM starvation)
**Files:**  dom/media/platforms/ffmpeg/FFmpegVideoDecoder.cpp
**Recurred:** FF153 9-bug audit (Bug #3 in BUG_FIXES_COMPLETED_ALL_9_BUGS_RESOLVED.xml)
**Symptom:** Random OOM / slowdown on long video sessions. intel_gpu_top shows GPU thrash.
**Root cause:** VA-API and Vulkan paths used `std::max(initial_pool_size, 16)` instead of
               `exactly 16`. On Intel HD 4000 UMA (shared CPU+GPU RAM), pool growth causes
               RAM starvation: each surface is a DMA-BUF allocation in shared memory.
**Fix:**    Hard-lock all decode paths to exactly 16 frames:
              mVideoFramePool = MakeUnique<VideoFramePool<LIBAV_VER>>(16);
            No std::max(), no dynamic growth. H.264 DPB compliance at Level 4.1 requires
            ≤ 16 reference frames. 16 is both minimum AND maximum.
**Rule:**   NEVER use std::max(initial, 16) for the frame pool on UMA hardware.
            Always use exactly 16.

---

### BUG E — std::abort() in vaQueryConfigProfiles crashes RDD process
**Files:**  dom/media/platforms/ffmpeg/FFmpegVideoDecoder.cpp
**Recurred:** FF153 9-bug audit (Bug #4)
**Symptom:** RDD process crashes on VA-API driver errors during capability query.
             Log shows sudden process exit, decode never starts.
**Fix:**    Replace std::abort() with proper error return:
              return MediaResult(NS_ERROR_DOM_MEDIA_FATAL_ERR,
                                 RESULT_DETAIL("VA-API profile query failed"));
**Rule:**   No std::abort() anywhere in the decode path. Fail gracefully with MediaResult.

---

### BUG F — IsDecodingSlow() software fallback loophole
**Files:**  dom/media/platforms/ffmpeg/FFmpegVideoDecoder.cpp
**Recurred:** FF153 9-bug audit (Bug #5)
**Symptom:** Under load, IsDecodingSlow() triggers → silent switch to software H.264.
             CPU spikes to 100%. Mission violated: CPU doing ASIC work.
**Fix:**    Remove the IsDecodingSlow() check entirely. Hardware-only is not negotiable.
**Rule:**   Do NOT let any "slow decode" escape hatch bypass the hardware-only policy.

---

### BUG G — Frame bridge null check drops all frames (mKnowsCompositor)
**Files:**  dom/media/ipc/RemoteVideoDecoder.cpp
**Recurred:** FF153 9-bug audit (Bug #6)
**Symptom:** All decoded frames silently dropped. Video decodes but nothing displays.
             CPU stays low (hardware decoding works), screen shows nothing.
**Root cause:** Zero-copy gate applied unconditionally even when mKnowsCompositor is null.
               When compositor bridge doesn't exist (no GPU process), all frames dropped.
**Fix:**    Zero-copy enforcement only when compositor bridge actually exists:
              if (mKnowsCompositor && mKnowsCompositor->GetTextureForwarder()) {
                // enforce zero-copy / DMA-BUF path
              } else {
                // fall through to shmem path
              }
**Note:**   With GPU process disabled (Wayland), mKnowsCompositor is set up via
            RDDParent::RecvInitVideoBridge() / CreateRddVideoBridge(). This is NOT the
            same as the BUG A failure — BUG A never reaches RDD at all.

---

### BUG H — Gorilla UserEnable() overridden by gfxInfo blocklist (zero-copy broken)
**Files:**  gfx/thebes/gfxPlatformGtk.cpp (line 282), gfx/config/gfxFeature.cpp
**Recurred:** FF154 Gorilla session 2026-07-15 (ERROR 12d in Compile.errors.fixed.so.far..txt)
**Symptom:** IMC reads abnormally high (2500+ MiB/s) during 1080p60 H.264 playback.
             intel_gpu_top confirms VA-API MFX ASIC is active, so hardware decode works.
             High bandwidth is from VA-API surfaces being memcpy'd through CPU on every frame.
**Root cause:**
  `gfxPlatformGtk::InitDMABufConfig()` called `featureZeroCopy.UserEnable()`, which sets
  `mUser = Enabled`. The `FeatureState::GetValue()` priority chain is:
    mRuntime > mUser(ForceEnabled) > mEnvironment > mUser(Enabled) > mDefault
  If gfxInfo returns anything other than `FEATURE_ALLOW_ALWAYS`, `Disable()` sets
  `mEnvironment = Blocklisted`, which outranks `mUser = Enabled`. Result: `HwDecodedVideoZeroCopy`
  gfxVar is false → `VideoFramePool::NeedsCopy()` returns true → every VA-API DMABuf surface
  is memcpy'd from GPU memory to a shmem buffer → back to GPU → ~5× extra UMA bandwidth.
**Fix (code):**
    // gfxPlatformGtk.cpp line 282 — BEFORE (wrong):
    featureZeroCopy.UserEnable("Forced by Gorilla hardware-only policy");
    // AFTER (correct):
    featureZeroCopy.UserForceEnable("Forced by Gorilla hardware-only policy");
  `UserForceEnable()` sets `mUser = ForceEnabled`, which is checked BEFORE `mEnvironment`
  in `GetValue()`, so gfxInfo can no longer override it.
**Fix (belt-and-suspenders pref, no rebuild):**
    user_pref("media.ffmpeg.vaapi.force-surface-zero-copy", 1);
  State=1 path in InitDMABufConfig() skips the gfxInfo GetFeatureStatus call entirely,
  so `mEnvironment` stays Unused and `UserEnable` succeeds even without the code fix.
**Rule:** In gfxPlatformGtk's hardware-only init code, ALWAYS use `UserForceEnable()` not
          `UserEnable()` for features that must be active regardless of gfxInfo.
          `UserEnable()` is subordinate to the environment (gfxInfo) tier — it is NOT a force.

---

### BUG I — WebRender uses GL compositor on Linux by default (native Wayland overlay disabled)
**Files:**  gfx/config/gfxConfigManager.cpp (line 151), modules/libpref/init/StaticPrefList.yaml
**Recurred:** FF154 Gorilla session 2026-07-15 (ERROR 12e in Compile.errors.fixed.so.far..txt)
**Symptom:** IMC reads ~2500 MiB/s during 1080p60 H.264 (expected ~500 MiB/s with overlay).
             `UseWebRenderCompositor` = false, `CompositorType()` = DRAW (not WAYLAND).
             VA-API decodes correctly but NV12 DMABuf surfaces feed through the WebRender GL
             pipeline instead of KMS hardware plane overlays.
**Root cause:**
  `StaticPrefList.yaml`: `gfx.webrender.compositor` defaults to `false` on Linux (true only
  on Win/macOS). `gfxConfigManager::ConfigureWebRenderCompositor()` line 151:
    mFeatureWrCompositor->SetDefaultFromPref("gfx.webrender.compositor", true, false,
                                              mWrCompositorEnabled);   // default=false on Linux
  With `UseWebRenderCompositor = false`:
    - `CompositorType()` = LAYERS_WR_DRAW (GL pipeline)
    - NV12 DMABuf → EGL texture → YUV→RGB shader → RGBA framebuffer → Mutter reads → display
    - Each frame: GPU reads NV12, writes RGBA → Mutter reads RGBA → ~4× extra GPU memory BW
    - On UMA this shows as IMC reads (CPU and GPU share the same DRAM controller)
  With `UseWebRenderCompositor = true` (native Wayland compositor):
    - `CompositorType()` = LAYERS_WR_WAYLAND (native overlay path)
    - NV12 DMABuf submitted directly as Wayland surface → KMS plane overlay → display
    - GPU reads once (scan-out), no YUV→RGB pass, no Mutter readback → ~500 MiB/s
**Fix (code, compile-time — replaces earlier pref-only fix):**
    // gfx/config/gfxConfigManager.cpp, inside ConfigureWebRender(), #ifdef MOZ_WAYLAND block:
    mFeatureWrCompositor->UserForceEnable(
        "Gorilla: native Wayland compositor for VA-API zero-copy overlay");
  `UserForceEnable()` sets `mUser = ForceEnabled`, which outranks `mEnvironment = Blocklisted`
  in the FeatureState priority chain. Placed after the HDR check, before ConfigureFromBlocklist.
  On Linux (non-Windows), the hardware stretching guard at line 171 does not fire
  (`mHwStretchingSupport.mBoth` is set to 1, `mScaledResolution` defaults false).
**Why code fix instead of pref:**
  about:support (2026-07-16) revealed `userJS.exists = false` — Firefox was launched without
  `-profile` flag, so user.js with `gfx.webrender.compositor.force-enabled = true` was never
  loaded. The pref-only fix is fragile. Code fix guarantees the compositor is always active
  on Wayland builds, regardless of profile or launch flags.
**Belt-and-suspenders pref (still in user.js, harmless):**
    user_pref("gfx.webrender.compositor.force-enabled", true);
  Redundant now but safe to keep — if the pref IS loaded, it hits `mWrCompositorForceEnabled`
  at line 154 before our Gorilla force-enable even runs.
**Side-effect (beneficial):** `UploadSWDecodeToDMABuf()` also returns true when
  `GetWebRenderCompositorType() == WAYLAND`, so if software decode ever runs it also
  takes the DMABuf zero-copy upload path instead of CPU shmem.
**Rule:** On Gorilla Wayland builds, native compositor is now compile-time enforced.
          No pref dependency. No user.js dependency.

---

## YOUTUBE-SPECIFIC NEGOTIATION (expected behavior after all fixes)

```
isTypeSupported('video/webm; codecs="vp9"')      → false  [Layer 1 + user.js pref]
isTypeSupported('video/webm; codecs="av01"')     → false  [Layer 1 + user.js pref]
isTypeSupported('video/mp4; codecs="avc1"')      → "probably" [H.264 allowed]
isTypeSupported('audio/mp4; codecs="mp4a.40"')   → "probably" [AAC, not gated]
isTypeSupported('audio/webm; codecs="opus"')     → false  [WebM container blocked]
```

Result: YouTube serves H.264 MP4 (video) + AAC MP4 (audio) via MSE.
RDD decodes H.264 with VA-API i965 in hardware. MFX engine active in intel_gpu_top.
CPU usage during playback: 0–3%.
IMC reads during 1080p60 H.264: ~500 MiB/s (native Wayland compositor / KMS overlay).
  If IMC reads are ~2500 MiB/s: check BUG H (zero-copy disabled) and BUG I (GL compositor).

---

## DEBUGGING CHECKLIST (when video fails)

**Step 1 — Which layer failed?**
  - METADATA_ERR (0x806e0006) from 4 sequential decoders = content-process gate
    fired before RDD. Check BUG A (proxy HardwareDecode check) and BUG B (audio
    MIME guard missing in SupportsMimeType).
  - "Strict HW decode mode" in log = FFmpegVideoDecoder::Init() gate fired in RDD.
    VA-API init failed. Check LIBVA_DRIVER_NAME, vainfo, /dev/dri permissions.
  - Video decodes but nothing displays = BUG G (frame bridge null, frames dropped).
  - canPlayType() returns "" for H.264 = Layer 1 DecoderTraits gate is over-blocking.
  - Video plays correctly but IMC reads > 1500 MiB/s during 1080p60:
    → First check BUG I: is `gfx.webrender.compositor.force-enabled = true` in user.js?
      about:support → "WebRender compositor" should show "Enabled (Native Wayland)".
    → Then check BUG H: is `media.ffmpeg.vaapi.force-surface-zero-copy = 1` in user.js?
      If UserForceEnable fix not in gfxPlatformGtk.cpp, this pref is mandatory.
    Both bugs together can account for ~5× excess IMC bandwidth on UMA (Ivy Bridge).

**Step 2 — Grep the Gorilla patches immediately**
  grep -n "GORILLA\|gorilla" dom/media/DecoderTraits.cpp
  grep -n "GORILLA\|gorilla\|IsBlocked\|HardwareDecode" dom/media/platforms/PDMFactory.cpp
  grep -n "GORILLA\|gorilla\|IsHardwareAccelerated" dom/media/platforms/ffmpeg/FFmpegVideoDecoder.cpp

**Step 3 — Check VA-API environment**
  LIBVA_DRIVER_NAME=i965 vainfo | grep H264   ← must show VAEntrypointVLD x3 profiles
  cat /etc/environment | grep LIBVA            ← must be pinned to i965
  ls -la /dev/dri/renderD128                  ← must exist
  getfacl /dev/dri/renderD128                 ← gorilla user must have rw-

**Step 4 — Check profile prefs are deployed**
  grep -E "vaapi|vp9|av1|gpu.process|webrender.compositor|zero-copy" \
    obj-x86_64-pc-linux-gnu/tmp/profile-default/user.js
  Required entries:
    media.ffmpeg.vaapi.enabled = true
    media.ffmpeg.vaapi.decode.force-enabled = true
    media.ffmpeg.vaapi-drm-display.enabled = true
    media.ffmpeg.vaapi.force-surface-zero-copy = 1       ← BUG H fix (belt-and-suspenders)
    gfx.webrender.compositor.force-enabled = true        ← BUG I fix (mandatory on Wayland)
    media.av1.enabled = false
    media.vp9.enabled = false
    media.mediasource.vp9.enabled = false
    layers.gpu-process.enabled = false
    layers.gpu-process.force-enabled = false
    media.gpu-process-decoder = false

**Step 5 — Test live**
  LIBVA_DRIVER_NAME=i965 MOZ_ENABLE_WAYLAND=1 ./obj-x86_64-pc-linux-gnu/dist/bin/firefox \
    -no-remote -profile ./obj-x86_64-pc-linux-gnu/tmp/profile-default 2>&1 | tee /tmp/ff.log
  Open YouTube, play H.264 video, watch intel_gpu_top for MFX activity.

---

## PDMFactory.cpp INVARIANTS (do not violate)

```cpp
// ✅ CORRECT — video guard present, audio passes through
DecodeSupportSet PDMFactory::SupportsMimeType(const nsACString& aMimeType) const {
  if (StringBeginsWith(aMimeType, "video/"_ns) &&
      IsBlockedSoftwareOnlyVideoCodec(aMimeType)) {
    return DecodeSupportSet{};
  }
  ...
}

// ✅ CORRECT — IsVideo() guard present in CreateDecoderWithPDM
if (config.IsVideo()) {
  if (IsBlockedSoftwareOnlyVideoCodec(config.mMimeType)) { ... reject ... }
}

// ✅ CORRECT — IsVideo() guard present in Supports()
if (aParams.mConfig.IsVideo()) {
  if (IsBlockedSoftwareOnlyVideoCodec(aParams.mConfig.mMimeType)) { ... }
}

// ❌ WRONG — no video guard, blocks audio MIMEs
if (IsBlockedSoftwareOnlyVideoCodec(aMimeType)) { ... }

// ❌ WRONG — proxy cannot report hardware capability
if (!aPDM->Supports(...).contains(DecodeSupport::HardwareDecode)) { ... reject ... }

// ✅ CORRECT hardware enforcement — in FFmpegVideoDecoder::Init() inside RDD:
if (!IsHardwareAccelerated()) {
  if (mCodecID == AV_CODEC_ID_H264) {
    return InitPromise::CreateAndReject(
        MediaResult(NS_ERROR_DOM_MEDIA_FATAL_ERR,
                    RESULT_DETAIL("Gorilla policy: H.264 hardware decode required")), ...);
  }
}
```

---

## GFX FEATURE PRIORITY CHAIN (critical for Gorilla patches)

`gfx/config/gfxFeature.cpp` — `FeatureState::GetValue()` priority (highest first):

```
mRuntime       ForceDisable() / SetFailed()  — set by crashes/runtime failures, OVERRIDES EVERYTHING
mUser          ForceEnabled                  — UserForceEnable() — wins over blocklist ✅
mEnvironment   Blocklisted                   — set by gfxInfo, ConfigureFromBlocklist()
mUser          Enabled                       — UserEnable()      — LOSES to blocklist ❌
mDefault       (pref default)
```

Rules for Gorilla code:
- `UserForceEnable()` = safe for mandatory features (skips gfxInfo)
- `UserEnable()` = only for optional features that gfxInfo is allowed to block
- Never use `UserEnable()` for features that must be active in hardware-only mode
- `ForceDisable()` / `SetFailed()` — set by runtime crashes, cannot be bypassed by ANY user pref.
  Example: GPU process crash → GPU_PROCESS feature gets `ForceDisable()` → stays disabled
  for the session regardless of `layers.gpu-process.force-enabled`.

---

## SOURCES

- `Second.Brain/LESSONS_MASTER.md` lines 21–26 (FF153 YouTube gating + audio block)
- `Second.Brain/LESSONS_MASTER.md` lines 448–458 (2026-06-25: YouTube + audio + compander)
- `Second.Brain/Brain/BUG_FIXES_COMPLETED_ALL_9_BUGS_RESOLVED.xml` (FF153 9-bug audit)
- `Second.Brain/Brain/Bug_Fixes_Report_Firefox_Unleashed_Zero_CPU_Media_Pipeline.xml`
- `Second.Brain/Brain/Session_2026_07_05_FF154_Media_Audit_*.xml`
- `Second.Brain/Brain/Media_audio_video_Firefox_154_Gorilla_Media_Stack_*.xml`
- `patches/Compile.errors.fixed.so.far..txt` ERROR 9, 12, 12b, 12c, 12d, 12e
- User-provided diagnosis document (2026-07-15, session c):
  "YouTube playback failure — confirmed root cause and fix"
- Session 2026-07-15 (d): zero-copy UMA bandwidth analysis (BUG H + BUG I)
- Session 2026-07-16: about:support verification confirmed BUG H code fix working,
  discovered user.js not loaded (no -profile flag), applied BUG I as code fix in
  gfxConfigManager.cpp (UserForceEnable for WEBRENDER_COMPOSITOR on MOZ_WAYLAND)
