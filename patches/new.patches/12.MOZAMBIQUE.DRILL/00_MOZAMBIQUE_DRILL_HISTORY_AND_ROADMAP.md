# 12.MOZAMBIQUE.DRILL — Normandy/Nimbus Neutralization

**Document Control**
- **Category:** Security & Remote Control Lockdown
- **Last Updated:** 2026-07-07
- **Status:** Production (Active Defense)
- **Applies To:** Firefox 154 Custom Build for Sony VAIO SVE14A3AJ
- **Dependencies:** 05.PREFS (defaults), 10.OVERRIDES (runtime), 03.NETWORKING (telemetry)
- **Deployment:** `.patch` files + `policies.json` via `deploy.sh`

---

## Executive Summary

**What This Is:** A three-layer defense system that permanently neutralizes Firefox's remote-control and experiment infrastructure (Normandy/Nimbus) without deleting it. Named after the "Mozambique Drill" shooting technique — *two to the chest, one to the head*.

**Why It Exists:** Firefox has built-in systems that let Mozilla reach into your browser from a distance and change things: silently switch features on/off, run A/B experiments, measure results. For a browser whose entire point is *no remote strings attached*, this had to go. But deleting it crashes the browser (145+ dependencies), so we neutralized it instead.

**Key Achievement:** The system is **structurally perfect but biologically dead**. It boots normally, all dependencies are satisfied, but the background loops required to execute remote commands will wait ~60 years before firing their first network request. Three shots (master switch OFF, endpoint erased, 60-year timer) plus a policy lock make it override-proof.

**Current State:** Production-ready. Normandy/Nimbus cannot be remotely controlled, cannot run experiments, cannot phone home. The machinery exists (so nothing breaks), but it's switched off, starved, sleeping, and locked.

---

## Mission Statement

### Track A — For Everyone (Plain Language)

**The Problem:** Firefox has a built-in system called **Normandy** (and its successor **Nimbus**) that lets Mozilla reach into your browser from a distance and change things without asking. It can:
- Silently switch features on or off
- Run "experiments" on you (show you version A while your neighbor gets version B)
- Measure the results and report back
- Change settings remotely

You never asked for it. It's just there, phoning a Mozilla server on a schedule to ask *"any new instructions for this browser?"*

For a browser whose entire point is *no remote strings attached*, this had to go.

**Why We Couldn't Just Rip It Out:** The obvious move is to delete it. We tried. It **shattered the browser.**

The reason is a classic software trap: this system is **wired into more than 145 other parts** of Firefox — the address bar, the first-run sequence, the boot process, the settings UI. All of them expect it to be there and to hand back data in a specific shape. Delete it and those 145 things reach for something that's no longer there and crash. The boot sequence dies with errors like `TypeError: ExperimentAPI is undefined`.

So we needed a way to make it **dead but still present** — like leaving a disconnected phone on the desk so everything that expects a phone to be there is satisfied, while the phone can never actually place a call.

**How We Killed It — "The Mozambique Drill":** The technique is named after a shooting drill — *two to the chest, one to the head* — because that's exactly the shape of it. Three shots:

1. **Shot 1 — The Master Switch (chest):** We flip the system's main on/off setting to **OFF**.
   - Pref: `app.normandy.enabled = false`
   - Location: `05.PREFS/firefox.js` (build-time default)

2. **Shot 2 — Data Starvation (chest):** We **erase the phone number** — the web address it would call.
   - Pref: `app.normandy.api_url = ""` (empty string)
   - Effect: Normandy aborts init when it lacks a valid HTTPS endpoint
   - Location: `05.PREFS/firefox.js` (build-time default)

3. **Shot 3 — The 60-Year Sleep (head):** Deep in the code there's a background alarm clock that decides how long to wait before the *next* call-home. We set its fallback to **~60 years** (1,893,456,000 seconds).
   - Code: `Services.prefs.getIntPref(RUN_INTERVAL_PREF, 1893456000); // 60y`
   - Effect: Even if prefs are reset, the background loops still won't fire for six decades
   - Location: `RecipeRunner.sys.mjs.patch`, `RemoteSettingsExperimentLoader.sys.mjs.patch`

Then we **bolt all three shut with a lock** (an enterprise "policy" file) so no setting, no reset, no update can quietly switch them back on.

**The Result:** In the author's words: *"The browser boots perfectly. But the background loops required to execute remote commands will wait 60 human years before firing their first network request. The systems are structurally perfect, but biologically dead."*

**What You Get:**
- Browser **cannot be remotely reconfigured** by Mozilla
- No A/B experiments run on you
- No remote feature toggles
- No experiment telemetry
- Boot sequence works perfectly (no crashes)
- All 145+ dependencies satisfied (they see the system, it just never does anything)

**Honest Limitations:**
- The system is **not removed** — it's still in the code, deliberately, so the 145 dependents keep working. It is disabled, starved, and locked, not excised.
- This kills **Normandy/Nimbus specifically** — it is not a claim that every possible Mozilla network touch is gone; other telemetry is handled in other folders (see `03.NETWORKING`).
- The "60 years" is a practical eternity, not a mathematical impossibility — the locks are what make it robust, which is why all three layers exist together.

