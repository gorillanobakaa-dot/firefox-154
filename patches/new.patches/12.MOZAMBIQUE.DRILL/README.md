# 🇲🇿 The Mozambique Drill — Neutralizing Firefox's Remote C2 Systems

## What It Is

A three-shot technique (named after the tactical shooting drill: two to the chest, one to the head) for permanently disabling Firefox's remote-control and experiment infrastructure **without** triggering compiler traps or fatal dependency panics.

| Shot | Name | Target | Effect |
|------|------|--------|--------|
| 1 | The Master Switch | `app.normandy.enabled` | Kills the Normandy C2 gate |
| 2 | The Data Starvation | `app.normandy.api_url` | Removes the remote endpoint |
| 3 | The Headshot (60-Year Sleep) | Fallback timer defaults in RecipeRunner + RemoteSettingsExperimentLoader | Background loops wait 60 years before their first network request |

## Why It Exists (The Glean Compilation Trap)

When we attempted to structurally excise Normandy and Nimbus (hollowing out `ExperimentAPI.sys.mjs`, deleting `Normandy.sys.mjs`), dependent components — the URL bar (`UrlbarPrefs`), `FirstStartup.sys.mjs`, the boot sequence — crashed with `TypeError` and `ModuleNotFoundError`. These systems have **145+ dependencies** across the codebase. The UI expects them to return specific data shapes. Returning `null` shatters the browser.

> **The compiler is perfectly happy. The browser boots perfectly. But the background loops required to execute remote C2 commands will wait 60 human years before firing their first network request. The systems are structurally perfect, but biologically dead.**

---

## The Three Shots — Code Details

### Shot 1: The Master Switch

**File:** `browser/app/profile/firefox.js`

Default Firefox ships with experiments enabled:
```js
pref("app.normandy.enabled", true);
```

The Mozambique Drill flips it to `false`:

```js
// 🦍 GORILLA UNLEASHED (Mozambique Drill — Chest Shot 1)
pref("app.normandy.enabled", false);
```

This single pref prevents the Normandy system from initializing its experiment-fetching pipeline during startup.

**To do it manually:** Edit `browser/app/profile/firefox.js` or your `user.js` and set:
```
user_pref("app.normandy.enabled", false);
```

### Shot 2: The Data Starvation

**File:** `browser/app/profile/firefox.js`

Default Firefox points at Mozilla's live endpoint:
```js
pref("app.normandy.api_url", "https://normandy.cdn.mozilla.net/api/v1");
```

The Mozambique Drill wipes it:
```js
// 🦍 GORILLA UNLEASHED (Mozambique Drill — Chest Shot 2)
pref("app.normandy.api_url", "");
```

The Normandy system is coded to abort initialization if it lacks a valid HTTPS endpoint. An empty string triggers the abort path silently.

**To do it manually:**
```
user_pref("app.normandy.api_url", "");
```

### Shot 3: The Headshot (60-Year Sleep)

Two files receive the timer dilation. Both use a shared pref `app.normandy.run_interval_seconds`, but the **fallback default** in the code is what matters — it's the safety net if the pref is missing or reset.

#### Target 1: `toolkit/components/normandy/lib/RecipeRunner.sys.mjs`

**Line 289** — the `updateRunInterval()` method:

```js
// BEFORE (stock Firefox — 6 hours):
const runInterval = Services.prefs.getIntPref(RUN_INTERVAL_PREF, 21600); // 6h
lazy.timerManager.registerTimer(TIMER_NAME, () => this.run(), runInterval);

// AFTER (Mozambique Drill — 60 years):
const runInterval = Services.prefs.getIntPref(RUN_INTERVAL_PREF, 1893456000); // 60y
lazy.timerManager.registerTimer(TIMER_NAME, () => this.run(), runInterval);
```

This is the timer that fires `RecipeRunner.run()` in a loop. With a 60-year interval, the browser will never poll for new recipes.

**To do it manually:** Edit line 289 of `toolkit/components/normandy/lib/RecipeRunner.sys.mjs` and replace:
```
-    const runInterval = Services.prefs.getIntPref(RUN_INTERVAL_PREF, 21600); // 6h
+    const runInterval = Services.prefs.getIntPref(RUN_INTERVAL_PREF, 1893456000); // 60y
```

