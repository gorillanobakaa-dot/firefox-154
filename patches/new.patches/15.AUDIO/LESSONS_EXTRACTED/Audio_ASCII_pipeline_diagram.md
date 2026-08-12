# Audio_ASCII_pipeline_diagram

**Source:** Audio_ASCII_pipeline_diagram.xml

## Rationale

# Unleashed 153: MASTER ARCHITECTURE & REMEDIATION PLAN

===========================================================================
                  PART I: PIPELINE TOPOLOGY (ASCII DIAGRAM)
===========================================================================
This diagram can be saved as a .txt file. It maps your exact patch 
points, IPC boundaries, and required FFI/header interactions on Linux.

[ HTMLMediaElement ] --> (MIME / Container Query)
        |
        v
+-----------------------+      Blocks VP8/9, AV1, Ogg/WebM
|  DecoderTraits.cpp    | ----------------------------------> [ REJECTED ]
|  (Codec Gatekeeper)   |      Allows H.264 / AAC
+-----------------------+
        |
        v
+-----------------------+      Kills Software Fallback (AgnosticDecoderModule.h)
|   PDMFactory.cpp      | ----------------------------------> [ REJECTED ]
| (Decoder Dispatcher)  |      Routes to RemoteDecoderModule
+-----------------------+
        |
        v
===================== IPC BOUNDARY (Cross-Process) ========================
        |
+-----------------------+      GPU Hardware Decoding via VA-API (VALibWrapper.h)
|FFmpegVideoDecoder.cpp | <--> libavcodec.so / libva.so
|   (ASIC Saturation)   |      Frames locked to pool size = 16
+-----------------------+
        |
        v
+-----------------------+      Zero-copy GPU Memory (ImageContainer.h / TextureClient.h)
|RemoteVideoDecoder.cpp | -->  VideoBridgeChild
|  (Compositor Bridge)  |      Requires mKnowsCompositor == true
+-----------------------+

---------------------------------------------------------------------------
                           AUDIO SUBSYSTEM
---------------------------------------------------------------------------

[ Audio Source ]
        |
        v
+-----------------------+      Applies Gain Boost (Max 2.0x, NOT 4.0x)
|   AudioStream.cpp     |      Soft-Knee Limiter (Threshold: 0.80f)
|  (Software Mixer)     |      Time-Stretcher (RLBoxSoundTouch)
+-----------------------+
        |
        v
===================== IPC BOUNDARY (Sandbox) ==============================
        |                      audioipc2_client_ffi_generated.h
        v
+-----------------------+      Sample Rate Locked: 48000 Hz
|   CubebUtils.cpp      | -->  Real-Time Priority (audio_thread_priority.h)
| (Hardware Interface)  |      cubeb.h
+-----------------------+
        |
        v
[ PulseAudio / PipeWire ] -->  [ Sony VAIO Hardware Speakers ]


===========================================================================
              PART II: THE AUDIO BUG ROOT CAUSE SUMMARY
===========================================================================
The "dead" volume below 60% and the vibrations above 60% are caused by a 
mathematical conflict between your software limiter and Linux's mixer.

1. The Over-Boost: You clamped the minimum software gain to 4.0x.
2. The Brick Wall: You set the limiter threshold to 0.95f, capped at 0.99f.
3. The Result: Any audio sample naturally over 0.24 amplitude is boosted to 
   0.96+ and instantly flattened. You effectively converted your dynamic 
   media audio into a flat-topped square wave.
4. The OS Conflict: Linux PulseAudio/PipeWire uses a cubic curve (v^3) for 
   its volume slider. A square wave played at low slider values sounds 
   incredibly muffled. Pushed past 60%, the square wave forces the laptop 
   speaker coils into mechanical over-excursion, vibrating the Sony VAIO 
   plastic chassis.

===========================================================================
              PART III: COHERENT IMPLEMENTATION GUIDE
===========================================================================
To seal the Fortress without destroying your hardware, apply these exact 
values and techniques across the codebase.

--- 1. CUBEB UTILS (Hardware Audio Interface) ---
File: dom/media/CubebUtils.cpp
Dependencies: cubeb.h, audioipc2_client_ffi_generated.h, audio_thread_priority.h

