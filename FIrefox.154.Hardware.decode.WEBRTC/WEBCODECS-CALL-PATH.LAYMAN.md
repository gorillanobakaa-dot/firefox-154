# 🧍 The Call That Never Reached the Chip — How Video Calling Moved Out of Your Browser

> *Topic `01-media` follow-up · Gorilla Unleashed Firefox 154 · Written for everyone · 2026-08-11*
> *Companion: `WEBCODECS-CALL-PATH.DEVELOPER.md` · Evidence: `evidence-2026-08-11/`*

---

## 🌍 The Big Picture

For twenty years, the deal between a web page and a browser was simple. The page
said *"here is a video, please play it."* The browser decided **how** — and on a
machine like this one it would hand the work to a dedicated chip inside the
processor, a small piece of silicon that does one job, does it in hardware, and
does it for about two watts.

That deal is quietly ending.

Modern calling apps no longer ask the browser to play video. They ask the browser
for **raw access to an encoder**, do the work themselves inside the page, and
hand back a stream of bytes the browser simply ferries across the network like
any other data. The browser is no longer the one deciding how video gets
decoded. The web page is. And a web page cannot use the dedicated chip in this
laptop, because that chip only speaks one language — H.264 — and the page has
chosen a different one.

We did not read this in an article. We measured it, on this machine, during a
real five-minute WhatsApp video call, while the person on the other end talked
back. **The dedicated video chip never woke up. Not once. It sat at zero percent
for the entire call while the processor burned eighteen watts doing the work by
hand.**

This document is the story of how we found that out, why our own build refused
the call, and what it means for anyone trying to keep an old computer useful.

## 🎭 The Main Characters

| Name | What It Is | Real-World Comparison |
|---|---|---|
| **The video ASIC** | A dedicated chip inside the Intel HD 4000 that decodes H.264 video in hardware, using almost no power | A pasta machine — it makes exactly one shape, perfectly, effortlessly, forever |
| **Software decoding** | The main processor doing the same job by brute force, in general-purpose code | Rolling and cutting that pasta by hand — same result, an hour of your life, and you are sweating |
| **The hardware-only policy** | Our build's rule: if the chip cannot do it, refuse rather than fall back to hand-rolling | A kitchen rule: we use the machine or we do not make pasta. No exhausted chefs |
| **WebCodecs** | A newer browser feature that hands a web page direct access to video encoders | Letting the customer walk into the kitchen and cook their own meal, using whatever method they like |
| **WhatsApp Web's calls** | A page that uses WebCodecs to encode video itself, then sends the bytes down a plain data pipe | The customer cooking in your kitchen, ignoring your machine, using a pan they brought from home |

## 🔢 How It Works — Step by Step

### Step 1: We assumed the problem was codecs. We were wrong three times.

Calls did not connect in our browser. The obvious suspects were all wrong, and
each was eliminated by measurement rather than argument:

- **"The network is blocking it."** No. The same call connected perfectly in
  Chromium on the same laptop, on the same wifi, minutes apart.
- **"Our browser cannot find its way through the router."** No. We tested the
  address-discovery machinery in isolation — it worked every time.
- **"A privacy setting added on 10 August broke it."** No. We ran the test with
  that setting on and off; the results were identical, character for character.
  We had publicly accused that change. **It was innocent, and we withdrew the
  accusation.**
- **"The microphone and camera are blocked."** No. We wrote a small test page;
  both devices opened immediately.

Four theories, four measurements, four corrections. That is not wasted effort —
it is what stops a wrong story being published as a right one.

### Step 2: The call had no video channel. In *either* browser.

Browsers keep an internal record of every call connection. We pulled that record
out of Chromium **during a working call** and found something that stopped the
investigation cold: the call had **no video channel and no audio channel**. None.

Not a broken one. Not a rejected one. There was simply no place in the
connection where audio or video was supposed to travel. Only a plain **data
pipe** — the same kind of channel used to send a file or a chat message.

That is the moment the entire theory collapsed. We had spent hours asking *"why
is our video codec being refused?"* The answer was that **nobody ever asked for
a video codec.** Our browser's codec policy was never consulted, because the
negotiation it governs never happened.

### Step 3: So where was the video going? Into the page itself.

If the video is not travelling in a video channel, but the other person can
clearly see and hear you, the video must be going down the data pipe — as
anonymous bytes.

That means the *page* is doing the encoding. WhatsApp's JavaScript takes frames
from your camera, compresses them itself using a browser feature called
**WebCodecs**, and drops the results into the data pipe like luggage onto a
conveyor belt. The browser never learns that those bytes are video. It cannot
route them to the dedicated chip, because as far as it knows, it is moving
cargo, not pictures.

Zoom's web version has worked this way for years. WhatsApp does it now too. This
is not a bug in either. It is a deliberate design choice, and it is spreading.

### Step 4: Why our build refused — the real reason, at last

WebCodecs still has to ask the browser for an encoder. And in our build, that
request goes through the same gate that governs everything else: **hardware or
nothing.**

When WhatsApp asked our browser for a VP8 encoder — VP8 being a format the Intel
HD 4000 has no chip for — our build did not politely answer *"no."* It threw an
error. WhatsApp's call setup hit that error and stopped, permanently, on
"Connecting…".

