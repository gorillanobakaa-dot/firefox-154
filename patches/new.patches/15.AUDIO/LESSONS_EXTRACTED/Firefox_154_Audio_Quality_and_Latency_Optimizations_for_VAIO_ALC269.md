# Firefox_154_Audio_Quality_and_Latency_Optimizations_for_VAIO_ALC269

**Source:** Firefox_154_Audio_Quality_and_Latency_Optimizations_for_VAIO_ALC269.xml

## Rationale

[AUDIT VERDICT 2026-08-02 — CURRENT-TRUE + one defect found 2026-08-02] the quoted AudioDestinationNode soft-clip has mismatched branches: at x=1.0 the polynomial gives 0.778 but the clamp jumps to 1.0 (0.22 discontinuity = click generator on >1.0 WebAudio peaks). Correct thresholds are ±3.0 where the Padé equals exactly 1.0 (as AudioStream's FastTanh does). Fix pending owner listening test.

We optimized browser audio performance for the Sony VAIO SVE14A3AJ laptop's native Realtek ALC269 speakers. First, the browser is forced to output audio directly at the hardware's native rate of 48 kHz instead of doing quality-reducing conversions from 44.1 kHz. Second, we added a safety limiter using a soft-clipping math equation. When sounds get too loud, the peaks are gently rounded out rather than getting chopped off, preventing harsh speaker scratching static and protecting the physical speakers from wear. Third, sound delay was reduced from 25ms to 10ms to sync tighter with GNOME/Wayland PipeWire tracks.

PROBLEM: Firefox defaults to dynamic device queries and standard 44.1kHz sampling rates, which forces software resamplers to run when playing back on the 48kHz Realtek ALC269 DAC, introducing digital distortion. Furthermore, volume changes combined with high-signal blocks clip hard against the digital ceiling (0dB), generating harsh distortion. Fallback latency for Linux fingerprinting resistance defaults to an excessively high 25ms, causing noticeable sync delay on GNOME Shell Wayland environments.

## Execution Logic

SOLUTION: 1. Force GetSampleRateForAudioContext to return 48000.0f under media.gorilla.hardware_only_mode to match the ALC269 DAC native clock rate directly.
2. Injected a Fast-Tanh soft clipper (rational approximation: x * (27 + x^2) / (27 + 9*x^2)) into the ProcessBlock engine loop in AudioDestinationNode.cpp when output volume calculations exceed maximum limits.
3. Modified the RFP fallback latency in AudioContext.cpp to return 10ms (0.010) inside Linux widget tracks.

Patched AudioContext.cpp and AudioDestinationNode.cpp inside the 01.MEDIA patch group. GetSampleRateForAudioContext checks StaticPrefs::media_gorilla_hardware_only_mode() to return 48000.0f early. OutputLatency() uses a ternary operator to return 0.010 if hardware-only mode is true. DestinationNodeEngine::ProcessBlock calls AllocateChannels and applies the rational tanh soft clipper to output channel buffers when static preference is active, overriding aOutput->mVolume to 1.0f.

CODE:
aOutput->AllocateChannels(channelCount);
for (uint32_t c = 0; c < channelCount; ++c) {
  float* dest = aOutput->ChannelFloatsForWrite(c);
  const float* src = channels[c];
  for (uint32_t i = 0; i < WEBAUDIO_BLOCK_SIZE; ++i) {
    float x = src[i] * volume;
    if (x > 1.0f) dest[i] = 1.0f;
    else if (x < -1.0f) dest[i] = -1.0f;
    else dest[i] = x * (27.0f + x * x) / (27.0f + 9.0f * x * x);
  }
}

PATHS: /home/gorilla/Documents/FIrefox.154.Work/patches/01.MEDIA/AudioContext.cpp, /home/gorilla/Documents/FIrefox.154.Work/patches/01.MEDIA/AudioDestinationNode.cpp, /home/gorilla/Documents/FIrefox.154.Work/patches/01.MEDIA/MASTER_PROJECT_LOG_FIREFOX_154_MEDIA_PATCHES.md

KEYWORDS: ALC269, AudioContext, AudioDestinationNode, soft-limiter, fast-tanh, 48000Hz, latency, PipeWire
