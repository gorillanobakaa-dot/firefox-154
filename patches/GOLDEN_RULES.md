# GOLDEN RULES — Gorilla Unleashed Firefox 154

One-line rules, each proven by a real bug or regression. If you break one, you will get the same bug we already fixed.

---

## MEDIA / CODEC

| # | Rule | File | Bug |
|---|------|------|-----|
| M1 | `RemoteDecoderModule::Supports()` ALWAYS returns `SoftwareDecode` — do NOT gate on it | `dom/media/platforms/PDMFactory.cpp` | A |
| M2 | `IsBlockedSoftwareOnlyVideoCodec()` kills audio unless guarded with `video/` MIME check | `dom/media/platforms/PDMFactory.cpp` | B |
| M3 | Hardware-only enforcement belongs in `FFmpegVideoDecoder::Init()` (RDD process), nowhere else | `dom/media/platforms/ffmpeg/FFmpegVideoDecoder.cpp` | A |
| M4 | Frame pool MUST be exactly 16 — no `std::max()`, no growth | `dom/media/platforms/ffmpeg/FFmpegVideoDecoder.cpp` | D |
| M5 | No `std::abort()` in decode path — use `MediaResult` error return | `dom/media/platforms/ffmpeg/FFmpegVideoDecoder.cpp` | E |
| M6 | No `IsDecodingSlow()` fallback — hardware-only is unconditional | `dom/media/platforms/ffmpeg/FFmpegVideoDecoder.cpp` | F |
| M7 | Zero-copy enforcement requires null check: `mKnowsCompositor && mKnowsCompositor->GetTextureForwarder()` | `dom/media/ipc/RemoteVideoDecoder.cpp` | G |
| M8 | VA-API runs in RDD process (`media.rdd-ffmpeg.vaapi.enabled`), NOT the GPU process | architecture | — |
| M9 | `LIBVA_DRIVER_NAME=i965` required in `/etc/environment` — iHD does not support Ivy Bridge | system config | — |

## GFX / GPU

| # | Rule | File | Bug |
|---|------|------|-----|
| G1 | GPU process MUST be `ForceDisable`d on Wayland — `GtkCompositorWidgetInitData` has no Wayland surface fields → black window | `gfx/thebes/gfxPlatformGtk.cpp:327-338` | ERROR 9 |
| G2 | `UserForceEnable()` outranks gfxInfo blocklist; `UserEnable()` does NOT | `gfx/config/gfxFeature.h` | H |
| G3 | Priority chain: `mRuntime > mUser(ForceEnabled) > mEnvironment > mUser(Enabled) > mDefault` | `gfx/config/gfxFeature.cpp` | H |
| G4 | WebRender native compositor force-enabled on Wayland for zero-copy overlay | `gfx/config/gfxConfigManager.cpp:161-163` | I |
| G5 | Without native compositor, NV12 DMABuf goes through GL readback → 5× excess IMC bandwidth on UMA | architecture | I |

## CSS / THEME

| # | Rule | File | Bug |
|---|------|------|-----|
| C1 | NEVER `transform: scale/translate` on `.toolbarbutton-1`, `.tabbrowser-tab`, or XUL toolbar children — collapses layout | `browser/themes/shared/master-redirect.css` | XUL crash |
| C2 | Use `outline` not `border` for hover — border changes box model, outline does not | `master-redirect.css` | layout thrash |
| C3 | Only animate `opacity` and `transform` — everything else triggers CPU reflow | `master-redirect.css` | perf |
| C4 | `will-change: auto !important` globally — prevents WebRender VRAM over-promotion | `master-redirect.css` | VRAM thrash |
| C5 | `-moz-context-properties: fill, fill-opacity, stroke !important` required for SVG icon fill inheritance | `master-redirect.css` | invisible icons |
| C6 | PNG files at `chrome://` MUST be actual PNG data — SVG-in-PNG silently rejected | `browser/branding/gorilla/content/` | blank logos |
| C7 | `box-sizing: border-box !important` on `.tab-background` — prevents parentheses clipping | `master-redirect.css` | visual |
| C8 | `contain: layout style` (NOT `contain: paint`) on major containers — `paint` breaks XUL flexbox | `master-redirect.css` | layout break |
| C9 | `master-redirect.css` CANNOT style toolkit widgets (`findbar`, `notification`) — edit source CSS directly | `toolkit/themes/shared/findbar.css` | find bar invisible |

## LOCALE / FTL