* Technique: Lower the gain floor to allow dynamic range. 
* Fix:
  double GetVolumeScale() {
    StaticMutexAutoLock lock(sMutex);
    // CHANGE: Reduce clamp from 4.0 to 1.5. This provides a 150% boost 
    // without instantly clipping the waveform.
    return std::max<double>(sVolumeScale, 1.5); 
  }

* Technique: Sync the sample rate to the OS.
* Fix: Hard-locking to 48000Hz is fine, but you must ensure PulseAudio is 
  actually running at 48kHz. If the OS defaults to 44.1kHz, `cubeb_stream_init` 
  will fail or cause severe IPC desync in the audioipc server.


--- 2. AUDIO STREAM (The Software Mixer) ---
File: dom/media/AudioStream.cpp

* Technique: Widen the Soft-Knee Limiter.
* Fix in `DataCallback`:
  // CHANGE: Lower threshold to 0.80f to start curving the audio earlier.
  const float threshold = 0.80f; 
  
  for (uint32_t i = 0; i < samples; i++) {
    float x = buffer[i] * scale; // Scale is now 1.5x from CubebUtils
    float abs_x = std::abs(x);

    if (abs_x > threshold) {
      // Smooth compression curve
      float compressed = threshold + (abs_x - threshold) / 
                         (1.0f + ((abs_x - threshold) / (1.0f - threshold)));
      // CHANGE: Cap at 0.95f instead of 0.99f to leave digital headroom.
      if (compressed > 0.95f) compressed = 0.95f;
      buffer[i] = (x > 0.0f) ? compressed : -compressed;
    } else {
      buffer[i] = x;
    }
  }


--- 3. DECODER TRAITS (The Codec Gatekeeper) ---
File: dom/media/DecoderTraits.cpp
Dependencies: OggDecoder.h, WebMDecoder.h, MP4Decoder.h

* Technique: Early return nullification.
* Fix: By returning `CANPLAY_NO` for WebM and Ogg early, you successfully 
  kill the instantiation of VP8/VP9/AV1 decoders. 
* Coherency Check: Ensure you do not leave dangling references to `TrackInfo` 
  or MIME types in `HTMLMediaElement.cpp`. If the front-end JS player 
  doesn't receive a definitive "No", it will hang the network thread 
  waiting for a codec load.


--- 4. PDM FACTORY (The Decoder Dispatcher) ---
File: dom/media/platforms/PDMFactory.cpp
Dependencies: AgnosticDecoderModule.h, RemoteDecoderModule.h

* Technique: Eradicating software fallback.
* Fix: You refined `SupportsMimeType` to only gate video. 
* Coherency Check: Because you are blocking all software modules, you must 
  ensure `AgnosticDecoderModule` gracefully handles a `nullptr` return. 
  Otherwise, the browser will crash when an unsupported video plays. Return 
  a handled `NS_ERROR_DOM_MEDIA_FATAL_ERR` rather than allowing a silent abort.


--- 5. FFMPEG VIDEO DECODER (ASIC Saturation) ---
File: dom/media/platforms/ffmpeg/FFmpegVideoDecoder.cpp
Dependencies: VALibWrapper.h, FFmpegLibWrapper.h

* Technique: UMA-Safe Buffer Capping.
* Fix: Locking the frame pool size to 16 prevents RAM starvation.
* Coherency Check: You removed `std::abort()` from `vaQueryConfigProfiles`. 
  You MUST replace it with a clean failure state (`return NS_ERROR_FAILURE;`). 
  If `libva` fails to initialize on Linux and you don't abort *and* don't 
  return an error, FFmpeg will attempt to map null GPU memory pointers, 
  causing a segmentation fault (SIGSEGV) in the renderer.


--- 6. REMOTE VIDEO DECODER (Compositor Bridge) ---
File: dom/media/ipc/RemoteVideoDecoder.cpp
Dependencies: VideoBridgeChild.h, TextureClient.h, ImageContainer.h

* Technique: Bridge-Aware Frame Processing.
* Fix: `mKnowsCompositor` zero-copy gating.
* Coherency Check: When `mKnowsCompositor` is false (e.g., if the GPU process 
  crashes on Linux and restarts), you must ensure `TextureClient` properly 
  releases the lock on the hardware frames. If you drop the frames without 
  unlocking the VA-API surfaces in `ImageContainer`, you will cause a VRAM 
  memory leak, eventually locking up your Intel HD 4000 GPU entirely.

## Execution Logic

(empty)
