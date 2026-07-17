# 🧍 The Media Overhaul — Making Video and Sound Work on an Old Computer — Plain English Guide

> *Topic `01-media` of the Gorilla Unleashed Firefox 154 build · Written for everyone · 2026-07-16*

---

## 🌍 The Big Picture

Modern web browsers try to be all things to everyone. They speak dozens of video 'languages' (codecs), and if the newest one shows up, they fall back on doing the math in software — using your main processor to decompress every single frame. On a laptop from 2012 with a graphics chip designed for the video codecs of *its* era, that fallback is a death sentence: the fan screams, the battery drains, the video stutters, and everything else on the machine grinds to a crawl.

This patch group replaces 'try everything, fall back to slow' with a strict rule: **only H.264, only in hardware, no exceptions**. H.264 is the one video codec this particular graphics chip (Intel HD 4000) has a dedicated decoding circuit for. When the browser sticks to H.264 and lets that circuit do the work, the main processor is barely involved — video plays smoothly, the machine stays cool, and battery lasts.

### ⚡ Now here's the part nobody tells you

The Intel HD 4000 is **not weak hardware.** When it is used for what it was designed to do — decode H.264 video — it is massively over-provisioned. A single 1080p60 YouTube stream (that is, full-HD video at 60 frames per second, the highest quality most videos come in) barely warms the decoder up. You would need on the order of **twenty such streams playing at once** — twenty simultaneous 1080p60 YouTube tabs — before the chip hit its ceiling. Nobody does that. Nobody has ever needed to. The chip has enormous unused headroom, sitting there, ready to work.

**Saturation** is the technical word for "running as fast as the hardware possibly can and cannot go faster." When people say a CPU is saturated, they mean it is at 100% and any new work has to wait in line. Our HD 4000's H.264 decoder is essentially never saturated by real-world browsing. It has huge unused capacity, sitting idle.

**ASIC** stands for *Application-Specific Integrated Circuit* — a piece of silicon that does exactly one thing and does it ridiculously well. Your CPU is the opposite of an ASIC: it is a generalist, good at everything and brilliant at nothing. Your graphics chip contains several ASICs, and one of them is a dedicated H.264 decoder. That ASIC cannot do anything else — but for H.264, it does the work using roughly *one-hundredth* the electricity a CPU would burn for the same job.

So why does an unmodified Firefox on this hardware stutter and drain the battery? **Because Firefox does not route the video work to the ASIC.** It picks VP9 (a codec the ASIC cannot decode) and does the math on the CPU instead — pinning one whole processor core at 100% per video stream, on a machine that only has four cores to begin with. The ASIC sits idle. The CPU cooks. The fan screams. The user concludes "this laptop is too old for the modern web" and buys a new one.

### 💰 Now the part they *really* don't tell you: who this saves money for

There is an actual reason YouTube, Netflix and the rest push VP9 and AV1 over H.264, and it is worth naming honestly. VP9 and AV1 are, on a technical level, genuinely better codecs than H.264 in one specific way: **they squeeze the same picture into fewer bytes.** A 1080p video encoded in VP9 is roughly 30–40% smaller on disk and on the wire than the same video in H.264. AV1 gets that number closer to 50%.

For a streaming platform delivering a billion hours of video every day, that difference is not a nice-to-have. **It is measured in billions of dollars per year** in reduced bandwidth bills, reduced CDN spend, reduced peering fees, reduced data-centre electricity for their servers. Real money. Every single one of those dollars goes into their pocket. Not yours.

**Because the cost of the trade did not go away — it just moved.** The cost of decoding a more efficient codec is much higher: more math per frame, more CPU cycles, more power drawn. That cost is now paid by **you** — by your CPU, your battery, your electricity meter, your fan's motor bearings, the number of years your laptop keeps working before it retires early. On a new machine you barely notice, because the new machine has its own ASIC for VP9 and AV1 (they got added around 2019 for VP9, around 2022 for AV1). On a laptop from 2012, you notice a lot. You notice all of it.