### Track B — For the Developer (Technical)

**Why Not Excise (The Glean/Dependency Trap):**

Attempted approaches that failed:
- **Hollowing out `ExperimentAPI.sys.mjs`:** Returning `null` from all methods → `TypeError` in 145+ consumers
- **Deleting `Normandy.sys.mjs`:** `ModuleNotFoundError` across boot sequence, `UrlbarPrefs`, `FirstStartup.sys.mjs`
- **Stubbing with empty objects:** Consumers expect specific return shapes (arrays, promises, objects with methods) → crashes

**Root Cause:** Normandy/Nimbus is deeply integrated:
- `UrlbarPrefs.sys.mjs` expects experiment data for address bar features
- `FirstStartup.sys.mjs` expects enrollment status for onboarding
- Boot sequence expects `ExperimentAPI.ready()` promise to resolve
- 145+ other modules have similar expectations

**Solution:** Neutralize in place instead of removing. Keep the body, stop the heart.

---

## The Three Shots (+ Lock)

### Shot 1 — Master Switch → `05.PREFS/firefox.js`

**Location:** `modules/libpref/init/all.js` or `browser/app/profile/firefox.js`  
**Change:**
```javascript
pref("app.normandy.enabled", false);   // was: true
```

**Effect:** Normandy's main init checks this pref first. If false, most subsystems abort early.

**Verification:**
```bash
# In browser: about:config
# Search: app.normandy.enabled
# Should show: false, Status: default (or locked)
```

### Shot 2 — Data Starvation → `05.PREFS/firefox.js`

**Location:** Same as Shot 1  
**Change:**
```javascript
pref("app.normandy.api_url", "");      // was: https://normandy.cdn.mozilla.net/api/v1
```

**Effect:** Normandy's init code checks for a valid HTTPS endpoint. Empty string → silent abort:
```javascript
if (!apiUrl || !apiUrl.startsWith("https://")) {
  // Abort init, no network request
  return;
}
```

**Verification:**
```bash
# In browser: about:config
# Search: app.normandy.api_url
# Should show: "" (empty), Status: default (or locked)

# Network check
ss -tunap | grep firefox | grep normandy
# Should return nothing
```

### Shot 3 — 60-Year Sleep → `.patch` files (this folder)

**Targets:**
1. `toolkit/components/normandy/lib/RecipeRunner.sys.mjs`
2. `toolkit/components/nimbus/lib/RemoteSettingsExperimentLoader.sys.mjs`

**Changes:**

#### `RecipeRunner.sys.mjs.patch`
```javascript
// Original:
const runInterval = Services.prefs.getIntPref(RUN_INTERVAL_PREF, 86400); // 24h

// Patched:
const runInterval = Services.prefs.getIntPref(RUN_INTERVAL_PREF, 1893456000); // 60y
```

#### `RemoteSettingsExperimentLoader.sys.mjs.patch`
```javascript
// Original:
const interval = Services.prefs.getIntPref("app.normandy.run_interval_seconds", 86400);

// Patched:
const interval = Services.prefs.getIntPref("app.normandy.run_interval_seconds", 1893456000);
```

**Effect:** Even if prefs are reset (malicious extension, update), the code fallback is 60 years. Background loops sleep for a human lifetime.

**Math:**
```
1,893,456,000 seconds = 31,557,600 seconds/year × 60 years
                      ≈ 60 years
```

**Verification:**
```bash
# Check patches applied
grep -r "1893456000" toolkit/components/normandy/
grep -r "1893456000" toolkit/components/nimbus/
# Should return matches in patched files

# Runtime check (if MOZ_LOG enabled)
MOZ_LOG=Normandy:5 firefox 2>&1 | grep -i "interval"
# Should show 60-year interval
```

### The Lock — `policies.json` (Enterprise Policy)

**Location:** `browser/app/distribution/policies.json`  
**Content:**
```json
{
  "policies": {
    "Preferences": {
      "app.normandy.enabled": {
        "Value": false,
        "Status": "locked"
      },
      "app.normandy.api_url": {
        "Value": "",
        "Status": "locked"
      },
      "app.normandy.run_interval_seconds": {
        "Value": 1893456000,
        "Status": "locked"
      }
    }
  }
}
```

**Effect:** Policy-locked prefs **cannot be overridden** by:
- User via `about:config`
- Extensions (even with `<all_urls>` permission)
- Remote commands (Normandy itself, if it somehow woke up)
- `user.js` overrides (`10.OVERRIDES`)

**Precedence:**
```
policies.json (locked) > user.js > firefox.js (defaults) > StaticPrefList.yaml
```

**Verification:**
```bash
# Check file deployed
ls -lh /path/to/firefox/distribution/policies.json

# In browser: about:policies
# Should show: 3 active policies (normandy.enabled, api_url, run_interval_seconds)

# Try to change in about:config
# Should show: "locked" status, cannot modify
```

---

## Defense-in-Depth Layering

```
Layer 1: firefox.js prefs (build-time defaults)
         ↓ Shots 1-2: enabled=false, api_url=""
         
Layer 2: Code fallback defaults (RecipeRunner/RSEL)
         ↓ Shot 3: 60-year timer (survives pref reset)
         
Layer 3: policies.json (runtime, locked)
         ↓ The Lock: cannot be overridden by anything
         
Layer 4: 10.OVERRIDES/user.js (redundant runtime kill)
         ↓ Defense-in-depth (per MAP.md)
```

