# Loudness sink — install and verification record (2026-08-10)

Deployed files (live copies are canonical; these are archive snapshots):
- ~/.config/pipewire/filter-chain.conf.d/60-loudness.conf   (the SC4 graph)
- ~/.config/systemd/user/loudness-sink.service               (runner: pipewire -c filter-chain.conf)
Package: swh-plugins (LADSPA sc4m). PipeWire builtin filter-chain plugins
contain NO compressor - the package is required.

Verification (matched conditions: media.volume_scale 2.0, all volumes 100%,
internal mic, same position):
  without compressor: RMS -19.15 dB, peaks at mic ceiling
  with    compressor: RMS  -8.67 dB, peaks at mic ceiling
  = +10.5 dB RMS. CPU: 13.9us + 23.1us busy per ~21333us quantum (~0.2%).

Operations:
  bypass:   make "Built-in Audio Analog Stereo" default (pavucontrol > Output Devices)
  disable:  systemctl --user disable --now loudness-sink.service
  re-check after ANY bulk cleanup: systemctl --user is-enabled loudness-sink.service   (want: enabled)
                                   systemctl --user is-enabled filter-chain.service    (want: masked)
DO NOT purge by pattern-match on "filter-chain": the masked unit is Debian's
stock parasite; loudness-sink.service is deliberate and verified.

Armor (added 2026-08-10, same session): both live files are chattr +i
(immutable) - cleanup scripts, purges, and even root rm bounce off until an
explicit 'sudo chattr -i <file>'. Disarm before any deliberate edit, re-arm
after. The one-click installer (tools/speaker_loudness_setup.py) offers the
same via --armor / --disarm.

Slider authority (added 2026-08-10, late evening): with the compressor sink
as default, the desktop slider writes the PRE-compressor volume and a 4:1
compressor absorbs ~75% of it - the slider feels dead, then cliffs.
Attempted fix "hardware sink as default + routing rules" FAILED: every
stream restart escaped the compressor back to the default. Final design
(owner-approved by ear): compressor stays default; loudness-volume-mirror
daemon (~/.local/bin + user unit, snapshots here) mirrors slider moves onto
the hardware sink through a 0.75-power map so pre+post combine to a normal
taper. Law: never leave the user volume control upstream of a compressor.
After cleanups verify BOTH: loudness-sink.service and
loudness-volume-mirror.service active.
