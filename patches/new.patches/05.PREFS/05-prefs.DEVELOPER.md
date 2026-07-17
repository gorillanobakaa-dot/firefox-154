# Preferences and Build Profile — mozconfig + StaticPrefList.yaml + app-branch defaults — Developer Track

> **Topic:** `05-prefs` · **Files:** `mozconfig (NEW_FILES/)`, `modules/libpref/init/StaticPrefList.yaml`, `modules/libpref/init/all.js`, `browser/app/profile/firefox.js`, `intl/locale/language.properties`
> **Generated:** 2026-07-16

---

## Module Summary

Two-layer configuration: (a) mozconfig — hardware-specific build recipe (`-march=native -O3`, LTO, jemalloc, Clang-21, `--disable-crashreporter/-updater/-parental-controls`, custom branding); (b) preference defaults — StaticPrefList.yaml defines the new `media.gorilla.hardware_only_mode` pref (bool, default true) plus AV1/VP9 HW-decode defaults=false to match Topic 01, and app-branch files (firefox.js, all.js) impose aggressive-purge defaults on AI/TopSites/Normandy/Nimbus/Pocket/telemetry. Locale properties file forces accept-language and disables multilingual/trending. This is a defaults layer only; Topic 10 (user.js) overrides at runtime, Topic 12 (policies.json) hard-locks the subset Mozilla could re-enable via remote config.

## Architecture

- **Pattern:** Compile-time defaults with intentional override hierarchy. Pref priority: StaticPrefList < firefox.js/all.js < prefs.js < user.js < policies.json.
- **Trust Boundary:** mozconfig excludes subsystems that would otherwise cross the browser's outbound trust boundary (crash reporter, updater). Cannot exfiltrate what is not compiled in.
- **Attack Surface:** Removing subsystems narrows attack surface — the crash reporter alone is a historical CVE breeding ground.
- **Dependencies:** `Clang 21 with LTO support`, `sccache for build caching`, `custom branding assets (referenced from firefox.js)`

## Kill Switches

### `mozconfig — --disable-* flags` — HARD ⚠️

- **Condition:** compile-time
- **Effect:** crashreporter, updater, parental-controls, various telemetry agents are NOT compiled into the binary. Cannot be enabled at runtime.
- **Reversibility:** reversible
- **Notes:** Requires rebuild to reverse.

### `StaticPrefList.yaml — media.gorilla.hardware_only_mode` — HARD ⚠️

- **Condition:** always
- **Effect:** New bool pref, default true. Consumed by Topic 01 at every codec gate.
- **Reversibility:** reversible
- **Notes:** Master toggle for Topic 01. About:config flip reverts codec policy without rebuild.

### `StaticPrefList.yaml — media.av1.enabled / media.wmf.vp9.enabled etc.` — HARD ⚠️

- **Condition:** always
- **Effect:** AV1/VP9 hardware-decode prefs default false. Reinforces Topic 01's C++ gates at pref layer.
- **Reversibility:** reversible
- **Notes:** Defence in depth: even if a code gate regresses, the pref still says no.

### `all.js — aggressive purge block` — HARD ⚠️

- **Condition:** always
- **Effect:** AI/TopSites-sponsored/Normandy/Nimbus/Pocket/PDF-AI-alt-text/translations-nag all forced false. Comment header: `--- GORILLA UNLEASHED: AGGRESSIVE PURGE (AI & TOPSITES) ---`.
- **Reversibility:** reversible
- **Notes:** Topic 12 hard-locks the Normandy/Nimbus subset via policies.json so Mozilla cannot re-enable via remote config.

### `firefox.js — usability-first defaults` — RUNTIME_GUARD ⚠️

- **Condition:** always
- **Effect:** signon.rememberSignons=true (kept), sessionstore.privacy_level=0 (full restore), tab-sleep timers tuned, sidebar experiments off. Deliberate usability choices, not blanket privacy-theatre.
- **Reversibility:** reversible
- **Notes:** Comment: `no nightly-only sidebar experiments — always off`. Distinguishes convenience-for-user (kept) from convenience-for-Mozilla (cut).

### `intl/locale/language.properties` — HARD ⚠️

- **Condition:** always
- **Effect:** accept-language fixed; multilingual/trending disabled. Fingerprinting-defence.
- **Reversibility:** reversible
- **Notes:** Small file, big effect.

## Performance Profile

| Component | Before | After | Mechanism |
|---|---|---|---|
| Build size | generic Firefox 154 | with disabled subsystems + LTO | mozconfig --disable-* flags + LTO dead-code elimination |
| media.gorilla.hardware_only_mode | not defined | defined as bool, default true | StaticPrefList.yaml addition |
| AI/TopSites/Normandy/Nimbus/Pocket defaults | true / partially enabled | false | all.js aggressive purge block |

