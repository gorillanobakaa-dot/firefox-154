# 🧍 The Control Panel and Factory Blueprint — Preferences and Build Recipe — Plain English Guide

> *Topic `05-prefs` of the Gorilla Unleashed Firefox 154 build · Written for everyone · 2026-07-16*

---

## 🌍 The Big Picture

This folder is two very different things in one place. First: **the factory blueprint** (`mozconfig`) — the recipe the compiler follows when it builds Firefox from source. This one is tailored for our specific CPU (Ivy Bridge i7-3632QM); the browser is compiled *for this exact chip* rather than for any generic Intel processor, which is the difference between a suit off the rack and a suit made to measure. It also leaves out entire subsystems we do not want (crash reporter, updater, telemetry agents), so they cannot even run because they were never included in the first place.

Second: **the default switch positions** — thousands of settings that the browser starts with, defined in `StaticPrefList.yaml`, `firefox.js`, `all.js`, and one locale properties file. Most preferences in Firefox have a default, and Mozilla picks that default. This folder replaces many of those defaults with values chosen for this build's audience — old hardware, weak connections, no interest in Mozilla's telemetry or in AI features that were bolted on for a market that is not us. The most important default defined here is a single new preference the whole build hinges on: `media.gorilla.hardware_only_mode`, which the Media topic consumes at every codec gate.

The critical thing to understand: **these are only defaults**. Later layers can override them — `user.js` in Topic 10 sets runtime prefs, and `policies.json` in Topic 12 hard-locks a small set. Think of this folder as the factory-fresh setting, before the user takes the box home and changes anything.

## 🎭 The Main Characters

| Name | What It Is | Real-World Comparison |
|---|---|---|
| **mozconfig** | The compiler's instruction sheet — how to build the browser from source | The recipe card for baking one specific cake, with substitutions written in for local ingredients |
| **StaticPrefList.yaml** | The master list of every preference the browser knows about, with its compile-time default | The switchboard at the back of the building — every switch labelled, with a default position wired in |
| **firefox.js / all.js** | Application-level default prefs that override StaticPrefList for this build | The pre-set channels on a rented TV — you can still change them, but the rental company chose the starting set |
| **media.gorilla.hardware_only_mode** | The master switch defined here, consumed by the Media topic (Topic 01) at every codec decision | The big red 'hardware-only' lever on the control panel — flip it off, get standard Firefox behaviour back |

## 🔢 How It Works — Step by Step

### Step 1: mozconfig — build for THIS CPU, drop what we do not want

`--enable-optimize=-march=native -O3` tells Clang: build this for the exact CPU we compile on, and optimise aggressively. `--disable-crashreporter --disable-updater --disable-parental-controls` and similar flags remove whole subsystems from the binary so they cannot even run. Not disabled at runtime — physically absent. Some things you cannot leak because they were never built.

### Step 2: StaticPrefList.yaml — the master pref registry

Every preference Firefox has a compile-time default for. The changes here (marked with `@gorilla-unleashed-*` headers) redefine those defaults for our build: telemetry off, AI features off, sponsored content off, VP9/AV1 hardware decode off (matches Topic 01), and — critically — the new `media.gorilla.hardware_only_mode` preference is *defined* here (default `true`). Topic 01 reads it.

### Step 3: firefox.js — 'app-branch' defaults with usability opinions

