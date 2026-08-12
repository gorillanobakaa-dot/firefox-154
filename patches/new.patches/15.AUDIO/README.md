# 15.AUDIO — the complete audio record of Project Unleashed

Assembled 2026-08-10, the day the chronic VAIO whisper was resolved by
measurement. This folder is the audio counterpart of its siblings
(01.MEDIA .. 14.EGRESS.LOCKDOWN): everything this project has learned,
broken, derived, and shipped about sound, from the lost April beginnings to
the verified +10.5 dB system fix.

## Map

| Item | What it holds |
|---|---|
| `TIMELINE.md` | The full chronology: every decision, error, and roadblock, Era 0 (lost April-May) through 2026-08-10. Start here. |
| `MATH_DSP_FORMULAS.md` | All the math: the Signomial Curve (three-zone compander, ex-"G1"), the dB-vs-linear catastrophe, waveshaper-vs-envelope law, pipeline ordering law, the shipped FF154 DSP chain, SC4 parameters, the cubic slider law. |
| `2026-08-10_WHISPER_SAGA.md` | Tonight's full session record including the two retracted theories and the measurement doctrine they produced. |
| `LESSONS_EXTRACTED/` | 28 audio concepts dumped from the SQLite brain (dual-track rationale + execution logic), one file each. |
| `SOURCE_XML/` | The authoritative lesson XMLs copied from both tiers: the main Brain and Firefox.154.Lessons (01.MEDIA + the whole 06.AUDIO.Pipewire.Wireplumber directory). 67 files. |
| `EXTRACTION_RAW/audio_fx_tiers.json` | Raw output of memory_tier_extract.py over the Firefox tiers (4,653 attributed snippets matching the audio regex) — the haystack the curated docs were distilled from. |
| `SYSTEM_FIX/` | Snapshot of the deployed loudness sink (SC4 filter-chain config + systemd user unit) and its verification record (+10.5 dB RMS, 0.2% CPU). Live copies: ~/.config/pipewire/filter-chain.conf.d/60-loudness.conf and ~/.config/systemd/user/loudness-sink.service — both chattr +i since 2026-08-10 (chattr -i before editing). |
| `tools/speaker_loudness_setup.py` | One-click installer of the same fix for OTHER machines: detects PipeWire or PulseAudio, installs the SC4 plugin via the native package manager, deploys the compressor sink, verifies by artifact, supports --status / --uninstall / --armor (chattr +i). Stdlib-only Python, ships alongside the browser release. |

## The one-paragraph story

Serious audio work began ~April 2026 (Era 0, mostly destroyed by a rogue
unattended agent; earliest surviving artifact 2026-05-17). The FF153 era
tried to recreate Sony xLOUD in AudioStream.cpp and learned the three hard
laws (linear domain only; envelope not waveshaper; volume before DSP) at the
price of square waves and a buzzing chassis. The FF154 era shipped a tuned
fixed-gain psychoacoustic chain and fought the OS plumbing (S24LE trap,
parasitic filter-chain, name-purge regressions). The kernel era chased a
+5.5 dB EAPD patch that 2026-08-10 measurement finally proved to be a
placebo. The whisper itself was never a bug: a low absolute speaker ceiling
meeting content mastered 20 dB quiet, with every linear gain already at max.
The answer was the thing the project had been circling since April —
envelope compression — landed system-wide as an SC4 filter-chain sink and
verified with the internal microphone: +10.5 dB, peaks capped, 0.2% CPU.

## Standing doctrine (do not relearn these)

1. Never apply dB-domain formulas to linear samples.
2. Loudness needs an envelope follower; memoryless curves are clippers only.
3. Software volume BEFORE the DSP/limiter.
4. `pw-record` taps of stream nodes LIE under CPU load on this machine —
   tap a known-level control stream first, or use the mic with a dual-band
   pilot. (Born 2026-08-10 after two false theories.)
5. Debian's stock `filter-chain.service` stays MASKED (it resurrects via
   preset after cleanups). `loudness-sink.service` is DELIBERATE — never
   purge it by pattern-match on "filter-chain".
6. After any bulk rename/cleanup, re-verify every fix that lives in a file
   (config, mask symlink, unit). This has bitten twice (2026-08-02 purge,
   kernel port).
7. "Clips the internal mic" proves relative headroom only (+29 dB capture
   boost) — never absolute loudness.
8. Sliders are cubic: 31% = -30 dB. The action lives in the top third.
