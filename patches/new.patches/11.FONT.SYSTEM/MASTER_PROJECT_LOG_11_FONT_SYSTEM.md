# 11.FONT.SYSTEM — Master Project Log

*Created 2026-08-02 by consolidating this folder's documentation set (merged verbatim below). Policy: one master project log per folder.*


---

# ═══ CONSOLIDATION 2026-08-02 — side documents merged VERBATIM below; originals deleted (recoverable: merged-docs-backup-2026-08-02.tar.gz + git history) ═══


---

# ═══ MERGED DOCUMENT: 11-font-system.AUDIT.md (verbatim · sha256:0172fda4f6dc854b · merged 2026-08-02) ═══

# IBM-Style Audit Report: 11-font-system

## SECTION A: DOCUMENT CONTROL

| Attribute | Value |
|---|---|
| **Target Category** | 11-font-system |
| **Files Scanned** | see payload |
| **Baseline** | Firefox 154 (mozilla-central) |
| **Date / Time** | 2026-07-16 22:44:31 |
| **Audit Status** | PASS |

## SECTION B: EXECUTIVE SUMMARY (Track A — Layman)

A startup optimisation that lets Firefox skip the operating-system font inventory scan and rely only on bundled fonts. Faster launch on any machine with many installed fonts or a slow disk. Gated behind a preference, default OFF, because turning it on without adequate bundled-font coverage would silently break non-Latin text. Ships alongside `get-microsoft-fonts.sh`, the legal acquisition script for the Microsoft fonts this build uses.

## SECTION C: TECHNICAL SUMMARY (Track B — Developer)

Cross-platform gated optimisation: gfx.bundled_fonts.skip_system_scan (bool default false) short-circuits PopulateFontList in gfxFcPlatformFontList / gfxFT2FontList / gfxDWriteFontList / gfxPlatformFontList after registering bundled fonts. Linux/fontconfig path is the only one exercised in this build; Windows/Android patches are documented portability spares. Companion get-microsoft-fonts.sh implements the ttf-ms-win11-auto method (Win11 Enterprise eval ISO → extract sources/install.wim → 7z pull needed fonts) for legal MS-font acquisition. README.fonts.md documents the binary-redistribution caveat.

## SECTION D: DETECTED DEFECTS

*No defects detected by rules or model.*

## SECTION E: PRODUCTION READINESS ASSESSMENT