This is where opinionated app-level defaults live. Password memory is enabled (usability over privacy theatre — the browser's own password manager is better than users writing passwords on sticky notes). Session-restore privacy level is set for full restoration. Tab-sleep timers tuned for a small memory budget. Sidebar experiments disabled ('no nightly-only stuff on a stable build'). Comment in the patch: `GORILLA: no nightly-only sidebar experiments — always off.`

### Step 4: all.js — the second app-branch, with the aggressive purge

The purge zone. AI features (chatbots, PDF alt-text via remote AI, translation nag), TopSites (sponsored tile ads), Normandy (remote experiments), Nimbus (feature-flag rollouts), and Pocket integration all forcibly set to `false` here. Comments include `AGGRESSIVE PURGE (AI & TOPSITES)` and `TELEMETRY STARVATION`. Note the aesthetic: telemetry isn't just turned off, it is *starved* — every food source cut simultaneously.

### Step 5: The locale properties file — accept-language + trending lock

One tiny file (`intl/locale/language.properties`) forces accept-language to a fixed value and disables multilingual/trending features. This is a fingerprinting defence: pages cannot see your language preferences drift over time, and there is no server-side 'we noticed you speak Bengali now, here are recommendations' behaviour.

## 🤔 Quirky Things Worth Knowing

### ⚠️ The build recipe is not portable — and the log says so

`-march=native -O3` means: build using every CPU instruction the machine we compile on knows about. The resulting binary runs faster on that machine, but may crash on any machine with a different CPU generation. The log opens with a warning: 'This is NOT portable. Never ship these binaries to other hardware.' If you want a portable build, you change one flag — but you also give up the speed.

### ⚠️ Password manager ON, but telemetry OFF

Most privacy-focused browser builds turn off *everything* including features that would actually help the user. This one keeps the password manager on: a local password manager is a legitimate usability tool, and the alternative (users typing passwords into every site or reusing them across sites) is measurably worse for privacy. The build distinguishes between 'convenience for you' (kept) and 'convenience for Mozilla' (cut).

### ⚠️ The master switch is defined here but READ by another topic

`media.gorilla.hardware_only_mode` is a preference. Its definition (the fact that it exists, its type, its default value `true`) lives in `StaticPrefList.yaml` in this folder. But nothing in this folder actually consumes it — every `if (StaticPrefs::media_gorilla_hardware_only_mode())` check lives in Topic 01. That's how prefs work: definition here, use elsewhere. Good separation of concerns.

## 💻 What Does This Mean For YOU?

### 🔋 Battery, Speed & Memory

The `-march=native -O3` build is measurably faster than a generic build on this exact CPU — cache locality is better, some AVX instructions are used, LTO removes dead code across module boundaries. Not benchmarked as a raw number in this folder. Tab-sleep timers reclaim RAM for backgrounded tabs.

### ⚡ Speed

Compiled subsystems that were removed cannot run — startup is faster because there is less code to load.

### 🕵️ Your Privacy

This is where the systematic privacy defaults live: telemetry, Normandy, Nimbus, AI-features, TopSites-sponsored, Pocket all default-off. Topic 12 hard-locks the ones Mozilla could otherwise re-enable via remote config.

### 🌐 Your Internet

Aggressive purge means fewer background connections at startup and steady-state. Not benchmarked; the mechanism is clear.

## 🔴 The Kill Switch — Explained

**What it is:** The whole folder IS the kill switch panel. Every preference that gates a feature elsewhere is set here. The single most important one is `media.gorilla.hardware_only_mode` (default `true`) — flip it to `false` and every gate in Topic 01 opens.

**Without it:** Without this folder, the browser has upstream defaults everywhere: telemetry on, AI features on, TopSites-sponsored on, no `media.gorilla.hardware_only_mode` pref at all (Topic 01's gates all fail-closed and become dead code). The build would be indistinguishable from stock Firefox at the preference level, even after all the code patches.

**Think of it like:** The whole factory-fresh setting page in the user manual. Individually the switches are small; collectively they define what the machine does when you first turn it on.

## 🌐 Open Source & Why It Matters To You

You can read every default. Every `pref("whatever", false)` line has a reason behind it, and the reasons are in the comments (`AGGRESSIVE PURGE (AI & TOPSITES)`, `TELEMETRY STARVATION`, and so on — colourful, but at least honest). A closed browser has thousands of defaults you cannot see; here they are one grep away.

## 📖 Glossary (Plain English Dictionary)

**mozconfig** — The build recipe file. Tells the compiler what to build, with which optimisations, and what to leave out.

**StaticPrefList.yaml** — The compile-time preference registry. Every pref Firefox knows about, defined here with a default value that becomes part of the binary.

**firefox.js / all.js** — Application-branch preference files loaded at startup. Override StaticPrefList defaults for this build.

**-march=native** — Compiler flag: 'build for the exact CPU I am running on right now.' Faster on this CPU; may crash on others.

**LTO (Link-Time Optimization)** — The compiler treats the whole binary as one unit at link time, finding optimisations across file boundaries. Slower to build, faster at runtime.

**Preference override layers** — Ordered from lowest to highest priority: StaticPrefList (built in) → firefox.js/all.js (app defaults) → prefs.js (user changes in about:config) → user.js (Topic 10) → policies.json (Topic 12, hard-locked).

---
*Human Track. Its Developer Track twin (`05-prefs.DEVELOPER.md`) covers the same changes in technical detail. Neither is a simplified copy of the other — they are the same truth in two languages.*