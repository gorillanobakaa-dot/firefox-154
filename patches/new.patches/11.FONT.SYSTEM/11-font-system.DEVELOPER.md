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