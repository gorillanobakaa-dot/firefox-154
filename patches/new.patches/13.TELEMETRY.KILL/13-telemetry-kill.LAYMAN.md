# 🧍 The Browser That Stopped Spying On Itself (And Got Faster) — Plain English Guide

> *Topic `13-telemetry-kill` of the Gorilla Unleashed Firefox 154 build · Written for everyone · 2026-07-17*

---

## 🌍 The Big Picture

Every modern web browser quietly keeps a diary about you. Not the websites you visit necessarily — but *how you use the browser*: how much memory it is using, how long things take, which features you touch. Firefox calls this **telemetry**, and it collects it constantly, in the background, whether you asked for it or not.

Mozilla are not cartoon villains — they use this to spot bugs and improve the product. But here is the catch nobody mentions: **collecting all that data is not free.** Your computer has to do real work to measure itself, package the numbers, and get them ready to send. On a brand-new laptop you would never notice. On a 12-year-old machine, that hidden work is stealing power you cannot spare.

We measured it. On this hardware, during video playback, the browser was burning **about 1 out of every 8 units of effort** its main brain had — not on showing you web pages, but on watching and reporting on itself. This build turns that off. All of it. And here is the beautiful part: the result is a browser that both respects your privacy AND runs noticeably faster, because those turn out to be the same fix. On old hardware, surveillance has a body count measured in wasted seconds and dead battery.

## 🎭 The Main Characters

| Name | What It Is | Real-World Comparison |
|---|---|---|
| **Memory Telemetry** | A part of Firefox that, every 60 seconds, walks through all the browser's memory and writes down how much it is using | A clipboard inspector who stops the whole factory every minute to count every item in the warehouse — the counting itself slows the factory down |
| **Glean / FOG** | Mozilla's newer, fancier data-collection system that records 'events' — timings, counts, little facts | A second set of auditors, each carrying a stopwatch, timing everything anyone does |
| **The Dispatcher** | A dedicated worker whose only job is to process all those recorded events | The clerk who files every stopwatch reading into a giant cabinet |
| **/proc/self/smaps** | A special system file that lists every scrap of memory — reading it forces the operating system to do heavy bookkeeping | Asking the government for a certified list of every brick in your house — accurate, but it ties up an official for ages |
| **The Kill Switch** | A single line we added that says 'telemetry is OFF' — permanently, at build time | Flipping the master breaker so the whole surveillance wing of the building never gets power |

## 🔢 How It Works — Step by Step

### Step 1: We caught it in the act

Using a profiler (a tool that shows exactly where a computer spends its effort), we watched the browser play a 1080p video and asked: what is the main process actually doing? The answer was uncomfortable — a big slice was not video at all.

### Step 2: We found the biggest thief — the memory counter

The Memory Telemetry inspector was reading that 'every brick in the house' file every 60 seconds. That single habit was eating 8.9% of the main brain's effort. We switched it off at the source — it simply no longer does the count.

### Step 3: We found the second thief — the stopwatch auditors

Glean's dedicated filing clerk was burning another 3.5%. We stopped the system from ever hiring that clerk in the first place — the initialisation that would start it is short-circuited.

### Step 4: We found the stragglers — and installed the master breaker

Even with the clerk gone, the little stopwatch readings were still being *taken* (just never filed). So we added one permanent switch — GORILLA_TELEMETRY_OFF — that tells the browser, at the moment it is built, 'do not even take the readings.' The build tool then physically removes that code, so it cannot run at all.

### Step 5: We proved it

We measured again. The memory counter: gone. The filing clerk: gone. The surveillance wing went from ~13% of the browser's effort down to under half a percent — the leftover being tiny bits welded so deep into Firefox's frame that removing them is not worth the risk.

## 🤔 Quirky Things Worth Knowing

### ⚠️ Privacy and speed were the same problem

This is the beautiful part. We did not trade privacy for speed or speed for privacy. The spying *was* the slowness. Kill one, you kill both.

