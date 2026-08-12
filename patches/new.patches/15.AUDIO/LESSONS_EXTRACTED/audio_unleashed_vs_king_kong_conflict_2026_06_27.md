# audio_unleashed_vs_king_kong_conflict_2026_06_27

**Source:** audio_unleashed_vs_king_kong_conflict_2026_06_27.xml

## Rationale

Audited the interaction between the kernel-level ALC269 Realtek codec amplifier override (+60dB King Kong quirk) and the browser-level Firefox AudioStream.cpp psychoacoustic enhancer DSP.

## Execution Logic

The audio signal pipeline flows: Firefox DSP -> PipeWire/Pulse -> ALSA Driver (King Kong) -> Speakers.
    Conflicts identified:
    1. Over-amplification & Speaker Blowout: Combining Firefox's software bass boost (+2.6dB) and make-up gain (+2.3dB) with the kernel's +60dB hardware amp capability override will send excessive voltage to the SVE speakers, exciting chassis resonance and risking physical damage to the speaker cones.
    2. Dynamic Range Compression: Firefox's soft-knee limiter clamps peaks above 0.93. Blasting this digitally compressed output via a +60dB hardware offset flattens the audio's dynamic range.
    3. Volume Resolution Loss: The +60dB shift destroys low-volume slider capability, rendering quiet playback impossible.
    4. EAPD Power Fix Integration: Resolving the EAPD low-power pin state using CONFIG_SND_HDA_PATCH_LOADER firmware enables normal hardware volume; stacking the King Kong quirk on top creates massive over-amplification.