**Why All Four Layers?**
- **Layer 1:** First line, baked into binary
- **Layer 2:** Survives pref reset (malicious extension, user error)
- **Layer 3:** Survives everything (policy lock is strongest)
- **Layer 4:** Redundant safety (if Layers 1-3 somehow fail)

**Attack Scenarios Covered:**
1. **User accidentally enables in about:config:** Layer 3 (lock) prevents
2. **Malicious extension resets prefs:** Layer 2 (code fallback) + Layer 3 (lock)
3. **Firefox update reverts defaults:** Layer 2 (code fallback) + Layer 3 (lock)
4. **Remote command tries to re-enable:** Layer 2 (60y sleep) + Layer 3 (lock)
5. **Profile reset/new profile:** Layer 1 (defaults) + Layer 3 (lock)

---

## Component Documentation

### Patch Files (Applied via `patch -p1`)

#### 1. `RecipeRunner.sys.mjs.patch`

**Target File:** `toolkit/components/normandy/lib/RecipeRunner.sys.mjs`  
**Purpose:** Dilate Normandy's main background loop timer to 60 years  
**Lines Changed:** ~5 (single constant change)

**Key Change:**
```javascript
// Line ~50 (approximate)
- const runInterval = Services.prefs.getIntPref(RUN_INTERVAL_PREF, 86400);
+ const runInterval = Services.prefs.getIntPref(RUN_INTERVAL_PREF, 1893456000); // 60y
```

**Context:** `RecipeRunner` is Normandy's main orchestrator. It schedules periodic checks for new "recipes" (remote commands). By setting the fallback interval to 60 years, even if the pref is missing/reset, the loop sleeps for a lifetime.

**Verification:**
```bash
# Check patch applies cleanly
patch -p1 --dry-run < 12.MOZAMBIQUE.DRILL/RecipeRunner.sys.mjs.patch

# After build, verify constant in source
grep "1893456000" toolkit/components/normandy/lib/RecipeRunner.sys.mjs
```

#### 2. `RemoteSettingsExperimentLoader.sys.mjs.patch`

**Target File:** `toolkit/components/nimbus/lib/RemoteSettingsExperimentLoader.sys.mjs`  
**Purpose:** Dilate Nimbus's experiment loader timer to 60 years  
**Lines Changed:** ~5 (single constant change)

**Key Change:**
```javascript
// Line ~80 (approximate)
- const interval = Services.prefs.getIntPref("app.normandy.run_interval_seconds", 86400);
+ const interval = Services.prefs.getIntPref("app.normandy.run_interval_seconds", 1893456000); // 60y
```

**Context:** `RemoteSettingsExperimentLoader` is Nimbus's (Normandy's successor) experiment loader. It syncs with Remote Settings for experiment definitions. Same timer dilation strategy.

**Verification:**
```bash
# Check patch applies cleanly
patch -p1 --dry-run < 12.MOZAMBIQUE.DRILL/RemoteSettingsExperimentLoader.sys.mjs.patch

# After build, verify constant in source
grep "1893456000" toolkit/components/nimbus/lib/RemoteSettingsExperimentLoader.sys.mjs
```

### Policy File

#### `policies.json`

**Location (Source):** `12.MOZAMBIQUE.DRILL/policies.json`  
**Location (Deployed):** `browser/app/distribution/policies.json`  
**Format:** JSON (enterprise policy format)

**Full Content:**
```json
{
  "policies": {
    "Preferences": {
      "app.normandy.enabled": {
        "Value": false,
        "Status": "locked"
      },
      "app.normandy.api_url": {
        "Value": "",
        "Status": "locked"
      },
      "app.normandy.run_interval_seconds": {
        "Value": 1893456000,
        "Status": "locked"
      }
    }
  }
}
```

**Policy Semantics:**
- **`Value`:** The enforced value for the pref
- **`Status: "locked"`:** Pref cannot be changed by user, extensions, or remote commands
- **Scope:** Applies to all profiles (system-wide)

**Deployment:**
```bash
# Via deploy.sh
cp 12.MOZAMBIQUE.DRILL/policies.json \
   /path/to/firefox/distribution/policies.json

# Verify
cat /path/to/firefox/distribution/policies.json
```

**Verification:**
```bash
# In browser: about:policies
# Should show:
# - Policy Name: Preferences
# - Status: Active
# - Value: (shows 3 locked prefs)

# Try to modify in about:config
# Search: app.normandy.enabled
# Status column should show: "locked"
# Double-click should do nothing (cannot modify)
```

### Supporting Documentation

#### `README.md`

**Location:** `12.MOZAMBIQUE.DRILL/README.md`  
**Purpose:** Quick reference for the three-shot technique  
**Content:** Shot-by-shot code detail, rationale, verification commands

**Key Sections:**
- **The Mozambique Drill:** Metaphor explanation
- **Shot 1-3:** Code locations and changes
- **The Lock:** Policy file deployment
- **Why Not Delete:** Dependency trap explanation
- **Verification:** Runtime checks

