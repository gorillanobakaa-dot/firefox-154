# 🧍 The Quota Housekeeping — Three Small But Correct Fixes — Plain English Guide

> *Topic `06-quota` of the Gorilla Unleashed Firefox 154 build · Written for everyone · 2026-07-16*

---

## 🌍 The Big Picture

This folder contains one file (`ActorsParent.cpp`) with three small changes to Firefox's storage-quota system. This is the code that decides how much disk space a website is allowed to use for things like IndexedDB, cache, and downloaded assets. The changes are surgical, and none of them are dramatic — but each one fixes a real, small correctness issue: making `about:home` not pop up a storage-permission prompt for the user's own homepage; changing which build channel prints diagnostic console messages; and removing a stale cleanup step for private-browsing origins that no longer needs to run.

This is the shortest topic in the whole build. It fits on one screen.

## 🎭 The Main Characters

| Name | What It Is | Real-World Comparison |
|---|---|---|
| **Quota Manager** | The subsystem that decides how much disk each website can use | The building super who allocates storage lockers |
| **about:home** | Firefox's own homepage / new-tab page | The front lobby of the building — it's the browser's own room, not a tenant |
| **Origin whitelist** | A short list of URLs Firefox treats as its own rather than as external websites | The staff-only door codes |

## 🔢 How It Works — Step by Step

### Step 1: Whitelist about:home for storage prompts

Firefox pops up a 'this site wants to store data' prompt on the first request. That prompt should never appear for the browser's own homepage — it's not a website, it's part of Firefox. A new constant `kAboutHomeOriginPrefix = "moz-safe-about:home"` is added to the prompt-bypass list alongside chrome:// and resource://.

### Step 2: Widen the console-log build gate

A diagnostic that used to only print on Nightly builds now prints on 'EARLY_BETA_OR_EARLIER' — which includes our build. Small change; the diagnostic is now visible in the console.

### Step 3: Remove a stale private-browsing origin-map clear

A block that used to clear a pair of maps during quota shutdown is deleted. Those maps are managed elsewhere; the clear was redundant and, on some paths, held a mutex that was already contested. Deletion, not disable — the code path no longer needs it.

## 🤔 Quirky Things Worth Knowing

### ⚠️ This is what a healthy patch looks like — small, boring, correct

Big flashy fixes get attention. Three-line correctness fixes like this one keep the build boring, which is exactly what we want. The whole folder is 20 lines of diff.

## 💻 What Does This Mean For YOU?

### 🔋 Battery, Speed & Memory

Negligible. One fewer prompt on first about:home visit; one dead code path removed.

### ⚡ Speed

Marginal.

### 🕵️ Your Privacy

Same as before — quota housekeeping, not a policy change.

### 🌐 Your Internet

Zero change.

## 🔴 The Kill Switch — Explained

**What it is:** None — these are point corrections, not toggleable behaviour.

**Without it:** First about:home visit prompts you to allow storage; console misses a diagnostic; shutdown does a redundant mutex-guarded clear.

**Think of it like:** Not a switch — three fresh screws where three worn ones used to be.

## 🌐 Open Source & Why It Matters To You

You can see every line. Three changes; the whole patch fits on one screen.

## 📖 Glossary (Plain English Dictionary)

**Quota Manager** — The Firefox subsystem that tracks and enforces per-origin disk-space limits for storage APIs.

**Origin** — A website's identity — protocol + host + port.

**moz-safe-about:** — Internal URL prefix Firefox uses for its own privileged 'about:' pages.

---
*Human Track. Its Developer Track twin (`06-quota.DEVELOPER.md`) covers the same changes in technical detail. Neither is a simplified copy of the other — they are the same truth in two languages.*