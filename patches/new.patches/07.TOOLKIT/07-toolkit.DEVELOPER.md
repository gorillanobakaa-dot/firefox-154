# Toolkit Lockdown — Extension/Theme Install Block, Sponsored-Content Excision, Translations Disable, ExperimentAPI Mock — Developer Track

> **Topic:** `07-toolkit` · **Files:** `toolkit/mozapps/extensions/AddonManager.sys.mjs`, `toolkit/mozapps/extensions/internal/AddonRepository.sys.mjs`, `toolkit/mozapps/extensions/internal/XPIInstall.sys.mjs`, `toolkit/mozapps/extensions/LightweightThemeManager.sys.mjs`, `toolkit/components/nimbus/ExperimentAPI.sys.mjs`, `toolkit/components/translations/actors/TranslationsParent.sys.mjs`, `browser/components/urlbar/QuickSuggest.sys.mjs`, `browser/components/urlbar/UrlbarProviderQuickSuggest.sys.mjs`, `browser/components/urlbar/UrlbarProviderSearchSuggestions.sys.mjs`, `browser/extensions/newtab/content-src/components/{Base,DiscoveryStreamBase,TopSites}`, `browser/base/content/nsContextMenu.sys.mjs`, `browser/components/preferences/{config/appearance.mjs,dialogs/browserLanguages.js}`, `third_party/application-services/components/merino/src/lib.rs`, `services/settings/dumps/main/search-config-v2.json`, `toolkit/themes/shared/design-system/dist/{semantic-categories,tokens-table}.mjs`
> **Generated:** 2026-07-17

---

## Module Summary

Sealed-appliance layer across 19 files. Five workstreams: (1) extension/theme install lockdown — AddonManager/AddonRepository throw at the API layer, XPIInstall short-circuits the file/side-load route, LightweightThemeManager locks the theme; (2) sponsored-content excision — new-tab Base/DiscoveryStreamBase/TopSites React components strip the discovery feed + sponsored tiles/shortcuts; (3) address-bar de-sponsoring — QuickSuggest + two Urlbar providers + Merino Rust backend + search-config JSON stop remote/sponsored suggestions (no keystroke egress); (4) translations disable — TranslationsParent blocks model downloads, browserLanguages.js disables langpack UI; (5) ExperimentAPI returns empty default mocks for all Nimbus queries so the 145+ dependent components (urlbar, first-run, settings) never hit a null — the toolkit-side companion to Topic 12's network-side Mozambique Drill.

## Architecture

- **Pattern:** Throw-at-the-boundary for installs (fail-closed), component-level excision for UI content, shape-preserving mock for ExperimentAPI (fail-safe). Three different neutralization strategies matched to three different failure tolerances.
- **Trust Boundary:** Removes the entire extension attack surface (installs impossible), the sponsored-content egress surface (no impression counting, no keystroke-to-Merino), and the translation-model download surface. ExperimentAPI mock preserves the internal API contract while cutting the experiment channel.
- **Attack Surface:** Extension install is one of the largest browser attack surfaces (malicious/compromised add-ons). Blocking all install routes eliminates it wholesale. Side-load block also stops OS-level malware that drops an XPI into the profile.
- **Dependencies:** `Coherent with Topic 12 (Normandy/Nimbus) — ExperimentAPI mock here + poll-timer dilation there`, `Coherent with Topic 05 (Pocket/TopSites prefs off) — this enforces at the code layer what 05 sets at the pref layer`

## Kill Switches

### `AddonManager.sys.mjs + AddonRepository.sys.mjs — install API layer` — HARD ⚠️

- **Condition:** any install attempt (AMO or web)
- **Effect:** Throws a custom install-block error before any download/unpack. AMO backend calls and web-install interfaces refused.
- **Reversibility:** reversible
- **Notes:** Fail-closed: the default is refuse.

### `XPIInstall.sys.mjs — file/side-load route` — HARD ⚠️

- **Condition:** any .xpi install attempt
- **Effect:** Short-circuits to abort with a block log, preventing side-loading (including OS-malware-dropped XPIs).
- **Reversibility:** reversible
- **Notes:** Closes the route store-review would not catch.

### `LightweightThemeManager.sys.mjs + design-system tokens` — HARD ⚠️

- **Condition:** always
- **Effect:** Theme locked; cannot be swapped by user, extension, or remote config.
- **Reversibility:** reversible
- **Notes:** Appearance is fixed by design.

### `ExperimentAPI.sys.mjs — Nimbus query interface` — SOFT ⚠️

- **Condition:** any getExperiment/getVariable/onUpdate query
- **Effect:** Returns empty default mock objects instead of live experiment data. 145+ dependent components get a valid 'nothing' answer; no experiment executes.
- **Reversibility:** reversible
- **Notes:** Shape-preserving mock — the toolkit-side companion to Topic 12. Removing (rather than mocking) would recreate the TypeError: ExperimentAPI is undefined cascade.

### `TranslationsParent.sys.mjs + browserLanguages.js` — HARD ⚠️