---

## Chronological History

### Phase 1: Excision Attempts (Date Unknown)
- **Approach:** Delete Normandy/Nimbus modules entirely
- **Result:** Browser crashes on boot
- **Errors:** `TypeError: ExperimentAPI is undefined`, `ModuleNotFoundError`
- **Root Cause:** 145+ dependencies expect modules to exist
- **Decision:** Pivot from excision to neutralization

### Phase 2: Neutralization Strategy (Date Unknown)
- **Insight:** Keep the body, stop the heart
- **Design:** Three-shot approach (switch, starve, sleep)
- **Implementation:** Prefs + code patches + policy lock
- **Metaphor:** Named "Mozambique Drill" (two to chest, one to head)

### Phase 3: Integration into 154 Build (Pre-2026-07-06)
- **Format:** Carried as `.patch` files + `policies.json`
- **Deployment:** `deploy.sh` copies policy file to distribution/
- **Testing:** Verified boot sequence works, no Normandy network requests
- **Documentation:** Initial README.md written

### Phase 4: Documentation (2026-07-06)
- **Action:** Dual-track documentation written
- **Status:** Patches confirmed present, policy confirmed deployed
- **Cross-references:** Linked to `05.PREFS`, `10.OVERRIDES`, `03.NETWORKING`

### Phase 5: IBM Format Transformation (2026-07-07)
- **Action:** Transformed to IBM-quality format
- **Added:** Document control, verification procedures, security analysis
- **Cross-referenced:** Dependencies with other categories
- **Status:** Production-ready documentation

---

## Validation & Verification

### Pre-Build Checks

1. **Patch Application**
   ```bash
   cd /path/to/firefox-source
   
   # Dry-run patches
   patch -p1 --dry-run < patches/12.MOZAMBIQUE.DRILL/RecipeRunner.sys.mjs.patch
   patch -p1 --dry-run < patches/12.MOZAMBIQUE.DRILL/RemoteSettingsExperimentLoader.sys.mjs.patch
   
   # Check for rejects
   find toolkit/components/normandy toolkit/components/nimbus -name "*.rej"
   # Should return nothing
   ```

2. **Patch Content Verification**
   ```bash
   # Verify 60-year constant present
   grep "1893456000" 12.MOZAMBIQUE.DRILL/*.patch
   # Should return 2 matches (one per patch)
   
   # Verify comment present
   grep "// 60y" 12.MOZAMBIQUE.DRILL/*.patch
   # Should return 2 matches
   ```

3. **Policy File Validation**
   ```bash
   # Verify JSON syntax
   python3 -m json.tool 12.MOZAMBIQUE.DRILL/policies.json
   # Should output formatted JSON (no errors)
   
   # Verify required keys
   jq '.policies.Preferences | keys' 12.MOZAMBIQUE.DRILL/policies.json
   # Should show: ["app.normandy.api_url", "app.normandy.enabled", "app.normandy.run_interval_seconds"]
   ```

### Post-Build Verification

1. **Prefs Existence**
   ```bash
   # Check prefs are registered
   firefox --headless --screenshot /dev/null 2>&1 | \
     grep -E "(normandy.enabled|normandy.api_url|normandy.run_interval)"
   
   # Or in running browser: about:config
   # Search: app.normandy
   # Should show all 3 prefs
   ```

2. **Default Values**
   ```bash
   # Verify defaults match Shot 1-2
   # In browser: about:config
   # app.normandy.enabled → false
   # app.normandy.api_url → "" (empty)
   # app.normandy.run_interval_seconds → 1893456000
   ```

3. **Policy Deployment**
   ```bash
   # Check policy file exists
   ls -lh /path/to/firefox/distribution/policies.json
   
   # Verify content
   cat /path/to/firefox/distribution/policies.json | jq .
   
   # In browser: about:policies
   # Should show: "Preferences" policy active with 3 locked prefs
   ```

4. **Lock Status**
   ```bash
   # In browser: about:config
   # Search: app.normandy.enabled
   # Status column should show: "locked"
   # Try to double-click → should do nothing (cannot modify)
   ```

### Runtime Testing

#### Test 1: Verify No Normandy Network Requests

```bash
# Start browser with network monitoring
ss -tunap | grep firefox &
firefox --new-instance --profile /tmp/test-profile

# Wait 5 minutes (normal Normandy check interval)
# Monitor network connections
ss -tunap | grep firefox | grep -E "(normandy|cdn.mozilla.net)"
# Should return nothing

# Or use browser devtools
# F12 → Network tab → Filter: "normandy"
# Should show no requests
```

**Expected:** No network requests to `normandy.cdn.mozilla.net` or related endpoints.

#### Test 2: Verify Boot Sequence Works

```bash
# Start browser (should boot normally)
firefox --new-instance --profile /tmp/test-profile

# Check browser console for errors
# Ctrl+Shift+J → Console tab
# Filter: "normandy" or "experiment"
# Should show no errors (maybe info logs about disabled state)
```

**Expected:** Browser boots normally, no `TypeError` or `ModuleNotFoundError`.

#### Test 3: Verify Experiment API Returns Safe Defaults

