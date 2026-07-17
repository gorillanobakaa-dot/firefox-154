# GPU Un-Blocklist — Ivy/Sandy Bridge WebRender + Native Wayland Compositor Force-Enable — Developer Track

> **Topic:** `02-gpu` · **Files:** `gfx/config/gfxConfigManager.cpp`, `gfx/thebes/gfxPlatform.cpp`, `widget/GfxDriverInfo.cpp`, `widget/GfxInfoBase.cpp`, `widget/gtk/GfxInfo.cpp`
> **Generated:** 2026-07-16

---

## Module Summary

Four-layer override of Firefox's GPU blocklist plus dead-coding of the sticky hardware-decode sanity-test kill switch, plus `UserForceEnable` of the native Wayland compositor. Together these re-enable WebRender rasterisation, Wayland zero-copy VA-API overlay, and the entire hardware-accelerated graphics path on Intel Ivy Bridge (PCI 0x0152/0x0162/0x0166/0x016A) and Sandy Bridge devices, plus generic Intel/AMD/NVIDIA hardware. The vendor-vs-codec cut is deliberate: general features (WebRender, layers, compositor) are force-approved for vendors 0x8086/0x1002/0x10de, while VP9/HEVC/AV1 hardware decode/encode continue to report `FEATURE_BLOCKED_PLATFORM_TEST` so the hardware-only H.264 policy from topic 01.MEDIA remains enforced. Companion pref settings (typically in user.js): `gfx.webrender.all=true`, `gfx.webrender.fallback.software=false`.

## Architecture

