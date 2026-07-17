# 10.OVERRIDES — Runtime Override Layer

**Document Control**
- **Category:** Runtime Configuration & User Preferences
- **Last Updated:** 2026-07-07
- **Status:** Production (Canonical v2.0 — Kernel-Synced Braveheart)
- **Applies To:** Firefox 154 Custom Build for Sony VAIO SVE14A3AJ
- **Dependencies:** 05.PREFS (defaults), 12.MOZAMBIQUE.DRILL (policy locks)
- **Deployment:** `deploy.sh` → runtime profile `user.js`

---

## Executive Summary

**What This Is:** The runtime "final say" on browser behavior — a single authoritative `user.js` file (~1121 lines) that overrides factory defaults on every browser launch. This is the operational control surface for the build.

**Why It Exists:** Firefox ships with defaults optimized for Mozilla's business model (telemetry, experiments, AI features, background services). This override layer strips those out and tunes the browser for this specific hardware without requiring a full rebuild for each adjustment.

**Key Achievement:** Consolidated from multiple scattered override files into one canonical profile, versioned and kernel-synced. Provides defense-in-depth against factory defaults that might revert, while enabling fast iteration without recompilation.

**Current State:** Production-ready. The file is the single source of truth for runtime preferences. A stale duplicate (`Surgical_Patches_V2/`) was quarantined 2026-07-06 to prevent confusion.

---

## Mission Statement

### Track A — For Everyone (Plain Language)

**The Problem:** Firefox ships as a "rental car" — hobbled with background spies, AI chatbots, telemetry, and phone-home services that waste memory, burn CPU, and report your behavior. The factory defaults assume you want these features; you don't get asked.

**The Solution:** This file is the "teardown sheet" — it turns off everything that shouldn't be running and tunes what remains for this specific laptop. It's read fresh on every launch, so it's the last word before the browser starts (except for the hard locks in `12.MOZAMBIQUE.DRILL`).

**Why Two Layers?** (Defaults + Overrides)
1. **Defense in depth:** If a factory default ever slips back to "on" (update, reset), this file turns it off again at runtime. Two locks beat one.
2. **Fast iteration:** Changing this file doesn't require rebuilding the entire browser — edit and restart. It's the quick-adjust layer for operational tuning.

**What You Get:**
- No telemetry, no experiments, no AI features, no background phone-home
- Memory/GC tuning for 8GB RAM + SSD
- Media settings synced with hardware decode (60fps webcam, H.264-only)
- Consistent behavior across launches (no "surprise" feature changes)

**Honest Limitations:**
- This is **not** a generic "privacy pack" — it's tuned for this exact hardware (Ivy Bridge i7-3632QM, HD 4000, 8GB RAM, Debian 13 + 6.12.6 kernel)
- Some settings are aggressive (e.g., tab unloading, GC frequency) — they assume SSD + fast CPU
- This file **cannot** override policy-locked prefs in `12.MOZAMBIQUE.DRILL` (by design — policies win)

### Track B — For the Developer (Technical)

**Precedence Chain** (from `05.PREFS`):
```
StaticPrefList.yaml (compile-time)
  ↓
firefox.js/all.js (build-time defaults)
  ↓
THIS user.js (runtime, writes user branch, wins over defaults)
  ↓
policies.json (12.MOZAMBIQUE.DRILL, locked prefs, cannot be overridden)
```

**Mechanism:** `user.js` is read on every profile startup and writes to the **user preference branch**, which overrides the default branch but is itself overridden by `locked` policy prefs.

**Scope:** ~1121 lines covering:
- Telemetry/phone-home kill (Mozilla + Google services)
- AI/chatbot feature removal (Sidebar, ChatGPT, ML suggestions)
- Background task suppression (updates, experiments, speculative connections)
- Performance tuning (GC/memory, tab unload, media decode)
- Privacy hardening (referrer policy, fingerprinting resistance)

**Cross-Category Consistency:**
- Telemetry prefs match `03.NETWORKING` (network lobotomy)
- Normandy/Nimbus prefs redundantly disabled (primary kill in `12.MOZAMBIQUE.DRILL`)
- Media prefs synced with `01.MEDIA` (hardware-only H.264, 60fps webcam)
- Session restore prefs match `05.PREFS` (password persistence enabled)