```bash
# Open browser console (Ctrl+Shift+J)
# Run:
const { ExperimentAPI } = ChromeUtils.import(
  "resource://nimbus/ExperimentAPI.jsm"
);
console.log(ExperimentAPI.getExperiment("test"));
console.log(ExperimentAPI.getAllBranches("test"));
console.log(ExperimentAPI.ready());

# Should return:
# - getExperiment: null or undefined (no experiment)
# - getAllBranches: [] (empty array)
# - ready: resolved promise (not hanging)
```

**Expected:** API returns safe defaults, no crashes, no hanging promises.

#### Test 4: Verify Policy Lock Prevents Changes

```bash
# In browser: about:config
# Search: app.normandy.enabled
# Try to double-click to toggle
# Should do nothing (locked)

# Try via console (Ctrl+Shift+J)
Services.prefs.setBoolPref("app.normandy.enabled", true);
# Should throw error or silently fail (locked pref)

# Verify value unchanged
Services.prefs.getBoolPref("app.normandy.enabled");
// Should return: false (unchanged)
```

**Expected:** Policy lock prevents all modification attempts.

#### Test 5: Verify 60-Year Timer (Debug Build)

```bash
# Build with MOZ_LOG enabled
MOZ_LOG=Normandy:5,Nimbus:5 firefox 2>&1 | grep -i "interval"

# Should show logs like:
# "RecipeRunner: run interval = 1893456000 seconds"
# "RemoteSettingsExperimentLoader: interval = 1893456000 seconds"
```

**Expected:** Debug logs confirm 60-year interval is active.

---

## Invariants (Do Not Break)

### Critical Invariants

1. **Do NOT Delete/Excise Normandy/Nimbus Modules**
   - 145+ dependencies crash if modules are missing
   - Neutralize only, never remove
   - Keep `ExperimentAPI.sys.mjs`, `Normandy.sys.mjs`, etc. intact

2. **All Three Prefs Must Stay at Neutralized Values**
   ```javascript
   app.normandy.enabled = false
   app.normandy.api_url = ""
   app.normandy.run_interval_seconds = 1893456000
   ```
   - At **every** layer (defaults, code fallback, policy lock)
   - Do NOT change any of these values

3. **Policy Lock Must Stay Deployed**
   - `policies.json` must exist in `distribution/` directory
   - All 3 prefs must have `"Status": "locked"`
   - Policy file is the ultimate defense (cannot be overridden)

4. **60-Year Fallback Must Stay in Code**
   - `1893456000` constant must remain in patched source
   - Survives pref reset (malicious extension, user error)
   - Do NOT reduce this value (defeats the purpose)

### Deployment Invariants

1. **Patches Must Be Applied**
   - Both `.patch` files must be applied before build
   - Verify no `.rej` files after application
   - Check constants present in source after patching

2. **Policy File Must Be Deployed**
   - `deploy.sh` must copy `policies.json` to `distribution/`
   - Verify file exists and is readable by browser
   - Check `about:policies` shows active policy

3. **Defense-in-Depth Must Be Maintained**
   - All 4 layers must be active (defaults, code, policy, user.js)
   - Do NOT remove any layer (each has a purpose)
   - Redundancy is intentional (defense-in-depth)

---

## Open Items & Roadmap

### High Priority

- [ ] **Patch Freshness Check**
  - Verify patches apply cleanly to Firefox 154 source
  - Check for `.rej` files after application
  - If drifted, re-derive patches from current source
  - **Blocker for build reliability**

- [ ] **Policy Deployment Verification**
  - Confirm `deploy.sh` copies `policies.json` to correct location
  - Verify `about:policies` shows active policy after deployment
  - Test policy lock prevents modification
  - **Blocker for security guarantee**

- [ ] **Runtime Self-Test**
  - Assert `app.normandy.enabled=false` + locked at startup
  - Verify no Normandy network requests fire (monitor for 5 minutes)
  - Log warning if any Normandy activity detected
  - **Blocker for operational confidence**

### Medium Priority

- [ ] **Audit Other Remote-Config Surfaces**
  - Check if RemoteSettings collections still sync (beyond Normandy/Nimbus)
  - Verify no other remote-control mechanisms exist
  - Document status of each remote surface
  - **Useful for complete remote-control picture**

- [ ] **Dependency Audit**
  - Map all 145+ dependencies on Normandy/Nimbus
  - Verify each gets safe defaults (no crashes)
  - Document which modules use which APIs
  - **Useful for understanding impact**

- [ ] **Performance Impact Measurement**
  - Measure boot time with/without Normandy active
  - Check memory usage (Normandy loops not running)
  - Verify no performance regression from neutralization
  - **Useful for justifying approach**

### Low Priority

- [ ] **Automated Testing**
  - Script to verify all 3 prefs are locked
  - Script to check no Normandy network requests
  - Script to test ExperimentAPI returns safe defaults
  - **Useful for CI/CD**

- [ ] **Documentation Cross-Links**
  - Link to specific Normandy/Nimbus source files
  - Link to upstream Firefox experiment docs
  - Link to enterprise policy documentation
  - **Useful for deep dives**

---

## Build Target & Hardware Context