- **Pattern:** Layered override at every point the blocklist is consulted. Failure mode being defended against is asymmetric: any one un-patched layer silently re-blocklists the GPU. So blocking is fixed at all layers, and one true force-enable is the entry point.
- **Trust Boundary:** The `FeatureState` machinery decides at runtime whether a graphics feature is enabled. Priority order (documented in CLAUDE.md): `mRuntime > mUser(ForceEnabled) > mEnvironment > mUser(Enabled) > mDefault`. Only `UserForceEnable()` sits above `mEnvironment` (which is where gfxInfo's blocklist verdict lives). `UserEnable()` sits BELOW it and is therefore overridable by the blocklist — a footgun that historically caused many well-intentioned fixes to silently no-op.
- **Attack Surface:** Blocklists exist historically because bad drivers really did crash browsers. By overriding, we accept a wider crash surface on genuinely broken drivers. Mitigation: the sanity-test failure path is dead-coded specifically so a *transient* crash does not permanently disable HW accel; a real repeated-crash driver would still surface user-visible errors. Codec-specific blocks are preserved (see vendor-vs-codec split).
- **Dependencies:** `Wayland compositor supporting DMABuf overlays (Mutter/GNOME 48 on this system)`, `i965 VA-API driver present and initialised`, `PipeWire or working audio stack (unrelated but often co-located failures)`

## Kill Switches

### `gfx/config/gfxConfigManager.cpp — WebRender native compositor init path` — HARD ⚠️

- **Condition:** Always on Wayland builds.
- **Effect:** `mFeatureWrCompositor->UserForceEnable("Gorilla: native Wayland compositor for VA-API zero-copy overlay")`. Using `UserForceEnable` (NOT `UserEnable`) is what makes this override the gfxInfo verdict. The native compositor lets NV12 DMABuf handles from the RDD-process VAAPI decoder go directly to Wayland surface planes without a GL round-trip — cuts memory-bus traffic on IMC by roughly 5×.
- **Reversibility:** reversible
- **Notes:** The distinction between `UserForceEnable` and `UserEnable` is the whole ballgame here. `UserEnable` returns UP to `mUser`, which loses to `mEnvironment` (gfxInfo). `UserForceEnable` promotes to `mUser(ForceEnabled)`, which beats `mEnvironment`. Grepping the tree for either name is a fast way to audit override intent.

### `widget/GfxInfoBase.cpp — GetFeatureStatusImpl vendor short-circuit` — HARD ⚠️

- **Condition:** GPU vendor ID matches Intel (0x8086), AMD (0x1002), or NVIDIA (0x10de).
- **Effect:** General features (WebRender, layers, compositor, hardware acceleration) return `FEATURE_STATUS_OK` before the static blocklist is consulted. HOWEVER: codec-specific features (`FEATURE_VP9_HW_DECODE`, `FEATURE_VP9_HW_ENCODE`, `FEATURE_HEVC_HW_DECODE`, `FEATURE_HEVC_HW_ENCODE`) continue to return `FEATURE_BLOCKED_PLATFORM_TEST` with failure id `FEATURE_FAILURE_GORILLA_NO_HW_CODEC`. This preserves topic 01.MEDIA's hardware-only H.264 invariant: the chip literally cannot decode VP9/HEVC in silicon, so we still block those.
- **Reversibility:** reversible
- **Notes:** Vendor-based rather than device-ID-based is intentional: covers essentially all consumer graphics hardware in one place. Bears the `@gorilla-unleashed-153` header from prior FF153 work — this is a proven, carried-forward mechanism.

### `widget/GfxDriverInfo.cpp — APPEND_DEVICE registry` — HARD ⚠️

- **Condition:** Always (compile-time commenting-out of registry entries).
- **Effect:** IvyBridge PCI IDs 0x0152 (GT1_2 HD 2500 desktop), 0x0162 (GT2_1 HD 4000 desktop), 0x0166 (GT2_2 HD 4000 mobile — this machine), 0x016A (GT2_3 HD P4000 workstation), plus SandyBridge 0x0102/0x0106/0x0116/0x0122/0x0126 are commented out of the DeviceFamily blocklist. `DeviceFamily::IntelWebRenderBlocked` at ~L615 only lists gen4/4.5/5 + PowerVR, so no edit was needed there (gen7 IvyBridge was never in it) — a positive finding worth noting.
- **Reversibility:** reversible
- **Notes:** Comments explaining WHY each APPEND_DEVICE line is dead are left in place so a future re-syncing pass does not blindly re-enable them.

### `gfx/thebes/gfxPlatform.cpp — sticky sanity-test kill-switch` — HARD ⚠️

- **Condition:** Always (compile-time removal of the persistent-pref-set path).
- **Effect:** The failed-hardware-decode sanity-test → persistent pref → permanent HW-accel disable chain is dead-coded. A transient hardware-decode probe failure (driver hiccup, race at startup, corrupt test vector) no longer welds the profile into software-only mode for the machine's lifetime.
- **Reversibility:** reversible
- **Notes:** Patch comment states the design rationale explicitly: 'One bad boot must not permanently disable HW accel.' This is arguably the highest-leverage change in the topic — it helps every user whose Firefox ever failed a sanity test once, whether they know it or not.

### `widget/gtk/GfxInfo.cpp — GTK platform probe` — HARD ⚠️

- **Condition:** Linux/GTK build paths.
- **Effect:** Short-circuits the Intel-DDX WebRender block (upstream Mozilla bug 1710400 — historically blocks Intel graphics on legacy X11 DDX), plus the `mGLMajorVersion < 3` guard, plus the 'missing codec in vaapitest results' → `FEATURE_BLOCKED_PLATFORM_TEST` mapping.
- **Reversibility:** reversible
- **Notes:** This is the earliest layer where a fresh GNOME/Wayland install can be silently blocklisted; ordering matters.

## Performance Profile

| Component | Before | After | Mechanism |
|---|---|---|---|
| WebRender rasterisation | blocked by gfxInfo (fallback to software layers) | hardware-accelerated on HD 4000 EUs | vendor short-circuit + device-family removal + sanity-test dead-code |
| Native Wayland compositor path | not force-enabled — subject to gfxInfo blocklist | UserForceEnable in gfxConfigManager | correct ForceEnable call — see kill switch notes |
| Zero-copy DMABuf overlay | GL readback path (5× IMC bandwidth) | direct DMABuf → Wayland surface | consequence of native-compositor enable |
| Sticky sanity-test failure | one failure = permanent HW-accel disable for the profile | dead-coded — transient failures do not stick | gfxPlatform.cpp kill-switch removal |

- **CPU:** GPU work (WebRender rasterisation, compositor, video overlay) moves off the CPU. Not benchmarked for THIS topic as before/after; the 12.8% parent-CPU win recorded in the project belongs to topic 13.TELEMETRY. Qualitatively: parent + content processes remain low during scrolling and video; the win is the avoidance of a software-rendering fallback that would otherwise pin one core continuously.
- **Memory:** Native compositor path eliminates GL readback of NV12 frames — cuts memory-bus traffic to IMC by ~5× vs the GL fallback path. Not measured as absolute bytes/sec, but the mechanism is well-established.
- **I/O:** DMABuf handles pass NV12 planes directly from RDD-process VAAPI decoder to Wayland compositor surface. Zero CPU copies on the video path.
- **Timer Interval:** N/A — event-driven.

## Security Analysis

### User Profiling

Not applicable — this is a local rendering-path change with no data-collection surface.

### Targeting

Narrows the attack surface for GPU-driver bugs specifically on Ivy Bridge/Sandy Bridge users of Firefox; but broadens the surface for anyone with a genuinely-buggy driver in the Intel/AMD/NVIDIA vendor blocks. Mitigation: sanity-test still runs, still surfaces user-visible errors on real failures — it just does not persistently disable the whole path. A truly broken driver would still crash the RDD or compositor process visibly.

### Trust Chain

Trust placed in the Wayland compositor (Mutter on this system), Mesa, i965, and the kernel media subsystem. All open source and independently auditable.

### Abuse Potential

The vendor short-circuit is coarse — it approves ANY 0x8086/0x1002/0x10de device, including devices Mozilla legitimately blocklisted for driver reasons. Trade-off is deliberate: false positives (a genuinely broken chip works via software fallback if the compositor rejects the DMABuf) are less costly than false negatives (a working chip running everything on the CPU forever).

## Implementation Flow

1. **`gfxPlatform::InitAcceleration / InitWebRenderConfig / InitHardwareVideoConfig`** — Startup path. Asks the FeatureState machinery whether FEATURE_WEBRENDER and FEATURE_HARDWARE_VIDEO_DECODING are OK.
   *Side effects:* Sets gfxVars (HardwareVideoDecodingEnabled, WebRender on) which are broadcast over IPC to content/RDD/GPU processes.
2. **`GfxInfoBase::GetFeatureStatusImpl (vendor short-circuit)`** — Consulted by the FeatureState query. Short-circuit added: if vendor ∈ {Intel, AMD, NVIDIA} → return OK for general features, BLOCKED_PLATFORM_TEST for VP9/HEVC HW codec features.
   *Side effects:* Blocklist static engine never consulted for general features on the covered vendors.
3. **`widget/gtk/GfxInfo.cpp — platform probe`** — Runs the GTK-specific hardware probe. Short-circuits Intel-DDX WebRender block (bug 1710400), gl-version guard, vaapitest missing-codec mapping.
   *Side effects:* Ensures the platform probe is not the source of a spurious FEATURE_BLOCKED verdict.
4. **`gfxConfigManager::ConfigureWebRender / gfxConfigManager::ConfigureFromBlocklist`** — Reads the resulting FeatureState. `UserForceEnable(...)` promotes the native-compositor feature above the gfxInfo blocklist tier.
   *Side effects:* Native Wayland compositor path selected; NV12 DMABuf handles go directly to Wayland surfaces.
5. **`gfxPlatform::sanity-test path`** — Sanity-test-failure → persistent-pref-set path dead-coded.
   *Side effects:* A single failed hardware-decode probe no longer permanently disables HW accel for the profile.
6. **`GfxDriverInfo::GetDeviceFamily`** — The registry that would list Ivy/Sandy Bridge as blocked is missing those APPEND_DEVICE calls — commented out with rationale.
   *Side effects:* Static blocklist engine finds no entry for these chip families → no verdict → falls back to the FeatureState default (OK).

## Technical Debt

🟢 **ACCEPTED** — Vendor short-circuit is coarse — approves all Intel/AMD/NVIDIA devices for general features, including any Mozilla legitimately blocklisted
  - *Recommendation:* Trade-off documented in the module summary. A narrower whitelist would need per-generation maintenance the project cannot afford.

🟠 **MEDIUM** — APPEND_DEVICE commented-out lines are drift-vulnerable on Firefox version bumps — a re-sync from upstream could quietly re-enable them
  - *Recommendation:* Automate a per-release grep for `APPEND_DEVICE(0x0166)` in the un-commented state as part of the toolchain-preflight script.

🟠 **MEDIUM** — No gtest asserts vendor short-circuit correctly preserves VP9/HEVC blocks — regression from BUG C class (blocking wrong feature IDs)
  - *Recommendation:* Add a gtest fixture that exercises GetFeatureStatusImpl for both general and codec-specific feature IDs on each vendor.

🟡 **LOW** — Dead-coded sanity-test kill switch relies on manual verification during test — no automated proof the code path is unreachable
  - *Recommendation:* Verify with a build-time static-analysis pass or a #error guard if the code is ever re-introduced.

## Impact If Removed / Disabled

Reverting: (1) WebRender falls back to the CPU-based layers acceleration path on IvyBridge/SandyBridge; (2) native Wayland compositor is not force-enabled, so decoded NV12 frames route through GL readback (5× IMC bandwidth); (3) any single failed hardware-decode sanity test permanently disables HW accel on that profile forever without user knowledge; (4) topic 01.MEDIA still enforces H.264-only but has no hardware path to run it on, so H.264 falls back to software too — the entire hardware-acceleration argument collapses.

## Testing Notes

Manual verification recipe:
1. `about:support` → Graphics section. Verify Compositing = WebRender, GPU #1 = Intel HD Graphics 4000, Driver Vendor = Mesa. If Compositing = 'Basic' or shows 'FEATURE_BLOCKED_*' the override did not stick.
2. `MOZ_LOG=WebRender:5 firefox 2>&1 | grep -i 'compositor\|dmabuf'` — expect native compositor init messages and DMABuf overlay success.
3. During 1080p H.264 playback, `intel_gpu_top` (from the intel-gpu-tools package) should show Render/3D engine and Video engine both active. RDD process CPU should be low. Parent/content near-idle.
4. Grep the built binary for retained sanity-test dead code — `nm libxul.so | grep -i sanity` and confirm expected symbols; if the compiler kept them they will show up.
5. Confirm codec block preserved: on `about:support`, VP9_HW_DECODE and HEVC_HW_DECODE must still show FEATURE_BLOCKED_PLATFORM_TEST. If they show OK, the vendor short-circuit is over-broad — regression from topic 01.MEDIA's invariant.

## Changelog Notes

See `patches/old.patches/02.GPU/MASTER_PROJECT_LOG_FIREFOX_154_GPU_PATCHES.md` for the four-layer architecture write-up. The `@gorilla-unleashed-153` header block in `widget/GfxInfoBase.cpp` (timestamp 20260529_120525) predates this Firefox 154 work — the vendor short-circuit mechanism was proven in FF153 and carried forward. The mission framing in the log ('de-facto planned obsolescence of working silicon') is the developer's own words, not this documentation project's editorial addition.

---
*Developer Track. Human Track twin: `02-gpu.LAYMAN.md`.*