**Deployment:** `deploy.sh` copies this file to the runtime profile as `user.js`. This is the **sole** runtime user.js — a duplicate previously in `05.PREFS` was removed to avoid overwrite races (per `MAP.md`).

---

## Component Documentation

### Primary Component: `user.js` (Runtime Override Profile)

**Location:** `10.OVERRIDES/user.js`  
**Size:** ~1121 lines  
**Version:** v2.0 — Kernel-Synced Braveheart  
**Format:** JavaScript preference declarations (`user_pref("key", value);`)

**Purpose:** Authoritative runtime preference overrides, applied on every browser launch.

**Key Sections** (from in-file header):

1. **Telemetry & Phone-Home Kill**
   - Mozilla telemetry (toolkit, browser, normandy)
   - Google SafeBrowsing, geolocation, crash reporting
   - Background update checks, experiments
   - **Verification:** `about:telemetry` should show "Telemetry is not recording"

2. **AI & Chatbot Removal**
   - Sidebar AI features, ChatGPT integration
   - ML-based suggestions (address bar, shopping)
   - Translation services (local-only allowed)
   - **Verification:** No AI icons in toolbar, no chatbot prompts

3. **Background Task Suppression**
   - Speculative connections, DNS prefetch, link preload
   - Idle tasks, background tab timers
   - Normandy/Nimbus (redundant with `12.MOZAMBIQUE.DRILL`)
   - **Verification:** `about:networking` should show minimal idle connections

4. **Performance Tuning**
   - GC frequency: `2000ms` (aggressive for SSD)
   - Tab unload: `20` tabs (8GB RAM limit)
   - Media: 60fps webcam (`media.getusermedia.camera.off_while_disabled.delay_ms = 0`)
   - Hardware decode: H.264-only (synced with `01.MEDIA`)
   - **Verification:** `about:memory` GC frequency, `about:support` media capabilities

5. **Privacy Hardening**
   - Referrer policy: `strict-origin-when-cross-origin`
   - Fingerprinting resistance (partial — not full Tor mode)
   - Cookie/storage isolation
   - **Verification:** Browser console should show no unexpected cross-origin requests

**Critical Settings:**

```javascript
// Password persistence (DO NOT CHANGE — see 05.PREFS)
user_pref("browser.sessionstore.privacy_level", 0);

// Hardware-only media decode (synced with 01.MEDIA)
user_pref("media.hardware-video-decoding.enabled", true);
user_pref("media.hardware-video-decoding.force-enabled", true);
user_pref("media.ffmpeg.vaapi.enabled", true);

// 60fps webcam (this hardware supports it)
user_pref("media.getusermedia.camera.off_while_disabled.delay_ms", 0);

// Aggressive GC for SSD (8GB RAM)
user_pref("javascript.options.mem.gc_incremental_slice_ms", 2000);

// Tab unload threshold (8GB RAM)
user_pref("browser.tabs.unloadOnLowMemory", true);
user_pref("browser.low_commit_space_threshold_mb", 2048);
```

---

## Chronological History

### Phase 1: Scattered Overrides (Pre-2026-07-05)
- Multiple `user.js` files existed in different locations
- `05.PREFS` contained a duplicate (caused overwrite races)
- `Surgical_Patches_V2/` folder had an older variant (30fps webcam cap, "forget logins")
- No clear "canonical" version

### Phase 2: Consolidation (2026-07-05)
- **Decision:** Consolidate into single authoritative profile
- **Action:** Created `10.OVERRIDES/user.js` as canonical source
- **Versioning:** Named "v2.0 — Kernel-Synced Braveheart"
- **Tuning:** Updated for current kernel (6.12.6), hardware, and build
- **Cleanup:** Removed duplicate from `05.PREFS` (per `MAP.md`)

### Phase 3: Quarantine of Stale Copy (2026-07-06)
- **Discovery:** `Surgical_Patches_V2/` contained outdated variant
- **Issues:** 30fps webcam cap (should be 60fps), `privacy_level=2` (breaks password persistence)
- **Action:** Quarantined stale copy to prevent accidental use
- **Documentation:** This roadmap written to establish canonical status

