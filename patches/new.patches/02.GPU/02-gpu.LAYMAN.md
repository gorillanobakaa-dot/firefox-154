# 🧍 The GPU Un-Blocklist — Making Firefox Actually Use the Graphics Chip You Paid For — Plain English Guide

> *Topic `02-gpu` of the Gorilla Unleashed Firefox 154 build · Written for everyone · 2026-07-16*

---

## 🌍 The Big Picture

Your graphics chip is a small factory built into your laptop. It has purpose-built machinery for drawing web pages fast (a system called WebRender), for decoding video without touching the CPU (the H.264 ASIC the Media topic talks about), and for pushing pixels to the screen efficiently on Linux (via Wayland). All of that machinery costs power, silicon, and design effort — and it is sitting *right there* in your 2012 laptop.

And Firefox refuses to use it. Not because it doesn't work — it works fine. Firefox refuses because a text file inside Firefox called the *blocklist* has your GPU's model number written on it, followed by the word 'blocked'. When the browser starts up, it reads this list, sees your chip's serial number, and says: no, we will not turn on hardware acceleration for that one. We will draw every pixel in software instead, on your CPU, at ten times the power cost.

This patch group takes the blocklist and, at four different points where it is consulted, makes it answer 'this GPU is fine'. Then it also disables a booby trap Firefox sets up: a 'sanity check' where **one failed video test — ever, even due to a random glitch — permanently disables hardware acceleration for the rest of the machine's life** unless someone knows to reset the pref. That booby trap is now dead code. One bad boot no longer means a lifetime of software rendering.

### 💰 Why the blocklist exists in the first place

Nobody at Mozilla is being malicious. Blocklists exist for a real reason: some very old graphics drivers really did crash the browser, and Mozilla did not want to spend engineering time keeping those old paths tested. So they marked whole generations of GPUs 'blocked' and moved on. **Their savings are real** — measured in engineer-hours per year that they do not have to spend testing Sandy Bridge, Ivy Bridge, or the AMD equivalents. Every hour they do not spend testing your GPU is an hour they can spend on the newest Ryzen.

**Your cost is also real.** It is the CPU your laptop is now doing GPU work on. It is the fan speeding up. It is the battery draining twice as fast as it should. It is the browser feeling sluggish on a chip that could run rings around web content if it were only permitted to. Mozilla saved a support-cost line item; you paid for it in electricity, battery life, and eventually in the price of a laptop you did not actually need to buy. Same shape as the Topic 01 story about YouTube and VP9 — different actor, same cost-shift.

### 🌍 Who this is for

Same audience as Topic 01: **the family that saved for months to buy a 2012 laptop.** For that user, the difference between 'GPU accelerated' and 'GPU blocklisted' is the difference between a browser that can be used to attend a class and one that cannot. It is not a benchmark, it is a lifeline. Every one of the five layers of override in this patch group exists so a person on a 2012 chip in 2026 can browse the same web everyone else does — on the hardware they already own, that already works, that a text file inside Firefox has been quietly telling them is inadequate.

**The chip works. Let the chip work.**

## 🎭 The Main Characters

| Name | What It Is | Real-World Comparison |
|---|---|---|
| **The Blocklist** | A hard-coded list inside Firefox of GPU model numbers Firefox will refuse to hardware-accelerate | The 'no entry' list at the door of a nightclub — except the club has a lifetime ban on a whole generation of chips based on nothing but their model number |
| **WebRender** | Firefox's modern graphics engine that uses the GPU to draw web pages | A conveyor belt with a robot doing the assembly — versus the old way, which is one person doing the whole job by hand |
| **gfxInfo / GfxInfoBase** | The internal 'is this GPU allowed to work?' oracle. Every graphics decision asks this oracle first. | The customs officer who checks your papers at every stage — patched here so it stamps APPROVED for Intel, AMD, and NVIDIA |
| **The Sticky Sanity Test** | A booby trap: if hardware video decode fails a self-test even once, a flag gets set that permanently disables hardware acceleration forever | A fuse box where the fuse doesn't just blow — it welds itself shut, so no one can ever replace it |
| **UserForceEnable** | The one call in Firefox that overrides the blocklist. Not 'suggest enabled' — actually, forcefully enabled | The manager overriding the bouncer — not by asking politely, but by physically moving the rope aside |
| **Ivy Bridge / Sandy Bridge / HD 4000** | The generation of Intel graphics chips (2011–2012) this build is defending. The reference machine's chip is PCI ID 0x0166 — HD 4000 mobile | The perfectly good used car that keeps being told it isn't allowed on the highway anymore |

## 🔢 How It Works — Step by Step

### Step 1: Layer 1 — the GTK graphics probe

Firefox has a Linux-specific probe (in `widget/gtk/GfxInfo.cpp`) that runs a bunch of tests when the browser starts. Historically, ANY unknown result — including 'we didn't get to that test yet' — could return the same answer as 'FAILED', which blocked WebRender. Even worse: there's a documented Mozilla bug (1710400) that told this probe to block Intel graphics on the older X11 driver even when it worked fine. All of that is now short-circuited so a healthy chip is called healthy.