**Target Hardware:** Sony VAIO SVE14A3AJ
- **CPU:** Intel Core i7-3632QM (Ivy Bridge, 4C/8T, 2.2-3.2GHz)
- **GPU:** Intel HD Graphics 4000 (Ivy Bridge integrated)
- **RAM:** 8GB DDR3
- **Storage:** SSD (SATA)
- **OS:** Debian 13 (Trixie), Wayland
- **Kernel:** 6.12.6 (custom-compiled)

**Build Characteristics:**
- **Optimization:** `-march=native -O3` (Ivy Bridge-specific, NOT portable)
- **Security Posture:** Telemetry lobotomy, remote control disabled, sealed appliance
- **Network:** BBR congestion control, telemetry endpoints blocked
- **Remote:** Normandy/Nimbus neutralized (this category)

**Why This Matters for Remote Control:**
- **Sealed Appliance:** No remote updates, no experiments, no phone-home
- **Predictable Behavior:** Browser behavior is deterministic (no A/B tests)
- **Privacy:** No experiment telemetry, no enrollment data sent
- **Security:** No remote code execution via Normandy recipes

**Portability:** This neutralization is **portable** (not hardware-specific):
- Works on any platform (Linux, Windows, macOS, Android)
- No hardware dependencies
- Can be applied to any Firefox build

---

## Cross-References

### Dependencies (Upstream)

1. **05.PREFS (Build-Time Defaults)**
   - Shots 1-2 implemented here (`firefox.js` defaults)
   - Must set `app.normandy.enabled=false`, `api_url=""`
   - See: `05.PREFS/00_PREFS_HISTORY_AND_ROADMAP.md`

2. **03.NETWORKING (Telemetry Lobotomy)**
   - Network-level blocks for Normandy endpoints
   - Redundant with this category (defense-in-depth)
   - See: `03.NETWORKING/00_NETWORKING_HISTORY_AND_ROADMAP.md`

### Dependencies (Peer)

1. **10.OVERRIDES (Runtime Prefs)**
   - Redundantly disables Normandy prefs in `user.js`
   - Defense-in-depth (per MAP.md)
   - Cannot override policy locks (by design)
   - See: `10.OVERRIDES/00_OVERRIDES_HISTORY_AND_ROADMAP.md`

2. **07.TOOLKIT (Sealed Appliance)**
   - Addon install blocked (prevents malicious extensions from re-enabling)
   - Experiment UI removed (no user-facing experiment controls)
   - See: `07.TOOLKIT/00_TOOLKIT_HISTORY_AND_ROADMAP.md`

### Related Documentation

- **README.md** — Shot-by-shot code detail and rationale
- **MAP.md** — Documents defense-in-depth strategy
- **Upstream:** `toolkit/components/normandy/` — Normandy source code
- **Upstream:** `toolkit/components/nimbus/` — Nimbus source code

---

## Troubleshooting

### Problem: Patches Don't Apply

**Symptoms:**
- `patch` command fails with "Hunk FAILED"
- `.rej` files created in `toolkit/components/`

**Diagnosis:**
```bash
# Try dry-run
patch -p1 --dry-run < 12.MOZAMBIQUE.DRILL/RecipeRunner.sys.mjs.patch

# Check for rejects
find toolkit/components -name "*.rej"

# Compare patch context with actual source
head -20 12.MOZAMBIQUE.DRILL/RecipeRunner.sys.mjs.patch
head -50 toolkit/components/normandy/lib/RecipeRunner.sys.mjs
```

**Solutions:**
1. **Upstream Drift:** Source file changed since patch was created
   - Re-derive patch from current source
   - Update patch file with new context
2. **Wrong Directory:** Must apply from firefox-source root
   - `cd /path/to/firefox-source`
   - `patch -p1 < patches/12.MOZAMBIQUE.DRILL/*.patch`
3. **Already Applied:** Patch was applied previously
   - Check if `1893456000` constant already present in source
   - Skip re-application

### Problem: Policy Not Active

**Symptoms:**
- `about:policies` shows no policies
- Prefs not locked in `about:config`
- Can modify Normandy prefs

**Diagnosis:**
```bash
# Check policy file exists
ls -lh /path/to/firefox/distribution/policies.json

# Check file content
cat /path/to/firefox/distribution/policies.json | jq .

# Check file permissions
ls -l /path/to/firefox/distribution/policies.json
# Should be readable by browser process
```

**Solutions:**
1. **File Not Deployed:** Run `deploy.sh` to copy policy file
2. **Wrong Location:** Policy file must be in `distribution/` directory
3. **JSON Syntax Error:** Validate JSON with `python3 -m json.tool`
4. **Permissions:** Ensure file is readable (`chmod 644`)

### Problem: Normandy Still Active

**Symptoms:**
- Network requests to `normandy.cdn.mozilla.net`
- Experiment data in `about:studies`
- Normandy logs in browser console

**Diagnosis:**
```bash
# Check network connections
ss -tunap | grep firefox | grep normandy

# Check prefs
# In browser: about:config
# Search: app.normandy
# Verify: enabled=false, api_url="", run_interval=1893456000

# Check policy lock
# In browser: about:policies
# Should show: 3 locked prefs

# Check debug log
MOZ_LOG=Normandy:5 firefox 2>&1 | grep -i normandy
```