#### Target 2: `toolkit/components/nimbus/lib/RemoteSettingsExperimentLoader.sys.mjs`

**Line 256** — the `XPCOMUtils.defineLazyPreferenceGetter`:

```js
// BEFORE (stock Firefox — 6 hours):
XPCOMUtils.defineLazyPreferenceGetter(
  this,
  "intervalInSeconds",
  RUN_INTERVAL_PREF,
  21600,                                          // <-- 6-hour default
  () => this.setTimer()
);

// AFTER (Mozambique Drill — 60 years):
XPCOMUtils.defineLazyPreferenceGetter(
  this,
  "intervalInSeconds",
  RUN_INTERVAL_PREF,
  1893456000, // 60y (Mozambique Drill)           // <-- 60-year default
  () => this.setTimer()
);
```

This controls how often the experiment loader pulls from Remote Settings. The `setTimer()` method (line 868) passes this value directly to `timerManager.registerTimer()`.

**To do it manually:** Edit line 256 of `toolkit/components/nimbus/lib/RemoteSettingsExperimentLoader.sys.mjs` and replace:
```
-      21600,
+      1893456000, // 60y (Mozambique Drill)
```

---

## The 60-Year Value

```
1893456000 seconds = 60 years exactly
```

Calculated as: `60 * 365.25 * 24 * 3600 = 1893456000`

This is large enough that any practical use of the timer system will never fire, but small enough to fit in a 32-bit signed integer (max ~68 years). The value survives integer overflow boundaries. No architecture or runtime will reject it.

---

## Defense-in-Depth: Locking Prefs at Every Layer

The user.js approach (`10.OVERRIDES/user.js`) is useful but vulnerable:
- A profile reset wipes user.js
- An auto-update can restore default prefs
- An extension with `moz-settings` access can flip prefs

The **firefox.js** default changes and the **code-level timer dilation** survive profile resets but still have a weakness: `pref()` in firefox.js only sets the **default value**. A distribution policy, a user.js entry, about:config, or (ironically) a Normandy/Nimbus rollout itself can write a user-branch value on top of it at runtime.

### The Three Levels of Pref Protection

Firefox has three escalating mechanisms for making a pref truly tamper-proof:

| Level | Mechanism | Scope | Survives |
|-------|-----------|-------|----------|
| **1 — Default** | `pref("name", value)` | Default branch only | Profile reset (defaults reloaded) |
| **2 — Locked at build time** | `pref("name", value, locked)` | Default branch + C++ lock flag | Everything except rebuild |
| **3 — Locked at runtime** | `Services.prefs.lockPref()` via `policies.json` | Default branch + C++ lock flag | Everything except deleting policies.json |

### Level 2: The `locked` Attribute (Build Time)

The `pref()` function in `firefox.js`/`all.js` accepts a third argument: the keyword `locked`. This is recognized by Mozilla's preference parser (in `modules/libpref/Preferences.cpp`) and sets the pref's internal lock flag at compile time.

```js
// ❌ Default only — can be overridden by anything
pref("app.normandy.enabled", false);

// ✅ Locked at build time — rejects all writes
pref("app.normandy.enabled", false, locked);
```

A locked pref **rejects writes from any source** — user.js, about:config, `Services.prefs.setBoolPref()`, distribution.ini, or even another extension. The only way to change it at runtime is to call `Services.prefs.unlockPref()` first, which requires chrome/privileged code access.

The Mozilla preference parser encodes this as a single character `L` in its internal format:
```
// Format: <type> <locked> <sanitized> ':' <name> ':' <value>? ':'
// locked = 'L' | '-'
L:L:app.normandy.enabled:false:
```

**Limitation:** This only works in the build-time preference files (`firefox.js`, `all.js`, `StaticPrefList.yaml`). You cannot use the `locked` keyword in `user.js`.

### Level 3: `policies.json` / Enterprise Policy Engine (Runtime)

The Firefox Enterprise Policy engine (`toolkit/components/enterprisepolicies/`) provides an even more flexible mechanism. It reads a `policies.json` file from `${InstallDir}/distribution/policies.json` and applies preferences with `Services.prefs.lockPref()`.

The `Preferences` policy supports per-pref locking:

```json
{
  "policies": {
    "Preferences": {
      "app.normandy.enabled": {
        "Value": false,
        "Status": "locked",
        "Type": "boolean"
      }
    }
  }
}
```

