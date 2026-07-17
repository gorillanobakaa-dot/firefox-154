# 🧍 The Toolkit Lockdown — Turning Firefox Into a Sealed Appliance — Plain English Guide

> *Topic `07-toolkit` of the Gorilla Unleashed Firefox 154 build · Written for everyone · 2026-07-17*

---

## 🌍 The Big Picture

Most of the other topics make the browser *faster* or *more private*. This one makes it **sealed and opinionated** — it turns Firefox from a general-purpose, infinitely-customisable tool into a fixed appliance, like a kitchen microwave: it does a specific set of things well, and you cannot bolt new parts onto it.

Why would anyone want that? Because a browser you cannot extend is a browser that *strangers* cannot quietly extend either. Every add-on, every theme, every language pack, every 'suggested' new-tab tile is also a door — and doors are how malware, spyware, and unwanted content get in. On a machine belonging to someone who is not a security expert (which is most of the target audience), the safest door is the one that was welded shut before they ever got the machine.

Four big changes: (1) **no add-ons or themes can be installed** — every install route (Mozilla's add-on store, drag-and-drop of a file, a website trying to push an extension) is blocked at the source; (2) **no built-in translation** — the translation-model downloads are disabled, keeping the browser monolingual and offline; (3) **no sponsored content on the new-tab page** — the ad tiles, the 'discovery' feed, the sponsored shortcuts are all excised; (4) **a fixed theme** — the appearance is locked so it cannot be changed by the user or by anything pretending to be the user.

**This is a real trade-off, stated honestly:** you cannot install a password-manager extension, an ad-blocker extension, or a dark-mode theme on this build. If you need those, this build is not for you. What you get in exchange is a surface with no configurable attack points.

## 🎭 The Main Characters

| Name | What It Is | Real-World Comparison |
|---|---|---|
| **AddonManager** | The subsystem that installs, manages, and updates extensions and themes | The building's front desk that signs for every delivery — now instructed to refuse all packages |
| **XPIInstall** | The specific code that unpacks and installs an extension file (.xpi) | The loading dock — now with the door bolted, so even a package that got past the front desk cannot be unloaded |
| **New Tab (DiscoveryStream / TopSites)** | The page you see when you open a new tab — normally full of sponsored tiles and a 'recommended stories' feed | The lobby noticeboard, normally rented out to advertisers, now blank by choice |
| **QuickSuggest / Merino** | The address-bar feature that shows sponsored suggestions as you type | The helpful concierge who was secretly paid to recommend certain shops — now silent |
| **TranslationsParent** | The subsystem that downloads and runs language-translation models | The in-house translator whose reference books are no longer delivered |
| **ExperimentAPI** | The Nimbus query interface that 145+ components ask 'is experiment X on?' | The information desk that used to phone HQ for answers — now hands back a blank 'nothing to report' card so nobody waiting in line gets stuck |

## 🔢 How It Works — Step by Step

### Step 1: Block every add-on install route

There are three ways an extension can get installed: from Mozilla's official add-on store (AMO), from a website that pushes one, or from a raw file on disk (side-loading). `AddonManager.sys.mjs` and `AddonRepository.sys.mjs` block the store and web routes by throwing a custom error at the API layer; `XPIInstall.sys.mjs` short-circuits the file route to abort with a block-log message. All three doors, bolted.

### Step 2: Lock the theme

`LightweightThemeManager.sys.mjs` and the design-system token files are patched so the appearance is fixed. The theme cannot be swapped — not by the user in settings, not by an extension (which cannot install anyway), not by a remote config. Consistent appearance, one fewer surface to manipulate.

### Step 3: Strip sponsored content from the new tab

Three React components (`Base.jsx`, `DiscoveryStreamBase.jsx`, `TopSites.jsx`) are patched to remove the sponsored-tile grid, the 'recommended by Pocket' discovery feed, and the sponsored shortcuts. The new tab becomes quiet — your own content, nothing rented out to advertisers.

### Step 4: Silence the address-bar sponsors

QuickSuggest (`QuickSuggest.sys.mjs`, `UrlbarProviderQuickSuggest.sys.mjs`, `UrlbarProviderSearchSuggestions.sys.mjs`) and the Merino backend (`merino/src/lib.rs`, plus a search-config JSON) are patched so the address bar no longer shows sponsored or remotely-fetched suggestions as you type. Your keystrokes are not sent to a suggestion server.

### Step 5: Disable translations

`TranslationsParent.sys.mjs` and `browserLanguages.js` block the download of translation models and language packs. The browser stays monolingual and offline — no model-download connection to Mozilla, no language-pack fetch.

### Step 6: The clever bit — ExperimentAPI returns a safe mock

This is the subtle one. 145+ Firefox components ask the Nimbus ExperimentAPI 'is experiment X enabled?' If you just remove it, all 145 crash (this is the same lesson as Topic 12). Instead, `ExperimentAPI.sys.mjs` is patched to return an empty default mock object for every query — so every component gets a valid 'nothing to report' answer and keeps working, while no actual experiment ever runs. Corpse standing, again.

## 🤔 Quirky Things Worth Knowing

### ⚠️ The sealed-appliance philosophy is a genuine security position, not laziness

It is easy to read 'no extensions' as the build being unfinished. It is the opposite: it is a deliberate stance that the most secure configurable surface is one with no configurable surface. Every extension API is also an attack API. For a non-expert user, removing the ability to install things removes the ability to be tricked into installing things.

### ⚠️ It talks to Topic 12

The ExperimentAPI mock here is the toolkit-side companion to Topic 12's Mozambique Drill. Topic 12 kills the *network* side of Normandy/Nimbus (poll timers, endpoint). This topic makes the *code* side safe by handing back mocks. Same corpse, two different guarantees.

### ⚠️ Translations off is a real limitation for the target audience

Honest note: the target audience is global — people who may well want to translate an English page into their own language. Turning translations off is the one sealed-appliance choice that cuts against them. It is done for offline/security reasons, but it is the change most worth revisiting for a distribution build. (The roadmap flags this as a known trade-off.)

## 💻 What Does This Mean For YOU?

### 🔋 Battery, Speed & Memory

No add-on subsystem running background update checks; no translation-model downloads; no sponsored-content fetches on every new tab. Each is a small saving; together, less background work.

### ⚡ Speed

New-tab page renders faster with no sponsored-tile network fetch. Address bar responds instantly with no remote-suggestion round-trip.

### 🕵️ Your Privacy

Substantial. Your address-bar keystrokes are not sent to a suggestion server (Merino). Your new-tab impressions are not counted for ad revenue. No add-on can read your browsing.

### 🌐 Your Internet

Fewer background connections — no AMO update pings, no Merino suggestion calls, no Pocket discovery feed, no translation-model downloads.

## 🔴 The Kill Switch — Explained

**What it is:** This topic is a bank of related lockdowns: extension installs blocked, theme locked, sponsored content stripped, translations disabled, and the ExperimentAPI made to return safe mocks so nothing crashes.

**Without it:** Firefox behaves as a normal, extensible browser: extensions installable (and side-loadable by malware), sponsored tiles and discovery feed on every new tab, address-bar keystrokes sent to Merino, translation models downloaded on demand, theme changeable by anything.

**Think of it like:** Converting a customisable workshop into a sealed vending machine — you lose the ability to rearrange it, and in exchange nobody else can rearrange it either.

## 🌐 Open Source & Why It Matters To You

Every lock is a readable patch. You can see exactly which install routes are blocked, exactly what the new tab strips, exactly what the address bar no longer sends. A closed 'secure' browser asks you to trust its claims; here the sealed appliance is sealed in the open, where the seals can be inspected.

## 📖 Glossary (Plain English Dictionary)

**Add-on / Extension** — A piece of third-party code that adds features to the browser. Powerful and useful — also a common malware and spyware vector.

**XPI** — The file format for a Firefox extension (a zip archive). 'XPIInstall' is the code that unpacks and installs one.

**AMO** — addons.mozilla.org — Mozilla's official extension and theme store.

**Side-loading** — Installing an extension from a local file rather than the official store — a route malware uses to bypass store review.

**QuickSuggest / Merino** — Firefox's sponsored address-bar suggestion feature (QuickSuggest) and its backend server (Merino). Sends partial keystrokes to fetch suggestions.

**DiscoveryStream** — The 'recommended stories' feed (powered by Pocket) on the new-tab page. Ad-supported.

**TopSites** — The grid of site tiles on the new-tab page. Some are sponsored (paid placements).

**ExperimentAPI (Nimbus)** — The interface 145+ components query to check experiment/feature-flag state. Patched here to return safe empty mocks so nothing crashes while no experiment runs.

---
*Human Track. Its Developer Track twin (`07-toolkit.DEVELOPER.md`) covers the same changes in technical detail. Neither is a simplified copy of the other — they are the same truth in two languages.*