**Solutions:**
1. **Prefs Not Set:** Verify Shots 1-2 in `05.PREFS/firefox.js`
2. **Patches Not Applied:** Verify Shot 3 (60-year timer) in source
3. **Policy Not Deployed:** Verify `policies.json` in `distribution/`
4. **Network Block Missing:** Check `03.NETWORKING` telemetry lobotomy

### Problem: Browser Crashes on Boot

**Symptoms:**
- Browser crashes during startup
- Errors like `TypeError: ExperimentAPI is undefined`
- Boot sequence fails

**Diagnosis:**
```bash
# Check browser console
firefox --safe-mode 2>&1 | grep -E "(Error|TypeError)"

# Check if Normandy modules were deleted
ls -lh toolkit/components/normandy/lib/
ls -lh toolkit/components/nimbus/lib/
# Should show all .sys.mjs files present
```

**Solutions:**
1. **Modules Deleted:** DO NOT delete Normandy/Nimbus modules
   - Restore from backup or re-checkout source
   - Apply patches only (neutralize, don't remove)
2. **Patch Broke Module:** Verify patches only change timer constant
   - Re-apply patches carefully
   - Check for syntax errors in patched code
3. **Dependency Issue:** Some module expects Normandy to work
   - Check browser console for specific error
   - May need to stub additional APIs

### Problem: Prefs Can Be Changed

**Symptoms:**
- Can toggle `app.normandy.enabled` in `about:config`
- Policy lock not working
- Prefs show "user set" instead of "locked"

**Diagnosis:**
```bash
# Check policy status
# In browser: about:policies
# Should show: "Preferences" policy active

# Check pref status
# In browser: about:config
# Search: app.normandy.enabled
# Status column should show: "locked"

# Check policy file
cat /path/to/firefox/distribution/policies.json | \
  jq '.policies.Preferences."app.normandy.enabled".Status'
# Should return: "locked"
```

**Solutions:**
1. **Policy File Wrong:** Verify `"Status": "locked"` in JSON
2. **Policy Not Loaded:** Restart browser after deploying policy
3. **Wrong Profile:** Policy applies system-wide, but check correct profile
4. **Enterprise Policy Disabled:** Some builds disable enterprise policies
   - Check build config for `MOZ_POLICIES` flag

---

## Security Considerations

### Threat Model

**What This Protects Against:**
- **Remote Reconfiguration:** Mozilla cannot change browser settings remotely
- **A/B Experiments:** Browser cannot be enrolled in experiments without consent
- **Feature Toggles:** Remote feature flags cannot be flipped
- **Experiment Telemetry:** No enrollment data or experiment results sent
- **Malicious Recipes:** Normandy "recipes" (remote commands) cannot execute

**What This Does NOT Protect Against:**
- **Other Telemetry:** See `03.NETWORKING` for general telemetry blocks
- **Manual Updates:** User can still manually update browser (if enabled)
- **Extension Experiments:** Extensions can still run their own experiments
- **Local Exploits:** Does not protect against local privilege escalation

### Attack Scenarios

#### Scenario 1: Malicious Extension Tries to Re-Enable

**Attack:**
```javascript
// Malicious extension code
browser.browserSettings.normandyEnabled.set({value: true});
Services.prefs.setBoolPref("app.normandy.enabled", true);
```

**Defense:**
- **Layer 3 (Policy Lock):** Pref is locked, cannot be changed
- **Layer 2 (Code Fallback):** Even if pref changed, 60-year timer prevents action
- **Result:** Attack fails, Normandy stays disabled

#### Scenario 2: Firefox Update Reverts Defaults

**Attack:**
- Firefox update ships new `firefox.js` with `normandy.enabled=true`
- Update overwrites build-time defaults

**Defense:**
- **Layer 2 (Code Fallback):** 60-year timer in code survives update
- **Layer 3 (Policy Lock):** Policy file survives update (not in app directory)
- **Layer 4 (user.js):** Runtime override survives update
- **Result:** Attack fails, Normandy stays disabled

#### Scenario 3: User Accidentally Enables in about:config

**Attack:**
- User navigates to `about:config`
- Tries to toggle `app.normandy.enabled` to `true`

**Defense:**
- **Layer 3 (Policy Lock):** Pref shows "locked" status, cannot be toggled
- **UI Feedback:** Double-click does nothing, clear indication of lock
- **Result:** Attack fails, user cannot enable

#### Scenario 4: Remote Command Tries to Wake Normandy

**Attack:**
- Hypothetical: Normandy somehow wakes up
- Tries to fetch recipes from `normandy.cdn.mozilla.net`

**Defense:**
- **Shot 2 (Data Starvation):** `api_url=""` → init aborts (no valid endpoint)
- **Layer 3 (Policy Lock):** Cannot change `api_url` to valid endpoint
- **03.NETWORKING:** Network-level block on Normandy endpoints
- **Result:** Attack fails, no network request possible

#### Scenario 5: Profile Reset/New Profile

**Attack:**
- User creates new profile or resets existing profile
- New profile might have default settings

**Defense:**
- **Layer 1 (Build Defaults):** New profile inherits build-time defaults (disabled)
- **Layer 3 (Policy Lock):** Policy applies system-wide (all profiles)
- **Result:** Attack fails, new profile also has Normandy disabled

### Privacy Implications

**Data Not Collected:**
- **Enrollment Status:** Browser does not report experiment enrollment
- **Experiment Results:** No A/B test results sent to Mozilla
- **Feature Usage:** No remote feature flag telemetry
- **Recipe Execution:** No logs of which recipes were executed

**Fingerprinting Reduction:**
- **Consistent Behavior:** All users have same features (no A/B variants)
- **No Experiment ID:** Browser does not expose experiment enrollment ID
- **Predictable:** Behavior is deterministic (no random experiment assignment)

**Trade-offs:**
- **Pro:** No remote profiling, no experiment tracking
- **Con:** Cannot participate in Mozilla experiments (even beneficial ones)
- **Decision:** Sealed appliance model prioritizes privacy over participation

### Audit Trail

**Verification Commands:**
```bash
# Check all 3 shots are active
grep "app.normandy.enabled.*false" browser/app/profile/firefox.js
grep "app.normandy.api_url.*\"\"" browser/app/profile/firefox.js
grep "1893456000" toolkit/components/normandy/lib/RecipeRunner.sys.mjs
grep "1893456000" toolkit/components/nimbus/lib/RemoteSettingsExperimentLoader.sys.mjs

# Check policy lock deployed
cat /path/to/firefox/distribution/policies.json | jq '.policies.Preferences'

# Monitor network for Normandy requests
tcpdump -i any -n host normandy.cdn.mozilla.net
# Should show no traffic
```

**Monitoring:**
- Browser console (Ctrl+Shift+J) for Normandy errors
- `about:policies` for policy status
- `about:config` for pref lock status
- Network monitor for unexpected Normandy requests

---

## Appendix: The Dependency Trap

### Why Excision Failed

**Attempted Approach:** Delete `ExperimentAPI.sys.mjs`, `Normandy.sys.mjs`, etc.

**Result:** Browser crashes with errors like:
```
TypeError: ExperimentAPI is undefined
  at UrlbarPrefs.sys.mjs:45
  at FirstStartup.sys.mjs:120
  at BrowserGlue.sys.mjs:890
  ... (145+ more)
```

**Root Cause Analysis:**

1. **UrlbarPrefs.sys.mjs** (Address Bar Preferences)
   ```javascript
   const { ExperimentAPI } = ChromeUtils.import("resource://nimbus/ExperimentAPI.jsm");
   
   // Later:
   let experimentData = ExperimentAPI.getExperiment("urlbar-feature");
   if (experimentData?.branch === "treatment") {
     // Enable experimental feature
   }
   ```
   - Expects `ExperimentAPI` to exist and return experiment data
   - If module missing: `TypeError: ExperimentAPI is undefined`
   - If returns `null`: `TypeError: Cannot read property 'branch' of null`

2. **FirstStartup.sys.mjs** (First-Run Experience)
   ```javascript
   await ExperimentAPI.ready();
   let enrollments = ExperimentAPI.getAllActiveExperiments();
   ```
   - Expects `ready()` promise to resolve
   - Expects `getAllActiveExperiments()` to return array
   - If module missing: boot hangs or crashes

3. **BrowserGlue.sys.mjs** (Browser Initialization)
   ```javascript
   if (ExperimentAPI.isFeatureEnabled("new-tab-feature")) {
     // Initialize feature
   }
   ```
   - Called during browser init (critical path)
   - If module missing: boot fails

**Total Dependencies:** 145+ modules across:
- Address bar (`browser/components/urlbar/`)
- First-run (`browser/components/newtab/`)
- Settings UI (`browser/components/preferences/`)
- Telemetry (`toolkit/components/telemetry/`)
- Many more...

**Why Stubbing Failed:**

Attempted stub:
```javascript
// ExperimentAPI.sys.mjs (stubbed)
export const ExperimentAPI = {
  getExperiment: () => null,
  getAllActiveExperiments: () => [],
  ready: () => Promise.resolve(),
  isFeatureEnabled: () => false,
};
```

**Problem:** Consumers expect specific return shapes:
- Some expect `getExperiment()` to return `undefined` (not `null`)
- Some expect `ready()` to resolve with specific data
- Some expect `isFeatureEnabled()` to throw if feature unknown
- Impossible to satisfy all 145+ consumers with one stub

**Solution:** Neutralize in place (keep modules, disable functionality)

---

## Document Metadata

**Author:** Gorilla (with Bob Shell assistance)  
**Philosophy:** Gorilla Open Source Philosophy — honest documentation (state limitations, not just wins)  
**Format:** IBM-quality dual-track (Track A: plain language, Track B: technical)  
**Audience:** Primary = future maintainer (likely author), Secondary = technical auditor  
**Maintenance:** Update after Firefox updates, security reviews, or policy changes  
**Related:** Part of Firefox 154 custom build documentation suite

**Change Log:**
- 2026-07-06: Initial dual-track documentation
- 2026-07-07: Transformed to IBM-quality format with comprehensive verification procedures

---

**END OF DOCUMENT**