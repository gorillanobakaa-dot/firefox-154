# The One-Inch Hole in the Fortress Wall — how WhatsApp calls came to the main browser

**Date:** 2026-08-11/12 · **Sequel to:** WEBCODECS-CALL-PATH.LAYMAN.md
**Status:** browser side verified end-to-end; awaiting a real answered call

## Where the last story ended

Yesterday we discovered WhatsApp doesn't use the browser's normal video-call
machinery at all. It compresses video *itself, inside the web page*, using a
tool called WebCodecs, and posts the result down a plain data pipe. And it
insists on one specific codec for this: VP8.

Our browser is a fortress: every codec that can't run on the 2012 laptop's
hardware chip was not just disabled but *removed*. VP8 has no hardware chip on
this machine — on ANY browser, a WhatsApp call burns CPU. So the fortress was
refusing a call that could never have been hardware-accelerated anyway.

## The decision

Cut a hole exactly one codec wide, in exactly one wall, that only one kind of
visitor can walk through:

- **Which codec:** VP8 only. VP9, AV1, everything else — still bricked up.
- **Which wall:** only the private door WebCodecs uses. Normal web video
  (YouTube's `<video>`, streaming, WebRTC) uses different doors that never
  changed. YouTube still gets told "H.264 only" and still lands on the
  hardware chip.
- **Who can open it:** nobody, by default. The hole is behind a switch
  (`media.gorilla.webcodecs_software_vp8`) that ships **off**. Downloaders
  get the fortress exactly as before. This machine flips it on in its own
  settings file.

If this sounds familiar: Firefox 152/153 did both things at once — YouTube on
the hardware chip AND WhatsApp calls — because back then the software codecs
were merely *hidden from YouTube*, not removed. This restores that behaviour
at the narrowest possible width.

## The four walls (each hidden behind the last)

Cutting the hole should have been one change. It was four, and each one only
became visible after the previous one fell. This is the real lesson.

1. **The wrong gatekeeper was consulted.** When a page asks "can you do VP8?",
   the answer accidentally came from the *YouTube-steering* gatekeeper, whose
   whole job is to say NO to VP8. Even Mozilla's own engineers left a note in
   the code saying this wiring is wrong. We routed the question correctly.

2. **A pantry was padlocked.** To set up a VP8 decoder the browser needs to
   read a recipe from the "WebM" pantry — and the fortress had padlocked that
   pantry shut with a setting. Unlocking it sounds scary but isn't: the
   fortress's REAL wall against WebM video is a separate iron gate that we
   proved still slams shut (we measured it: YouTube-facing answers unchanged).

3. **The wrong worker kept grabbing the job.** With the recipe available, a
   hardware-only worker kept claiming the VP8 job first — then refusing to do
   it, on principle, every time. We moved the software worker to the front of
   the queue *inside the WebCodecs door only*.

4. **Our fix was written in a room nobody enters.** The first version of that
   queue change sat inside a block of code that, on Linux, never runs at all
   (it's for iPhones). The logs showed an empty worker list — the tell. Moved
   it outside; done.

## Proof, not promises

A support check that says "yes" proves nothing — the third wall said "yes"
and then refused the actual work. So the final proof was a full rehearsal in
the real browser, no window needed: open the real camera, compress five real
frames to VP8, then decompress all five back. **5 out of 5, both directions.**
Same test on factory settings: VP8 politely refused, exactly as shipped.

## The two impostors along the way

- **"ICE failed" in the console** looked like a network problem. It wasn't —
  when the video pipeline died, the call tore everything down, and the network
  layer's obituary got printed as if it were the cause. The network layer,
  measured on its own, connects to Meta's servers flawlessly.
- **The frozen call screen** (black self-view, a hang-up button that ignores
  clicks) turned out to be Firefox's own guard dog: WhatsApp's call code ran
  more than 30 straight seconds on this 2012 CPU, the guard killed the
  script, and the page's buttons died with it. The guard is now off on this
  machine. That story has its own write-up.

## What it costs

Nothing, until a call happens. During a call: roughly one-and-a-third CPU
cores and ~18 watts — the same price Chromium pays on this machine, because
the price is physics (no VP8 chip exists in an Ivy Bridge), not our build.
