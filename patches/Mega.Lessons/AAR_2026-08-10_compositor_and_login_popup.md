# After-Action Review — 2026-08-10: the flashing browser and the black pill

**Two bugs, one day, one method.** Both fixes shipped, verified, and — for the
second one — reported upstream to Mozilla as
[bug 2062283](https://bugzilla.mozilla.org/show_bug.cgi?id=2062283).

Every technical section has a **Plain-language version**. Read whichever suits you.

---

## Part One — the flashing browser

### What the user saw

Red and green bands flashing across pages. Images from a previously-opened tab
bleeding into the next tab. Firefox's own toolbar and devtools icons turning to
garbled noise. Intermittent — sometimes minutes, sometimes a quiet day.

### What it was

The WebRender **native Wayland compositor** (one `wl_subsurface` per layer,
composited by Mutter) was active and desynchronising buffers. gnome-shell's
journal caught it in the act, timestamped inside the artifact window:

```
meta_wayland_buffer_process_damage: assertion 'buffer->resource' failed
```

### Why the first fix attempt was a no-op — the day's first lesson

On 2026-08-09 the pref `gfx.webrender.compositor.force-enabled` was commented
out of user.js as an A/B test. The artifacts returned anyway — because the
feature was force-enabled **twice more, at layers above the pref**:

1. `gfxConfigManager.cpp` carried an **unconditional**
   `mFeatureWrCompositor->UserForceEnable(...)` — compiled into libxul.so.
2. `browser/app/profile/firefox.js` set `gfx.webrender.compositor` AND
   `gfx.webrender.compositor.force-enabled` to `true` as **application
   defaults** — and commenting a `user_pref` out of user.js only removes the
   user value; the app default underneath stays.

The pref test was structurally incapable of testing anything. A quiet day after
the change was mistaken for evidence.

**Plain-language version:** we thought we had a light switch. We flipped it off
and the light stayed on — because someone had soldered the wire in the wall AND
glued a second switch in the ON position behind the plate. Flipping the visible
switch tested nothing. The lesson: before trusting an on/off test, prove the
switch is actually connected — turn it on and off and *watch the light change*.

### The fix, each step verified at the artifact

- Removed the C++ hunk; rebuilt; confirmed the marker string count in
  libxul.so went 1 → 0 and the mtime moved.
- Runtime test STILL showed the compositor active (449 `NativeLayerRootWayland`
  log lines under `MOZ_LOG=WidgetCompositor:5`) — which is how the second
  soldered wire (firefox.js defaults) was found at all.
- Removed the two default lines; `mach build faster`; log lines went 449 → 0.
- Patch set synced: the C++ patch quarantined
  (`patches/quarantine/gfx_config_gfxConfigManager.cpp.patch.REVERTED-…`), the
  05.PREFS firefox.js patch edited and verified to reproduce the live tree
  byte-for-byte from the vault vanilla.
- A journal watcher for the mutter assertion ran the rest of the day —
  including a 10-minute 1080p60 hardware-decode session — and stayed at
  **zero**.

**Retraction recorded:** an earlier claim that "13 wl_subsurface creations
prove the native compositor is active" was wrong — both compositor paths make
the same startup subsurface count. The discriminating instrument is
`MOZ_LOG=WidgetCompositor:5`, not `WAYLAND_DEBUG`. Instruments must be
validated by observing them *change* across the condition they claim to detect.

**Cost accepted knowingly:** without the native compositor, VA-API frames take
the GL composite path (~4–5× memory bandwidth on paper). Measured over 10
minutes of 1080p60: GPU averaged 629 MHz of its 1150 ceiling, RDD (hardware
decode) at 2.2% CPU. The feared cost did not materialise. Re-testing the
overlay path later is one user.js line — which now actually works.

---

## Part Two — the black pill on every login form

### What the user saw

Click an empty login field on any site → a black rounded pill appears under the
field, about 25px tall, with a sliver of clipped text at its bottom edge.
Unreadable, unclickable-looking, present for weeks. First guess: "badly
implemented CSS sheet."

### The investigation — what was ruled out, in order, each by evidence

| Suspect | Verdict | Evidence |
|---|---|---|
| The compositor bug (Part One) | innocent | pill is crisp, consistent, predates the fix |
| Page CSS / the site | innocent | same pill on every site; devtools console errors were all ad-blocking noise, constant across good and bad frames |
| Our icon-clamp CSS (master-redirect line 193) | innocent | commented out, cache flushed, restarted — pill unchanged; restored |
| `autocomplete-row-item.css`, `autocomplete-popup.js` | innocent | byte-identical to vault vanilla |
| Design tokens / missing `--space-*` | innocent | all five space tokens present |
| Our FTL blank-line trim | innocent | legal Fluent syntax |
| Known upstream bug | none found | Bugzilla searched |

**Plain-language version:** we lined up everything we'd ever changed that
touches that popup and interrogated each one separately. Every single one had
an alibi. That's when it stopped being "our build broke something" and became
"we are looking at a real Firefox bug nobody has noticed."

### The instrument that solved it

Static reading was exhausted, so the popup was **wiretapped live** in the
Browser Toolbox: a `popupshown` listener capturing geometry, then a
monkey-patched `adjustHeight()` logging every call with the row heights *as the
code saw them at that instant*:

```
adjustHeight @ t+0ms     matchCount: 2  rowHeights: 0,4    -> maxHeight set to 25px
popupshown   @ t+16ms
adjustHeight @ t+1600ms  matchCount: 0  rowHeights: 51,38  -> maxHeight set to 0px
```

One trace, whole story: the popup measures its rows **before their content
exists** (0px and 4px — empty shells), locks max-height at 25px, the content
arrives and inflates the rows to 51px + 38px under the lid. The only
re-measure fires after the field blurs, when matchCount is 0, so it writes 0px
— the correction never lands while the popup is visible. Reproduced five
consecutive times, identical.

**Plain-language version:** the popup takes its own measurements the instant it
opens — but its text arrives by a slower courier. It sizes itself around two
empty boxes, then the contents show up and don't fit, and it never re-measures
while you're looking at it. We proved this by attaching a recorder to the
measuring routine and watching it happen, timestamped, five times in a row.

### What the rows actually were — the twist

The clipped content was **two Mozilla advertisements**:

1. **"Import your logins from Google Chrome" + "Learn more"** — shown to
   anyone with no saved logins, on every login form. Its label arrives by
   *asynchronous Fluent localization* (rich `data-l10n-name` content) — which
   is exactly why the row was empty at measurement time. The ad was invisible
   because of its own delivery mechanism.
2. Behind it (revealed on click): the **Firefox Relay "Get a free email mask"**
   doorhanger — an upsell for a Mozilla subscription service requiring a
   Mozilla account. Our locale rebrand had faithfully renamed it "Gorilla
   Unleashed Relay email mask": a rebranded ad for a product our audience
   cannot use.

**Plain-language version:** the mystery box turned out to be two adverts in a
trench coat. One was so broken it couldn't display itself; the other was hiding
behind it. Neither serves a person with no credit card on a 2012 laptop —
they serve Mozilla's sign-up funnel.

### The fix — three layers, in order of what they remove

1. **`user_pref("signon.showAutoCompleteImport", "")`** — deletes the Chrome
   import nag at its gate (`importableBrowsers` never populates).
2. **`user_pref("signon.firefoxRelay.feature", "disabled")`** — deletes the
   Relay integration entirely: rows, doorhanger, and any traffic to
   `relay.firefox.com` (whose promo URLs carry `utm_campaign` trackers).
   `FirefoxRelayUtils.relayIsAvailableOrEnabled()` accepts only
   available/offered/enabled, so "disabled" is a hard off.
3. **The root fix**, because after the ads died the "Manage Passwords" footer
   (also async-rendered, 33.4px real vs 20px measured) was *still* clipped —
   proving the defect bites every async row, not just ads:

   `toolkit/content/widgets/autocomplete-popup.js` `adjustHeight()` now
   attaches a **ResizeObserver** to the visible rows and re-runs itself when
   any row changes size while the popup is open. No feedback loop is possible:
   adjustHeight writes only the richlistbox max-height, never row sizes.
   Captured as `07.TOOLKit/toolkit_content_widgets_autocomplete-popup.js.patch`
   and verified: vault vanilla + patch == live tree.

Verified on screen: popup opens, snaps to full height, "Manage Passwords"
fully readable. Before/after screenshots attached to the upstream report.

**Plain-language version:** we removed the two adverts (they were never for
you), and then fixed the measuring routine itself so the popup re-measures
whenever its contents change size. That last fix protects every future popup
row, whatever fills it — and we handed it to Mozilla for every Firefox user.

### Upstream

Filed as **[bug 2062283](https://bugzilla.mozilla.org/show_bug.cgi?id=2062283)**
(Toolkit :: UI Widgets, defect) with the trace, the diagnosis, before/after
screenshots and the offer of the patch. Every stock Firefox user with no saved
logins gets this clipped ad on every login form; nobody reported it because
the broken thing is an ad nobody mourns. If upstream lands its own fix, drop
our patch at the next rebase and take theirs.

---

## The lessons, distilled

1. **A pref test is a no-op if the value is forced at a layer above.** The
   pref stack has at least three floors: compiled `UserForceEnable`, app
   defaults (firefox.js), user value (user.js). Removing the user value tests
   nothing unless the floors above are clear. *Prove the switch is connected
   before trusting the flip.*
2. **Validate the instrument before the experiment.** The subsurface count
   "proved" something it could not detect; the useful instrument
   (`MOZ_LOG=WidgetCompositor:5`) was validated by watching it change 449 → 0
   across the condition. An instrument that cannot show the difference is
   scenery.
3. **Dynamic bugs need live instruments, not more reading.** Six suspects were
   acquitted by static diff; the wiretap solved it in one trace. When
   behaviour depends on *timing*, attach a recorder to the running thing.
4. **Absence of change is not evidence of fix** for an intermittent bug. The
   quiet day after the 08-09 pref edit was luck. The standing verification is
   a journal watcher on the assertion line — greppable, continuous, free.
5. **Rule things out one at a time, each with its own evidence, and write the
   alibis down.** The §39 log entry meant zero re-treading when the pill
   survived the first two fixes.
6. **Ads hide bugs.** A broken promotional surface goes unreported because
   users don't mourn it — grep any "nobody ever noticed" bug for the
   possibility that the broken thing is something nobody wanted.
7. **Rebranding is not de-Mozilla-ing.** The locale pass had produced a
   "Gorilla Unleashed Relay email mask" — our name on their upsell. Renaming a
   thing is not the same as deciding whether it should exist.
8. **Fix the disease after evicting the symptoms.** Killing both ads still
   left the footer clipped. If we had stopped at the prefs, the bug would be
   waiting inside every future async row.
9. **Give it back.** The root fix costs Mozilla nothing to take and fixes it
   for the kids this project is actually for — most of whom will never run
   this build, but all of whom run Firefox.

---

## Artifact index

| Artifact | Where |
|---|---|
| Compositor C++ patch (reverted) | `patches/quarantine/gfx_config_gfxConfigManager.cpp.patch.REVERTED-compositor-artifacts-2026-08-10.bak` + quarantine README post-mortem |
| firefox.js defaults fix | `patches/new.patches/05.PREFS/browser_app_profile_firefox.js.patch` (verified vs vault) |
| Popup root fix | `patches/new.patches/07.TOOLKIT/toolkit_content_widgets_autocomplete-popup.js.patch` (verified vs vault) |
| Both ad-kill prefs | `~/.mozilla/ff154-main/user.js` == `patches/new.patches/10.OVERRIDES/NEW_FILES/user.js` (byte-identical) |
| Full investigation log | `patches/FIrefox.154.Look/notes/THEME_FIX_LOG_2026-07-31.md` §39 + addenda |
| Upstream report | <https://bugzilla.mozilla.org/show_bug.cgi?id=2062283> |
| Lesson atoms | `SECOND.BRAIN/.../Firefox.154.Lessons/07.TOOLKIT/` and `02.GPU/` (chroma `firefox_154`) |
| Compositor session memory | agent memory `firefox-native-compositor-artifacts` |
