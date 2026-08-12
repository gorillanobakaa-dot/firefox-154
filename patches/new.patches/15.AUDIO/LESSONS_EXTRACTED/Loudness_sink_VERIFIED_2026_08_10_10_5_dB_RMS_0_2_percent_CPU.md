# Loudness_sink_VERIFIED_2026_08_10_10_5_dB_RMS_0_2_percent_CPU

**Source:** Loudness_sink_VERIFIED_2026_08_10_10_5_dB_RMS_0_2_percent_CPU.xml

## Rationale

The compressor fix was measured working: music now plays 10.5 dB louder at the same settings, peaks stay safely capped, and the CPU cost is nothing. The listening slider that used to be pinned at max now sits comfortably at 44 percent.

PROBLEM: Needed objective proof the SC4 loudness sink delivers the predicted gain without CPU cost before calling the whisper saga closed.

## Execution Logic

SOLUTION: Mic A/B at matched settings. Saga closed: chronic VAIO whisper = low speaker ceiling + quiet-mastered content; answer = system-wide compression, delivered and verified.

Matched-conditions mic verification (media.volume_scale 2.0, all volumes 100 percent, same internal mic): RMS -19.15 dB without compressor vs -8.67 dB with SC4 filter-chain sink = +10.5 dB RMS, mic clipping both times so gain is a floor estimate. pw-top: loudness_sink 13.9us + loudness_sink_out 23.1us busy per ~21333us quantum (~0.2 percent core). All chip-brief criteria met: gain in 8-12 dB target, peaks unchanged at ceiling, default sink kept, toggle documented, media.volume_scale confirmed back at 2.0. See install lesson for paths and bypass commands.

KEYWORDS: loudness sink verified, 10.5 dB, SC4, whisper saga closed, mic verification
