# 09.REMOTE — History, Roadmap & Overview

## Document Control
- **Category:** Remote Control Lockdown
- **Last Updated:** 2026-07-06
- **Status:** Active Development
- **Verification Required:** Yes (see Validation section)
- **Related Documents:** 
  - `../DOCUMENTATION_TEMPLATES.md` (IBM format guide)
  - `../MAP.md` (cross-category index)
  - `../10.OVERRIDES/user.js` (preference layer)
  - `../12.MOZAMBIQUE.DRILL/policies.json` (locked preferences)

---

## Executive Summary

**What This Does (Plain Language):**
Permanently disables Firefox's two remote-control backdoors (Marionette and Remote Agent) so nothing can drive or inspect the browser from outside. These are legitimate automation tools, but also attack surfaces.

**Technical Summary:**
Remote automation lockdown for Sony VAIO SVE14A3AJ. Implements: (1) Marionette automation server hard-disabled (`enabled = false`, setter dead-ended, `--marionette` flag discarded), (2) Remote Agent / WebDriver BiDi hard-disabled (`#enabled = false`, `#allowSystemAccess = false`, setters dead-ended, `--remote-debugging-port` flag discarded). Physical locks — no flag or env var can wake them.

**Critical Context:**
> **This removes browser-automation capability.** You cannot use Selenium, WebDriver, or remote debugging tools with this build. Deliberate trade-off: smaller attack surface vs. automation flexibility.

---

## Mission Statement

### Mission: Close Remote Control Backdoors
Firefox ships with two hidden "service hatches" that let another program **operate the browser from outside** — click things, read pages, control it remotely.

**Legitimate Uses:**
- Automated testing
- Developer tooling
- Browser automation (Selenium, WebDriver)

**Security Risk:**
If something can quietly switch one on, it can quietly drive your browser.

**Our Response:**
**Bolted both hatches shut and threw away the key.**

**The Two Hatches:**
1. **Marionette** — Automation backend
2. **Remote Agent** — Remote debugging / WebDriver BiDi

---

## Document Reconstruction Note

> **Written 2026-07-06.** Reconstructed from `_rebase_2026-07-05/diffs/09.REMOTE__*` via inline `GORILLA` markers.

> **Dual-track** per Gorilla Open Source Philosophy: Track A (plain language) leads, Track B (technical) follows.

---

# TRACK A — For Everyone (Plain English)

## What Is This Folder?

Firefox ships with two hidden "service hatches" that let another program **operate the browser from outside** — click things, read pages, control it remotely.

**Why They Exist:**
- Automated testing
- Developer tooling
- Browser automation

**The Problem:**
They are also a genuine **attack surface**. If something can quietly switch one on, it can quietly drive your browser.

## What We Did

We **bolted both hatches shut and threw away the key.**

### In Plain Terms:

**1. Hard-Wired to "Off"**
- Not "off by default"
- *Off, permanently*

**2. Dead-End Switch**
- The switch that would turn them on has been turned into a **dead end**
- Flipping it does nothing

**3. Flags Ignored**
- Command-line flags and environment variables that normally enable them are **read and discarded**
- Browser sees the request and ignores it

**Patch Comments Call This:**
*"PHYSICAL LOCK"* — *"No flag or env var can wake it."*

## What This Means for You

**Security:**
No external program — malicious or otherwise — can use these standard mechanisms to remotely control or snoop on your browser.

**Trade-Off:**
You give up the ability to use browser automation tools (Selenium, WebDriver) on this build.

**Deliberate Choice:**
Smaller attack surface vs. automation flexibility.

## What This Does NOT Do (Honest Account)

### 1. Removes Browser-Automation Capability
- **Cannot use:** Selenium, WebDriver, remote debugging
- **That's the point:** But it's a real limitation
- **If you need automation:** This build is not for you

### 2. Shuts Two Standard Entry Points
- Closes Marionette and Remote Agent
- **Not a claim:** That *no* conceivable remote/inspection path exists
- **See roadmap:** We list what still needs checking rather than declaring victory

## The Short Story

A hardened, single-user appliance shouldn't answer to remote puppet-strings. These two files remove the puppet-strings entirely, in a way that can't be re-enabled by a setting, flag, or environment variable.

---

# TRACK B — For the Developer (Technical)

## Component Documentation

### 1. Marionette.sys.mjs — PHYSICAL LOCK

**Status:** Modified | **Deploy Path:** `remote/marionette/Marionette.sys.mjs` | **Last Verified:** 2026-07-06