- **CPU:** `-march=native -O3` + LTO produces measurably faster code on this exact CPU vs a generic build. Not benchmarked topic-locally.
- **Memory:** jemalloc reduces fragmentation on long-running sessions. Compiled-out subsystems reduce library size.
- **I/O:** Removed subsystems (crash reporter, updater, telemetry agents) do not run background threads or open network connections. Steady-state IO reduced.
- **Timer Interval:** Tab-sleep and GC timers configured via prefs; the concrete cadences live in Topic 04's CCGCScheduler.cpp.

## Security Analysis

### User Profiling

Multiple channels cut at the pref layer: telemetry, Normandy, Nimbus, AI features, TopSites-sponsored, Pocket. Coherent with Topic 13 (source-level telemetry kill) and Topic 12 (policies.json hard-lock).

### Targeting

Normandy/Nimbus experimentation channels disabled by pref here + hard-locked in Topic 12 + neutered in Topic 12's code patches. Three layers of defence.

### Trust Chain

Removed subsystems cannot exfiltrate. Compile-out is stronger than runtime disable.

### Abuse Potential

Aggressive purge reduces the attack surface for supply-chain-style attacks where a remote config could re-enable a dormant feature.

## Implementation Flow

1. **`mozconfig sourced by mach configure`** — Sets compiler flags, disables subsystems, defines branding. Consumed at build time.
   *Side effects:* Binary layout differs from stock: some libs absent, others optimised differently.
2. **`StaticPrefList.yaml compiled into libpref`** — Every defined pref becomes part of the binary with its default value. `media.gorilla.hardware_only_mode` added; AV1/VP9 defaults set false.
   *Side effects:* About:config shows the pref; Topic 01 reads it via StaticPrefs::media_gorilla_hardware_only_mode().
3. **`firefox.js / all.js loaded at profile init`** — Applies app-branch defaults on top of StaticPrefList.
   *Side effects:* About:config shows these as 'default' values, distinguishing from user-set.
4. **`intl/locale/language.properties baked in at build`** — Locale defaults fixed.
   *Side effects:* Accept-language stable across sessions; no drift.
5. **`(later layers) user.js overlay from Topic 10 + policies.json hard-lock from Topic 12`** — This folder's defaults are the base; user.js can override for runtime tuning, policies.json enforces the subset Mozilla could otherwise re-enable via remote experiments.
   *Side effects:* Prefs originally chosen by Mozilla lose to prefs re-chosen by us.

## Technical Debt

🟡 **LOW** — The `@gorilla-unleashed-153` headers pre-date the no-brand-spam rule — they are pre-existing identifiers per the rule, but any new such headers should NOT be added
  - *Recommendation:* Leave existing markers in place; do not add new ones. Prefer function-descriptive comments.

🟠 **MEDIUM** — The aggressive-purge block in all.js is one giant block — hard to see when a single line is regressed on rebase
  - *Recommendation:* Consider splitting by category (AI / TopSites / Normandy / Nimbus / Pocket) with sub-headers so per-category regressions are visible.

🟡 **LOW** — media.gorilla.hardware_only_mode is documented in the log but not in an in-tree comment adjacent to its YAML definition
  - *Recommendation:* Add a StaticPrefList.yaml comment linking to the Topic 01 gate sites.

## Impact If Removed / Disabled

Reverting mozconfig -> generic build, subsystems reactivated. Reverting StaticPrefList changes -> Topic 01 code gates dead-code (pref undefined) and every codec accepted. Reverting all.js -> AI features return, TopSites-sponsored returns, Normandy remote experiments run, telemetry channels re-open. Reverting firefox.js -> usability defaults change (password prompts, session-restore behaviour). Reverting language.properties -> accept-language leaks locale changes.

## Testing Notes

`grep -n 'media.gorilla.hardware_only_mode' modules/libpref/init/StaticPrefList.yaml` — expect defn. `about:config` -> verify the pref shows true. Check `about:preferences` -> Firefox Suggest and Sponsored Suggestions should be off by default (aggressive purge working). `about:policies` -> hard-locked entries from Topic 12 visible.

## Changelog Notes

Migrated from FF153. media.gorilla.hardware_only_mode was originally a mozconfig #define; promoted to a proper StaticPrefList entry on FF154 rebase so it can be toggled at about:config without rebuild. Aggressive-purge block consolidated 2026-07-10.

---
*Developer Track. Human Track twin: `05-prefs.LAYMAN.md`.*