### Phase 4: IBM Format Transformation (2026-07-07)
- **Action:** Transformed documentation to IBM-quality format
- **Added:** Document control, executive summary, verification procedures
- **Cross-referenced:** Dependencies with other categories
- **Status:** Production-ready, canonical

---

## Validation & Verification

### Pre-Deployment Checks

1. **Syntax Validation**
   ```bash
   # Verify JavaScript syntax (should exit 0)
   node -c 10.OVERRIDES/user.js
   ```

2. **Duplicate Detection**
   ```bash
   # Ensure no other user.js exists in workspace
   find /home/gorilla/Documents/FIrefox.154.Work -name "user.js" -type f
   # Should return ONLY: 10.OVERRIDES/user.js
   ```

3. **Cross-Category Consistency**
   ```bash
   # Media prefs should match 01.MEDIA
   grep "media.hardware-video-decoding" 10.OVERRIDES/user.js
   grep "media.ffmpeg.vaapi" 10.OVERRIDES/user.js
   
   # Session restore should match 05.PREFS
   grep "browser.sessionstore.privacy_level" 10.OVERRIDES/user.js
   # Should be: user_pref("browser.sessionstore.privacy_level", 0);
   ```

### Post-Deployment Verification

1. **Profile Presence**
   ```bash
   # Verify file was copied to runtime profile
   ls -lh ~/.mozilla/firefox/*.default-release/user.js
   ```

2. **Effective Preferences**
   - Navigate to `about:config`
   - Search for key prefs (e.g., `app.normandy.enabled`)
   - Verify they match `user.js` values
   - Check "Status" column — should show "user set" (not "default")

3. **Telemetry Verification**
   - Navigate to `about:telemetry`
   - Should display: "Telemetry is not recording"
   - No data collection sections should be populated

4. **AI Feature Absence**
   - Check toolbar for AI icons (should be none)
   - Open sidebar (Ctrl+B) — no AI/chatbot options
   - Address bar should not show ML-based suggestions

5. **Media Capabilities**
   - Navigate to `about:support`
   - Search for "Media" section
   - Verify: `HARDWARE_VIDEO_DECODING: available`
   - Verify: `VAAPI: available` (Linux only)

6. **Network Idle State**
   - Navigate to `about:networking`
   - Check "HTTP" tab — should show minimal idle connections
   - No connections to `normandy.cdn.mozilla.net`, `shavar.services.mozilla.com`

### Runtime Monitoring

```bash
# Monitor preference changes during session
tail -f ~/.mozilla/firefox/*.default-release/prefs.js | grep -E "(normandy|telemetry|experiment)"
# Should show no changes (prefs stay as set by user.js)
```

---

## Invariants (Do Not Break)

### Critical Invariants

1. **Single Canonical Source**
   - This file is the **ONLY** runtime `user.js`
   - Do NOT reintroduce duplicates in `05.PREFS` or elsewhere
   - Stale `Surgical_Patches_V2/` copy must remain quarantined

2. **Password Persistence**
   ```javascript
   user_pref("browser.sessionstore.privacy_level", 0);
   ```
   - Must stay `0` (allows password persistence)
   - See `05.PREFS` for rationale (deliberate choice, not oversight)

3. **Media Hardware Decode**
   - Keep synced with `01.MEDIA` (H.264-only, hardware-forced)
   - 60fps webcam setting must match hardware capability
   - Do NOT revert to 30fps cap from stale copy

4. **Telemetry Consistency**
   - All telemetry prefs must match `03.NETWORKING` lobotomy
   - Normandy/Nimbus prefs redundantly disabled (primary kill in `12.MOZAMBIQUE.DRILL`)

5. **GC/Memory Tuning**
   - Settings assume SSD + 8GB RAM + fast CPU
   - Do NOT copy to slower hardware without adjustment

### Deployment Invariants

1. **Deploy Script**
   - `deploy.sh` must copy this file to runtime profile
   - Must NOT copy any other `user.js` variant
   - Must preserve file permissions (readable by browser process)

