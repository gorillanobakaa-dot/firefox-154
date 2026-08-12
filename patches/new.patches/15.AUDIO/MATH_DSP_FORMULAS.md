# The Audio Math — every formula this project derived, broke, and fixed

Collected 2026-08-10 from the lesson tiers. Attribution beside each block.
The half-remembered names resolve as: "G1 curve" (Gemini-era brand, retired
2026-08-02) = "signomial curve" = the three-zone compander below. "Sigmoid
curve" appears in the vocal-intensity envelope model. "Polynomial soft-knee"
is the June 5 first-generation limiter.

---

## 1. The Signomial Curve — three-zone linear-domain compander

Source: `SOURCE_XML/01.MEDIA/firefox_media_audio_video_patches_20260619.xml`
(audio_fixes_v2 reference; the FF153 tree that hosted it is gone from disk).

Constants (precomputed, zero per-sample division):

```cpp
// -- Tunable parameters (canonical shipped values) -----------------------
static constexpr float kLowerBound = 0.10f;  // below this -> 2x expansion
static constexpr float kUpperBound = 0.50f;  // above this -> 0.80 compression
static constexpr float kRExp       = 2.00f;  // expansion ratio  (Zone A)
static constexpr float kRComp      = 0.80f;  // compression ratio (Zone C)
static constexpr float kCeiling    = 0.99f;  // hard safety ceiling

// -- Precomputed constants (zero per-sample division) --------------------
static constexpr float kW      = kUpperBound - kLowerBound;        // 0.40
static constexpr float kYLower = kLowerBound * kRExp;              // 0.20
static constexpr float kKneeA  = (kRComp - kRExp) / (2.0f * kW);   // -1.50
// y_upper from the spline at z=W: y_lower + W*R_exp + knee_a*W^2
static constexpr float kYUpper = kYLower + kW * kRExp + kKneeA * kW * kW; // 0.76
```

Internal-consistency proof (verified 2026-08-10): 0.10 x 2.0 = 0.20 = kYLower;
(0.80 - 2.00)/(2 x 0.40) = -1.50 = kKneeA; 0.20 + 0.40 x 2.0 - 1.50 x 0.16
= 0.76 = kYUpper. The surviving code is the real implementation, not prose.

Tuning guide (variants recorded in the same lesson):

| Knob | Canonical | Variant | Effect |
|---|---|---|---|
| kLowerBound | 0.10 | 0.08 | "expand more" — expansion deeper into the signal range |
| kRExp | 2.00 | 2.50 | "stronger boost" |
| kRComp | 0.80 | 0.60 | "compress more aggressively" |
| kCeiling | 0.99 | 0.95 | "lower the ceiling" |
| kUpperBound | 0.50 | — | raise it: spline lasts longer before compression |

Per-sample transfer (C1-continuous at both zone boundaries):

```cpp
const float abs_x = std::abs(x);
float y;
if (abs_x < kLowerBound) {
  y = abs_x * kRExp;                          // Zone A - linear expansion
} else if (abs_x < kUpperBound) {
  const float z = abs_x - kLowerBound;        // Zone B - quadratic spline knee
  y = kYLower + z * kRExp + kKneeA * z * z;
} else {
  y = kYUpper + (abs_x - kUpperBound) * kRComp; // Zone C - linear compression
  if (y > kCeiling) y = kCeiling;
}
buf[i] = (x >= 0.0f) ? y : -y;
```

Verification greps of that era: `kYLower = 0.20f`, `kYUpper = 0.76f` must
exist; the older broken `y_low = 0.12f` must NOT.

## 2. The catastrophic dB-domain mistake (why Rule 1 exists)

Source: Compander_DSP_Signomial_Curve, 6_Stage_Hybrid_DSP_Implementation.

The dB-compressor formula `y = T + (1 - T) * tanh((x - T) / (1 - T))` was
applied to raw float32 samples in [-1, 1]. In the dB domain T is a threshold
in decibels; on linear samples the algebra explodes: outputs hit ~1.70, the
safety clamp at 0.95 turned sines into squares, and the VAIO chassis buzzed.

**Rule 1: never apply a dB-domain formula to linear amplitude samples.**

## 3. Waveshaper vs compressor (why the signomial was retired)

Source: dsp_pipeline_ordering_and_waveshapers (graded CURRENT-TRUE 2026-08-02).

