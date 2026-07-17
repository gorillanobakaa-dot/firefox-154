## 11.FONT.SYSTEM (4 patch files)

Font system patches — skip expensive OS font scanning at startup when
bundled fonts (via FINAL_TARGET_FILES.fonts) provide sufficient coverage.

Controlled by pref `gfx.bundled_fonts.skip_system_scan` (bool, default false).

### Files
- `gfxFcPlatformFontList.cpp.patch` — Linux/fontconfig: skip FcConfigGetFonts system scan
- `gfxFT2FontList.cpp.patch` — Android/FT2: skip FindFontsInDir system font directory scan
- `gfxDWriteFontList.cpp.patch` — Windows/DWrite: skip GetFontsFromCollection system enumeration
- `gfxPlatformFontList.cpp.patch` — Base: log message when bundled-only mode active

### Applying
```bash
cd firefox-source
patch -p1 < patches/11.FONT.SYSTEM/gfxFcPlatformFontList.cpp.patch
patch -p1 < patches/11.FONT.SYSTEM/gfxFT2FontList.cpp.patch
patch -p1 < patches/11.FONT.SYSTEM/gfxDWriteFontList.cpp.patch
patch -p1 < patches/11.FONT.SYSTEM/gfxPlatformFontList.cpp.patch
```

### Reverting
```bash
cd firefox-source
patch -p1 -R < patches/11.FONT.SYSTEM/gfxFcPlatformFontList.cpp.patch
patch -p1 -R < patches/11.FONT.SYSTEM/gfxFT2FontList.cpp.patch
patch -p1 -R < patches/11.FONT.SYSTEM/gfxDWriteFontList.cpp.patch
patch -p1 -R < patches/11.FONT.SYSTEM/gfxPlatformFontList.cpp.patch
```