- **Overall readiness:** 🟡 88%
- **Done:**
  - [x] Four platform paths patched consistently
  - [x] Safety pref default OFF (activation deliberate)
  - [x] browser/fonts/moz.build wires bundled set
  - [x] get-microsoft-fonts.sh implements legal acquisition
  - [x] README.fonts.md explains the use-vs-redistribution EULA line
  - [x] .gitignore excludes *.ttf/*.ttc (with TwemojiMozilla.ttf exception per CC-BY)
- **To Do:**
  - [ ] P2: automated bundled-font coverage test — render Latin/Cyrillic/Arabic/Hebrew/Thai/CJK/emoji corpus using ONLY bundled set, fail on tofu
  - [ ] P2: build-time warning at packaging if MS fonts are present in omni.ja (redistribution reminder)
  - [ ] P3: document the observed startup-time delta measurement on a font-heavy test system

## SECTION F: PHASED EXPANSION PLAN

### Phase 1 — `toolchain-preflight.sh`
- **Tweak:** Add a bundled-font coverage gate that renders the corpus above and reports missing glyphs per bundled font.
- **Expected impact:** Removes the foot-gun of enabling the pref without verifying coverage.

## POSITIVE OBSERVATIONS

- ✅ Default-OFF is the mature engineering choice — machinery present and documented, activation deliberate.
- ✅ Cross-platform patch parity even though only Linux is exercised — preserves portability without pretending Windows/Android are active. Honest.
- ✅ README.fonts.md is unusually candid about the EULA line — most projects would either hide the caveat or over-simplify. Names what is legal (use) and what is not (binary redistribution) with the concrete workaround.
- ✅ The get-microsoft-fonts.sh + .gitignore-excludes-binaries combination is a clean pattern for 'ship the method, not the assets' when the assets have restrictive licensing.

## VERIFICATION COMMANDS

```bash
grep -n 'gfx.bundled_fonts.skip_system_scan' gfx/thebes/gfxFcPlatformFontList.cpp
ls browser/fonts/   # after get-microsoft-fonts.sh: expect segoeui/segoeuib/seguisb/SegUIVar/YuGothR/YuGothB/consola + TwemojiMozilla
about:config -> gfx.bundled_fonts.skip_system_scan -> default false
# Manual test: enable pref; open a Bengali or Thai Wikipedia page; verify no tofu boxes
```



---

# ═══ MERGED DOCUMENT: 11-font-system.DEVELOPER.md (verbatim · sha256:4c7e2dff5e9a96c7 · merged 2026-08-02) ═══

# Font-System Optimisation — Gated Skip of OS Font Enumeration + Legal Microsoft Font Acquisition — Developer Track

> **Topic:** `11-font-system` · **Files:** `gfx/thebes/gfxFcPlatformFontList.cpp (Linux — live)`, `gfx/thebes/gfxFT2FontList.cpp (Android — spare)`, `gfx/thebes/gfxDWriteFontList.cpp (Windows — spare)`, `gfx/thebes/gfxPlatformFontList.cpp (cross-platform)`, `browser/fonts/moz.build`, `get-microsoft-fonts.sh`, `README.fonts.md + README.md`
> **Generated:** 2026-07-16

---

## Module Summary

Startup-optimisation infrastructure that lets Firefox skip the OS-wide font enumeration and rely exclusively on bundled fonts. Gated by `gfx.bundled_fonts.skip_system_scan` pref (default false — machinery ready, activation deliberate). Implemented uniformly across four platform paths (fontconfig, DWrite, FT2, cross-platform); only the Linux path is exercised on this build. Companion: `get-microsoft-fonts.sh` for legal acquisition of Microsoft fonts via Windows 11 Enterprise 90-day eval ISO; README.fonts.md documents the EULA line between use (permitted) and binary redistribution (not permitted).

## Architecture

- **Pattern:** Gated compile-time-present, runtime-off optimisation with cross-platform parity. Safety pref default false to avoid 'fast but broken' where insufficient bundled-font coverage silently breaks non-Latin scripts.
- **Trust Boundary:** Marginal fingerprinting-defence side-effect — OS font list becomes unobservable by the browser's own code path.
- **Attack Surface:** N/A
- **Dependencies:** `Bundled font set present in browser/fonts/`, `moz.build wiring registers them at FINAL_TARGET_FILES.fonts`

## Kill Switches

### `gfxPlatformFontList / gfxFcPlatformFontList / gfxFT2FontList / gfxDWriteFontList — PopulateFontList early-return` — RUNTIME_GUARD ⚠️

- **Condition:** `gfx.bundled_fonts.skip_system_scan` == true
- **Effect:** System font enumeration skipped; only bundled fonts registered. Pref default false — activation is deliberate.
- **Reversibility:** reversible
- **Notes:** Turn on ONLY after verifying bundled-font coverage against target-page glyphs.

### `get-microsoft-fonts.sh + .gitignore *.ttf/*.ttc rule` — HARD ⚠️

- **Condition:** operational
- **Effect:** Repository does not commit MS-font binaries (EULA). Script fetches from Microsoft's own eval ISO on the user's machine.
- **Reversibility:** reversible
- **Notes:** See README.fonts.md for binary-redistribution caveat when shipping compiled binaries with fonts baked into omni.ja.

## Performance Profile

- **CPU:** Startup CPU reduced when pref on — no fontconfig walk of ~/.fonts or /usr/share/fonts.
- **Memory:** Bundled fonts loaded regardless; system fonts not enumerated → no shadow font-record table built.
- **I/O:** Substantial disk-read reduction on font-heavy systems.
- **Timer Interval:** Startup-only.

## Security Analysis

### User Profiling

OS font list is one of the strongest fingerprinting signals. Skipping enumeration removes the browser's own visibility into it.

### Targeting

N/A

### Trust Chain

N/A

### Abuse Potential

N/A

## Implementation Flow

1. **`gfxPlatformFontList::InitFontList`** — Pref check + early return after bundled-font registration if pref true.
   *Side effects:* When pref on: fontconfig walk skipped entirely.
2. **`get-microsoft-fonts.sh`** — Downloads Win11 Enterprise eval ISO, extracts sources/install.wim, pulls needed fonts via 7z, verifies, installs into browser/fonts/.
   *Side effects:* Populates browser/fonts/ with MS TTF/TTC files locally (not committed).

## Technical Debt

🟢 **ACCEPTED** — Windows and Android portability-spare patches will never run on this build
  - *Recommendation:* Documented in the roadmap as deliberate portability preservation.

🟠 **MEDIUM** — Bundled-font coverage is not automatically verified against a target-glyph set
  - *Recommendation:* Add a preflight test that renders a corpus of glyphs (Latin, Cyrillic, Arabic, Hebrew, Thai, CJK, emoji) using ONLY the bundled set and warns on tofu.

🟠 **MEDIUM** — README.fonts.md's binary-distribution caveat is easy to miss when packaging
  - *Recommendation:* Add a build-time warning at packaging time if MS fonts are present in omni.ja.

## Impact If Removed / Disabled

Reverting: no optimisation available; every browser start does full OS font enumeration. get-microsoft-fonts.sh removal: users lose the documented legal acquisition path for MS fonts.

## Testing Notes

With pref off (default): behaviour identical to upstream. With pref on: render Bengali/Thai/Arabic/CJK sample pages and verify no tofu boxes. Startup benchmark: measure time-to-first-paint on a machine with 500+ system fonts, pref off vs on.

## Changelog Notes

Implemented as gated OFF-by-default 2026-07-07. get-microsoft-fonts.sh + README.fonts.md added later after clarifying the Windows 11 Enterprise eval ISO usage rights.

---
*Developer Track. Human Track twin: `11-font-system.LAYMAN.md`.*


---

# ═══ MERGED DOCUMENT: 11-font-system.LAYMAN.md (verbatim · sha256:3871b2d41b76779e · merged 2026-08-02) ═══

# 🧍 Font System — Skip the OS Font Scan by Using Only Bundled Fonts — Plain English Guide

> *Topic `11-font-system` of the Gorilla Unleashed Firefox 154 build · Written for everyone · 2026-07-16*

---

## 🌍 The Big Picture

Every time Firefox starts, it does invisible housework: it takes a complete inventory of every font file installed on your operating system. On a machine with hundreds of fonts (design workstations, developers with icon-font packs) or a slow disk (HDDs, especially the ones our target audience runs), this inventory takes several seconds — every single launch. You never see the inventory happening. You just feel the wait.

This patch group adds an *optimisation* — not a policy change, an optimisation — that lets Firefox skip the OS font scan entirely and use only its own bundled fonts. Faster startup, more consistent rendering (bundled fonts do not vary between machines), and one fewer disk-heavy operation on every launch.

**Two important honesty notes:** first, this is **default OFF**. The machinery is built and available, controlled by a single pref `gfx.bundled_fonts.skip_system_scan`, and you have to deliberately turn it on after verifying the bundled fonts cover what your web-pages need. Turn it on without adequate coverage and pages with unusual scripts (say, Bengali or Thai) will render with fallback boxes instead of text.

Second: this build runs only on Linux, so in practice only the Linux path is exercised. The Windows and Android patches (in `gfxDWriteFontList.cpp` and `gfxFT2FontList.cpp`) are kept as portability spares — the optimisation is inherently OS-specific and we did not want to lose it if we ever needed to move platforms.

Separately, this folder also holds the **`get-microsoft-fonts.sh`** script — the legal way to obtain Microsoft's Segoe UI / Consolas / Yu Gothic fonts from Microsoft's own Windows 11 Enterprise evaluation ISO. See `README.fonts.md` for the full explanation.

## 🎭 The Main Characters

| Name | What It Is | Real-World Comparison |
|---|---|---|
| **gfxPlatformFontList** | The cross-platform 'list all fonts I can use' subsystem | The librarian who catalogues every book in the building on opening morning |
| **Bundled Fonts** | The set of font files shipped inside this build (Segoe UI, Yu Gothic, Consolas, Twemoji) | The pre-selected library the librarian was already given — no need to walk the building |
| **System Font Scan** | The full inventory of every font installed on the OS | The walk-the-building trip that takes minutes on a big library or on slow stairs |
| **gfx.bundled_fonts.skip_system_scan** | The master switch (default OFF) that turns the optimisation on | The 'skip inventory' switch on the librarian's desk — safe only when the pre-selected library is confirmed complete |

## 🔢 How It Works — Step by Step

### Step 1: The four platform paths — one live, three spare

The optimisation is implemented in four platform-specific files: `gfxFcPlatformFontList.cpp` (Linux / fontconfig — the one this build actually uses), `gfxFT2FontList.cpp` (Android), `gfxDWriteFontList.cpp` (Windows), and cross-platform `gfxPlatformFontList.cpp`. All four patched consistently so the optimisation is available on any platform we might build for later.

### Step 2: The safety pref, default OFF

The switch defaults to `false`. Even after applying the patches, the browser behaves exactly as before until someone flips the switch. This prevents the 'fast but broken' trap where a startup optimisation quietly breaks Bengali/Thai/Arabic text because the bundled fonts do not cover those scripts.

### Step 3: When ON: system scan short-circuited, bundled fonts used exclusively

The initialisation path checks the pref; if true, it returns from `PopulateFontList` immediately after registering the bundled fonts, skipping the fontconfig / DWrite / FT2 enumeration entirely. Startup measurably faster on font-heavy systems.

### Step 4: The companion — get-microsoft-fonts.sh

This folder also carries the legal font-acquisition script. Microsoft's Segoe UI / Consolas / Yu Gothic are the visible identity of this build. Their EULA lets you *use* them but not *redistribute* the binaries; the script downloads them from Microsoft's own Windows 11 Enterprise 90-day evaluation ISO. See `README.fonts.md` for the full legal reasoning.

## 🤔 Quirky Things Worth Knowing

### ⚠️ Default OFF is a feature, not a limitation

The whole point of the safety pref is that this optimisation is a foot-gun without confirmed bundled-font coverage. Turning it on without checking would break real pages for real users. The gated default is the mature engineering choice.

### ⚠️ The 'portability spares' are honest about being spare

The Windows and Android patches will never run on this build. They exist because font-loading is one of the few places the project kept cross-platform code — the optimisation is genuinely OS-specific. Documented, not hidden.

### ⚠️ Fonts and legality — the honest binary-redistribution rule

Microsoft fonts are legal to *use* (via the Enterprise eval ISO); NOT legal to *redistribute* as binaries. A compiled binary that ships the fonts inside `omni.ja` also crosses the redistribution line. Clean options: (a) recipients run `get-microsoft-fonts.sh` and rebuild, or (b) build with open fonts (Noto, SIL OFL) which are legal to redistribute in binary form. `README.fonts.md` says this out loud.

## 💻 What Does This Mean For YOU?

### 🔋 Battery, Speed & Memory

Startup faster when the pref is on (bounded by installed-font count and disk speed). On a heavy design workstation, easily seconds saved per launch.

### ⚡ Speed

Startup-time win, not a runtime win. Once the browser is up, no difference.

### 🕵️ Your Privacy

Marginal — the OS-font inventory could in principle be used to fingerprint the specific machine.

### 🌐 Your Internet

Zero.

## 🔴 The Kill Switch — Explained

**What it is:** The whole topic is gated behind one pref. Default OFF — nothing you can enable by accident.

**Without it:** Every browser start does a full OS font inventory. On a slow disk that is measurable delay per launch.

**Think of it like:** The 'skip inventory' switch — off by default, because inventory catches you when your pre-selected library is missing books you needed.

## 🌐 Open Source & Why It Matters To You

You can verify the safety default. Grep for the pref — it is false in the patched code, false in every pref file. The optimisation is present and documented, not hidden and enabled behind your back.

## 📖 Glossary (Plain English Dictionary)

**gfxPlatformFontList** — Firefox's platform-abstraction layer for enumerating and loading fonts.

**fontconfig** — The Linux system-wide font-configuration library. What normally does OS font enumeration on this platform.

**DirectWrite (DWrite)** — The Windows font-rendering API. Used by the Windows portability-spare patch.

**FT2 (FreeType 2)** — The font-rendering library used on Android.

**omni.ja** — The compressed archive Firefox ships most of its assets in (chrome UI, JS, images, and — when bundled — fonts).

**SIL OFL** — SIL Open Font License — a permissive font license under which Google's Noto and other open fonts are distributed. Legal to redistribute in binary form.

---
*Human Track. Its Developer Track twin (`11-font-system.DEVELOPER.md`) covers the same changes in technical detail. Neither is a simplified copy of the other — they are the same truth in two languages.*


---

# ═══ MERGED DOCUMENT: 11-font-system.PRECHECK.json (verbatim · sha256:4f53cda18c2baa0c · merged 2026-08-02) ═══

```json
[]
```


---

# ═══ MERGED DOCUMENT: 11-font-system.PRECHECK.md (verbatim · sha256:fa5d689f05f7f6ef · merged 2026-08-02) ═══

# Offline Pre-Check: 11-font-system

*Generated 2026-07-16 22:44:31 by doc_audit.py (rule-based, no model involved).*

## File Inventory

| File | Lang | Lines | Complexity | SHA256 (16) |
|---|---|---|---|---|
| browser_fonts_moz.build.patch | patch | 17 | 2 | `1d343cbc81cc2778` |
| gfx_thebes_gfxDWriteFontList.cpp.patch | patch | 33 | 5 | `5c3da26ab1a2d0a8` |
| gfx_thebes_gfxFT2FontList.cpp.patch | patch | 93 | 24 | `4a5d7f362d3ea289` |
| gfx_thebes_gfxFcPlatformFontList.cpp.patch | patch | 37 | 4 | `72de962e36d64822` |
| gfx_thebes_gfxPlatformFontList.cpp.patch | patch | 15 | 6 | `e73131588cd15b9f` |
| get-microsoft-fonts.sh | sh | 124 | 7 | `094047f35c1c7635` |

## Rule Findings (0)

*All offline rules passed.*
