# 🧍 The 'Performance' Folder — Honestly, Mostly About Making Firefox Compile — Plain English Guide

> *Topic `04-performance` of the Gorilla Unleashed Firefox 154 build · Written for everyone · 2026-07-16*

---

## 🌍 The Big Picture

This folder has a misleading name. It is called `04.PERFORMANCE`, and if you looked only at the name you would expect it to be full of speed-tuning code. It is not. It contains five files, and four of them exist for one purpose: **to make the browser compile at all** on the newer, stricter C++ compiler this build uses (Clang 21). The one file that IS a genuine performance tweak (`CCGCScheduler.cpp`) is small — one number pinned for our specific 4-core CPU. All the *real* speed tuning — memory limits, garbage-collector budgets, network prefs — actually lives in `05.PREFS` and `10.OVERRIDES`. That is the honest picture.

The honesty matters. When a folder called *Performance* would be more accurately called *Compile-Fixes-Plus-One-Small-Tweak-Plus-A-Telemetry-Wire-We-Cut*, calling it what it is beats pretending it is a bigger deal than it is. The whole project runs on that principle.

## 🎭 The Main Characters

| Name | What It Is | Real-World Comparison |
|---|---|---|
| **Clang 21** | The newer, stricter C++ compiler this build uses | The strict math teacher who catches every sloppy shortcut the old teacher used to let slide |
| **SFINAE / IsComplete<T>** | A safety trick that asks 'does this thing exist yet?' before trying to poke at it | Checking the box is delivered before trying to open it |
| **Cycle Collector (CC)** | The garbage collector that finds and frees memory Firefox no longer needs — runs periodically in short slices | The cleaning crew that comes through every few minutes rather than once a day (short bursts, no lockdown) |
| **Frame Budget (16.6 ms)** | The time between two frames on a 60 Hz screen; the CC must fit its work inside this or you see stutter | The 16-millisecond commercial break — you can do a quick job in it, but not a big one |

## 🔢 How It Works — Step by Step

### Step 1: The compile fix — SFINAE guards in Maybe.h + MaybeStorageBase.h

The stricter Clang 21 refused to evaluate certain type traits on types that were not yet fully defined. Four small `IsComplete<T>` guards were added: before evaluating a trait on some type T, first check whether T actually exists yet; if not, return `false` and move on. Without this fix, Firefox 154 does not compile. That is the whole story for 4 of the 5 files.

### Step 2: The one genuine performance tweak — CCGCScheduler.cpp

The Cycle Collector's slice budget is pinned to 4 ms and its inter-slice delay to 120 ms. On our 4-core CPU running at 60 Hz Wayland, the frame budget is 16.6 ms per frame. A 4 ms CC slice fits inside it with room for actual rendering; a longer slice would push past the frame boundary and cause a visible micro-stutter. This is the only file in the folder that changes runtime behaviour.

### Step 3: The telemetry wire — Stencil.cpp

The JavaScript compile cache had a Glean metric buried in it, silently phoning home cache-hit statistics on every page load. That metric is now behind `#ifndef GLEAN_DISABLED`. Same pattern as the network topic and the main telemetry topic — no privileged telemetry channel is left open anywhere.

## 🤔 Quirky Things Worth Knowing

### ⚠️ The folder's real purpose is 'stuff without a better home'

MaybeStorageBase.h is neither performance nor privacy — it is a build fix. But it does not fit in a 'build fixes' folder either, because there is not one. So it lives here, and the folder just has to wear the wrong name. This is how real codebases actually look.

### ⚠️ The compile fix pattern is one of five

The Clang 21 migration hit five different breakage patterns across Firefox. This folder addresses Pattern 1 (protected `mIsSome` accessed from templates). The other four are caught by an automated `preflight-clang21.py` script that runs before every build. This folder plus that script is the full defence.

## 💻 What Does This Mean For YOU?

### 🔋 Battery, Speed & Memory

Micro-stutter during garbage collection is measurably reduced — CC slices now fit inside frame budgets. Not a raw benchmarked number; the observable symptom is fewer 'the page hiccuped' moments.

### ⚡ Speed

Marginal but real: cycle collection no longer pushes past frame boundaries.

### 🕵️ Your Privacy

One more telemetry wire cut. Small individually; part of a systematic pattern.

### 🌐 Your Internet

Zero change.

## 🔴 The Kill Switch — Explained

**What it is:** None. This topic has no runtime toggles — everything is compile-time (build fix or DCE'd telemetry).

**Without it:** Without the SFINAE fix, the browser does not build. Without the CC tuning, GC slices sometimes exceed 16.6 ms and you see a micro-stutter. Without the Stencil telemetry gate, JIT cache statistics phone home on every page load.

**Think of it like:** Not a kill switch — a set of tiny structural fixes. Think of it as replacing three worn-out bolts so the machine actually holds together.

## 🌐 Open Source & Why It Matters To You

This folder is small and unglamorous. Naming it 'Performance' when it is mostly compile-fixes could have been dressed up in marketing; instead the project log opens with 'The name is misleading.' That kind of honesty is possible only in open source, where the reader can check the claim by opening the four files and seeing for themselves. In a closed product, marketing wins by default; here, arithmetic wins.

## 📖 Glossary (Plain English Dictionary)

**SFINAE** — Substitution Failure Is Not An Error — a C++ template trick that lets code check whether something exists before trying to use it.

**Cycle Collector (CC)** — Firefox's garbage collector for reference-cycle memory. Runs in short slices to avoid pausing the whole browser.

**Frame budget** — The time between two screen refreshes. At 60 Hz it is 16.6 ms. If any operation takes longer, you see stutter.

**Clang 21** — The C++ compiler used to build this Firefox. Newer versions catch more bugs at build time; requires source code to be extra-correct.

**Glean** — Mozilla's telemetry framework. See Topic 13 for the full story.

---
*Human Track. Its Developer Track twin (`04-performance.DEVELOPER.md`) covers the same changes in technical detail. Neither is a simplified copy of the other — they are the same truth in two languages.*