When `Status` is `"locked"`, the enterprise policy engine calls:
1. `Services.prefs.getDefaultBranch("")` to get the default branch
2. `branch.setBoolPref("app.normandy.enabled", false)` to set the default value
3. `Services.prefs.lockPref("app.normandy.enabled")` to lock it

This is functionally identical to the `locked` attribute but operates at **runtime** rather than **build time**. The trade-off:
- **Build-time `locked` attribute**: Can't be bypassed without rebuilding Firefox
- **Runtime `policies.json`**: Can be bypassed by deleting/renaming the policies.json file (but requires filesystem access to the install directory)

### How the Mozambique Drill Uses All Three

| Mechanism | What it protects | How to bypass |
|-----------|-----------------|---------------|
| `pref(..., locked)` in firefox.js | `app.normandy.enabled`, `app.normandy.api_url`, `app.normandy.run_interval_seconds` | Rebuild Firefox |
| `policies.json` in `distribution/` | Same 3 prefs (redundant lock) | Delete `distribution/policies.json` |
| Code-level fallback in RecipeRunner | `1893456000` default in `getIntPref()` | Rebuild Firefox |
| Code-level fallback in RSEL | `1893456000` default in `defineLazyPreferenceGetter` | Rebuild Firefox |
| `user.js` in profile dir | Runtime kill switches (redundant) | Profile reset |

The result: even if an attacker somehow writes a user-branch value to `app.normandy.run_interval_seconds`, the locked default prevents it from taking effect. And even if the pref is somehow reset entirely, the code-level fallback in `getIntPref(RUN_INTERVAL_PREF, 1893456000)` is still 60 years.

### Key Lesson: `pref()` vs `locked` vs `lockPref()` vs `policies.json`

| Method | When it runs | Locked? | Use case |
|--------|-------------|---------|----------|
| `pref("x", val)` | Build-time | No | Soft defaults that should be overridable |
| `pref("x", val, locked)` | Build-time | **Yes** | Hard defaults that must never change |
| `user_pref("x", val)` | Profile load | No | User preferences |
| `policies.json` with `Status: "locked"` | Runtime | **Yes** | Enterprise/distribution locking |
| `Services.prefs.lockPref("x")` | Runtime | **Yes** | Programmatic locking in JS/C++ |

**The golden rule:** If you care that a pref stays at a particular value and should *never* be changed at runtime, use **both** Level 2 (build-time `locked` attribute) *and* Level 3 (policies.json). They cover different failure modes:

- Level 2 covers: rebuild-time guarantee, immune to filesystem tampering
- Level 3 covers: runtime flexibility, survives if someone patches firefox.js but forgets policies.json

---

## Files Changed

| # | File | Change |
|---|------|--------|
| 1 | `browser/app/profile/firefox.js` | `app.normandy.enabled` → `false, locked`, `app.normandy.api_url` → `"", locked`, `app.normandy.run_interval_seconds` → `1893456000, locked` |
| 2 | `toolkit/components/normandy/lib/RecipeRunner.sys.mjs` | `21600` → `1893456000` in `updateRunInterval()` |
| 3 | `toolkit/components/nimbus/lib/RemoteSettingsExperimentLoader.sys.mjs` | `21600` → `1893456000` in `defineLazyPreferenceGetter` |
| 4 | `browser/app/distribution/policies.json` | Runtime lock on all 3 Mozambique Drill prefs |

---

## Origin Story

The Mozambique Drill was conceived in a human-AI pair session on 2026-06-11:

1. The **human** identified the strategic vulnerability: "Can we extend the timer to 60 years?"
2. The **AI** (a model no longer available) ingested thousands of lines of raw system code — `Normandy.sys.mjs`, `RecipeRunner.sys.mjs`, `RemoteSettingsExperimentLoader.sys.mjs` — in seconds and located the exact variable declarations.
3. We deployed **targeted regex-based code replacement** to inject the 60-year payload directly into the `.sys.mjs` backend files without triggering compiler syntax errors.

The name comes from the Mozambique Drill (also known as the "Failure Drill" or "Double Tap to the Chest, One to the Head") — a shooting technique that ensures the target is completely neutralized. Three shots, three different angles, one result.

<p align="center"><b>Structurally perfect. Biologically dead.</b></p>