**What It Does (Plain Language):**
This is the Marionette automation server that lets tools like Selenium control the browser. We permanently disabled it.

**Technical Description:**
Marionette automation server hard-disabled with physical lock.

**Implementation:**

**Hard-Coded Disabled:**
```javascript
this.enabled = false;  // Hard-coded
```

**Dead-End Setter:**
```javascript
set enabled(value) {
  this._enabled = false;  // Dead-end — no external write takes effect
}
```

**Flag Handling:**
```javascript
// --marionette command-line flag
subject.handleFlag("marionette", false);  // Read and discarded
this.enabled = false;  // Re-asserted
```

**Result:**
Marionette automation server never starts, regardless of prefs/flags/env.

**Verification Procedure:**
```bash
# Check for GORILLA markers
grep -n "GORILLA\|PHYSICAL LOCK" Marionette.sys.mjs

# Check hard-coded disabled
grep -n "this.enabled = false" Marionette.sys.mjs

# Test at runtime
# 1. Launch Firefox with --marionette flag
./firefox --marionette

# 2. Check about:support
# Marionette should show: Disabled

# 3. Try to connect with Selenium
# Should fail to connect
```

**Cross-Reference:**
- See `RemoteAgent.sys.mjs` for Remote Agent lockdown
- See Invariants section for security rationale

**Audit Status:** ✅ Conformant (2026-07-06)

---

### 2. RemoteAgent.sys.mjs — PHYSICAL LOCK

**Status:** Modified | **Deploy Path:** `remote/RemoteAgent.sys.mjs` | **Last Verified:** 2026-07-06

**What It Does (Plain Language):**
This is the Remote Agent that provides remote debugging and WebDriver BiDi protocol. We permanently disabled it.

**Technical Description:**
Remote Agent / WebDriver BiDi hard-disabled with physical lock.

**Implementation:**

**Hard-Coded Disabled:**
```javascript
this.#allowSystemAccess = false;  // Hard-coded
this.#enabled = false;            // Hard-coded
```

**Dead-End Setters:**
```javascript
set allowSystemAccess(value) {
  this.#allowSystemAccess = false;  // Dead-end
}

set enabled(value) {
  this.#enabled = false;  // Dead-end
}
```

**Flag Handling:**
```javascript
// --remote-debugging-port and system-access flags
#handleRemoteDebuggingPortFlag(subject) {
  // Read flags
  // Then force:
  this.#allowSystemAccess = false;
  this.#enabled = false;
  // Discarded
}
```

**Result:**
- No remote-debugging endpoint
- No BiDi protocol
- No system access

**Verification Procedure:**
```bash
# Check for GORILLA markers
grep -n "GORILLA\|PHYSICAL LOCK" RemoteAgent.sys.mjs

# Check hard-coded disabled
grep -n "#enabled = false\|#allowSystemAccess = false" RemoteAgent.sys.mjs

# Test at runtime
# 1. Launch Firefox with --remote-debugging-port flag
./firefox --remote-debugging-port=9222

# 2. Try to connect to debugging port
curl http://localhost:9222/json
# Should fail to connect

# 3. Check about:support
# Remote Agent should show: Disabled
```

**Cross-Reference:**
- See `Marionette.sys.mjs` for Marionette lockdown
- See Invariants section for security rationale

**Audit Status:** ✅ Conformant (2026-07-06)

---

## Chronological History (Recovered)

### Firefox 153 Era
**Initial Development:**
- Authored as remote-automation lockdown
- Marionette hard-disabled
- Remote Agent hard-disabled
- Physical locks implemented

### 2026-07-05
**Rebase to Firefox 154:**
- 2 diffs captured
- Clean migration (no .rej files)

### 2026-07-06
**Documentation:**
- This document written
- Dual-track format applied

---

## Validation & Verification

### Pre-Deployment Checks

```bash
# 1. Check for GORILLA markers
grep -r "GORILLA\|PHYSICAL LOCK" *.mjs
# Should show markers in both files

# 2. Verify hard-coded disabled
grep "enabled = false" Marionette.sys.mjs
grep "#enabled = false" RemoteAgent.sys.mjs

# 3. Check dead-end setters
grep -A 2 "set enabled" Marionette.sys.mjs RemoteAgent.sys.mjs
# Should show forced false assignments

# 4. Verify flag handling
grep "handleFlag.*marionette" Marionette.sys.mjs
grep "handleRemoteDebuggingPortFlag" RemoteAgent.sys.mjs
```

### Runtime Verification