This is not a conspiracy. Nobody in a boardroom decided to punish old-laptop owners. It is something duller and, in a way, worse: **it is a cost-shift that nobody has to sign off on.** They saved billions. You paid it in electricity, in shortened battery life, in a fan that dies three years early, and eventually in the price of a new laptop you did not actually need. The savings are real, they are one-sided, and the person absorbing the shifted cost was never asked and was never told.

### 🌍 Who this build is actually for

Here is the part that matters — the reason all of the above is worth writing down.

**The people this build exists for did not save six months to buy a laptop so YouTube could save a dollar on bandwidth.**

Somewhere on Earth right now, a family pooled money for months to buy a fifteen-year-old machine. Their kid uses it to attend a Khan Academy lecture. Their mother uses it to video-call a relative who works abroad. Their older brother uses it to fill out a job application on a government portal that only works in a browser. To them, the older, "inefficient" H.264 codec is not a compromise — **it is a lifeline.** It is the difference between the lecture that plays and the one that freezes on frame two. Between the job application that submits and the one that times out.

The corporations pushing the "more efficient" codecs are, in almost all cases, **richer than most countries on Earth.** That is not a rhetorical flourish — it is arithmetic. Look up Alphabet's or Meta's market cap next to the GDP of any country in Africa, most of Central and South America, and much of Asia. You will find they exceed it, often by a wide margin. Go on, look. The tools to check this are one search away.

From their side of the desk, the bandwidth they save by moving to VP9 is a rounding error on a spreadsheet. From your side of the desk — from the bottom of the pyramid — the same decision is a machine that will not play the video, a call that will not connect, a page that will not load. **Their small technical win is your total practical loss.** That is not "progress." That is a handful of trillion-dollar companies designing the modern web exclusively for the newest 20% of hardware, and treating the other 80% of the planet as acceptable collateral damage — mostly by not thinking about them at all.

**We think about them.** This build is not written for someone with a Ryzen 9 and 32 gigabytes of RAM; that person is fine either way, on any browser. It is written for the fifteen-year-old laptop kept alive on love and duct tape, the one that has to work because there is no replacement waiting in the closet. Nothing here is charity — the old chip is genuinely capable of the work; we are just insisting the software let it do the job it was built for. The efficiency their codecs deliver is real; it is just aimed at the wrong problem. Their problem is a bandwidth bill. Your problem is being on the internet at all.

Progress is fine. Progress that quietly evicts most of the world from the internet is not progress — **it is enclosure**, dressed in the language of engineering.

**This is what this patch group refuses to accept.** The hardware is fine. The machine is fine. The problem is a browser that has quietly decided everyone should be running a laptop from the last three years — and a video industry that has moved to codecs designed to require it. Call it what it is: **planned obsolescence dressed up as progress.** Every person on an older laptop who has been told "your computer is too slow for YouTube" was lied to. Their computer is not too slow. Their computer's dedicated video decoder is sitting at a tiny fraction of its capacity while the CPU is dying — because the software decided to route the work to the wrong chip, on purpose, and never told them there was a choice.

That is the fight this build is picking, in one small corner of the internet. The chip works. Let the chip work.

---

A second, smaller overhaul happens to *sound*. Old laptop speakers are tinny — no real bass, and they distort if you push the volume up. The audio pipeline was rewritten to add a small dose of bass enhancement plus a gentle soft-clipper (borrowed from music production) that lets you push louder without the crackly buzz.

## 🎭 The Main Characters

| Name | What It Is | Real-World Comparison |
|---|---|---|
| **H.264** | The one video format your graphics chip has a dedicated decoder for | The one shape of key that fits your front door |
| **VP9 / AV1 / HEVC / VP8** | Newer video formats that require the main processor to decode them frame-by-frame | Different-shaped keys — they don't fit your door, so you'd have to pick the lock every time |
| **VA-API** | The Linux bridge that lets Firefox hand H.264 video to the graphics chip's built-in decoder | The dedicated dishwasher hookup — bypasses the sink entirely |
| **PDMFactory** | The bouncer at the door: it decides which video format gets in and which gets turned away | A bouncer with one rule: 'H.264 only, no arguments' |
| **DecoderTraits** | The bouncer's *first* check — happens before the video even reaches the player | The metal detector at the entrance, before you even reach the bouncer |
| **Frame Pool** | A tray of reusable memory slots the decoder recycles for each video frame | 16 dinner plates that get washed and reused instead of buying disposables |
| **FastTanh** | A gentle mathematical curve used to soften loud audio peaks without hard clipping | A gymnast landing softly on a mat vs. hitting concrete — same fall, no injury |