| # | Rule | File | Bug |
|---|------|------|-----|
| L1 | NEVER modify text inside `< >` HTML tags in .ftl files — breaks `data-l10n-name` DOM hydration → invisible windows | `browser/locales/en-US/**/*.ftl` | DOM crash |
| L2 | Grep for "Gorilla Gorilla" duplicates after automated Firefox→Gorilla replacement | all `.ftl` and `.properties` | rebranding |
| L3 | No blank lines between Fluent message value and `.description` attribute — FATAL parse error | `.ftl` files | Fluent parser |

## TELEMETRY / PERFORMANCE

| # | Rule | File | Bug |
|---|------|------|-----|
| T1 | `MemoryTelemetry::GatherReports()` MUST be short-circuited — reads `/proc/self/smaps` every 60s, wastes 8.9% parent CPU | `xpcom/base/MemoryTelemetry.cpp` | perf |
| T2 | `FOG::InitializeFOG()` MUST return before `fog_init()` — Glean dispatcher thread wastes 3.5% parent CPU | `toolkit/components/glean/xpcom/FOG.cpp` | perf |
| T3 | Setting `toolkit.telemetry.enabled=false` does NOT stop MemoryTelemetry — it has its own timer | `xpcom/base/MemoryTelemetry.cpp:149` | arch |
| T4 | Glean SDK handles uninitialized state as no-op — safe to skip `glean::initialize()` | `toolkit/components/glean/src/init/mod.rs` | arch |
| T5 | Skipping `fog_init()` stops dispatch PROCESSING but NOT inline metric recording — call sites still `launch()` tasks that pile up (0.84% + slow buffer growth). Make `dispatcher::global::launch()` drop tasks when `!TESTING_MODE` | `third_party/rust/glean-core/src/dispatcher/global.rs` | perf |
| T6 | Editing ANY `third_party/rust/*` vendored file REQUIRES updating its SHA256 in that crate's `.cargo-checksum.json` `files` map, or the build fails checksum verification | `third_party/rust/<crate>/.cargo-checksum.json` | build |
| T7 | Prefer soft short-circuit (return early, keep symbols) over structural excision (delete files) for telemetry — excision orphans `mozilla::glean::` symbols → `NS_ERROR_FACTORY_NOT_REGISTERED` + 157 shim headers (see Brain `fog_glean_excision_sop.xml`) | strategy | history |

## BUILD / LAUNCH

| # | Rule | File | Bug |
|---|------|------|-----|
| B1 | `rm -f .parentlock` before `mach run` if Firefox was killed | `obj-*/tmp/profile-default/` | launch fail |
| B2 | `rm -rf startupCache/*` after CSS/locale/branding changes | `obj-*/tmp/profile-default/` | stale UI |
| B3 | `mach build faster` for non-C++ only; `mach build` for C++/Rust | — | wrong binary |
| B4 | Launch MUST include `-profile obj-x86_64-pc-linux-gnu/tmp/profile-default` to load `user.js` | launch command | BUG I pref inert |
| B5 | Launch MUST include `--class gorilla-unleashed` for Wayland app_id match | launch command | wrong .desktop |

## DESKTOP / WAYLAND

| # | Rule | File | Bug |
|---|------|------|-----|
| D1 | `.desktop` `Icon=` must be basename only — GNOME on Wayland ignores absolute paths | `gorilla-unleashed.desktop` | no icon |
| D2 | `StartupWMClass=gorilla-unleashed` must match `--class` flag exactly | `gorilla-unleashed.desktop` | wrong grouping |
| D3 | Icons in `~/.local/share/icons/hicolor/{size}x{size}/apps/` with correct pixel dimensions per file | icon install | wrong size |

---

## 6-LAYER CODEC GATE (read order = packet flow)

```
Layer 1: DecoderTraits        → MIME whitelist (H.264 only)
Layer 2: PDMFactory            → hardware_only_mode StaticPref, CreateDecoderWithPDM gating
Layer 3: RDD delegation        → RemoteDecoderModule (do NOT trust its DecodeSupport return)
Layer 4: VA-API init           → FFmpegVideoDecoder::Init(), IsHardwareAccelerated() check
Layer 5: i965 driver pin       → LIBVA_DRIVER_NAME=i965 in /etc/environment
Layer 6: RDD sandbox DRM       → /dev/dri/* access from RDD process
```

## GFX FEATURE PRIORITY (highest wins)

```
mRuntime  >  mUser(ForceEnabled)  >  mEnvironment  >  mUser(Enabled)  >  mDefault
   ^               ^                      ^                 ^               ^
ForceDisable   UserForceEnable      gfxInfo blocklist    UserEnable     SetDefault
```

`UserForceEnable` beats the blocklist. `UserEnable` does NOT.
