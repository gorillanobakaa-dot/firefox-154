# 09.REMOTE — Master Project Log

*Created 2026-08-02 by consolidating this folder's documentation set (merged verbatim below). Policy: one master project log per folder.*


---

# ═══ CONSOLIDATION 2026-08-02 — side documents merged VERBATIM below; originals deleted (recoverable: merged-docs-backup-2026-08-02.tar.gz + git history) ═══


---

# ═══ MERGED DOCUMENT: 09-remote.AUDIT.md (verbatim · sha256:345f52a54dba631d · merged 2026-08-02) ═══

# IBM-Style Audit Report: 09-remote

## SECTION A: DOCUMENT CONTROL

| Attribute | Value |
|---|---|
| **Target Category** | 09-remote |
| **Files Scanned** | see payload |
| **Baseline** | Firefox 154 (mozilla-central) |
| **Date / Time** | 2026-07-16 22:42:15 |
| **Audit Status** | PASS |

## SECTION B: EXECUTIVE SUMMARY (Track A — Layman)

Two of Firefox's built-in remote-control backdoors (Marionette and Remote Agent / WebDriver BiDi) are permanently disabled — at three layers each — so nothing can drive or inspect the browser from outside. Trade-off: no browser-automation tooling on this build.

## SECTION C: TECHNICAL SUMMARY (Track B — Developer)

Three-site dead-coding per channel: instance `enabled` init false, setter dead-ended, CLI flag branch inert. Applied to Marionette.sys.mjs and RemoteAgent.sys.mjs. Two listening sockets removed. Automation-attack surface eliminated.

## SECTION D: DETECTED DEFECTS

*No defects detected by rules or model.*

## SECTION E: PRODUCTION READINESS ASSESSMENT

- **Overall readiness:** 🟢 96%
- **Done:**
  - [x] Marionette three-layer lockdown
  - [x] Remote Agent (WebDriver BiDi) three-layer lockdown
  - [x] --marionette and --remote-debugging-port CLI flags dead-coded
  - [x] Trade-off documented
- **To Do:**
  - [ ] P3: automated integration test that `firefox --marionette` binds no socket

## POSITIVE OBSERVATIONS

- ✅ Three-layer redundancy per channel — any single layer would be defeatable in isolation.
- ✅ Deliberate dead-coding rather than deletion — preserves the shape of the API so dependent code does not crash.
- ✅ Same architectural pattern as 12.MOZAMBIQUE.DRILL — coherent, not ad-hoc.

## VERIFICATION COMMANDS

```bash
ss -tlnp | grep -E ':2828|:9222'   # expect no output
firefox --marionette --remote-debugging-port=9222 & sleep 3; ss -tlnp | grep -E ':2828|:9222'   # still no output
grep -n 'enabled' remote/components/Marionette.sys.mjs
```



---

# ═══ MERGED DOCUMENT: 09-remote.DEVELOPER.md (verbatim · sha256:d8e51947c010e000 · merged 2026-08-02) ═══

# Remote Automation Lockdown — Marionette + Remote Agent Hard Disable — Developer Track

> **Topic:** `09-remote` · **Files:** `remote/components/Marionette.sys.mjs`, `remote/components/RemoteAgent.sys.mjs`
> **Generated:** 2026-07-16

---

## Module Summary

Three-layer dead-code lockdown of both browser-automation channels. Marionette: instance `enabled = false` at construction, `set enabled(value)` setter body removed, `--marionette` CLI flag branch dead-coded. Remote Agent (WebDriver BiDi): identical treatment with `#enabled = false`, `#allowSystemAccess = false`, setters dead-ended, `--remote-debugging-port` branch dead-coded. Trade-off explicit: browser is unusable with Selenium/WebDriver by design.

## Architecture

- **Pattern:** Belt-and-suspenders dead-coding at three independent activation surfaces per channel.
- **Trust Boundary:** Removes a browser-automation channel that would otherwise be a listening socket. Substantial attack-surface reduction for targeted-attack scenarios.
- **Attack Surface:** Two fewer listening TCP sockets in the browser process.

## Kill Switches

### `Marionette.sys.mjs — `enabled` init + setter + CLI parser branch` — HARD ⚠️

- **Condition:** compile-time (source-level dead-coding)
- **Effect:** Marionette cannot be turned on by any means short of source edit + rebuild.
- **Reversibility:** reversible
- **Notes:** Rebuild required.

### `RemoteAgent.sys.mjs — `#enabled` init + `#allowSystemAccess = false` + setters + CLI parser branch` — HARD ⚠️

- **Condition:** compile-time
- **Effect:** WebDriver BiDi Remote Agent cannot be turned on. Same three-layer redundancy.
- **Reversibility:** reversible
- **Notes:** Rebuild required.

## Performance Profile

- **CPU:** Marginal.
- **Memory:** Marginal.
- **I/O:** One or two fewer TCP listeners.
- **Timer Interval:** N/A

## Security Analysis

### User Profiling

N/A

### Targeting

Removes a class of remote-attack surface. If an attacker reaches localhost (via XSS-in-browser, malicious-extension escape) they cannot enable a browser-automation socket.

### Trust Chain

N/A

### Abuse Potential

Substantial reduction: browser-automation-socket abuse is a documented attack pattern for targeted browser exploitation.

## Implementation Flow

1. **`Marionette constructor`** — Sets `this.enabled = false`.
   *Side effects:* Instance starts disabled.
2. **`Marionette setter`** — Setter body dead-ended.
   *Side effects:* External code calling `Marionette.enabled = true` has no effect.
3. **`startup CLI parse for --marionette`** — Flag parses but branch does nothing.
   *Side effects:* No socket bound.
4. **`RemoteAgent equivalent (three sites)`** — Same pattern for WebDriver BiDi.
   *Side effects:* No listening socket.

## Technical Debt

🟢 **ACCEPTED** — Automated-testing capability gone — cannot self-verify with Selenium
  - *Recommendation:* Documented trade-off. Testing lives elsewhere (headless CI on stock Firefox).

## Impact If Removed / Disabled

Selenium/WebDriver/BiDi tooling would work — and so would any attacker who could poke localhost.

## Testing Notes

`ss -tlnp | grep -E ':2828|:9222'` — expect no output. Try `firefox --marionette --remote-debugging-port=9222` — flags accepted, no sockets bound.

## Changelog Notes

Locked down 2026-07-06. Cross-references 12.MOZAMBIQUE.DRILL for parallel Normandy/Nimbus lockdown pattern.

---
*Developer Track. Human Track twin: `09-remote.LAYMAN.md`.*


---

# ═══ MERGED DOCUMENT: 09-remote.LAYMAN.md (verbatim · sha256:e187874301343383 · merged 2026-08-02) ═══

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


---

# ═══ MERGED DOCUMENT: 09-remote.PRECHECK.json (verbatim · sha256:4f53cda18c2baa0c · merged 2026-08-02) ═══

```json
[]
```


---

# ═══ MERGED DOCUMENT: 09-remote.PRECHECK.md (verbatim · sha256:42d1785cd6e742d2 · merged 2026-08-02) ═══

# Offline Pre-Check: 09-remote

*Generated 2026-07-16 22:42:15 by doc_audit.py (rule-based, no model involved).*

## File Inventory

| File | Lang | Lines | Complexity | SHA256 (16) |
|---|---|---|---|---|
| remote_components_Marionette.sys.mjs.patch | patch | 46 | 4 | `809097a96e171e19` |
| remote_components_RemoteAgent.sys.mjs.patch | patch | 71 | 4 | `db4b74fb87a23476` |

## Rule Findings (0)

*All offline rules passed.*
