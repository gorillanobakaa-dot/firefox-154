# 2026-08-11 — Cascade pumping fixed (Stage 5b pref gate + soft knee)

**Follow-up to:** `2026-08-10_WHISPER_SAGA.md`, `VERIFICATION.md`, `TIMELINE.md`
**Deep record:** brain + chroma lesson `Loudness_Compressor_Cascade_Pumping_Soft_Knee`
(SECOND.BRAIN/.../Firefox.154.Lessons/06.AUDIO.Pipewire.Wireplumber/)

## What happened

User report: sound "in waves rolling up to the shore". Diagnosis: the
2026-08-10 session shipped the same loudness compressor **twice** — Stage 5b
in `AudioStream.cpp` AND the PipeWire SC4 `loudness_sink` — identical
parameters (−20 dBFS, 4:1, 3 ms/150 ms, +12 dB), both live. In series:
~16:1, ~+24 dB makeup, two unsynchronised 150 ms release envelopes beating.
The 08-10 brain atom predicted it ("either alone suffices") but the cascade
was never auditioned end-to-end.

## Fix (built 2026-08-11, full `./mach build`, dsp-preflight PASS)

1. **`media.gorilla.loudness_compressor.enabled`** (StaticPrefList.yaml,
   RelaxedAtomicBool, **default true**): gates ONLY the Stage 5b compressor
   block — EQ stages (bass 1.8×, treble 1.4×, xLOUD 0.4) stay always-on
   (SC4 does no EQ). Pref read hoisted to once per `Process()` callback.
   Set **false** in `~/.mozilla/ff154-main/user.js`: this machine gets its
   loudness from SC4 alone, every app equally.
2. **8 dB soft knee** in Stage 5b (matches SC4): `kCompKneeDb=8.0f`,
   `kCompKneeLo=0.06309573f` (−24 dBFS); quadratic dB-domain blend inside the
   knee; **algebraically identical** to the old hard-knee curve above it —
   the +10.5 dB RMS mic verification remains valid (Δ < ~1 dB near threshold).

## Deliberately NOT done

- **No extra gain** (user floated ~+6 dB → −14 dBFS): current chain peaks at
  −3 dBFS from full-scale input; +6 dB clips 0 dBFS and drives the Stage 6
  limiter into constant engagement (a new pumping source). Any retune goes
  through `dsp-ab-lab.py` measurement first — "let's not operate on faith"
  (user, verbatim).
- **loudness-sink.service untouched** — disabling it is "remove the
  loudness", explicitly rejected.

## A/B methods

- No-rebuild (used for diagnosis): `pactl set-default-sink <hw-sink>` bypasses
  SC4 reversibly; restore with `pactl set-default-sink loudness_sink`.
- Post-build: flip `media.gorilla.loudness_compressor.enabled` in
  about:config — true briefly recreates the cascade, false kills it.

## Status

Built and deployed 2026-08-11; sink restored to `loudness_sink`; user.js set.
**End-to-end listening confirmation on the new build: still pending** — the
user was pulled onto the WhatsApp call work before reporting back. If waves
persist with the pref false, the diagnosis is wrong and the next suspect is
Stage 5b's hard knee alone (now soft) or SC4's own settings — measure, don't
guess.