### ⚠️ Turning it 'off' in the settings was not enough

Firefox has a setting to disable telemetry. It does not actually stop the memory counting — that runs on its own timer regardless. The only real 'off' was in the source code itself. The setting is a light switch that is not connected to the light.

### ⚠️ We chose the scalpel, not the sledgehammer

A previous attempt tried to rip the whole system out. It caused crashes and needed 157 emergency patches to even compile. This time we left the machinery in place but cut its power — same result, no wreckage.

### ⚠️ Editing a sealed part needs a new sticker

Part of the fix is inside a 'vendored' Rust component (glean-core) — a sealed factory part. The build refuses to accept an edited sealed part unless its checksum sticker is updated too. Forget the sticker and the build rejects the whole thing. This tripped an earlier attempt.

## 💻 What Does This Mean For YOU?

### 🔋 Battery, Speed & Memory

On the target hardware, roughly 1/8th of the main process's workload during video playback handed back to you. Cooler running, a quieter fan, longer battery, and more responsiveness left over for the actual web page. Measured: ~13.2% -> ~0.39% of the parent process during 1080p playback.

### ⚡ Speed

Zero change to how fast pages load — except the machine has more spare effort, so everything around the page (scrolling, switching tabs) feels lighter.

### 🕵️ Your Privacy

Nothing about how you use this browser is measured, packaged, or prepared for sending. The data was going nowhere anyway (upload was already blocked), but now the browser does not even write it down. There is no diary.

### 🌐 Your Internet

No change to network behaviour — the win here is local CPU and battery.

## 🔴 The Kill Switch — Explained

**What it is:** A single line — GORILLA_TELEMETRY_OFF = true — added deep in the browser's guts. Because it is set permanently at build time (not a setting you toggle), the build tool is smart enough to see 'this can never be false' and physically deletes all the surveillance code that sits behind it.

**Without it:** Every time the browser did anything — drew a frame, opened a connection — it would quietly take a measurement, do the math, and file it. Thousands of times a minute. Invisible, constant, and on your dime.

**Think of it like:** The master power breaker for an entire wing of a building you never use. You do not walk around unplugging each lamp — you cut power to the whole wing at the fuse box, once, and it stays dark.

## 🌐 Open Source & Why It Matters To You

Remember Edward Snowden? He showed the world that data collection is rarely 'just for improving the product' — once the pipes exist, they get used. The only real defence is being able to *look inside the software* and see for yourself whether it is watching you. This is exactly why this change is public and readable. You do not have to *trust* that the telemetry is off — you can read the one line that turns it off, and read the proof that it worked. A closed browser asks for your faith. An open one hands you the flashlight.

## 📖 Glossary (Plain English Dictionary)

**Telemetry** — Data a program collects about how it is being used, usually sent back to its makers. Think of a car quietly logging your every trip and mailing it to the factory.

**Glean / FOG** — Mozilla's modern telemetry system ('Firefox On Glean'). The newer, more organized set of auditors with stopwatches.

**Profiler** — A tool that shows exactly where a program spends its effort, like a fitness tracker for software. It is how we caught the wasted work.

**Kill Switch** — A single deliberate off-switch that disables a whole feature. Ours is permanent and built-in, not a setting.

**/proc/self/smaps** — A Linux system file listing every piece of memory a program uses. Reading it is accurate but expensive — like a full certified inventory instead of a quick glance.

**Parent Process** — The browser's main 'brain' that coordinates everything. Freeing up its effort makes the whole browser feel faster.

**Dead-code elimination (DCE)** — When the build tool sees code that can never run (like the branch behind a permanently-true switch) and physically removes it from the finished program.

**Vendored crate** — A third-party code component (here, Rust's glean-core) copied into the source tree. Editing one requires updating its checksum sticker or the build rejects it.

---
*Human Track. Its Developer Track twin (`13-telemetry-kill.DEVELOPER.md`) covers the same changes in technical detail. Neither is a simplified copy of the other — they are the same truth in two languages.*