### Step 2: Layer 2 — the vendor gate

In `widget/GfxInfoBase.cpp` (the central blocklist engine), a short-circuit was added: if the GPU vendor is Intel (0x8086), AMD (0x1002), or NVIDIA (0x10de), the blocklist is bypassed and a green light is returned for general graphics features. This is a bulk fix — it covers all three major vendors in one place, which is the vast majority of hardware on Earth. Crucially, VP9 and HEVC hardware decode still return BLOCKED — because we DON'T have those decoders in silicon on this chip, and the Media topic depends on them staying blocked. It's a scalpel, not a sledgehammer.

### Step 3: Layer 3 — the device-family registry

There is a giant hard-coded list of PCI device IDs organized by chip family (`widget/GfxDriverInfo.cpp`). Ivy Bridge and Sandy Bridge were listed there under 'block from WebRender'. The APPEND_DEVICE lines for our chip family — 0x0152, 0x0162, **0x0166** (this machine), 0x016A, plus the whole Sandy Bridge set — were commented out. The list no longer knows we exist. The comments left in place explain why so nobody 'fixes' them by uncommenting.

### Step 4: Layer 4 — the booby trap

In `gfx/thebes/gfxPlatform.cpp` there was a mechanism where a single failed hardware-decode sanity test would set a persistent preference that permanently disabled hardware acceleration on that profile — forever. Not until reboot: forever. This has been dead-coded. Comments in the patch explain: 'One bad boot must not permanently disable HW accel.' Now a transient failure — a bad frame during startup, a driver hiccup, whatever — no longer welds the fuse shut for eternity.

### Step 5: Layer 5 — the Wayland compositor force-enable

The last piece is in `gfx/config/gfxConfigManager.cpp`: the native Wayland compositor is *force-enabled* (using a call named `UserForceEnable`, not the weaker `UserEnable` — this distinction matters, see the Kill Switch section). This lets video frames go straight from the video decoder to the screen without a detour through the CPU. Without it, decoded frames would take a scenic route: GPU decode → CPU copy → GPU upload → display, quintupling the memory bandwidth used. On a chip that shares its memory bus with everything else in the machine, that's the difference between smooth and stuttery.

## 🤔 Quirky Things Worth Knowing

### ⚠️ The blocklist is Firefox's own opinion about your hardware

None of this is a technical limitation. The HD 4000 works. WebRender works on it. VA-API decode works. Mozilla's own developers just decided, at some point in 2015 or so, that supporting this chip was more trouble than they wanted, so they added its model number to a text file. This patch group calls their bluff.

### ⚠️ The blocklist is DIFFERENT from the codec block from Topic 01

This one is confusing but important: we're UN-blocking the GPU here (so it can accelerate everything), while over in Topic 01 we're BLOCKING codecs (so nothing but H.264 gets decoded). These aren't contradictory — they're two halves of the same argument: 'use the chip for what it can do, and refuse the work it can't.' The vendor short-circuit in Layer 2 explicitly still returns BLOCKED for VP9/HEVC hardware decode, because those genuinely aren't in the silicon.

### ⚠️ The sticky sanity test is the actual villain

The blocklist can be worked around. The sticky sanity-test flag cannot — it's a self-inflicted permanent wound. If a user's Firefox failed a hardware sanity check *once*, five years ago, on a driver bug that has since been fixed, that user's profile has been running Firefox in software mode ever since without knowing. Dead-coding this is the change most likely to help users who haven't even heard of this project.

### ⚠️ One override call, one word, huge consequences

There are two calls in Firefox that touch feature state: `UserEnable()` and `UserForceEnable()`. They look nearly identical. `UserEnable()` says 'the user would like this on, but the blocklist can still say no.' `UserForceEnable()` says 'this is on, blocklist can go fly a kite.' The whole native-compositor force-enable stands or falls on using the second one, not the first. Many well-meaning attempts to fix this class of problem have failed for exactly this reason.

## 💻 What Does This Mean For YOU?

### 🔋 Battery, Speed & Memory

The GPU doing GPU work instead of the CPU doing GPU work is enormous. Web page rendering, video, animations — all of it moves from the general-purpose CPU (which was cooking) to the purpose-built graphics chip (which was idle). Fan behavior and battery drain during normal browsing move from 'noticeable' to 'quiet'. Not benchmarked as a single before/after number for this topic; the whole-project telemetry number (12.8% parent CPU) belongs to Topic 13 and is separate.

### ⚡ Speed

Web page scrolling and animation on GPU-heavy sites (maps, dashboards, video-heavy pages) becomes smooth where it used to stutter. Video is no longer routed through the CPU compositor (a huge bandwidth waste). The measurable win is negative: the *absence* of the software-rendered stutters that used to happen constantly.