## 🔢 How It Works — Step by Step

### Step 1: The metal detector — DecoderTraits

Before a web page even tries to load a video, the browser asks 'can I play this?' This layer answers a firm NO for anything wrapped in a WebM or Ogg container, and NO for anything advertising itself as VP8 or VP9. YouTube and similar sites see the NO and quietly pick the H.264 version instead, without the user ever noticing a rejection happened.

### Step 2: The bouncer — PDMFactory

If a video makes it past the first check, PDMFactory does a stricter one. It calls a new function called `IsBlockedSoftwareOnlyVideoCodec` and, if the codec isn't H.264, refuses to hand out a decoder. The comment beside it reads: 'STRICT — decision recorded 2026-07-05'. No fallback, no negotiation. This is what makes the policy actually enforced instead of merely wished-for.

### Step 3: The hardware handoff — FFmpegVideoDecoder

For allowed H.264 video, the code hands the work over to the graphics chip via VA-API. If — for any reason — the hardware refuses (bad driver, wrong file, etc.) the decoder does NOT quietly try again in software. It fails loudly with a clear error. Loud failure is a feature: silent software fallback was the original bug.

### Step 4: The dinner-plate trick — Frame Pool of exactly 16

Decoded video frames need memory buffers. The original code let this pool grow as needed. On a laptop where the graphics chip *shares* the same memory as everything else (that's what "UMA" — unified memory architecture — means), that growth doesn't just eat RAM: it clogs the single road that CPU, desktop, and video decoder all have to share. The fix pins the pool to exactly 16 frames — enough for smooth playback, small enough not to hog the road.

### Step 5: The audio makeover — bass and soft-clipping

The audio pipeline was extended with two constants: a bass-boost gain of 1.8× and an 'X-loud' boost of 0.4×. Crucially, these are FIXED — they do NOT change when you drag the volume slider. (The old code accidentally tied them to a slider that YouTube always sets to 1.0, so the boost was silently doing nothing.) A soft-clipper based on the `FastTanh` function catches loud peaks and smooths them instead of letting them crackle.

There's also a **second, quieter soft-limiter** at the very end of the audio chain (in a component called AudioDestinationNode). Think of it as a second gymnast's mat, in case anything slipped past the first one. Belt and suspenders. And the Web Audio system's own generic compressor — which would otherwise fight our carefully-tuned DSP — is politely told to step aside (it becomes a pass-through) whenever hardware-only mode is active.

### Step 5b: The audio pipe gets a direct line to the speakers — 48 kHz

The Realtek audio chip in this class of laptop (the ALC269) runs natively at 48 kHz. YouTube and many web pages send audio at 44.1 kHz (CD-quality). Normally the browser has to *resample* — convert 44.1 to 48 in software, using more CPU and adding a small amount of "graininess" nobody asked for. The patch tells the browser: when hardware-only mode is on, just talk to the chip at 48 kHz directly, and do not touch what comes in. Less CPU, cleaner sound, one less pointless conversion step.

There is a master switch that controls all of the above: a preference called `media.gorilla.hardware_only_mode`. When it is on (which is the default for this build), all the video-blocking and audio-DSP behaviour above is active. When it is off, the browser reverts to standard Firefox behaviour. This is deliberate — nothing here is welded shut, and a curious user can flip the switch and compare.

### Step 6: WebRTC gets the same treatment

Video-call apps (Google Meet, Jitsi) also negotiate codecs. Two files in the WebRTC layer were changed so this browser advertises 'I only speak H.264' in the call setup handshake. Peers pick H.264 for the call automatically. Otherwise, a well-meaning peer offering VP9 would trigger the same software-decode meltdown mid-meeting.

## 🤔 Quirky Things Worth Knowing

### ⚠️ The 'nice' fallback was the bug

For years, Firefox's answer to 'hardware decode failed' was 'try again in software so the user isn't inconvenienced'. On modern hardware, that's kind. On old hardware, it is the difference between a video that plays and a laptop that overheats. Every layer here has been rewired to prefer a loud failure over a silent slow fallback.

### ⚠️ The audio DSP was silently dead for a long time

The bass and loudness code existed but was multiplied by the volume slider — which YouTube pins to 1.0 and does the volume adjustment itself before sending audio to the browser. So the DSP was mathematically active but effectively inert. Decoupling the DSP gains from the slider is the entire fix.

### ⚠️ Sixteen frames — no more, no less

You'll find `MakeUnique<VideoFramePool<LIBAV_VER>>(16)` in four places. That literal 16 is doing real work: below 16, the video jitters; above 16, RAM competition with the browser UI starts causing swap. The comment says 'exactly 16' for a reason.

### ⚠️ The block list is written in negative

Instead of a small allowlist ('accept H.264'), the code is a growing blocklist ('reject VP8, VP9, AV1, HEVC, WebM, Ogg…'). This is defensive: web standards keep inventing new codecs, and the blocklist is the honest record of every one we've had to add.

## 💻 What Does This Mean For YOU?

### 🔋 Battery, Speed & Memory

Not benchmarked as a single number for this topic, but qualitative: H.264 videos on YouTube play through the dedicated hardware decoder rather than the main processor, so the fan behavior and battery drain during video playback move from 'noticeable' to 'barely there'. The 16-frame pool cap prevents memory-bus contention on the shared-memory (UMA) setup.

### ⚡ Speed

Video playback on H.264 content is smooth end-to-end. The measurable win is negative — the *absence* of the multi-second stutters that used to happen when VP9 got selected. Not measured as a specific ms number.

### 🕵️ Your Privacy

No direct privacy angle for this topic — this is about local performance, not data collection. (See the Telemetry topic for privacy.)

### 🌐 Your Internet

YouTube will use a bit more bandwidth per pixel to send you an H.264 stream than a VP9 one — H.264 is a less efficient codec on the wire (see the Big Picture). This is us reversing part of the cost-shift: we hand a rounding-error's worth of bandwidth back to YouTube's servers, and in exchange we get back a huge amount of local CPU and battery. On our side of the deal the trade is obviously worth it; on YouTube's side the extra bytes are so small compared to their global traffic that they will not even notice. **The cost lives where it belongs again.**

## 🔴 The Kill Switch — Explained

**What it is:** One function — `IsBlockedSoftwareOnlyVideoCodec` — is the single point where 'no' is said. It returns true for VP8, VP9, AV1, HEVC, and every non-H.264 video MIME type. Every layer that creates a decoder calls this function first.

**Without it:** Without it, the moment a page offers VP9 (which YouTube does by default when it thinks your machine can handle it), Firefox creates a software VP9 decoder. That decoder pins one CPU core at 100% per stream, and on this hardware there aren't cores to spare.

**Think of it like:** It's the doorman with the list. Not 'we'll try to be selective' — a physical list, and if you're not on it, you don't get in. Simple, unglamorous, and it's the only kind of security that actually holds.

## 🌐 Open Source & Why It Matters To You

The comment in PDMFactory reads 'STRICT — decision recorded 2026-07-05'. That single line is why this matters as open source: the *reason* for the strictness is recorded in the code, visible to anyone. If a future maintainer wonders 'why is this so aggressive?', they see the date and can find the incident. A closed browser would just say 'trust our decode policy'; here you can read it, argue with it, and change it if your hardware is newer.

But there is a bigger reason, and it goes back to the cost-shift story above.

When the software running on your machine is closed — when only Google, Apple, Microsoft, or Mozilla can change how it works — **you have no escape hatch from decisions they make in their own interest.** If they decide tomorrow that your codec is obsolete, or your chip is unsupported, or your device is no longer in the sales tier they care about, that is the end of the conversation. You do not get a vote. You do not even get a warning that a vote happened.

Open source is the only technical arrangement that puts the escape hatch back. It is why this build could be made at all. It is why the changes to make an old chip work again are one hundred and fifty patches to real, readable source code — not a lobbying campaign begging a corporation to please, sir, could you spare a driver update. Every person who reads even one line of the patches in this folder can verify what was done, why, and to what effect. Nobody has to take our word for it. Nobody has to take *their* word for it either.

For the family with the fifteen-year-old laptop, this is not an abstract principle. **It is the difference between a machine that can be maintained and a machine that can only be replaced.**

## 📖 Glossary (Plain English Dictionary)

**Codec** — The 'language' a video is compressed in. H.264, VP9, AV1 are all different codecs.

**Container** — The file wrapper around video+audio. .mp4, .webm, .ogv. A container can hold different codecs; the browser has to peek inside to know what it will find.

**Hardware decode** — The graphics chip has a purpose-built silicon circuit that decompresses certain codecs directly. It's roughly 100× more power-efficient than doing the same math on the CPU.

**Software fallback** — When hardware decode isn't available, doing the decompression on the CPU instead. Historically Firefox did this quietly; this build deliberately does not.

**VA-API** — The Linux standard for handing video decode work to graphics chips. Requires a working driver — on this hardware, the `i965` driver is the only one that supports the Intel HD 4000.

**MSE (Media Source Extensions)** — The mechanism YouTube uses to feed video to the browser piece by piece. It's the layer that asks 'can you play this?' — which is where the blocklist gets consulted.

**WebRTC** — The technology behind video calling in the browser (Meet, Jitsi). It has its own separate codec negotiation, which is why two extra files needed patching.

**Frame pool** — A pre-allocated set of memory buffers that the decoder recycles. Cheaper than allocating memory for every frame.

**Saturation** — The point at which a piece of hardware is running as fast as it possibly can and cannot go faster. A saturated CPU sits at 100%. A saturated network link is passing every bit it can. The HD 4000's H.264 decoder is essentially never saturated during normal web use — that is the whole point of this build.

**ASIC (Application-Specific Integrated Circuit)** — A piece of silicon designed to do exactly one job and do it with extreme power efficiency, often around one-hundredth the electricity a CPU would need for the same task. The H.264 decoder inside your graphics chip is an ASIC. So is the encryption accelerator in a modern phone. ASICs are the reason your phone can play video for eight hours on a small battery.

**Planned obsolescence** — When a product is designed, or supported by its makers, in a way that makes it stop being usable long before it physically wears out — pushing users to buy replacements. The software version of it: dropping support for older hardware, or moving to formats that older hardware cannot handle at speed. Any individual step is usually defensible on technical grounds; the collective effect is a working machine getting declared "too slow" and thrown into a landfill.

**Cost-shifting** — When a company cuts its own bills by pushing those costs onto its users, often invisibly. Streaming services do exactly this when they move to a more efficient codec: their bandwidth and server bills drop (billions of dollars a year), your CPU works harder to decode the more efficient codec, so your electricity bill and your battery drain go up. On new hardware the transfer is small enough that nobody notices. On older hardware it is what makes the machine feel "too slow." The savings are real and one-sided; the person absorbing the shifted cost is never asked and never told.

**Codec efficiency** — How tightly a codec can compress a video without visibly hurting quality. VP9 is roughly 30–40% more efficient than H.264; AV1 is roughly 50% more efficient. "More efficient" means smaller files and less bandwidth to deliver them — which is great for whoever pays the bandwidth bill, and expensive for whoever has to do the decoding math.

**Digital divide** — The gap between people who can fully participate in the modern internet (recent hardware, fast connections, up-to-date software) and people who cannot (older hardware, slower connections, older software). Every "efficiency improvement" that assumes new hardware widens the divide, one release at a time. Most of the software industry acts as if the divide does not exist; this build acts as if it does.

**Enclosure** — Historically, the process of taking common land (which anyone could use to graze animals or gather firewood) and fencing it off as private property. The modern web version: taking capabilities that used to work on any hardware — like playing a video — and quietly making them require new hardware, so the old hardware effectively no longer has access. The land is still there; you just cannot use it any more.

---
*Human Track. Its Developer Track twin (`01-media.DEVELOPER.md`) covers the same changes in technical detail. Neither is a simplified copy of the other — they are the same truth in two languages.*