2. **Policy Precedence**
   - This file **cannot** override `policies.json` locked prefs
   - Do NOT attempt to override `12.MOZAMBIQUE.DRILL` locks here
   - Redundant disables are acceptable (defense-in-depth)

---

## Open Items & Roadmap

### High Priority

- [ ] **Periodic Diff Against Defaults**
  - Diff `user.js` against `05.PREFS/StaticPrefList.yaml` defaults
  - Identify prefs that no longer need overriding (upstream default changed)
  - Remove redundant overrides to reduce maintenance burden
  - **Frequency:** Quarterly or after major Firefox updates

- [ ] **Effective Prefs Report**
  - Generate annotated "last-wins" report for audit
  - Show which prefs come from defaults, user.js, or policies
  - Useful for debugging unexpected behavior
  - **Tool:** Could use `about:config` export + annotation script

### Medium Priority

- [ ] **Cross-Link AI Removal**
  - Map AI-removal prefs to their source patches in `07.TOOLKIT`
  - Document which prefs disable which UI components
  - Useful for understanding what each pref actually does

- [ ] **Cross-Link Telemetry**
  - Map telemetry prefs to network endpoints in `03.NETWORKING`
  - Verify no telemetry prefs are missing from either layer
  - Ensure defense-in-depth coverage

- [ ] **Performance Tuning Validation**
  - Benchmark GC frequency impact (2000ms vs defaults)
  - Measure tab unload threshold effectiveness (20 tabs)
  - Validate memory pressure thresholds for 8GB RAM

### Low Priority

- [ ] **Portability Assessment**
  - Document which settings are hardware-specific
  - Create "portable" variant for different hardware
  - Useful if build moves to different machine

- [ ] **Automated Testing**
  - Script to verify critical prefs after deployment
  - Alert if any critical pref reverts to default
  - Could run as post-launch check

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
- **Media:** Hardware H.264 decode only (no software fallback)
- **Network:** Telemetry lobotomy, BBR congestion control
- **Remote:** Normandy/Nimbus neutralized (cannot be remotely controlled)

**Why This Matters for Overrides:**
- GC/memory settings assume SSD (fast I/O) + 8GB RAM
- Tab unload thresholds tuned for 8GB limit
- Media prefs assume HD 4000 VAAPI capability
- Aggressive background task suppression assumes always-on power

**Portability Warning:** These settings are **NOT** safe for:
- Machines with <8GB RAM (tab unload too aggressive)
- HDDs (GC frequency too high, causes I/O thrashing)
- Older GPUs without VAAPI (media decode will fail)
- Battery-powered laptops (background suppression too aggressive)

---

## Cross-References

### Dependencies (Upstream)

1. **05.PREFS (Build-Time Defaults)**
   - This file overrides defaults set in `StaticPrefList.yaml`, `firefox.js`, `all.js`
   - Must stay consistent with `browser.sessionstore.privacy_level` rationale
   - See: `05.PREFS/00_PREFS_HISTORY_AND_ROADMAP.md`

2. **12.MOZAMBIQUE.DRILL (Policy Locks)**
   - Policy-locked prefs **cannot** be overridden by this file
   - Normandy/Nimbus prefs redundantly disabled here (defense-in-depth)
   - See: `12.MOZAMBIQUE.DRILL/00_MOZAMBIQUE_DRILL_HISTORY_AND_ROADMAP.md`

### Dependencies (Peer)

1. **01.MEDIA (Hardware Decode)**
   - Media prefs must match hardware-only H.264 configuration
   - 60fps webcam setting must match hardware capability
   - See: `01.MEDIA/00_MEDIA_HISTORY_AND_ROADMAP.md`

2. **03.NETWORKING (Telemetry Lobotomy)**
   - Telemetry prefs must match network-level blocks
   - Speculative connection prefs must match network tuning
   - See: `03.NETWORKING/00_NETWORKING_HISTORY_AND_ROADMAP.md`

3. **07.TOOLKIT (AI/Addon Lockdown)**
   - AI removal prefs must match UI component patches
   - Addon install prefs must match sealed-appliance model
   - See: `07.TOOLKIT/00_TOOLKIT_HISTORY_AND_ROADMAP.md`

