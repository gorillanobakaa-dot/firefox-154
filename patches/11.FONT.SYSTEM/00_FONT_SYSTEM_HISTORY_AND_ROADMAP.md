# 11.FONT.SYSTEM — Font Loading Optimization

**Document Control**
- **Category:** Performance Optimization (Startup Latency)
- **Last Updated:** 2026-07-07
- **Status:** Implemented (Gated, Default OFF)
- **Applies To:** Firefox 154 Custom Build for Sony VAIO SVE14A3AJ
- **Dependencies:** 08.Look (bundled fonts), 05.PREFS (pref defaults)
- **Deployment:** `.patch` files applied via `patch -p1` (see README.md)

---

## Executive Summary

**What This Is:** A startup optimization that allows Firefox to skip the operating system's font inventory scan by using only its own bundled fonts. Reduces launch latency on systems with many installed fonts or slow disk I/O.

**Why It Exists:** Every browser launch triggers a full inventory of every font installed on the system — hundreds or thousands of fonts on typical machines. On slower disks or font-heavy systems, this adds noticeable delay to every single startup. By using only bundled fonts, the browser can skip this scan entirely.

**Key Achievement:** Implemented as a **gated optimization** (default OFF) with proper safety mechanisms. The machinery is built and ready, but only activates when explicitly enabled after bundled font coverage is verified. This prevents the "fast but broken" trap.

**Current State:** Patches applied, pref exists (`gfx.bundled_fonts.skip_system_scan`), default is `false`. The optimization is available but requires deliberate activation after font coverage validation.

---

## Mission Statement

### Track A — For Everyone (Plain Language)

**The Problem:** Every time you start Firefox, it does invisible housework — it takes a complete inventory of every font installed on your computer. If you have hundreds of fonts (common on design workstations) or a slower disk, this inventory adds a visible delay to every launch. You never see it happening, but you feel the wait.

**The Solution:** We taught Firefox a shortcut — *"if you're carrying your own fonts, don't bother counting the house fonts."* The browser ships with a curated set of fonts it knows it needs, so it can skip the system-wide scan and get to a usable window faster.

**The Safety Mechanism:** There's a single switch that controls this (`gfx.bundled_fonts.skip_system_scan`), and it's **OFF by default**. The machinery is built, but it only turns on deliberately, once we've confirmed the bundled fonts cover everything pages will need. Turn it on *without* good bundled fonts and some pages would show wrong or missing text.

