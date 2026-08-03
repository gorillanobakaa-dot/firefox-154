# Why Gorilla Unleashed exists

*Written down 2026-08-01, at the author's instruction, so it is never again implicit.*

## Who this is for

There are kids in Lima, in South Africa, in Angola, across Southeast Asia, who save
for a **year** to buy a laptop. What they can afford is a machine like the one this
build is made on: a 2012 laptop that in the UK would go in a bin — that today costs
the price of two coffees on the used market. For its buyer, it is not e-waste. It is
**the computer** — the one that has to do school, work, everything. And it has to do
it on 1–2 GB of RAM, a spinning disk, an integrated GPU, and often internet paid for
by the megabyte.

## The machine this is built on

The reference machine is a pink Sony VAIO SVE14A3AJ, bought for the author's wife,
who never warmed to it, replaced it with a 2011 MacBook Air, and was going to throw
it away. It was adopted instead. In 2012 it was a monster — 16 GB of RAM when small
companies ran servers on less, an i7 when i7 was the absolute ceiling (the tamer i7
chosen deliberately, for heat and longevity — a future-proofing bet that paid off).
The only upgrade in ~15 years: a Kingston DC600M *enterprise* SSD. Today it compiles
Firefox and Linux kernels.

Nursed, not just used: the CPU/GPU die rides on a **Honeywell phase-change thermal
sheet (PTM7950-class)** — enthusiast-grade interface material in place of 2012
factory paste that would have it throttling in the 90s by now.

And the bet is measurable (live sensors, 2026-08-01, mid-session under compile +
AI-ingestion load): package at **47 °C on a 36 % fan** — that sheet is why. Battery at **96.7 % health,
0 charge cycles**, after ~15 years. The SSD at 99 % life — rated 3,504 TBW, which at
the author's hardest developer usage projects to **~530 years** of remaining
endurance. The dedicated Radeon GPU is **disabled in BIOS on purpose**: the machine
runs iGPU-only — the same silicon reality as the audience's machines — and banks the
heat budget as component life.

This is the counterexample to planned obsolescence, running. A 15-year-old laptop is
not junk; over-specced once, cared for, and paired with software that respects it,
its components have decades — some of them centuries — of service left. The
audience's machines are the same story with smaller numbers. What they lack is not
capability. It is software that stops wasting them.

Three years ago the author discovered where machines like it go when we bin them:
South America, Africa, the Middle East, Southeast Asia — bought second-hand,
15 years old, and treasured. But the ones that travel are the *ordinary* ones:
2–4 GB of RAM, HDD. And for the kid who gets one, it is the only connection to the
internet, to education, to YouTube tutorials, to opportunities that otherwise do
not exist.

Modern Firefox does not respect that machine. Each release crams more in: on-device
ML translation engines, AI chatbots, sponsored content pipelines, telemetry
frameworks, experiment delivery channels, recommendation services — each one a
background process, a timer, an allocation, a network call that Mozilla's average
user never notices. On a 16 GB developer laptop, "negligible." On a 2 GB machine,
three tabs already cost ~3 GB. There is no negligible. **Every megabyte of RAM and
every background wakeup is stolen from someone who paid a year of savings for it.**

## What the build therefore is

A lean browsing machine. Modern web compatibility, modern security patches — with
everything that serves Mozilla instead of the user gated, locked, or gone.

The test applied to every feature, every pref, every service:

> **Does a kid on a 2 GB machine with paid-per-MB data need this running?**

If no: it does not run.

And the working tiebreaker, for every doubtful call (one modern tab already eats
~1 GB — the whole machine is a two-tab budget):

> **If it saves RAM, CPU cycles, or network bandwidth — apply it.
> If it costs them — ditch it, patch it, or remove it.**

## The silicon principle (use what is already there)

The second half of the doctrine, and the reason for the entire media patch set:
**never make the CPU do what an ASIC on the die will do for free.** A 2012 machine
has real silicon — a GPU, a hardware H.264 decoder, fixed-function blocks — that
sits idle while modern software burns the CPU instead. This build inverts that:

- **H.264-only codec policy** (compiled into DecoderTraits): the era's hardware
  decodes H.264; VP9/AV1 would fall back to software decode and drown a 2-core CPU.
  So the build refuses them, and sites negotiate H.264 the hardware plays for free.
- **VA-API hardware decode** wired up and forced on (RDD process, i965), with
  zero-copy DMABuf paths so decoded frames never bounce through the CPU.
- **WebRender's Wayland native compositor** forced on, so video goes to a hardware
  overlay plane instead of a shader pipeline — measured on the reference machine:
  memory bandwidth from ~2500 MiB/s to ~500 MiB/s.