```bash
# 1. Test Marionette disabled
# Launch with flag
./firefox --marionette

# Check about:support
# Marionette: Disabled

# Try Selenium connection
# Should fail

# 2. Test Remote Agent disabled
# Launch with flag
./firefox --remote-debugging-port=9222

# Try to connect
curl http://localhost:9222/json
# Should fail (connection refused)

# Check about:support
# Remote Agent: Disabled

# 3. Check no listening ports
netstat -tlnp | grep firefox
# Should not show 9222 or Marionette port

# 4. Verify in Browser Console
# Open Ctrl+Shift+J
# Type: Services.marionette.enabled
# Should return: false
```

---

## Invariants (Do Not Break)

### 1. Marionette.enabled Stays Hard-Coded False

**Rule:**
`Marionette.enabled` must remain hard-coded `false`, setter must stay dead-ended.

**Why:**
Core security posture. No remote automation.

**Verification:**
```bash
grep "this.enabled = false" Marionette.sys.mjs
grep -A 2 "set enabled" Marionette.sys.mjs
# Must show forced false
```

### 2. RemoteAgent #enabled and #allowSystemAccess Stay Hard-Coded False

**Rule:**
Both private fields must remain hard-coded `false`, setters must stay dead-ended.

**Why:**
Core security posture. No remote debugging or system access.

**Verification:**
```bash
grep "#enabled = false\|#allowSystemAccess = false" RemoteAgent.sys.mjs
grep -A 2 "set.*Access\|set enabled" RemoteAgent.sys.mjs
# Must show forced false
```

### 3. Flags Stay Read-and-Discarded

**Rule:**
`--marionette` and `--remote-debugging-port` flags must be read and discarded.

**Why:**
Prevent command-line re-enablement.

**Verification:**
```bash
grep "handleFlag.*marionette.*false" Marionette.sys.mjs
grep "handleRemoteDebuggingPortFlag" RemoteAgent.sys.mjs
# Must show flag handling that forces disabled
```

### 4. Do Not "Re-Enable for Debugging"

**Rule:**
Never temporarily re-enable and forget to revert.

**Why:**
Reopens the backdoor. Easy to forget in development.

**Prevention:**
- Use separate debug build if needed
- Never commit re-enablement
- Preflight checks catch this

---

## Open Items / Roadmap

### High Priority 🔴

- [ ] **Confirm no other remote/inspection entry points remain**
  - **Check:** Legacy CDP endpoints
  - **Check:** DevTools remote server
  - **Check:** `devtools.debugger.remote-enabled` pref
  - **Action:** Verify they're off too, or document why they can't start
  - **Benefit:** Complete remote access audit

- [ ] **Add self-test/preflight for disabled state**
  - **Purpose:** Assert Marionette + Remote Agent report disabled at runtime
  - **Implementation:** Check `Services.marionette.enabled === false`
  - **Benefit:** Guards against future rebase silently restoring upstream defaults
  - **Pattern:** Mirrors existing toolchain-preflight pattern

### Medium Priority 🟡

- [ ] **Note automation trade-off in top-level README**
  - **Content:** No Selenium/WebDriver support
  - **Purpose:** Set expectations for users
  - **Benefit:** Avoid confusion about missing features

- [ ] **Document DevTools remote debugging status**
  - **Question:** Is DevTools remote server also disabled?
  - **Action:** Test and document
  - **Benefit:** Complete picture of remote access

### Low Priority 🟢

- [ ] **Add runtime check for listening ports**
  - **Purpose:** Verify no remote ports open
  - **Implementation:** Check netstat output
  - **Benefit:** Additional verification layer

### Completed ✅

- [x] Marionette hard-disabled with physical lock
- [x] Remote Agent hard-disabled with physical lock
- [x] Command-line flags read and discarded
- [x] Setters dead-ended
- [x] Document written with dual-track format
- [x] Clean migration to Firefox 154 (no .rej files)

---

## Build Target & Hardware

**⚠️ CRITICAL: This is about security lockdown, not hardware-specific.**

### Target Machine — Sony VAIO SVE14A3AJ

**Platform:**
- Model: Sony VAIO SVE14A3AJ
- Chipset: Intel HM76 Express
- BIOS: R0210V5

**CPU:**
- Model: Intel Core i7-3632QM
- Cores: 4 cores / 8 threads

**Operating System:**
- Distribution: Debian 13 (trixie) 64-bit
- Desktop: GNOME 48
- Display Server: Wayland
- Kernel: Custom `Linux 7.x-unleashed.gorilla-*`

### Implications for Code Editors

**DO NOT:**

