# 🧍 Remote Control Lockdown — Bolting Marionette and Remote Agent Shut — Plain English Guide

> *Topic `09-remote` of the Gorilla Unleashed Firefox 154 build · Written for everyone · 2026-07-16*

---

## 🌍 The Big Picture

Firefox ships with two hidden 'service hatches' called **Marionette** and the **Remote Agent** (WebDriver BiDi). These exist so automated testing tools like Selenium can drive the browser from outside — click things, read pages, take screenshots. They are legitimate developer tools. They are also, from the outside, exactly the kind of hatch an attacker would want to walk through: something that can drive the browser without a person at the keyboard.

This patch group **bolts both hatches shut and throws away the key.** Not disabled by a preference (could be flipped back on) and not disabled by a command-line flag (could be re-enabled by launching differently). Physically dead-coded at three points per channel: the internal `enabled` flag is initialised `false`; the setter that would flip it back is dead-ended; the command-line flags (`--marionette`, `--remote-debugging-port`) are silently discarded.

**Trade-off worth being honest about:** you cannot use Selenium, WebDriver, or any browser-automation tool with this build. If you need those tools, this build is not for you.

## 🎭 The Main Characters

| Name | What It Is | Real-World Comparison |
|---|---|---|
| **Marionette** | Firefox's older browser-automation backend used by Selenium and internal Mozilla tooling | The service door in the back — for staff, not for customers |
| **Remote Agent / WebDriver BiDi** | The newer W3C-standardised remote-debugging + automation protocol | The other service door — different design, same access |
| **--marionette / --remote-debugging-port** | The command-line switches that would normally wake either hatch up | The words 'open sesame' — this build hears them and ignores them |

## 🔢 How It Works — Step by Step

### Step 1: Internal `enabled` field set to false at construction

Both Marionette and Remote Agent are singleton services that store their own on/off state. That state is now hardcoded false at instantiation.

### Step 2: The setter is dead-ended

Both classes have a setter method that could flip the flag on. The setter body is now empty. Even if code paths call it, the flag stays false.

### Step 3: The command-line flags are silently discarded

The parsers still exist (removing them ripples through option-parsing), but the branches that would act on the flags are dead-coded. The flags parse successfully; they just do nothing.

## 🤔 Quirky Things Worth Knowing

### ⚠️ Three shots to be sure

Just setting a pref would not be enough (prefs get reset). Just dead-coding the setter would not be enough (the constructor could initialise to true). Just discarding the flag would not be enough (the pref could still turn it on). All three together = actually dead.

### ⚠️ The tooling still 'appears' to work — it just does nothing

Selenium tools that try to connect get a connection failure. But the browser does not error out or warn; from its own perspective, everything is normal.

## 💻 What Does This Mean For YOU?

### 🔋 Battery, Speed & Memory

One less background service listening on a socket. Tiny.

### ⚡ Speed

Marginal — startup does not initialise the WebDriver protocol.

### 🕵️ Your Privacy

This is the topic where a real attack surface is closed. A remote-control hatch on the internet-facing browser is exactly the kind of thing a targeted attack looks for.

### 🌐 Your Internet

One fewer listening socket.

## 🔴 The Kill Switch — Explained

**What it is:** The lock is at the source level, in three redundant places per channel. To reverse: rebuild with all three restored.

**Without it:** Firefox starts a listening socket for Marionette / Remote Agent on any invocation with the flags set, exposing browser-automation to anything that can connect.

**Think of it like:** Not one lock — a bolt, a chain, and welding the hinge. Belt, suspenders, and gluing the trousers to the belt.

## 🌐 Open Source & Why It Matters To You

You can verify the lock. Grep for `enabled` in the two files. See the constant. See the dead setter. See the discarded flag. In a closed browser this is a marketing claim; here it is arithmetic.

## 📖 Glossary (Plain English Dictionary)

**Marionette** — Firefox's older browser-automation backend. Underlies Selenium's Firefox driver.

**WebDriver BiDi** — The newer W3C standard for bidirectional browser automation. Implemented in Firefox as the Remote Agent.

**Dead-coded** — Code that still exists in source but cannot reach a state where its effect would happen. Distinguished from deleted: removing might break callers; dead-coding preserves the shape.

---
*Human Track. Its Developer Track twin (`09-remote.DEVELOPER.md`) covers the same changes in technical detail. Neither is a simplified copy of the other — they are the same truth in two languages.*