Any memoryless per-sample curve — signomial included — reshapes the waveform
itself (harmonic distortion, "tinny", chassis resonance). A true compander
tracks the signal envelope over time (attack/release) and applies a gain that
varies slowly relative to the waveform.

**Rule 2: memoryless math is only legitimate as a peak-edge soft-clipper
(touching only |x| near the ceiling). Loudness leveling requires an envelope.**

This is exactly why the 2026-08-10 system fix uses SC4 (an envelope-tracking
RMS compressor with attack/release) instead of any static curve.

## 4. Pipeline ordering law

Source: dsp_pipeline_ordering_and_waveshapers, dsp_volume_and_clipping_lessons.

```
decoded samples -> software volume (mVolume x volume_scale) -> DSP/limiter -> DAC
```

- Volume BEFORE DSP: the limiter must see the final intended amplitude.
  (June bug: limiter protected to 0.99, then cubeb multiplied by 4.0 -> 3.96.)
- GetVolumeScale() must not clamp with std::max — system-level volume
  reduction must remain possible.

## 5. The shipped FF154 chain (AudioStream.cpp, tuned ~2026-07-15)

Source: live tree dom/media/AudioStream.cpp, verified healthy by measurement
2026-08-10 (+8 dB vs unity at 2731 Hz: volume_scale 2.0 (+6 dB) x DSP (~+2 dB)).

```
x -> one-pole crossover split (bass LP 220 Hz, treble split 3500 Hz)
  bass'   = bass   * 1.8            // +5.1 dB Fletcher-Munson low shelf
  treble' = treble * 1.4            // +2.9 dB presence
  bass''  = bass' + 0.2 * FastTanh(bass' * 0.4)   // xLOUD harmonic synthesis
  y = (bass'' + mid + treble') * 1.1              // +0.8 dB makeup
  out = soft-knee limiter at 0.9:
        out = 0.9 + 0.1 * FastTanh((y - 0.9) * 10)   (mirrored for negative)
FastTanh(w) = w * (27 + w^2) / (27 + 9 w^2)   for |w| < 3, else sign(w)
```

Superseded generation for contrast (6-stage hybrid, FF153): crossover
250/4000, volume-tracked dynamic gains, 0.99 signomial ceiling.

## 6. The full compander model — G(x), E(t), RMS

Source: `SOURCE_XML/01.MEDIA/Remediation_Plan.xml` (the design document the
signomial implementation approximates). This is where all three
half-remembered names live in one place:

1. **Gain function G(x)** — the compander ("signomial curve"):
   low-level expansion (|x| < T_low): apply k_exp = 2.0x ("the Magnifying
   Glass"); high-level compression (|x| > T_high): apply k_comp ("the Safe
   Ceiling").
2. **Sigmoid envelope E(t)** — vocal-intensity growth modeled with a
   sigmoid-aware soft knee, logistic form 1 / (1 + e^-k), so volume grows
   smoothly.
3. **RMS integration** — gains computed over the frame buffer, not per
   sample, to prevent crackling and quantization noise.

Architectural mapping (same document): AudioStream.cpp implements the
**Polynomial Approximation of G(x)** (hence "polynomial curve");
CubebUtils.cpp is the parameter store for T_low and k_exp.

## 7. The 2026-08-10 system-level answer (SC4 parameters)

When measurement proved the speakers' absolute ceiling is low and content is
mastered at -16..-20 LUFS, the in-browser DSP could not add more loudness
without distortion (peaks already at full scale). The correct lever is
envelope compression before the DAC, system-wide:

```
SC4 (LADSPA sc4m, swh-plugins), mono graph auto-replicated to stereo:
  RMS mode (RMS/peak = 0), attack 3 ms, release 150 ms,
  threshold -20 dB, ratio 4:1, knee 8 dB, makeup +12 dB
Result, mic-verified at matched settings: +10.5 dB RMS, peaks unchanged,
0.2% of one core.
Worst case: 0 dBFS input peak -> 20 dB over threshold -> 5 dB out + makeup
= lands ~-3 dBFS: no clipping by construction.
```

## 8. PipeWire volume law (why sliders lie)

Source: pipewire_volume_scaling_analysis + 2026-08-10 measurements.

PipeWire/PulseAudio sliders use a cubic loudness curve: amplitude = v^3.
31% slider = 0.31^3 ~ -30 dB. The audible action lives in the top third of
every slider. Streams at "117%" add only +4.1 dB. No stack of linear sliders
can exceed the digital ceiling — see Rule in section 7.
