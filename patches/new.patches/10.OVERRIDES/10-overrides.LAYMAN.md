# 🧍 The Runtime Override Layer — the User.js That Has the Final Say — Plain English Guide

> *Topic `10-overrides` of the Gorilla Unleashed Firefox 154 build · Written for everyone · 2026-07-16*

---

## 🌍 The Big Picture

This folder contains a single, hand-tuned `user.js` file with roughly 1,100 lines of preference overrides. Every time Firefox starts, it reads this file *last* — after the compile-time defaults from Topic 05, after any settings in the profile — and applies its values on top. It is the final layer of preference control before the browser starts talking to the network.

**Why have this layer at all?** Firefox's own factory defaults (which Mozilla picks) are optimised for Mozilla's business: telemetry on, AI features on, experiments on, background services on. The compile-time overrides in Topic 05 turn most of those off. But Firefox also updates — and updates sometimes silently *reset* preferences back to their upstream defaults. Having a runtime layer that re-applies our chosen values on every launch is a defence against that quiet drift.

The secondary reason: iteration speed. Changing a compile-time default in Topic 05 requires a full rebuild (10–20 minutes). Changing `user.js` requires editing the file and restarting the browser (10 seconds). During development this matters a lot.

**What is in it:** memory and GC tuning for the reference machine's RAM budget, media settings synchronised with the hardware-only decode policy, aggressive telemetry / experiment / AI kill-switches, and dozens of small usability tweaks. All commented, all readable.

## 🎭 The Main Characters

| Name | What It Is | Real-World Comparison |
|---|---|---|
| **user.js** | The runtime-override preference file — applied last on every browser launch | The pilot's pre-flight checklist — every switch touched, in order, right before takeoff |
| **Precedence chain** | StaticPrefList (Topic 05, built-in) → firefox.js / all.js (Topic 05, app-branch) → prefs.js (user changes in about:config) → user.js (this) → policies.json (Topic 12, hard-lock) | A stack of transparent slides, each written on top of the last |

## 🔢 How It Works — Step by Step

### Step 1: One file, ~1,100 lines, human-readable

Every line is `user_pref("name", value);` with a comment above it explaining why. Deliberately monolithic — one place to look, one grep to find any setting.

### Step 2: Applied on every browser start

Firefox reads user.js after loading the profile's prefs.js, and the values overwrite whatever was there. Even if Firefox updated overnight and silently reset something, this file catches the reset and restores our value on the next launch.

### Step 3: Kernel-synced defaults

The file's status header reads 'Kernel-Synced Braveheart' — the values chosen here explicitly align with the custom `7.x-unleashed.gorilla-eapd` kernel's settings. Network buffer sizes match sysctl caps, memory pressure thresholds match what the kernel can handle.

## 🤔 Quirky Things Worth Knowing

### ⚠️ It cannot override policy-locked prefs from Topic 12

The tiny set of preferences hard-locked by policies.json sit above user.js in the precedence chain. If user.js tries to set one, the value is silently ignored. That is by design — Topic 12 is the layer we want to be un-overrideable.

### ⚠️ A stale duplicate was quarantined 2026-07-06

There used to be multiple user.js files scattered across the project. They were consolidated into this one canonical file and the duplicates put behind a `.disabled` extension. Single source of truth.

## 💻 What Does This Mean For YOU?

### 🔋 Battery, Speed & Memory

Tab-sleep timers, GC heap ceilings, and image-cache limits are all sized for our RAM budget rather than defaults. The observable is fewer swap incidents and less background CPU.

### ⚡ Speed

Startup lighter — background services (Normandy check, telemetry init) do not run.

### 🕵️ Your Privacy

Every AI/experiment/telemetry pref that Topic 05 might not have caught is caught here. Belt-and-suspenders.

### 🌐 Your Internet

Fewer background connections. See Topic 03 for the network stack side.

## 🔴 The Kill Switch — Explained

**What it is:** The whole file IS a bank of ~1,100 kill switches (or affirmative switches, or tunings). Each is one line; each can be reverted individually.

**Without it:** Firefox runs with factory-default preferences. Everything this file overrides silently comes back to Mozilla's chosen value.

**Think of it like:** The full lighting cue-sheet for a theatre show — 1,100 cues in order, each one small, the whole doing the actual work of running the show.

## 🌐 Open Source & Why It Matters To You

The single most auditable thing in the whole build. One file, plain text, every line commented. Compare to closed browsers where equivalent settings are opaque, undocumented, and often silently mutated by updates.

## 📖 Glossary (Plain English Dictionary)

**user.js** — A Firefox convention: a file in the profile directory that gets its `user_pref(...)` lines applied on every start, overriding anything in prefs.js.

**prefs.js** — The file Firefox writes to when you change a preference via about:config. Persisted, but overrideable by user.js on next start.

**Precedence chain** — The order in which preference sources are applied at startup. Last one wins. Our chain: StaticPrefList → firefox.js/all.js → prefs.js → user.js → policies.json.

---
*Human Track. Its Developer Track twin (`10-overrides.DEVELOPER.md`) covers the same changes in technical detail. Neither is a simplified copy of the other — they are the same truth in two languages.*