- **Condition:** any translation-model/langpack fetch
- **Effect:** Model downloads blocked; monolingual/offline. Langpack download UI disabled.
- **Reversibility:** reversible
- **Notes:** Known trade-off — flagged in the roadmap as the sealed-appliance choice most worth revisiting for a global distribution audience.

### `QuickSuggest + Urlbar providers + Merino lib.rs + search-config JSON` — HARD ⚠️

- **Condition:** address-bar typing
- **Effect:** No sponsored or remotely-fetched suggestions; partial keystrokes not sent to Merino.
- **Reversibility:** reversible
- **Notes:** Privacy win — the urlbar stops being a keystroke-egress channel.

### `New-tab Base.jsx / DiscoveryStreamBase.jsx / TopSites.jsx` — HARD ⚠️

- **Condition:** new-tab render
- **Effect:** Discovery feed + sponsored tiles + sponsored shortcuts removed from the component tree.
- **Reversibility:** reversible
- **Notes:** Enforces at the code layer what Topic 05 sets at the pref layer (defence in depth).

## Performance Profile

- **CPU:** No add-on update-check threads; no new-tab sponsored-content fetch/render; no Merino round-trips. Not benchmarked topic-locally.
- **Memory:** Add-on subsystem still present (mocked/blocked) but does not load third-party extension code.
- **I/O:** Fewer background connections: no AMO pings, no Merino suggestion calls, no Pocket discovery feed, no translation-model downloads.
- **Timer Interval:** N/A

## Security Analysis

### User Profiling

Address-bar keystrokes no longer egress to Merino; new-tab impressions no longer counted; no add-on can read browsing data (none can install).

### Targeting

ExperimentAPI mock cuts the code-side experiment channel (complements Topic 12's network side).

### Trust Chain

Removing extension install removes trust dependency on AMO review, on extension signing, and on the user's judgement about what to install.

### Abuse Potential

Eliminates the compromised/malicious-extension attack class entirely — arguably the single largest reduction in attack surface in the whole build.

## Implementation Flow

1. **`AddonManager.installAddon / AddonRepository backend`** — Throws install-block error at the API boundary before any network/unpack.
   *Side effects:* Install UI surfaces an error; nothing is downloaded.
2. **`XPIInstall install pipeline`** — Short-circuits to abort with block log.
   *Side effects:* Side-load (including malware-dropped XPI) refused.
3. **`ExperimentAPI.getExperiment / getVariable / etc.`** — Returns empty default mock for every query.
   *Side effects:* 145+ dependent components receive a valid empty answer and proceed; no experiment runs.
4. **`TranslationsParent model-fetch path`** — Model download blocked.
   *Side effects:* Monolingual/offline; no Mozilla model-server connection.
5. **`Urlbar providers + Merino`** — Sponsored/remote suggestions suppressed; keystrokes not sent.
   *Side effects:* Address bar shows only local suggestions.
6. **`New-tab React render`** — Discovery/TopSites/sponsored components removed from the tree.
   *Side effects:* Quiet new-tab page.

## Technical Debt

🟠 **MEDIUM** — Translations disabled cuts against the global distribution audience
  - *Recommendation:* Revisit for distribution builds — consider allowing on-device translation models (no telemetry) while keeping the download path locked to a trusted mirror. Flagged in the roadmap.

🟡 **LOW** — Install-block is implemented by throwing rather than a single central policy gate
  - *Recommendation:* Consolidate the three throw-sites behind one `isInstallAllowed()` returning false, so the policy is one-line auditable.

🟠 **MEDIUM** — ExperimentAPI mock returns generic empties — a component expecting a specific-shaped variable could still misbehave
  - *Recommendation:* Add a smoke test that boots the browser and asserts no console error mentioning ExperimentAPI/Nimbus across urlbar/first-run/settings.

## Impact If Removed / Disabled

Reverting: extensions/themes installable (and side-loadable by malware); new-tab sponsored tiles + discovery feed return; address-bar keystrokes sent to Merino; translation models download on demand; ExperimentAPI returns live data and experiments can run. The sealed appliance becomes a normal extensible browser with its full sponsored-content and remote-experiment surface.

## Testing Notes

Try to install any extension from AMO -> blocked with error. Drag an .xpi onto the browser -> refused. Open a new tab -> no sponsored tiles, no discovery feed. Type in the address bar with network capture running -> no request to merino.services.mozilla.com. about:translations -> disabled. Boot + navigate urlbar/first-run/settings -> zero ExperimentAPI/Nimbus console errors (proves the mock is shaped correctly).

## Changelog Notes

Initial toolkit lobotomy in FF153 (2026-06-08/09); FF154 rebase resolved sys.mjs path conflicts (2026-07-05); static audit confirmed all .rej cleared, codebase stable (2026-07-10). ExperimentAPI mock is the toolkit-side companion to Topic 12's network-side neutralization.

---
*Developer Track. Human Track twin: `07-toolkit.LAYMAN.md`.*