We proved this with a five-line test page, run in both browsers:

| Format asked for | Our build | Chromium |
|---|---|---|
| VP8 | **error** | yes |
| VP9 | **error** | yes |
| H.264 | yes | yes |

Same page. Same laptop. Minutes apart. That is the whole bug, in one table.

### Step 5: The uncomfortable measurement

Here is the part that changes the argument rather than settling it.

We measured Chromium — the browser where the call *works* — during the live
call:

| What we measured | Reading |
|---|---|
| Call length | 5 minutes, real conversation |
| Data moved | 45 MB, all of it relayed through Meta's servers |
| Speed | about 1.36 megabits per second |
| **Dedicated video chip** | **0.0% busy — idle the entire call** |
| Processor | ~130% of one core (of eight) |
| **Power drawn by the chip package** | **16–18 watts** |

The browser that "works" is not using the hardware either. **It cannot.** There
is no VP8 chip in this laptop, so there is no hardware path for anyone to take.
Chromium is not smarter than our build. It is simply willing to do the work by
hand, quietly, at eighteen watts, on a fifteen-year-old battery.

So our policy was never denying you a hardware-accelerated call. **It was
refusing a call that could never have been hardware-accelerated in the first
place.** The policy was right about the facts and wrong about the outcome — it
protected the processor by removing the feature.

## 🤔 Quirky Things Worth Knowing

### ⚠️ We published a wrong diagnosis in July, and this corrects it

On 24 July this project concluded that WhatsApp Web "does not negotiate H.264
properly" and called it a WhatsApp compatibility problem. **That was wrong.**
There was never a negotiation to fail — WhatsApp does not negotiate video codecs
with the browser at all. We reached the right verdict ("calls will not work") via
completely the wrong reasoning, which meant every fix that followed aimed at the
wrong target.

That same document recommended **using Zoom instead**, for better hardware
decoding. That is also wrong, and worse than wrong: Zoom's web client uses the
same in-page technique, so it is *guaranteed* software decoding. If you want the
dedicated chip to actually do work, **Microsoft Teams** (which really does use
H.264) or **Jitsi** (which can be told to use H.264) are the ones that reach it.

Correcting your own published documents is the price of claiming transparency.
This paragraph is that price being paid.

### ⚠️ The off-switch did not work

Our build has a master switch — *hardware-only mode* — that is supposed to let
you turn the whole policy off. It does not work properly. Two of the three code
changes obey it; the third ignores it entirely and enforces the policy
unconditionally.

So anyone who found the switch, flipped it, and expected standard browser
behaviour got… the policy anyway, silently. A switch that lies is worse than no
switch, because it sends you looking for the problem somewhere else. We found
this by flipping it and measuring — the result was identical. It is being fixed
in the same patch as everything else.

### ⚠️ Nobody is being singled out — that is the point

It is tempting to read this as Meta deciding old computers should die. The
duller truth: encoding video inside the page gives them one identical code path
across every browser and platform, and avoids licensing fees on H.264 — a format
that costs money to use and that the royalty-free alternatives (VP8, VP9, AV1)
do not.

Nobody sat down and decided to break a 2012 laptop. They decided to simplify
their engineering and reduce a licence bill, and the laptop broke as a side
effect nobody was in the room to notice. That is how almost all of this happens.
It is not cruelty. It is an absence of anyone whose job it was to care.

## 💻 What Does This Mean For YOU?

**If you are using this build:** WhatsApp video calls will not work until the
patch lands, and once it does, they will work by burning about eighteen watts
and a core and a half of your processor. On a laptop with a tired battery, a
long call is a real cost — expect heat, fan noise, and materially shorter
runtime. That is not our build being inefficient; that is what the call costs
anyone on this hardware, including Chromium.

**If you want calls that actually use your machine's video chip:** use Teams or
Jitsi, or make calls on your phone. Phones have H.264 chips *and* the apps use
them properly. The strange result of all this is that the £30 phone in your
pocket handles a video call more efficiently than the laptop — not because it is
faster, but because its software still lets the hardware do its job.

**If you are watching normal video — YouTube, films, anything that is not a
call:** none of this affects you. The hardware-only policy works exactly as
designed there, the dedicated chip does the work, and the saving is real and
large. This entire story is about one narrow case: live calls, where the app has
taken the wheel.

**And the wider warning, which is why we wrote this publicly:** "my browser
supports hardware video decoding" is no longer enough to guarantee anything. The
web is moving video processing *into the page*, where your hardware cannot be
reached. Every app that makes that move converts an efficient task into an
expensive one for everybody — but the bill only arrives for people whose
machines cannot absorb it quietly. On a new laptop, eighteen watts disappears
into a big battery and a quiet fan. On this one, it is the difference between a
call and a dead machine.

We cannot fix that from inside a browser. What we can do is measure it, name it,
and refuse to pretend the loss is invisible.

---

*Every number in this document came from this laptop on 2026-08-11 and is
reproducible from the archived evidence. Nothing here was estimated. Where we
were wrong — four times — we said so and left the corrections in.*