### Related Documentation

- **MAP.md** — Documents decision to consolidate into single `user.js`
- **deploy.sh** — Deployment script that copies this file to runtime profile
- **user.js (in-file header)** — Detailed plain-English annotations for each section

---

## Troubleshooting

### Problem: Preferences Not Taking Effect

**Symptoms:**
- Settings in `user.js` don't appear in `about:config`
- Browser behavior doesn't match expected configuration

**Diagnosis:**
```bash
# Check if file was deployed
ls -lh ~/.mozilla/firefox/*.default-release/user.js

# Check for syntax errors
node -c 10.OVERRIDES/user.js

# Check browser console for pref errors
# (Open browser, Ctrl+Shift+J, look for "user.js" errors)
```

**Solutions:**
1. **File Not Deployed:** Run `deploy.sh` to copy file to profile
2. **Syntax Error:** Fix JavaScript syntax (missing semicolon, quote mismatch)
3. **Policy Override:** Check if pref is locked in `12.MOZAMBIQUE.DRILL/policies.json`
4. **Profile Mismatch:** Verify correct profile is being used (`about:profiles`)

### Problem: Telemetry Still Active

**Symptoms:**
- `about:telemetry` shows "Telemetry is recording"
- Network connections to Mozilla telemetry servers

**Diagnosis:**
```bash
# Check telemetry prefs in user.js
grep -i telemetry 10.OVERRIDES/user.js

# Check effective prefs in browser
# Navigate to about:config, search "telemetry"
```

**Solutions:**
1. **Pref Not Set:** Verify all telemetry prefs are in `user.js`
2. **Policy Override:** Check `12.MOZAMBIQUE.DRILL` for conflicting locks
3. **Network Block:** Verify `03.NETWORKING` telemetry lobotomy is active
4. **Restart Required:** Close all browser windows and restart

### Problem: Password Persistence Broken

**Symptoms:**
- Browser forgets passwords on restart
- Login forms don't auto-fill

**Diagnosis:**
```bash
# Check privacy_level setting
grep "browser.sessionstore.privacy_level" 10.OVERRIDES/user.js
# Should be: user_pref("browser.sessionstore.privacy_level", 0);
```

**Solutions:**
1. **Wrong Value:** Ensure `privacy_level` is `0` (not `2`)
2. **Stale Copy:** Verify not using old `Surgical_Patches_V2` variant
3. **Policy Override:** Check `12.MOZAMBIQUE.DRILL` for conflicting lock
4. **See:** `05.PREFS/00_PREFS_HISTORY_AND_ROADMAP.md` for rationale

### Problem: Media Playback Fails

**Symptoms:**
- Videos don't play or show codec errors
- Webcam doesn't work or limited to 30fps

**Diagnosis:**
```bash
# Check media prefs
grep -E "(hardware-video-decoding|vaapi|getusermedia)" 10.OVERRIDES/user.js

# Check browser capabilities
# Navigate to about:support, search "Media"
```

**Solutions:**
1. **Hardware Decode Disabled:** Verify `media.hardware-video-decoding.force-enabled = true`
2. **VAAPI Missing:** Check `01.MEDIA` patches are applied
3. **Wrong FPS Cap:** Ensure webcam delay is `0` (not `3000` from stale copy)
4. **See:** `01.MEDIA/00_MEDIA_HISTORY_AND_ROADMAP.md` for hardware requirements

### Problem: Performance Issues

**Symptoms:**
- Browser feels sluggish
- High memory usage
- Frequent tab unloading

**Diagnosis:**
```bash
# Check GC/memory settings
grep -E "(gc_incremental|unloadOnLowMemory|low_commit_space)" 10.OVERRIDES/user.js

# Monitor memory in browser
# Navigate to about:memory, click "Measure"
```

**Solutions:**
1. **GC Too Aggressive:** Increase `gc_incremental_slice_ms` (currently 2000ms)
2. **Tab Unload Too Eager:** Increase `low_commit_space_threshold_mb` (currently 2048MB)
3. **Wrong Hardware:** These settings assume SSD + 8GB RAM + fast CPU
4. **See:** Build Target section for hardware requirements

