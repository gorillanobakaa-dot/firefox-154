# 🦍 The AI Excision — Taking the AI Out of the Browser, Roots and All — Plain English Guide

> *Topic `14-ai-excision` of the Gorilla Unleashed Firefox 154 build · Written for everyone · 2026-08-03*

---

## 🌍 The Big Picture

In 2025–2026 Mozilla built a whole AI wing onto Firefox: an "AI Window" (a browser mode with a chatbot at the centre), a sidebar chatbot, link summarizers, "smart" tab grouping, and a local machine-learning engine with its own model downloader. On a modern machine with 32 GB of RAM you might not notice. On the machines this build is for — a 2012 laptop, or a €150 machine a kid in Lima or Luanda saved a year for — this wing is dead weight that eats memory and disk for features nobody asked for.

This topic documents how the whole wing was removed. Not switched off. **Removed** — the directories no longer exist in the source tree.

## 🕵️ The Nasty Part: How It Was Wired In

Here is the part worth understanding, because it explains why this took surgery and not a settings flip.

The clean way to add an optional feature is to make the feature plug itself into the browser. Mozilla did the opposite: they went into about forty core files — the *New Window* shortcut, session restore, the address bar, the right-click menu, the Clear-Data dialog, even the **theme engine** — and hard-coded a question into each one: *"should this be an AI thing instead?"* The question is a call **into** the AI code. So just to learn the answer is "no", every one of those components was forced to load AI code. Every message the browser might show you was silently rewritten through an AI-targeting filter. The theme engine watched every window, forever, for an AI attribute.

Software that loads components you didn't ask for, that acts without telling you — that is the behaviour pattern of malware, whoever ships it.

## 🔧 How It Came Out — Tourniquet First, Then Surgery

**Step 1 — The dead phone line.** Deleting the AI module outright makes those forty askers crash (they reach for something that's gone). So first we replaced it with a tiny stub — a disconnected phone that answers *"no"* to every question. Browser boots, everything calm, AI functionally dead. That was the safety net.

**Step 2 — Remove the asking itself.** With the net in place, we went file by file and cut each question out, restoring each component to the shape it had before the AI era — and we could *check* that shape, because older Firefox versions (ESR) still show exactly how each file worked without AI. `Ctrl+N` just opens a window again. The File menu no longer has "New AI Window". Session restore no longer wonders whether your windows were AI windows.

**Step 3 — Pull the roots.** Once nothing asked anymore, the stubs had no callers, and the whole directories left the tree. A component turns out to be anchored in five hidden places besides its own code — including, fittingly, the **telemetry registry**: the deepest root holding the AI to the tree was its own measurement hooks. All five anchors are documented in the developer track so the next removal is a checklist, not an expedition.

## 💥 Bonus: Three Crashes That Were Already There

The deep testing found three time-bombs left by an earlier, shallower removal pass: the browser would have **crashed on every tab right-click**, on **every window close**, and on **every link right-click** — because core menus still tried to load AI modules that no longer shipped. All three are fixed. This is why the rule here is *verify against the running binary*, never against "it looks right".

## 📉 What You Gain, What You Lose

**Gain:** no AI window, no chatbot sidebar, no AI ads ("Try Smart Window!") in your menus, no model downloader waiting to pull gigabytes of AI models onto a 32 GB eMMC disk, fewer modules loaded in every window, and a browser that does not ask an AI layer for permission to open a window.

**Lose:** the AI features themselves — which is the point. Translations (a *real* feature people need) was carefully preserved: it lost only its AI-era wrapper and now answers to a plain on/off setting, the way it did before.

Everything is reversible: the removed code is parked, byte-for-byte, next to this document.
