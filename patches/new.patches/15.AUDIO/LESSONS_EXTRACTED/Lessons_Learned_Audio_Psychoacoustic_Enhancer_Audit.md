# Lessons_Learned_Audio_Psychoacoustic_Enhancer_Audit

**Source:** Lessons_Learned_Audio_Psychoacoustic_Enhancer_Audit.xml

## Rationale

[AUDIT VERDICT 2026-08-02 — SPLIT — mostly TRUE, item 8 DANGEROUS] D-001..D-P002 fixes are TRUE and current. Item 7's 0.80/0.99 limiter values are early-gen (current: knee 0.9, bound 1.0). Item 8 ('gains must track mVolume dynamically') is SUPERSEDED-DANGEROUS: the final design uses FIXED gains precisely because mVolume tracking made the DSP inert (in-page sliders pin ~1.0); software volume is applied separately BEFORE the DSP stage.


    Audited and refactored the laptop audio enhancer DSP pipeline to establish thread safety, sample-rate adaptability, type-compatibility, and real-time CPU optimization on Firefox.

## Execution Logic

The refactoring in dom/media/AudioStream.cpp and dom/media/AudioStream.h addresses:
    1. Thread-safety: Removed a static array filterState[64][4] that caused data races (D-001) and channel bleed on hash collisions across concurrent audio streams.
    2. Multi-channel Safety: Prevented surround sound track corruption (D-002) by checking for mChannels > 2 and bypassing processing for multi-channel formats.
    3. Null-safety: Guarded the mPsychoEnhancer lazy instantiation (D-003) to prevent fatal browser crashes on allocation failure under OOM.
    4. Type-compatibility: Standardized the process signature to accept AudioDataValue* instead of float* (D-004) to maintain compile compatibility on mobile/S16 platforms.
    5. Division-by-zero: Added validation in ComputeAlpha (D-P001) to prevent NaN coefficients if the sample rate is 0.
    6. CPU Latency Optimization: Replaced transcendental std::tanh calls with a fast Padé rational approximation FastTanh (D-P002) in the real-time loop.
    7. Compander Ceiling Guard & Hard Clipping: Setting kCeiling to abnormally low levels (e.g. 0.25f) or using a linear hard-clipping clamp (if (out > kCeiling) out = kCeiling) brutally squares off peaks, generating high-frequency harmonics that physically rattle the laptop chassis. Soft-knee compression via FastTanh when output exceeds 0.80f asymptotically limits it to 0.99f without clipping.
    8. Static Volume Fallback (Mute-under-80% Bug): Querying CubebUtils::GetVolumeScale() alone is incorrect because it represents the system-wide static master scale (always hardcoded to 1.0f at runtime). Stream-specific volume slider changes must be tracked dynamically via an atomic member (mVolume) in AudioStream::SetVolume and multiplied to compute the correct Fletcher-Munson dynamic gains at low volume levels (preventing muting below 80% volume).
    9. Upgraded Pre-flight Semantic check: Programmed logic checks in `cpp_preflight_protocol.py` that check: (a) kCeiling >= 0.90f, (b) absence of raw hard-clipping clamp patterns, (c) dynamic volume tracking verification ensuring calls to `->UpdateGains` incorporate `mVolume`, and (d) presence of the `FastTanh` soft-knee limiter.