### Problem: Duplicate user.js Files

**Symptoms:**
- Multiple `user.js` files found in workspace
- Unclear which is canonical

**Diagnosis:**
```bash
# Find all user.js files
find /home/gorilla/Documents/FIrefox.154.Work -name "user.js" -type f
```

**Solutions:**
1. **Remove Duplicates:** Only `10.OVERRIDES/user.js` should exist
2. **Quarantine Stale:** Move old copies to `Agents.Work.Trash/`
3. **Update Deploy:** Ensure `deploy.sh` only copies canonical version
4. **See:** MAP.md for consolidation rationale

---

## Security Considerations

### Threat Model

**What This Protects Against:**
- **Remote Profiling:** Telemetry disabled, no behavior data sent to Mozilla
- **Experiment Manipulation:** Normandy/Nimbus disabled (redundant with `12.MOZAMBIQUE.DRILL`)
- **Background Surveillance:** Speculative connections, prefetch, idle tasks suppressed
- **AI Data Collection:** ML features disabled, no local model training

**What This Does NOT Protect Against:**
- **Network-Level Tracking:** See `03.NETWORKING` for DNS/TLS hardening
- **Fingerprinting:** Partial resistance only (not full Tor Browser mode)
- **Malicious Extensions:** See `07.TOOLKIT` for addon install lockdown
- **Physical Access:** No disk encryption or secure boot (OS-level concern)

### Defense-in-Depth Layers

1. **Build-Time Defaults** (`05.PREFS`)
   - First line of defense, baked into binary
   - Survives profile reset

2. **Runtime Overrides** (THIS FILE)
   - Second line, applied on every launch
   - Survives pref reset via UI

3. **Policy Locks** (`12.MOZAMBIQUE.DRILL`)
   - Third line, cannot be overridden
   - Survives malicious extension or remote command

4. **Network Blocks** (`03.NETWORKING`)
   - Fourth line, blocks at socket level
   - Survives pref manipulation

### Audit Trail

**Verification Commands:**
```bash
# Generate effective prefs snapshot
firefox --headless --screenshot /dev/null 2>&1 | grep "user_pref"

# Compare against canonical user.js
diff <(grep "user_pref" 10.OVERRIDES/user.js | sort) \
     <(grep "user_pref" ~/.mozilla/firefox/*.default-release/prefs.js | sort)

# Check for unexpected network connections
ss -tunap | grep firefox
```

**Monitoring:**
- Browser console (Ctrl+Shift+J) for pref errors
- `about:networking` for unexpected connections
- `about:telemetry` for data collection status

---

## Appendix: Version History

### v2.0 — Kernel-Synced Braveheart (2026-07-05)
- **Status:** Current canonical version
- **Changes:**
  - Consolidated from multiple scattered files
  - Updated for kernel 6.12.6 + current hardware
  - 60fps webcam (was 30fps in old variant)
  - Password persistence enabled (`privacy_level=0`)
  - Aggressive GC tuning for SSD
  - Comprehensive telemetry/AI removal
- **Lines:** ~1121

### v1.x — Surgical Patches V2 (Pre-2026-07-05, QUARANTINED)
- **Status:** Obsolete, do not use
- **Issues:**
  - 30fps webcam cap (should be 60fps)
  - `privacy_level=2` (breaks password persistence)
  - Outdated kernel tuning
  - Scattered across multiple locations
- **Fate:** Quarantined 2026-07-06

---

## Document Metadata

**Author:** Gorilla (with Bob Shell assistance)  
**Philosophy:** Gorilla Open Source Philosophy — honest documentation (state limitations, not just wins)  
**Format:** IBM-quality dual-track (Track A: plain language, Track B: technical)  
**Audience:** Primary = future maintainer (likely author), Secondary = technical auditor  
**Maintenance:** Update after major Firefox releases, kernel changes, or hardware upgrades  
**Related:** Part of Firefox 154 custom build documentation suite

**Change Log:**
- 2026-07-06: Initial dual-track documentation
- 2026-07-07: Transformed to IBM-quality format with comprehensive verification procedures

---

**END OF DOCUMENT**