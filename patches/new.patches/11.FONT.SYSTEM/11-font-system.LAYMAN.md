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