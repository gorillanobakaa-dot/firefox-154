# 🧍 The Mozambique Drill — Neutralising Normandy and Nimbus (Two to the Chest, One to the Head) — Plain English Guide

> *Topic `12-mozambique-drill` of the Gorilla Unleashed Firefox 154 build · Written for everyone · 2026-07-17*

---

## 🌍 The Big Picture

Firefox contains two systems — **Normandy** and its successor **Nimbus** — that let Mozilla reach into your browser *from a distance* and change things without asking. They can silently switch features on or off, run A/B experiments on you (you get version A, your neighbour gets version B, Mozilla watches which behaves better), and measure the results. You never signed up for it; it is there by default; and if it stops working for any reason, Firefox has 145+ other components that expect it to be there and will crash if it is not.

This patch group is named after the '**Mozambique Drill**', a firearms training pattern of *two shots to the chest, one to the head*. That is exactly the shape of the fix — three redundant kills, applied at different layers so no single point of failure can bring the target back:

- **Shot 1 (chest):** The master switch is flipped. Preference `app.normandy.enabled` set to `false` at build time in Topic 05.
- **Shot 2 (chest):** The remote endpoint URL is erased. Even if the switch were flipped back on, the client would have nowhere to connect.
- **Shot 3 (head):** The internal 'check for new instructions' timer that would fire the network requests is dilated to sixty years. Not 'disabled' — set to fire once, in the year 2085.
- **Insurance shot:** The preferences are hard-locked via `policies.json`, so even a user in about:config cannot flip them back on. That is what makes it *override-proof*.

And because deleting the code entirely would break 145+ dependent components (attempted, failed, documented — the log describes the crash trace), the machinery is **left standing but dead**. Structurally perfect, biologically dead.

## 🎭 The Main Characters

| Name | What It Is | Real-World Comparison |
|---|---|---|
| **Normandy** | The older Firefox remote-experiment / remote-config system | A supervisor with a two-way radio, listening for instructions from HQ |
| **Nimbus** | Normandy's newer replacement, using RemoteSettings | The same supervisor with a shinier radio |
| **RecipeRunner** | The Normandy component that periodically calls out to check for new remote 'recipes' | The scheduled 'any updates for me?' phone call |
| **RemoteSettingsExperimentLoader** | The Nimbus equivalent — polls RemoteSettings for new experiment definitions | The Nimbus version of the same phone call |
| **policies.json** | An enterprise-grade preference hard-lock file that overrides even user.js | The corporate policy binder that not even the IT department can override |

## 🔢 How It Works — Step by Step

### Step 1: Shot 1 — the master switch

In Topic 05's firefox.js, app.normandy.enabled = false. Nothing runs at all when this is off. That would be enough by itself — except Firefox updates sometimes silently reset it, so we have shots 2 and 3.

### Step 2: Shot 2 — the endpoint URL is emptied

app.normandy.api_url is set to empty. Even if the master switch were flipped back on, the client would have no address to contact. Any attempted network call fails immediately in URL validation.

### Step 3: Shot 3 — the internal timer is dilated to 60 years

The head shot. RecipeRunner and RemoteSettingsExperimentLoader both have internal timers that fire their 'check for updates' network requests. Those timers are set to 1893456000 seconds (~60 years) between fires. The threads are alive, the objects exist — they just will not do anything until 2085.

### Step 4: The insurance shot — policies.json hard-lock

Firefox has an enterprise-focused system where preferences can be locked at the policies.json level. Locked prefs override even user.js. Even if the user opens about:config and tries to flip them back on, the change is silently rejected.

### Step 5: The machinery stays present so 145+ dependent components do not crash

The initial attempt was to just delete Normandy/Nimbus. It did not go well: the address bar, first-run, settings UI, and boot sequence all depend on Nimbus. Deleting the code triggers a cascade of TypeError: ExperimentAPI is undefined errors, and the browser fails to start. So the fix is different: leave the machinery in place, but make sure it never does anything harmful.

## 🤔 Quirky Things Worth Knowing

### ⚠️ 60 years is not a round number, it is 1893456000 seconds

60 x 365.25 x 24 x 3600 approx 1,893,456,000 seconds. Chosen specifically to be far past any reasonable lifespan of the machine.

### ⚠️ The name is not casual

The Mozambique Drill is a real firearms technique. Two-to-the-chest is not always enough (target may be wearing armour or high on adrenaline); the head shot is what guarantees the fix takes. Same shape here.

### ⚠️ This is the pattern for anything you cannot delete

Same design as Topic 09 (Marionette + Remote Agent). Same design as Topic 13 (telemetry). When code is entangled with 145+ other components, the answer is: keep the corpse standing so nothing that touches it crashes, but make sure the corpse never does anything.

## 💻 What Does This Mean For YOU?

### 🔋 Battery, Speed & Memory

One background service that used to poll a remote server every day now does not. Negligible per-poll, meaningful over months.

### ⚡ Speed

Slightly faster startup, slightly less steady-state CPU.

### 🕵️ Your Privacy

This is the topic that closes the *targeting* channel — the mechanism by which Mozilla could reach in and A/B-test on you specifically.

### 🌐 Your Internet

One fewer background connection to Mozilla infrastructure per day.

## 🔴 The Kill Switch — Explained

**What it is:** The Mozambique Drill — three separate kill mechanisms plus one hard-lock, applied to two related subsystems.

**Without it:** Mozilla can remotely toggle features, run A/B experiments, and measure results on your specific browser.

**Think of it like:** Not a single lock — a bolt, a chain, a welded hinge, and a corporate policy binder saying 'do not unlock this door under any circumstances'.

## 🌐 Open Source & Why It Matters To You

Every one of the four shots is auditable. Grep the prefs, grep the URL, grep the 1893456000 constant, grep the policies.json entry. In a closed browser this would be marketing; here it is arithmetic in four files.

## 📖 Glossary (Plain English Dictionary)

**Normandy** — Firefox's older remote-config / remote-experiment system. Polls a Mozilla endpoint for 'recipes' — bundles of JS to run in the browser.

**Nimbus** — Normandy's successor. Uses RemoteSettings as the transport. Same purpose.

**policies.json** — A Firefox enterprise-management file that hard-locks preferences. Sits above user.js in the precedence chain.

**Mozambique Drill** — A firearms training technique — two shots to the chest, one to the head — used to guarantee incapacitation when a single shot may not be enough.

**1893456000** — 60 years in seconds. The dilated interval for Normandy/Nimbus 'check for updates' timers.

---
*Human Track. Its Developer Track twin (`12-mozambique-drill.DEVELOPER.md`) covers the same changes in technical detail. Neither is a simplified copy of the other — they are the same truth in two languages.*