### 🕵️ Your Privacy

No direct privacy angle here — this is about local performance, not data collection. (See Topic 13 for privacy.)

### 🌐 Your Internet

Zero change to how the browser talks to the internet. Everything here is between Firefox and your graphics chip.

## 🔴 The Kill Switch — Explained

**What it is:** The four-layer override + the sticky-sanity-test dead-code + the `UserForceEnable` of the native Wayland compositor. Not one switch — five, chained. Because the failure this is defending against (Firefox refusing to use your GPU) can happen at any of five layers, all five have to be neutralised for the fix to actually stick.

**Without it:** Without any one of these five: Firefox falls back to software rendering. Your CPU does what your GPU should be doing. The fan spins up. The battery drains. The user, again, concludes 'this laptop is too old for the modern web' — even though the laptop's graphics chip has been idle the whole time.

**Think of it like:** It's like fixing a jammed door with five separate locks: a broken deadbolt, a rusted chain, a wedge kicked underneath, a warning sticker, and a booby trap that fires the alarm every time you try to open it. Fixing four of them still doesn't get you through the door. All five, or nothing.

## 🌐 Open Source & Why It Matters To You

The Mozilla project log for this exact patch group contains the following sentence, written by our developer months before this project's mission statement even existed: *'Firefox blocklists Sandy/Ivy Bridge GPUs, disabling WebRender and hardware video decode and silently pushing all that work onto the 2012 CPU — de-facto planned obsolescence of working silicon.'* That is the person doing the fix, describing the code being fixed, using the exact words this project has been using in its layman docs. It is not paranoia when it is quoted from the log of the very thing being repaired.

Open source is what makes this repairable at all. The blocklist is a text file inside Firefox. A closed browser could carry the exact same list, and no one outside its company would ever know. There is no user interface that shows it to you, no about:config that reveals it, no support forum where it is discussed. You would simply experience a slow browser and be told your machine is old. **Being able to open the source, find the text file, and comment out the lines that name your chip** — that is not a technical curiosity, it is the last remaining escape hatch. It is the difference between a machine that can be maintained and a machine that can only be replaced.

## 📖 Glossary (Plain English Dictionary)

**Blocklist** — A list, hard-coded inside Firefox's source, of GPU model numbers Firefox refuses to hardware-accelerate. Some entries are ancient (from chips of the mid-2000s). Some are more recent and less defensible.

**WebRender** — Firefox's modern graphics engine, released around 2018. It uses the GPU to draw web pages instead of the CPU. Roughly 10× more power-efficient for typical browsing on hardware that supports it — which the HD 4000 does.

**VA-API** — The Linux standard interface for handing video decode work to the graphics chip. Same one used by the Media topic.

**PCI ID** — The unique 4-hex-digit code that identifies a specific chip. Our HD 4000 is 0x0166 (mobile) or 0x0162 (desktop). Firefox's blocklist uses these codes to identify what to block.

**gfxInfo** — Firefox's internal 'GPU information oracle'. Every graphics decision asks it: 'is feature X allowed on the current GPU?' The vendor short-circuit patch is applied here.

**Sanity test** — A short self-test Firefox runs at startup to check that hardware acceleration actually works. The bug fixed here: a single failure permanently disabled hardware acceleration on that user profile, forever.

**Native compositor** — The system that composes (assembles) the final image sent to your screen. On Wayland, the 'native' compositor lets video frames skip a CPU roundtrip. Without it, decoded frames get copied to the CPU and back, wasting 5× the memory bandwidth.

**UserForceEnable vs UserEnable** — Two Firefox API calls that look nearly identical. `UserForceEnable` overrides the blocklist; `UserEnable` does not. Getting this wrong is the single most common reason well-meaning graphics fixes fail silently.

**Ivy Bridge / Sandy Bridge** — Intel processor generations from 2011 (Sandy Bridge) and 2012 (Ivy Bridge). The reference machine is Ivy Bridge. Both generations have graphics chips that fully support WebRender and H.264 hardware decode — and both are on Firefox's blocklist for no defensible technical reason.

**Saturation** — The point at which hardware is running as fast as it possibly can. A saturated CPU is at 100%. The HD 4000's WebRender pipeline is essentially never saturated by normal web browsing; it has huge unused capacity.

**ASIC** — Application-Specific Integrated Circuit — a chunk of silicon designed to do one job with extreme power efficiency. Your GPU contains several: an H.264 video decoder (see Topic 01), and (in modern Wayland pipelines) an overlay compositor. Software fallback replaces these with the CPU doing the same work at ~100× the electricity cost.

**Planned obsolescence** — See Topic 01's glossary. The unusual thing about this GPU topic is that the log for the patch itself uses the phrase — a Mozilla developer's-eye view that the blocklist mechanism has become one.

---
*Human Track. Its Developer Track twin (`02-gpu.DEVELOPER.md`) covers the same changes in technical detail. Neither is a simplified copy of the other — they are the same truth in two languages.*