1. **Re-enable Marionette or Remote Agent**
   - Reason: Core security posture
   - Risk: Reopens attack surface
   - Result: Defeats lockdown purpose

2. **Remove dead-end setters**
   - Reason: Prevent external re-enablement
   - Risk: Flags/prefs could work again
   - Result: Security hole

3. **Allow flags to work**
   - Reason: Command-line is attack vector
   - Risk: Malware could launch with flags
   - Result: Remote control possible

4. **Temporarily enable for debugging and forget to revert**
   - Reason: Easy to forget
   - Risk: Backdoor left open
   - Result: Security vulnerability

**DO:**

1. **Verify disabled state at runtime**
   ```bash
   # In Browser Console
   Services.marionette.enabled
   # Must return: false
   ```

2. **Test flags are ignored**
   ```bash
   ./firefox --marionette --remote-debugging-port=9222
   # Should not enable either feature
   ```

3. **Check no listening ports**
   ```bash
   netstat -tlnp | grep firefox
   # Should not show remote ports
   ```

4. **Use separate debug build if automation needed**
   - Don't modify production build
   - Keep lockdown intact

---

## Cross-References

### Required Companion Documents
- `../10.OVERRIDES/user.js` — Runtime overrides (may have related prefs)
- `../12.MOZAMBIQUE.DRILL/policies.json` — Locked preferences (may lock remote prefs)

### Related Categories
- `../07.TOOLKIT/` — Toolkit lockdown (complementary security)
- `../03.NETWORKING/` — Network tuning (separate but complementary)

### Build System
- `../deploy.sh` — Deployment script
- `../MAP.md` — Cross-category index

### Documentation
- `../DOCUMENTATION_TEMPLATES.md` — IBM format guide
- `../LLM_TEMPLATE_USAGE_GUIDE.md` — Template usage

---

## Troubleshooting

### Symptom: Marionette Still Works

**Check:**
```bash
# 1. Verify hard-coded disabled
grep "this.enabled = false" Marionette.sys.mjs

# 2. Check setter
grep -A 2 "set enabled" Marionette.sys.mjs
# Should show dead-end

# 3. Test at runtime
# In Browser Console:
Services.marionette.enabled
# Must return: false
```

**Common Causes:**
- Lockdown not deployed
- Old build artifacts
- Patches not applied

**Fix:**
Redeploy Marionette.sys.mjs, clean build.

### Symptom: Remote Debugging Port Opens

**Check:**
```bash
# 1. Verify hard-coded disabled
grep "#enabled = false" RemoteAgent.sys.mjs

# 2. Check listening ports
netstat -tlnp | grep firefox
# Should not show port 9222

# 3. Try to connect
curl http://localhost:9222/json
# Should fail
```

**Common Causes:**
- Lockdown not deployed
- Old build artifacts
- Different remote debugging mechanism

**Fix:**
Redeploy RemoteAgent.sys.mjs, clean build, verify no other remote endpoints.

### Symptom: Selenium Can Connect

**Symptom:**
Selenium/WebDriver successfully connects to browser.

**Check:**
```bash
# 1. Verify both files deployed
ls -la remote/marionette/Marionette.sys.mjs
ls -la remote/RemoteAgent.sys.mjs

# 2. Check for GORILLA markers
grep "GORILLA" remote/marionette/Marionette.sys.mjs
grep "GORILLA" remote/RemoteAgent.sys.mjs

# 3. Verify hard-coded disabled
grep "enabled = false" remote/marionette/Marionette.sys.mjs
```

**Common Cause:**
Lockdown not deployed or old build.

**Fix:**
Clean build, redeploy both files, test again.

### Symptom: Need Automation for Testing

**Symptom:**
Want to use Selenium/WebDriver for testing.

**Solution:**
This build is not for you. Options:
1. Use separate debug build without lockdown
2. Use different browser for automation
3. Test manually on this build

**Do NOT:**
Temporarily re-enable and forget to revert.

### Symptom: DevTools Remote Debugging Works

**Symptom:**
Can connect to DevTools remotely.

**Check:**
```bash
# 1. Check DevTools remote pref
# In about:config
# Search: devtools.debugger.remote-enabled
# Should be: false

# 2. Check for other remote endpoints
netstat -tlnp | grep firefox
# Note any unexpected ports
```

**Action:**
If DevTools remote works, add to Open Items for investigation.

---

*For questions about this document or the remote control lockdown, refer to the inline GORILLA markers in the source files or the original development sessions (Firefox 153 era, migrated to 154 in 2026-07).*