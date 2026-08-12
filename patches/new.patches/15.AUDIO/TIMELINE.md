# Audio Work Timeline — every decision, error, and roadblock

Reconstructed 2026-08-10 from the SQLite brain (28 concepts), the Firefox.154
lesson XMLs, the kernel brain, patch logs, and the 2026-08-10 measurement
session. Each entry says what was decided, what went wrong, and what survived.

---

## Era 0 — The lost beginning (April–May 2026)

Serious audio work started around **April 2026** (owner's recollection). Most
April-era artifacts did NOT survive: a Gemini agent left running unattended
"optimized" the tree, and the later 16,000-occurrence "gorilla" name-purge ate
more (any file with the old names, including config masks). What remains of
the era is forensic residue:

- **2026-05-17** — pristine Firefox 153 source baseline timestamp (the oldest
  surviving dated marker in the audio record).
- **2026-05-25..31** — PROVENANCE sweep of the FIrefox.153.Work tree,
  including `correction_tools/mass_zero_byte_ghost.py` — a repair tool for
  zero-byte-ghosted files, i.e. direct evidence of the damage-repair effort.
- The `Firefox.Scripts.Backup.Docs/01_Media_Audio_Video/` human-readable docs
  (incl. `Unleashed_153_Report.docx`) survive only as a brain snapshot of the
  directory listing; the directory itself is gone from disk.

Anything claimed about April must be treated as oral history; nothing dated
before 2026-05-17 survives in any tier.

## Era 1 — Firefox 153, the "G1" compander (May–June 2026)

- **2026-06-05..06** — the first media engine rewrite (30-Day Timeline,
  Phase 1): CubebUtils.cpp and AudioStream.cpp gutted, global 48000 Hz lock,
  400% volume boost injected in the software callback, first "gain-aware
  polynomial soft-knee limiter". The earliest surviving dated audio
  engineering record.

**Goal:** recreate Sony's xLOUD DSP in AudioStream.cpp because the SVE14A3AJ
speakers are too quiet.

- A Gemini model coined the brand name "G1" for the custom compander curve,
  named after the performer of the test ballad. Renamed 2026-08-02 to
  **Signomial Curve** — named for what it is. (This is the origin of the
  half-remembered "ladosi / signomial / polynomial curve" names.)
- **ERROR — dB-domain formula on linear samples.** The dB compressor formula
  `y = T + (1 - T) * tanh(...)` was applied directly to float32 samples in
  [-1, 1]. Output jumped to ~1.70, hard-clamped at 0.95 → square waves →
  severe chassis vibration. Lesson: *never use a dB-domain formula on linear
  amplitude.* (Compander_DSP_Signomial_Curve, 6_Stage_Hybrid_DSP)
- **ERROR — pipeline ordering blindness.** A limiter ran in DataCallback on
  pre-gain samples while cubeb applied 4.0x gain afterwards. Protecting to
  0.99 then multiplying by 4 = output 3.96, DAC clipping. Lesson: *software
  volume BEFORE the DSP; the compressor must see final amplitude.*
- **ERROR — instantaneous waveshaping as "compression".** Memoryless formulas
  reshape the wave itself (sine → square, tinny + chassis buzz). True
  companders track an envelope (attack/release); memoryless math is only
  acceptable as a peak-edge soft-clipper.
- **Fix of that era — audio_fixes_v2:** three-zone linear-domain compander
  (expansion / C1 quadratic spline knee / compression with ceiling),
  precomputed constexpr constants. Full code preserved in
  SOURCE_XML/firefox_media_audio_video_patches_20260619.xml and
  MATH_DSP_FORMULAS.md. The FIrefox.153.Work tree itself is gone from disk.
- 6-stage hybrid DSP of that era: 250/4000 Hz crossover, volume-tracked
  dynamic gains, 0.99 signomial ceiling — all later superseded.

## Era 2 — Firefox 154 port and system plumbing (June 2026)

- **2026-06-19** — media/audio/video patch wave lands in FF154
  (firefox_media_audio_video_patches_20260619: the 9-bug series, DSP port).
- **2026-06-26 — PipeWire ALC269 pipeline unlock.** End-to-end audit method
  canonized. Two of its claims later corrected:
  - **ERROR:** the "S24LE upgrade" was itself the no-sound bug — the HDA
    driver exposes S16/S32 only (pipewire_s24le_format_rejection).
  - **ERROR:** Debian's stock `filter-chain.service` was found inserting a
    resampler/EQ node into the graph ("parasitic") and was believed disabled;
    user-scope disable cannot beat a global preset. **Masked** 2026-06-26.
    It RESURRECTED after a bulk cleanup deleted the mask symlink; re-masked
    2026-08-02. Doctrine: re-verify `is-enabled == masked` after any cleanup.
- **2026-06-27 — the King Kong conflict.** Kernel-level +60 dB ALC269
  amp-caps override ("King Kong") audited against the Firefox DSP: stacking
  +60 dB hardware offset on the browser's bass boost risked speaker damage,
  destroyed slider resolution (blasting at 2%), flattened dynamics.
  **Decision: retire King Kong**; docs claimed a firmware-driven EAPD boot
  fix would replace it — **that replacement was never installed** (and 2026-08-10
  measurement proved it unnecessary: the stock driver raises EAPD itself).
- **2026-06-28** — kernel 7.1.2 `eapd.5db` build ships the surviving alc269
  amp-caps-offset patch (+5.5 dB claim, never measured).

## Era 3 — FF154 DSP as shipped (July 2026)

- **2026-07-05** — media audit, DSP auditor rebuild, 60fps unlock session.
- **2026-07-08** — **ERROR (architectural):** DynamicsCompressorNode bypass
  added under media.gorilla.hardware_only_mode, justified as "prevents
  re-compression of AudioStream DSP output". The premise is false — WebAudio
  and AudioStream are parallel output paths, never chained. Verified
  2026-07-15 only as "applied", never as "correct".
- **≈ 2026-07-10..15** — final shipped DSP tuning in AudioStream.cpp:
  crossover 220/3500 Hz, FIXED gains (bass 1.8x, treble 1.4x — no longer
  volume-tracked), xLOUD drive 0.4 blend 0.2 (reduced from 0.9/40% for
  chassis resonance), makeup 1.1x, FastTanh soft-knee limiter at 0.9
  (raised from 0.8). media.volume_scale default "2.0".

## Era 4 — audits and contamination (August 2026)

- **2026-08-02 — the name-purge regression + audio-path forensics.** The
  16,000-occurrence "gorilla" name-purge deleted the three custom PipeWire
  configs (named 10-gorilla-*.conf) AND the mask symlink holding off Debian's
  stock filter-chain.service. The parasite resurrected; 44.1 kHz content got
  stock-quality resampled to 48 kHz — the "metallic edge". Fix: configs
  restored with purge-proof names (10-unleashed.conf: device clock FOLLOWS
  content rate), parasite re-masked. Canonized the layer-by-layer forensic
  method: prove patches byte-identical vs vanilla, prove the binary by
  negative-space string checks, only then descend. Same day: the
  **DSP A/B lab** (measure / simulate / listen) methodology recorded, and
  the audit pass grades every audio lesson (CURRENT-TRUE / HISTORICAL-TRUE /
  SUPERSEDED-DANGEROUS); G1 renamed Signomial Curve; 192 kHz unlock build
  recorded (firefox_192khz_unlock_build_success).
- **2026-08-09** — kernel port audit: Gemini-contaminated 7.1.2 port had
  silently dropped 11/12 patches; only the alc269 EAPD fixup survived.
  Doctrine: verify artifacts, never docs or exit codes.

## Era 5 — 2026-08-10: the whisper saga resolved

Full record in 2026-08-10_WHISPER_SAGA.md. Summary:

- Complaint: sliders past 100% for a whisper. Suspects eliminated by
  measurement: mixers (~8 dB total), EAPD (verified functional via hwdep
  toggle + mic), kernel patch (proven metadata-only placebo — targets a
  mute-only pin amp and a vendor widget that is not an amp), browser DSP
  (verified healthy: +8 dB measured via calibrated dual-band mic test).
- **Two wrong theories retracted the same evening:** (1) the compressor
  bypass as cause — the playback path never touches WebAudio; (2) a
  "phase cancellation" bug — an artifact of pw-record stream taps dropping
  chunks under CPU load. Doctrine: on this machine, tap a known-level
  pw-play control before trusting any digital capture; prefer the mic with
  a simultaneous dual-band pilot.
- **Verdict:** nothing broken. Low absolute speaker ceiling x content
  mastered at -16..-20 LUFS x YouTube normalization that only attenuates.
  Digital peaks already at full scale — no linear gain could ever help.
- **Fix shipped:** system-wide SC4 compressor sink (see SYSTEM_FIX/).
  Measured **+10.5 dB RMS** at matched settings, peaks unchanged, 0.2% CPU.
  The June "filter-chain is a parasite" doctrine is hereby superseded for
  THIS deliberate unit — see README.md reconciliation.

## Era 5 addendum — same evening: the fix ships to everyone

- **2026-08-10 20:05** — libxul rebuilt with the envelope loudness compressor
  in AudioStream.cpp (Stage 5b: the SC4 parameters as an envelope follower)
  and the DynamicsCompressorNode bypass removed. Two-point mic verification:
  -30 dBFS tone exits +10 dB hotter (-12.0 dBFS, design predicted -11.9);
  -12 dBFS tone exits +0.5 dB. Compression confirmed, not gain. Patch
  masters regenerated from SafetyVault pristine diffs.
- **2026-08-10 20:09** — speaker_loudness_setup.py published:
  https://github.com/gorillanobakaa-dot/speaker-loudness-fix
  (MIT, dual-track README including the honest story of the fifteen-month
  premise error). The fix that took a fortune in reasoning compute to find
  is now a free download for anyone with a whispering laptop.