- WebRTC capped (`max_fs`/`max_fr`) to resolutions the silicon handles.

Every efficiency pref in the Brain database follows this rule: offload to the GPU,
the decode ASIC, any fixed-function hardware present — and spend the saved CPU
cycles on what the user is actually doing.

### The deck is stacked — cost-shifting, and why the codec policy is a fight

The pressure against these machines is not neglect. It is economics. Streaming
platforms push VP9/AV1 because newer codecs cut **their** bandwidth bill — whether
the viewer's silicon can hardware-decode them is not their problem. A 2012 laptop's
fixed-function ASIC can decode multiple 1080p60 H.264 streams while the CPU idles;
serve that same laptop VP9 and it goes to 100 % CPU software decode — dropped
frames, fans flat-out, heat stress through factory thermal paste that was never
replaced and never will be, in a family that cannot afford to know why the laptop
is dying. **The bandwidth saving lands on the platform's ledger. The cost lands on
the child's CPU.**

Browser blocklists compound it: old GPUs and drivers are swept onto deny-lists
tuned for the average case, so even the hardware acceleration these machines *do*
have is switched off by default. Software decode again, from the other direction.

This build refuses both halves of that bargain. Compiled `CANPLAY_NO` for VP9/AV1
means sites must negotiate the H.264 the ASIC plays for free — the client's
silicon, not a platform's bandwidth budget, decides how video gets decoded. And
`UserForceEnable()` (which outranks the gfxInfo blocklist — golden rule 2) turns
the machine's own hardware decode back on over the deny-list's objection. These
are not preferences. They are the mission's teeth — implemented as patch topics
`01.MEDIA` (hardware-only codec policy) and `02.GPU` (the four-layer un-blocklist,
plus the dead-coding of the sticky sanity-test booby trap, where one transient
failed startup probe used to weld a profile into software rendering *permanently*
— a disability inflicted precisely on the owners least able to diagnose it).
Note the discipline in `02.GPU`: general acceleration is force-approved, but
VP9/HEVC hardware decode stays honestly BLOCKED — the silicon principle cuts both
ways: use everything that exists, claim nothing that does not.

## How it is enforced (one intent, every layer that can hold it)

1. **mozconfig** — strip at build time what can be stripped.
2. **Compiled defaults** — patches to `firefox.js` / `StaticPrefList.yaml` bake the
   safe value into the binary itself (vanilla ships `browser.translations.enable=true`;
   this build compiles `false` — the on-device ML engine never wakes).
3. **Locks** — `pref(..., locked)` + `policies.json` weld the lid: no update, no
   experiment push, no misclick can flip a protection back on.

Telemetry honesty: the machinery is **gated, not dead** ("the fly in the jar") —
no egress, but the honest accounting of what still idles is maintained in
`patches/new.patches/14.EGRESS.LOCKDOWN/`. Every source edit carries a
`GORILLA` provenance comment: anyone — developer or layperson — can audit what
changed and why. See `00.Open.Source.Philosophy (2).md`.

## The documentation is a front, not an appendix

The same asymmetry that ships the costs also ships the ignorance. A cost-shift you
cannot see cannot be fought — and the seeing is hoarded behind jargon.

That is why every topic in this project is documented twice: a DEVELOPER track, and
a **LAYMAN track** that explains in plain language, with real-world comparisons,
what the machinery is, whose interests its defaults serve, and what was changed
here and why. The layman documentation consumes an inordinate amount of effort and
tokens — deliberately. It is not marketing and it is not an appendix. It is the
transfer of the know-how itself — the same know-how that keeps the reference
machine alive — to people who were priced out of it. The GORILLA provenance
comments in the source serve the same end: a developer *and* a layperson can audit
every change, what it costs, and who it serves.

Teaching the user what their machine can really do, and what software quietly does
to it, is the project's third front. The blocklist patch frees the silicon; the
locked prefs keep it free; the documentation makes sure the *next* person doesn't
need a specialist to understand why. You cannot fight power you cannot see.
The documentation makes it visible. That is the fight.

## Why the work is slow and careful

One person maintains this against a moving upstream, with AI agents as hired hands —
and with the scars to show why nothing is trusted unverified: fabricated prefs from
an earlier AI have been found *inside the config*, and every claimed fact is now
checked against Firefox's own source (searchfox), its standards bodies, and the
built binary before it ships. The prefs audit of 2026-08-01 (1613 prefs → 1509,
every survivor verified on five axes) is the standard.

A machine that costs two lattes here is a year of someone's life there.
That asymmetry is the entire project.
