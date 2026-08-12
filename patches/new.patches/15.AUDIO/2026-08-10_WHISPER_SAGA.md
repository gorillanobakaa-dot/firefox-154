# 2026-08-10 — The Whisper Saga: full session record

The evening the chronic "sliders past 100% for a whisper" complaint was
finally resolved. Recorded with the wrong turns intact, per house doctrine:
errors are part of the record.

## The complaint

Every volume control at or past 100% (YouTube 100%, pavucontrol stream
104-117%, sink 73-100%, alsamixer maxed) produced "just audible" sound.
Kernel 7.1.2 build 3 (forensic-eapd-sdr-bbr) booted the same morning 11:20;
browser libxul rebuilt 14:12 (WebRender compositor revert).

## Layers eliminated, in order, with the evidence

1. **PipeWire/mixer chain** — accounted for only ~8 dB (sink 73% = -8.2 dB,
   Master -7 dB, PCM -0.2 dB). Not a whisper's worth.
2. **Kernel ALC269 patch** — proven a placebo by reading the codec:
   ALC269_FIXUP_VAIO_EAPD_5DB only rewrites AC_AMPCAP_OFFSET metadata on
   NID 0x14 (out-amp is mute-only, nsteps=0) and NID 0x21 (a Vendor Defined
   Widget on this codec, not an amp). KERNEL.BRAIN itself marks "+5.5 dB"
   as never measured. Bonus contradiction: docs/alc269.c.md says the patch
   was REMOVED in 7.1.2, yet the 08-10 build re-applied it with the offset
   changed 0x04 -> 0x14, undocumented. The "firmware-driven EAPD boot fix"
   the doc promises was never installed anywhere.
3. **EAPD** — proven FUNCTIONAL live: hwdep verb toggle on NID 0x14 while
   playing a 1237 Hz tone; mic level fell from -17 dB RMS to the -64 dB
   floor and returned on restore. The stock driver raises EAPD itself.
4. **Hardware ceiling headroom** — 0 dBFS tone at sink 100% clipped the
   internal mic (mic capture path has +29 dB boost, so this proves relative
   headroom, not absolute loudness — a distinction that mattered later).

## Wrong turn 1 — the Stable Volume / DynamicsCompressor theory

The fork's DynamicsCompressorNode bypass (added 2026-07-08, premise
"prevents re-compression of AudioStream DSP output") is architecturally
mis-justified: WebAudio graphs output via AudioCallbackDriver and never
chain through AudioStream. Theory: YouTube Stable Volume routes through the
compressor and loses its make-up gain. RETRACTED: the live stream carried
the tab title as media.name = plain HTMLMediaElement path; no Stable Volume
menu exists on this player; WebAudio uninvolved. The bypass remains wrong
on its own merits but was innocent of the whisper.

## Wrong turn 2 — the "phase cancellation" ghost

Digital taps (pw-record --target <node>) showed the browser emitting
-24 dB peaks, "cancellation" behavior with inverted volume response, and a
frequency sweep rendered as clicks-only. ALL ARTIFACTS: a control tap of a
known -12 dB pw-play tone read -20.3 pk / -36.9 RMS with 16 dB crest —
impossible for a sine. Under CPU load this machine's extra capture clients
drop chunks: RMS craters, peaks mangle, spectrograms show click stripes.

**Instrument doctrine born tonight: before trusting any capture, tap a
known-level control stream the same way. Prefer the internal mic with a
simultaneous dual-band pilot (400 Hz system pilot + test tone in another
band); dropouts hit both bands equally and cancel out of the comparison.**

## The verified truth

Calibrated dual-band test (speaker+mic response delta between 2731 Hz and
400 Hz measured at +25.9 dB via the same path first):

- Browser tone came out +8 dB hot vs unity — exactly volume_scale 2.0
  (+6 dB) x AudioStream DSP (~+2 dB) x stream 0.92. The fork's audio path
  is HEALTHY, DSP active, in the shipped libxul.
- Live music at every slider max: mic RMS -19.2 dB vs -5.7 dB for a
  full-scale sine at the same sink — ~13 dB of RMS headroom locked behind
  content dynamics, with digital peaks already at full scale.
- Stats-for-nerds on the test videos: content loudness -16.1 and -20.2 dB
  vs target -14.0; YouTube normalization only attenuates, never boosts.

**Verdict: nothing broken. Low absolute speaker ceiling x quiet-mastered
content x normalization that never helps. No linear gain anywhere in the
stack could ever fix it; only envelope compression could.**

## The fix

1. Interim (live pref): media.volume_scale drives the fork's FastTanh
   limiter every DataCallback; raising it to 4.0-6.0 is instant compression
   + makeup. Returned to 2.0 once the system fix landed.
2. Durable: SC4 loudness compressor sink (see SYSTEM_FIX/), default output
   for all apps. Mic-verified at matched settings: RMS -19.15 -> -8.67 =
   **+10.5 dB**, peaks unchanged at ceiling, ~0.2% of one core. The owner's
   comfortable listening level now sits at 44% of the slider with headroom
   to spare — previously unreachable at every control maxed.

## Doctrine updates from tonight

- The June "filter-chain is a parasite" rule applies to Debian's STOCK
  filter-chain.service (still masked - verify after cleanups). The new
  loudness-sink.service is a DELIBERATE, verified filter-chain: do not
  purge it by pattern-match.
- "Clips the mic" proves relative headroom only; the capture path has
  +29 dB boost. Absolute loudness claims need an acoustic reference.
- apt on this box may need -o Acquire::ForceIPv4=true (IPv6 DNS flaps).
- Media documents in the fork autoplay AAC/m4a but not WAV from file://
  (useful for headless test rigs; wav CANPLAY_MAYBE yet never started).