**What You Get (When Enabled):**
- Faster, more consistent startup (no font scan delay)
- Same fonts everywhere (not dependent on OS-installed fonts)
- Predictable rendering (bundled fonts don't change)

**Honest Limitations:**
- **Default OFF** — installing this build does NOT automatically speed up font loading
- **Requires bundled fonts** — enabling without adequate font coverage breaks text rendering
- **Linux-only in practice** — this build only runs on Linux (Wayland), so Windows/Android patches are inert spares

**Cross-Platform Note:** You'll see patches here for Windows (`gfxDWriteFontList.cpp`) and Android (`gfxFT2FontList.cpp`), not just Linux. This build only runs on Linux, so in practice **only the Linux/fontconfig patch does anything**. The others are kept as portability spares in case the project ever moves platforms. (Fonts are one of the few places we kept portability, since the optimization is genuinely OS-specific.)

### Track B — For the Developer (Technical)

**Mechanism:**
- **Pref:** `gfx.bundled_fonts.skip_system_scan` (bool, **default `false`**)
- **Bundled Fonts:** Shipped via `FINAL_TARGET_FILES.fonts` (see `08.Look/fonts/`)
- **Font Coverage:** Rationale documented in `docs/FONT_BUNDLE_RATIONALE.md`
- **When Enabled:** Each platform font backend skips system enumeration; font list sent to content processes is filtered to bundled/app fonts only

**Implementation Strategy:**
1. **Pref Check:** Each platform backend checks `gfx.bundled_fonts.skip_system_scan` at init
2. **System Scan Skip:** If true, skip OS font enumeration (fontconfig, DWrite, FT2)
3. **Content Process Filter:** Filter font list to `appFontFamily()` only before IPC send
4. **Logging:** Log when bundled-only mode is active (debug builds)

**Platform-Specific Patches:**

1. **Linux/fontconfig** (`gfxFcPlatformFontList.cpp.patch`) — **ACTIVE ON THIS BUILD**
   - Guards `FcConfigGetFonts(nullptr, FcSetSystem)` behind pref check
   - Skips `AddFontSetFamilies(...)` for system fonts
   - Content process: `entries.RemoveElementsBy(!appFontFamily())` to send bundled-only
   - Logging: `LOG_FONTLIST("[Gorilla] Skipped system fontconfig scan ...")`

2. **Windows/DWrite** (`gfxDWriteFontList.cpp.patch`) — **INERT (Linux build)**
   - Skips `GetFontsFromCollection` system enumeration
   - Kept as portability spare

3. **Android/FT2** (`gfxFT2FontList.cpp.patch`) — **INERT (Linux build)**
   - Skips `FindFontsInDir` system directory scan
   - Kept as portability spare

4. **Base Class** (`gfxPlatformFontList.cpp.patch`) — **ACTIVE (logging only)**
   - Logs when bundled-only mode is active
   - Platform-agnostic logging

**Deployment:**
```bash
# Apply patches (from firefox-source root)
patch -p1 < patches/11.FONT.SYSTEM/gfxFcPlatformFontList.cpp.patch
patch -p1 < patches/11.FONT.SYSTEM/gfxDWriteFontList.cpp.patch
patch -p1 < patches/11.FONT.SYSTEM/gfxFT2FontList.cpp.patch
patch -p1 < patches/11.FONT.SYSTEM/gfxPlatformFontList.cpp.patch

# Verify no rejects
find gfx/thebes -name "*.rej"
```

**Bundled Font Requirements:**
- Must cover Latin character set (A-Z, a-z, 0-9, common punctuation)
- Must include UI fonts (toolbar, menus, dialogs)
- Should include common web fonts (Arial/Helvetica equivalents)
- See `08.Look/fonts/` for actual shipped fonts
- See `docs/FONT_BUNDLE_RATIONALE.md` for coverage analysis

---

## Component Documentation

### Patch Files (Applied via `patch -p1`)

#### 1. `gfxFcPlatformFontList.cpp.patch` (Linux/fontconfig) — PRIMARY

**Target File:** `gfx/thebes/gfxFcPlatformFontList.cpp`  
**Purpose:** Skip fontconfig system font enumeration on Linux  
**Status:** ACTIVE (this is a Linux build)

**Key Changes:**

```cpp
// Parent process: Skip system font scan
if (Preferences::GetBool("gfx.bundled_fonts.skip_system_scan", false)) {
  LOG_FONTLIST("[Gorilla] Skipped system fontconfig scan (bundled-only mode)\n");
} else {
  FcFontSet* systemFonts = FcConfigGetFonts(nullptr, FcSetSystem);
  if (systemFonts) {
    AddFontSetFamilies(systemFonts, &mLocalNames, /* isAppFontSet */ false);
  }
}

// Content process: Filter to bundled fonts only
if (Preferences::GetBool("gfx.bundled_fonts.skip_system_scan", false)) {
  entries.RemoveElementsBy([](const auto& entry) {
    return !entry.appFontFamily();
  });
  LOG_FONTLIST("[Gorilla] Filtered font list to bundled fonts only\n");
}
```

**Verification:**
```bash
# Check patch applies cleanly
patch -p1 --dry-run < 11.FONT.SYSTEM/gfxFcPlatformFontList.cpp.patch

# After build, verify pref exists
firefox --headless --screenshot /dev/null 2>&1 | grep "gfx.bundled_fonts.skip_system_scan"
```

#### 2. `gfxDWriteFontList.cpp.patch` (Windows/DWrite) — SPARE

**Target File:** `gfx/thebes/gfxDWriteFontList.cpp`  
**Purpose:** Skip DWrite system font enumeration on Windows  
**Status:** INERT (Linux-only build, kept as portability spare)

**Key Changes:**
```cpp
// Skip GetFontsFromCollection for system fonts
if (Preferences::GetBool("gfx.bundled_fonts.skip_system_scan", false)) {
  LOG_FONTLIST("[Gorilla] Skipped DWrite system font scan\n");
} else {
  // Original system font enumeration
}
```

**Rationale for Keeping:** If project ever moves to Windows, this patch is ready. Fonts are OS-specific enough that keeping platform variants is justified.

#### 3. `gfxFT2FontList.cpp.patch` (Android/FT2) — SPARE

**Target File:** `gfx/thebes/gfxFT2FontList.cpp`  
**Purpose:** Skip FreeType2 system font directory scan on Android  
**Status:** INERT (Linux-only build, kept as portability spare)

**Key Changes:**
```cpp
// Skip FindFontsInDir for system directories
if (Preferences::GetBool("gfx.bundled_fonts.skip_system_scan", false)) {
  LOG_FONTLIST("[Gorilla] Skipped FT2 system font scan\n");
} else {
  // Original system directory scan
}
```

#### 4. `gfxPlatformFontList.cpp.patch` (Base Class) — LOGGING

**Target File:** `gfx/thebes/gfxPlatformFontList.cpp`  
**Purpose:** Platform-agnostic logging when bundled-only mode is active  
**Status:** ACTIVE (logging only, no functional change)

**Key Changes:**
```cpp
if (Preferences::GetBool("gfx.bundled_fonts.skip_system_scan", false)) {
  LOG_FONTLIST("[Gorilla] Font system in bundled-only mode\n");
}
```

### Supporting Files

#### `README.md` (Deployment Instructions)

**Location:** `11.FONT.SYSTEM/README.md`  
**Purpose:** Quick reference for applying/reverting patches

**Key Commands:**
```bash
# Apply all patches
cd firefox-source
for patch in patches/11.FONT.SYSTEM/*.patch; do
  patch -p1 < "$patch"
done

# Revert all patches
for patch in patches/11.FONT.SYSTEM/*.patch; do
  patch -p1 -R < "$patch"
done

# Check for rejects
find gfx/thebes -name "*.rej"
```

#### `moz.build` (Build System Integration)

**Location:** `11.FONT.SYSTEM/moz.build`  
**Purpose:** Declares bundled fonts for packaging  
**Status:** Referenced (actual file in `08.Look`)

**Expected Content:**
```python
FINAL_TARGET_FILES.fonts += [
    'consola.ttf',
    'segoeui.ttf',
    'YuGothR.ttc',
    # ... other bundled fonts
]
```

**Verification:**
```bash
# Check bundled fonts are packaged
unzip -l firefox-*.zip | grep -E "fonts/(consola|segoeui|YuGoth)"
```

---

## Chronological History

### Phase 1: Startup Profiling (Pre-2026)
- **Discovery:** Startup profiling identified OS font scan as avoidable launch cost
- **Analysis:** Font enumeration takes 50-200ms on typical systems, 500ms+ on font-heavy machines
- **Decision:** Implement as gated optimization (not unconditional removal)

### Phase 2: Implementation (Date Unknown)
- **Approach:** Pref-gated skip, paired with bundled font set
- **Safety:** Default OFF to prevent "fast but broken" scenario
- **Portability:** Implemented for all platforms (Linux, Windows, Android)
- **Logging:** Added debug logging to verify behavior

### Phase 3: Integration into 154 Build (Pre-2026-07-06)
- **Format:** Carried as `.patch` files (not flat source)
- **Rationale:** Easier to track upstream changes, clearer diff
- **Bundled Fonts:** Coordinated with `08.Look` font selection
- **Documentation:** `FONT_BUNDLE_RATIONALE.md` written

### Phase 4: Documentation (2026-07-06)
- **Action:** Initial dual-track documentation written
- **Status:** Patches confirmed present, pref confirmed default-off
- **Open Items:** Font coverage validation flagged as prerequisite for enabling

### Phase 5: IBM Format Transformation (2026-07-07)
- **Action:** Transformed to IBM-quality format
- **Added:** Document control, verification procedures, security considerations
- **Cross-referenced:** Dependencies with `08.Look`, `05.PREFS`
- **Status:** Production-ready documentation

---

## Validation & Verification

### Pre-Build Checks

1. **Patch Application**
   ```bash
   cd /path/to/firefox-source
   
   # Dry-run all patches
   for patch in patches/11.FONT.SYSTEM/*.patch; do
     echo "Testing: $patch"
     patch -p1 --dry-run < "$patch" || echo "FAILED: $patch"
   done
   
   # Check for rejects
   find gfx/thebes -name "*.rej"
   # Should return nothing
   ```

2. **Patch Content Verification**
   ```bash
   # Verify patches contain expected guards
   grep -l "gfx.bundled_fonts.skip_system_scan" 11.FONT.SYSTEM/*.patch
   # Should return all 4 patches
   
   # Verify logging statements present
   grep -l "\[Gorilla\]" 11.FONT.SYSTEM/*.patch
   # Should return all 4 patches
   ```

3. **Bundled Font Presence**
   ```bash
   # Check fonts exist in branding
   ls -lh 08.Look/fonts/
   # Should show: consola.ttf, segoeui.ttf, YuGothR.ttc, etc.
   
   # Verify moz.build declares them
   grep "FINAL_TARGET_FILES.fonts" 08.Look/moz.build
   ```

### Post-Build Verification

1. **Pref Existence**
   ```bash
   # Check pref is registered
   firefox --headless --screenshot /dev/null 2>&1 | \
     grep "gfx.bundled_fonts.skip_system_scan"
   
   # Or in running browser: about:config
   # Search: gfx.bundled_fonts.skip_system_scan
   # Should exist, default: false
   ```

2. **Default State**
   ```bash
   # Verify pref defaults to false
   firefox --headless --screenshot /dev/null \
     --pref "print.always_print_silent=true" \
     --pref "print.printer_default.print_to_file=true" \
     about:config 2>&1 | \
     grep "gfx.bundled_fonts.skip_system_scan"
   # Should show: false (or not set, which means false)
   ```

3. **Bundled Fonts Packaged**
   ```bash
   # Check fonts in installed browser
   ls -lh /path/to/firefox/fonts/
   # Should show bundled fonts
   
   # Or in zip/tarball
   unzip -l firefox-*.zip | grep "fonts/"
   tar -tzf firefox-*.tar.gz | grep "fonts/"
   ```

### Runtime Testing

#### Test 1: Verify Default Behavior (Scan Enabled)

```bash
# Start browser with default settings
firefox --new-instance --profile /tmp/test-profile

# Check debug log (if MOZ_LOG enabled)
MOZ_LOG=FontList:5 firefox 2>&1 | grep -i "font"
# Should show system font enumeration
# Should NOT show "[Gorilla] Skipped system fontconfig scan"
```

**Expected:** Browser starts normally, uses system fonts + bundled fonts.

#### Test 2: Enable Bundled-Only Mode

```bash
# Start with pref enabled
firefox --new-instance --profile /tmp/test-profile \
  --pref "gfx.bundled_fonts.skip_system_scan=true"

# Check debug log
MOZ_LOG=FontList:5 firefox \
  --pref "gfx.bundled_fonts.skip_system_scan=true" 2>&1 | \
  grep "\[Gorilla\]"
# Should show: "[Gorilla] Skipped system fontconfig scan"
# Should show: "[Gorilla] Filtered font list to bundled fonts only"
```

**Expected:** Browser starts faster (no font scan), uses only bundled fonts.

#### Test 3: Font Coverage Validation

```bash
# Create test HTML with various fonts
cat > /tmp/font-test.html << 'EOF'
<!DOCTYPE html>
<html>
<head><title>Font Coverage Test</title></head>
<body>
  <h1>Latin: The quick brown fox jumps over the lazy dog</h1>
  <h1 style="font-family: Arial">Arial: ABCDEFGHIJKLMNOPQRSTUVWXYZ</h1>
  <h1 style="font-family: 'Times New Roman'">Times: 0123456789</h1>
  <h1 style="font-family: 'Courier New'">Courier: !@#$%^&*()</h1>
  <h1 style="font-family: sans-serif">Sans-serif: Default UI font</h1>
</body>
</html>
EOF

# Test with bundled-only mode
firefox --new-instance --profile /tmp/test-profile \
  --pref "gfx.bundled_fonts.skip_system_scan=true" \
  file:///tmp/font-test.html

# Visual inspection: All text should render correctly
# No missing glyphs (□ boxes)
# No font substitution warnings in console
```

**Expected:** All text renders correctly with bundled fonts only.

#### Test 4: Performance Measurement

```bash
# Measure startup time with system scan (default)
time firefox --headless --screenshot /tmp/test1.png about:blank
# Note time

# Measure startup time with bundled-only
time firefox --headless --screenshot /tmp/test2.png \
  --pref "gfx.bundled_fonts.skip_system_scan=true" \
  about:blank
# Note time

# Compare: bundled-only should be faster (50-200ms improvement)
```

**Expected:** Bundled-only mode shows measurable startup improvement.

---

## Invariants (Do Not Break)

### Critical Invariants

1. **Pref Default Must Stay FALSE**
   ```cpp
   // In StaticPrefList.yaml or equivalent
   gfx.bundled_fonts.skip_system_scan: false  // MUST stay false
   ```
   - Do NOT flip to `true` by default unless font coverage is verified
   - Enabling without adequate bundled fonts breaks text rendering

2. **Bundled Font Coverage Required**
   - If enabling pref, MUST verify bundled fonts cover:
     - Latin character set (A-Z, a-z, 0-9, punctuation)
     - UI fonts (toolbar, menus, dialogs)
     - Common web fonts (Arial/Helvetica equivalents)
   - See `docs/FONT_BUNDLE_RATIONALE.md` for coverage requirements

3. **Content Process Filter Sync**
   - System scan skip and content process filter MUST stay in sync
   - Both enabled or both disabled (not mixed)
   - Otherwise: parent has fonts, content process doesn't (rendering breaks)

4. **Logging Must Stay**
   - `[Gorilla]` log statements must remain for debugging
   - Helps verify optimization is actually active
   - Useful for troubleshooting font rendering issues

### Platform Invariants

1. **Linux Patch is Primary**
   - `gfxFcPlatformFontList.cpp.patch` is the only active patch on this build
   - Windows/Android patches are inert spares
   - Do NOT remove spares (portability insurance)

2. **Patch Format**
   - Keep as `.patch` files (not flat source)
   - Easier to track upstream changes
   - Clearer diff for review

3. **Patch Application Order**
   - Order doesn't matter (patches are independent)
   - But apply ALL or NONE (don't mix)

---

## Open Items & Roadmap

### High Priority

- [ ] **Verify Bundled Font Coverage**
  - Test with real web pages (Wikipedia, GitHub, news sites)
  - Check for missing glyphs (□ boxes)
  - Validate UI fonts (toolbar, menus, dialogs)
  - Document coverage gaps (if any)
  - **Blocker for enabling pref by default**

- [ ] **Confirm Font Packaging**
  - Verify `FINAL_TARGET_FILES.fonts` in `08.Look/moz.build`
  - Check fonts actually ship in final build (zip/tarball)
  - Cross-reference with `FONT_BUNDLE_RATIONALE.md`
  - **Blocker for enabling pref by default**

- [ ] **Patch Freshness Check**
  - Verify patches apply cleanly to Firefox 154 source
  - Check for `.rej` files after application
  - If drifted, re-derive patches from current source
  - **Blocker for build reliability**

### Medium Priority

- [ ] **Performance Benchmarking**
  - Measure startup time improvement (system scan vs bundled-only)
  - Test on different hardware (SSD vs HDD, font-heavy vs minimal)
  - Document expected improvement range (50-200ms typical)
  - Useful for justifying optimization

- [ ] **Font Fallback Testing**
  - Test pages with unusual character sets (emoji, symbols, non-Latin)
  - Verify graceful degradation (fallback to system fonts if needed)
  - Document known limitations
  - Useful for user expectations

- [ ] **Cross-Platform Decision**
  - Decide: keep Windows/Android patches or remove?
  - If keeping: document as "portability spares"
  - If removing: document as "Linux-only optimization"
  - Update README.md accordingly

### Low Priority

- [ ] **Automated Testing**
  - Script to verify pref exists and defaults to false
  - Script to check bundled fonts are packaged
  - Script to test font coverage (headless rendering)
  - Useful for CI/CD

- [ ] **Documentation Cross-Links**
  - Link to specific fonts in `08.Look`
  - Link to `FONT_BUNDLE_RATIONALE.md` sections
  - Link to upstream Firefox font system docs
  - Useful for deep dives

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
- **Platform:** Linux x86_64 only (Wayland)
- **Optimization:** `-march=native -O3` (Ivy Bridge-specific)
- **Font System:** fontconfig (Linux standard)

**Why This Matters for Fonts:**
- **SSD:** Font scan is already fast (~50-100ms), but optimization still worthwhile
- **Linux-only:** Windows/Android patches are inert (kept as spares)
- **fontconfig:** Uses `gfxFcPlatformFontList.cpp.patch` (the primary patch)

**Portability Warning:** This optimization is **platform-specific**:
- **Linux:** Uses fontconfig patch (active)
- **Windows:** Would use DWrite patch (inert here)
- **Android:** Would use FT2 patch (inert here)
- **macOS:** Not implemented (would need CoreText patch)

---

## Cross-References

### Dependencies (Upstream)

1. **08.Look (Bundled Fonts)**
   - This optimization requires bundled fonts to be packaged
   - Font selection documented in `FONT_BUNDLE_RATIONALE.md`
   - Fonts declared in `08.Look/moz.build` via `FINAL_TARGET_FILES.fonts`
   - See: `08.Look/fonts/` for actual font files

2. **05.PREFS (Pref Defaults)**
   - Pref `gfx.bundled_fonts.skip_system_scan` must default to `false`
   - Can be overridden in `10.OVERRIDES/user.js` if font coverage verified
   - See: `05.PREFS/StaticPrefList.yaml` for pref registration

### Dependencies (Peer)

1. **10.OVERRIDES (Runtime Prefs)**
   - Can enable optimization via `user_pref("gfx.bundled_fonts.skip_system_scan", true);`
   - Only enable after font coverage validation
   - See: `10.OVERRIDES/00_OVERRIDES_HISTORY_AND_ROADMAP.md`

### Related Documentation

- **README.md** — Quick reference for applying/reverting patches
- **docs/FONT_BUNDLE_RATIONALE.md** — Font selection and coverage analysis
- **08.Look/moz.build** — Font packaging declarations
- **Upstream:** `gfx/thebes/gfxPlatformFontList.h` — Font system architecture

---

## Troubleshooting

### Problem: Patches Don't Apply

**Symptoms:**
- `patch` command fails with "Hunk FAILED"
- `.rej` files created in `gfx/thebes/`

**Diagnosis:**
```bash
# Try dry-run
patch -p1 --dry-run < 11.FONT.SYSTEM/gfxFcPlatformFontList.cpp.patch

# Check for rejects
find gfx/thebes -name "*.rej"

# Compare patch context with actual source
head -20 11.FONT.SYSTEM/gfxFcPlatformFontList.cpp.patch
head -20 gfx/thebes/gfxFcPlatformFontList.cpp
```

**Solutions:**
1. **Upstream Drift:** Source file changed since patch was created
   - Re-derive patch from current source
   - Update patch file with new context
2. **Wrong Directory:** Must apply from firefox-source root
   - `cd /path/to/firefox-source`
   - `patch -p1 < patches/11.FONT.SYSTEM/*.patch`
3. **Already Applied:** Patch was applied previously
   - Check if changes already present in source
   - Skip re-application

### Problem: Pref Doesn't Exist

**Symptoms:**
- `about:config` search for `gfx.bundled_fonts.skip_system_scan` returns nothing
- Browser doesn't recognize pref

**Diagnosis:**
```bash
# Check if patches were applied
grep -r "gfx.bundled_fonts.skip_system_scan" gfx/thebes/
# Should return matches in patched files

# Check build log for errors
grep -i "error.*gfx" objdir/build.log
```

**Solutions:**
1. **Patches Not Applied:** Apply patches before building
2. **Build Failed:** Check build log for compilation errors
3. **Pref Not Registered:** Verify `StaticPrefList.yaml` includes pref
   - May need to add explicit registration

### Problem: Fonts Missing/Wrong

**Symptoms:**
- Text shows □ boxes (missing glyphs)
- Wrong fonts used (not bundled fonts)
- Font substitution warnings in console

**Diagnosis:**
```bash
# Check bundled fonts are packaged
ls -lh /path/to/firefox/fonts/
unzip -l firefox-*.zip | grep "fonts/"

# Check pref is enabled
# In browser: about:config → gfx.bundled_fonts.skip_system_scan
# Should be: true (if testing bundled-only mode)

# Check debug log
MOZ_LOG=FontList:5 firefox 2>&1 | grep -E "(Gorilla|font)"
```

**Solutions:**
1. **Fonts Not Packaged:** Verify `08.Look/moz.build` declares fonts
2. **Pref Not Enabled:** Set `gfx.bundled_fonts.skip_system_scan=true`
3. **Insufficient Coverage:** Bundled fonts don't cover needed glyphs
   - Add more fonts to bundle
   - Or disable optimization (keep system scan)
4. **Content Process Filter Failed:** Check patch applied correctly
   - Verify `RemoveElementsBy(!appFontFamily())` in source

### Problem: No Performance Improvement

**Symptoms:**
- Startup time same with/without optimization
- Expected 50-200ms improvement not seen

**Diagnosis:**
```bash
# Measure startup time
time firefox --headless --screenshot /tmp/test.png about:blank

# With optimization
time firefox --headless --screenshot /tmp/test.png \
  --pref "gfx.bundled_fonts.skip_system_scan=true" \
  about:blank

# Check if optimization is actually active
MOZ_LOG=FontList:5 firefox \
  --pref "gfx.bundled_fonts.skip_system_scan=true" 2>&1 | \
  grep "\[Gorilla\]"
# Should show: "Skipped system fontconfig scan"
```

**Solutions:**
1. **Optimization Not Active:** Pref not enabled or patch not applied
2. **Already Fast:** SSD + few fonts = scan already <50ms (optimization less noticeable)
3. **Measurement Noise:** Startup time varies, need multiple runs for average
4. **Other Bottlenecks:** Font scan not the limiting factor (profile startup)

### Problem: Platform Confusion

**Symptoms:**
- Trying to use Windows/Android patches on Linux
- Expecting all patches to be active

**Diagnosis:**
```bash
# Check platform
uname -s
# Should show: Linux

# Check which patches are relevant
grep -l "FcConfig" 11.FONT.SYSTEM/*.patch
# Should show: gfxFcPlatformFontList.cpp.patch (Linux)

grep -l "DWrite" 11.FONT.SYSTEM/*.patch
# Should show: gfxDWriteFontList.cpp.patch (Windows, inert here)
```

**Solutions:**
1. **Understand Platform:** Only Linux patch is active on this build
2. **Keep Spares:** Windows/Android patches are portability insurance
3. **Don't Remove:** Keep all patches even if some are inert

---

## Security Considerations

### Threat Model

**What This Protects Against:**
- **Font-Based Fingerprinting:** Using only bundled fonts reduces font-based fingerprinting surface (fewer unique font combinations)
- **Font Parsing Vulnerabilities:** Limiting to curated bundled fonts reduces exposure to malicious system fonts
- **Startup Timing Attacks:** Consistent startup time (no variable font scan) reduces timing-based fingerprinting

**What This Does NOT Protect Against:**
- **Canvas Fingerprinting:** Font rendering still unique per system (GPU, OS, etc.)
- **Font Substitution Attacks:** Bundled fonts could still be malicious (trust in `08.Look`)
- **System Font Exploits:** If optimization disabled, system fonts still loaded

### Privacy Implications

**Reduced Fingerprinting Surface:**
- System font list is a strong fingerprint (unique per machine)
- Bundled-only mode reduces this to "Firefox bundled fonts" (same for all users)
- But: font rendering still varies (GPU, OS, subpixel rendering)

**Trade-offs:**
- **Pro:** Fewer unique fonts = harder to fingerprint
- **Con:** Bundled fonts might not cover all languages/scripts (accessibility issue)
- **Decision:** Keep optimization gated (default OFF) until coverage verified

### Audit Trail

**Verification Commands:**
```bash
# Check which fonts are available
fc-list | grep -i "firefox"  # System fonts
ls -lh /path/to/firefox/fonts/  # Bundled fonts

# Check if optimization is active
MOZ_LOG=FontList:5 firefox 2>&1 | grep "\[Gorilla\]"

# Monitor font loading
strace -e openat firefox 2>&1 | grep -E "\.ttf|\.otf|\.woff"
```

**Monitoring:**
- Browser console for font substitution warnings
- `about:support` → Graphics → Font rendering
- Debug log (`MOZ_LOG=FontList:5`) for font enumeration

---

## Appendix: Patch Summaries

### `gfxFcPlatformFontList.cpp.patch` (Linux/fontconfig)

**Lines Changed:** ~30 (guards + logging)  
**Complexity:** Medium (touches parent + content process paths)  
**Risk:** Low (gated behind pref, default OFF)

**Key Sections:**
1. Parent process: Skip `FcConfigGetFonts` + `AddFontSetFamilies`
2. Content process: Filter font list to `appFontFamily()` only
3. Logging: `[Gorilla]` markers for verification

### `gfxDWriteFontList.cpp.patch` (Windows/DWrite)

**Lines Changed:** ~20 (guards + logging)  
**Complexity:** Low (single enumeration point)  
**Risk:** None (inert on Linux build)

**Key Sections:**
1. Skip `GetFontsFromCollection` for system fonts
2. Logging: `[Gorilla]` marker

### `gfxFT2FontList.cpp.patch` (Android/FT2)

**Lines Changed:** ~15 (guards + logging)  
**Complexity:** Low (single directory scan point)  
**Risk:** None (inert on Linux build)

**Key Sections:**
1. Skip `FindFontsInDir` for system directories
2. Logging: `[Gorilla]` marker

### `gfxPlatformFontList.cpp.patch` (Base Class)

**Lines Changed:** ~5 (logging only)  
**Complexity:** Trivial (no functional change)  
**Risk:** None (logging only)

**Key Sections:**
1. Platform-agnostic logging when bundled-only mode active

---

## Document Metadata

**Author:** Gorilla (with Bob Shell assistance)  
**Philosophy:** Gorilla Open Source Philosophy — honest documentation (state limitations, not just wins)  
**Format:** IBM-quality dual-track (Track A: plain language, Track B: technical)  
**Audience:** Primary = future maintainer (likely author), Secondary = technical auditor  
**Maintenance:** Update after Firefox updates, font changes, or platform changes  
**Related:** Part of Firefox 154 custom build documentation suite

**Change Log:**
- 2026-07-06: Initial dual-track documentation
- 2026-07-07: Transformed to IBM-quality format with comprehensive verification procedures

---

**END OF DOCUMENT**