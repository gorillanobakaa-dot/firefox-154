# Theme fix session log — 2026-07-31 (tree restore + FF154 token rename fix)

> **APPEND-ONLY AUDIT LOG — convention (adopted 2026-07-31 at user request).**
> Prior incident: an agent (Gemini) undid months of work and seeded knowledge
> bases with convincing-but-wrong CSS entries that passed casual review.
> Countermeasures, mandatory for every entry appended here:
> 1. **Append, never rewrite.** New work = new dated entry at the bottom.
>    Corrections reference the wrong entry explicitly; they do not edit it.
> 2. **Exact coordinates and values.** file:line, selector, the literal value
>    applied, and the command used to apply/deploy it.
> 3. **Every claim carries a verification command** a reader can run TODAY to
>    confirm the entry still matches reality. An entry with no check is
>    treated as unverified gossip.
> 4. **State fingerprint.** Each entry ends with sha256 of every file it
>    touched (Look master + tree copy + packaged copy where applicable).
>    Divergence between the three = broken deploy chain; divergence from the
>    log = someone changed it after the entry — investigate before trusting
>    EITHER.

Context: `/home/gorilla/firefox-main` was restored from the vanilla SafetyVault
tree + `Future.proof.APPLIED-STATE.2026-07-16.tar.gz` overlays + the 20 CSS
copies from `patches/FIrefox.154.Look/`. This log records every CSS/theme
modification made TODAY, with evidence. Build: `build_gorilla.sh`, 35:40,
then `mach build faster` (5 s) for the CSS-only follow-up.

## 1. global-shared.css — master-redirect @import position (pre-session fix, deployed today)

- File: `toolkit/themes/shared/global-shared.css` (copy of
  `patches/FIrefox.154.Look/global-shared.css`)
- `@import url("chrome://browser/skin/master-redirect.css")` sits in the
  LEADING import block (line 24), not after style rules (old bug: line 441 →
  silently dropped, rules C9/C10).
- Verified in the PACKAGED build:
  `dist/bin/chrome/toolkit/skin/classic/global/global-shared.css:24`.

## 2. CSS copy map used for the restore (20 files, non-obvious destinations)

| Look file | Tree destination |
|---|---|
| master-redirect.css | browser/themes/shared/ |
| browser-shared.css | browser/themes/shared/ |
| urlbar-searchbar.css | browser/themes/shared/ |
| unified-extensions.css | browser/themes/shared/addons/ |
| preferences.css | browser/themes/shared/preferences/ |
| aboutPrivateBrowsing.css | browser/themes/shared/privatebrowsing/ |
| global-shared.css | toolkit/themes/shared/ |
| common-shared.css | toolkit/themes/shared/in-content/ |
| tokens-{brand,platform,shared}.css | toolkit/themes/shared/design-system/dist/ |
| aboutaddons.css | toolkit/mozapps/extensions/content/ |
| aboutconfig.css | toolkit/components/aboutconfig/content/ |
| contentSearchHandoffUI.css | browser/components/search/content/ |
| activity-stream.css | browser/extensions/newtab/css/ |
| nova-activity-stream.css | browser/extensions/newtab/css/nova/activity-stream.css (RENAMED on copy) |
| aboutDialog.css | browser/branding/gorilla/content/ |
| content-aboutDialog.css | browser/base/content/aboutDialog.css (RENAMED on copy) |
| installing_page.css, profile_cleanup_page.css | browser/branding/gorilla/stubinstaller/ |

Also: the 8 font binaries (`consola/segoeui/segoeuib/seguisb/SegUIVar/
TwemojiMozilla .ttf`, `YuGothB/R.ttc`) from FIrefox.154.Look → `browser/fonts/`
(configure hard-fails without them; the snapshot only carried moz.build).

## 3. master-redirect.css — FF154 design-token rename overrides (NEW today)

**Root cause found from live screenshots**: FF154 renamed the toolbar/field
variables in `tokens-shared.css`; chrome consumers (`browser-shared.css:298,
323-324,701-703,710`, `urlbar-searchbar.css:66-67`) read the NEW names, while
master-redirect only forced the LEGACY names (`--toolbar-bgcolor`,
`--toolbar-field-color`, `--lwt-*`). Observed symptoms and their exact vars:

| Symptom (screenshot-verified) | Unthemed var (vanilla value) |
|---|---|
| Typed urlbar text black-on-black | `--toolbar-field-text-color` (FieldText) |
| Urlbar flashes white when focused / dropdown open | `--toolbar-field-background-color-focus` (Field) |
| Toolbars, tab strip, bookmarks bar pale / transparent-over-content | `--toolbar-background-color` (light color-mix) |
| Find bar container pale | same + `--toolbar-text-color`, `--toolbar-color-scheme` |

**Fix**: added to the `:root, #main-window, #browser-window, window` block of
`master-redirect.css` (marked `GORILLA OVERRIDE 2026-07-31`):

```css
--toolbar-background-color: #000000 !important;
--toolbar-text-color: #00FFFF !important;
--toolbar-color-scheme: dark !important;
--toolbar-field-background-color-focus: #000000 !important;
--toolbar-field-text-color: #00FFFF !important;
--toolbar-field-text-color-focus: #00FFFF !important;
--toolbox-background-color-inactive: #000000 !important;
--toolbox-text-color-inactive: #00FFFF !important;
```

CSS mechanics note for the next session: `!important` on `:root` wins the
cascade ON `:root`; it does NOT beat a normal re-declaration of the same
custom property on a descendant element. It works here because
urlbar-searchbar.css re-declares `--urlbar-background-*` on the element but
defines them AS `var(--toolbar-field-*)`, which still inherit from `:root`.

## 4. browser-shared.css — deliberate divergence from the 07-16 snapshot

The Look copy uses `var(--toolbar-background-color)` etc. where the 07-16
snapshot hardcoded `#000000/#00FFFF !important` (findbar container, lines
701-703). Kept the var() form; it now resolves black via §3. If the find bar
container ever regresses pale, this indirection is the first suspect.

## 5. Deliberately KEPT (not bugs)

- **Pink active tab — user-approved 2026-07-31 ("a good addition"). Do NOT
  "fix" it to black.** Comes from vanilla `tab.tokens.css` selected-tab
  colors, untouched by master-redirect.
- menupopup native-GTK restoration block in master-redirect.css (context
  menus keep OS chrome — ERR-UI-004 class).

## 6. Open items (NOT CSS, not fixed today)

- "Gorilla Gorilla" doubled brand string in bookmarks-toolbar placeholder —
  locale/brand.ftl issue.
- about:preferences JS errors: `sidebar.verticalTabs` double-add,
  `browser.privatebrowsing.autostart` not registered (prefs-patch fallout).

## 7. Operational notes

- startupCache: registered profiles → `~/.cache/mozilla/firefox/*/startupCache/`;
  absolute `-profile` dirs (e.g. `~/.mozilla/ff154-main`) → `<profile>/startupCache/`.
  CSS changes NEVER show without flushing the right one.
- CSS-only iteration loop: edit Look copy → cp to tree → `check_css_import_position.py`
  → `env -u CLAUDECODE ./mach build faster` (seconds) → flush startupCache → relaunch.
- Persistent profile: `~/.mozilla/ff154-main`, launcher `~/.local/bin/ff154`.

## 8. State fingerprint — end of 2026-07-31 session work

How applied/deployed (all of §1–§3):
```
edit  patches/FIrefox.154.Look/<file>          # single source of truth
cp    → /home/gorilla/firefox-main/<dest>       # per §2 copy map
lint  python3 patches/lint/check_css_import_position.py <files>
build ./build_gorilla.sh (full, 35:40) then:
      env -u CLAUDECODE ./mach build faster     # CSS-only repack, 5 s
```

Verification commands (run these; all passed 2026-07-31):
```bash
# import in leading block of PACKAGED css (rule C9/C10)
grep -n master-redirect /home/gorilla/firefox-main/obj-x86_64-pc-linux-gnu/dist/bin/chrome/toolkit/skin/classic/global/global-shared.css
# → line 24, @import url("chrome://browser/skin/master-redirect.css")

# the 8 token overrides present in the PACKAGED master-redirect
grep -c 'toolbar-field-text-color\|toolbar-background-color' /home/gorilla/firefox-main/obj-x86_64-pc-linux-gnu/dist/bin/browser/chrome/browser/skin/classic/browser/master-redirect.css
```

sha256 (Look master = tree copy = packaged copy for each file, verified identical):
```
3044bd0440bf4aa020be3d8732eeb9e2974e7cee032fa620998aba8725159b49  master-redirect.css (x3 locations)
40867421ff26ac905e7a1e9da5449823b45dba2401b2911301afd037cec0435f  global-shared.css   (x3 locations)
abfd2da240800b5d032f5374aa4e4a42e3cafdfbeaece5b1776e1d3da464b136  browser-shared.css  (Look + tree; toolkit-side packaging n/a)
```
Re-fingerprint command:
```bash
sha256sum patches/FIrefox.154.Look/{master-redirect,global-shared,browser-shared}.css \
  /home/gorilla/firefox-main/browser/themes/shared/{master-redirect,browser-shared}.css \
  /home/gorilla/firefox-main/toolkit/themes/shared/global-shared.css
```
Visual state at entry time (user-confirmed): urlbar cyan-on-black fixed after
token overrides; pink active tab KEPT (user-approved); "Gorilla Gorilla"
locale string + about:preferences JS errors still open (§6).

## 9. 2026-07-31 (later) — about: pages memory-tier audit; NO code changed

Commissioned by user after the Gemini DB-poisoning incident. Deliverables (in
`patches/Mega.Lessons/`):
- `ABOUT_PAGES_MEGA_LESSON.md` — coverage index for all 46 about: pages +
  audit verdicts. sha256 `af8f3dae731e2d8647eb304742a4f18b6460776fc382a39ce854158d7df39c2d`
- `ABOUT_PAGES_EVIDENCE.md` — generated verbatim snippet consolidation from
  3 memory tiers (chroma DB firefox_154/170 docs, 345 XMLs, patches .md).
  sha256 `530d0898c0b7047129a46cbbdc5cb229b3f4dfd9338db5d67e2ba492a528295f`

Key verdicts (details + verification commands in the mega lesson):
- DB docs 32 & 112 CORRUPT: naming-scrub mangled `media.gorilla.hardware_only_mode`
  → `media..hardware_only_mode` inside the database.
- The live "Gorilla Gorilla" UI bug = 508 doubled lines across 8 deployed FTL
  files (preferences.ftl 252, browser.ftl 171, aboutAddons.ftl 66, …); zero
  data-l10n attribute damage. Mechanism was pre-documented in DB doc id 3.
- 3 nonexistent-pref claims in networking/media docs
  (`network.http.http3.support-version1`, `media.hardware_decode_policy.*`).
No source, CSS, or locale file was modified in this entry.

## 10. 2026-07-31 (evening) — FTL locale repair, 15 files (Gemini sed-rebrand damage)

Context from user: Gorilla branding is INTENTIONAL (ancient-hardware community
build; brand meant to flow via -brand terms in brand.ftl). Repair therefore =
surgical, NOT revert-to-vanilla. Single-"Gorilla" flavored labels (e.g. "New
Gorilla Tab") deliberately KEPT.

Three repairs, in order, all under `/home/gorilla/firefox-main`:

1. **Dedup doubled brand** (8 files, 623 replacements): loop-replace
   `Gorilla Gorilla`→`Gorilla` and `Unleashed Unleashed`→`Unleashed` until
   stable. Files: browser.ftl(209), preferences.ftl(315), aboutAddons.ftl(78),
   aboutPrivateBrowsing.ftl(13), menubar.ftl(4), appmenu.ftl(2),
   sanitize.ftl(1), default-bookmarks.ftl(1).
2. **Graft 41 missing FF154 messages** (branded files were version-skewed):
   browser.ftl +22 (urlbar-result-menu-*/searchmode-*), appmenu.ftl +15
   (profiles/monitor/relay/vpn), preferences.ftl +4. Blocks copied VERBATIM
   from the vault vanilla files, appended under a `# GORILLA REPAIR
   2026-07-31` comment; branding propagates via { -brand-* } placeables.
3. **Fix poisoned Fluent variant keys, tree-wide** (12 files): the rebrand sed
   had mutated MACHINE tokens inside placeables — `[windows]`→`[Gorilla
   windows]` in `{ PLATFORM() -> }` selectors — making whole messages parse as
   Junk (silently dead UI: menubar Settings item, popup-warning button,
   aboutAddons options labels…). Regex fix on variant keys only:
   `\bGorilla (windows|macos|linux|other|ios|android)\b`→`\1` (and reversed
   order). Extra damaged files found beyond the known 8: aboutLogins.ftl,
   tabbrowser.ftl, aboutSupport.ftl, aboutProfiles.ftl, handlerDialog.ftl,
   unknownContentType.ftl, profileDowngrade.ftl.

**Verification (all run, all passed 2026-07-31):**
```bash
# Fluent parse: 0 Junk entries across browser+toolkit+branding locales
# (fluent.syntax via ~/.mozbuild/srcdirs/firefox-main-*/_virtualenvs/build/bin/python)
# zero doubled brand in PACKAGED build:
grep -rc 'Gorilla Gorilla' /home/gorilla/firefox-main/obj-x86_64-pc-linux-gnu/dist/bin/browser/localization/en-US/browser/browser.ftl   # → 0
# grafted message packaged:
grep -c 'urlbar-searchmode-popup-search-settings' <same dir>/browser.ftl      # ≥1
```
Deploy: `env -u CLAUDECODE ./mach build faster`; profile startupCache
(`~/.mozilla/ff154-main/startupCache/`) flushed. Pre-repair backups of the 8
dedup files: session scratchpad `ftl_backup_pre_repair/` (ephemeral — the
durable rollback is the vault + this entry's exact transform description).

sha256 post-repair (15 files):
```
baad9f4e629207be45a8b6f515e1f47526e635e20066351e8804a157da5a2da8  browser/locales/en-US/browser/browser.ftl
fc0ed99a3899ad29bac56dc72e4cd94ce6bf534a91a11ad56060a501cff1ad37  browser/locales/en-US/browser/menubar.ftl
c9903a02ef21af6867bff8edead2eeee491c302b8858b3e3973efb14a45d2b7d  browser/locales/en-US/browser/appmenu.ftl
3948b7c39738116ac2098d6dc5d9a84e09e67ed357492e5087101a1e8fffab62  browser/locales/en-US/browser/sanitize.ftl
a9e9816a0536221a1d96d621a7e8f741ecc51ef4f5e9f9b0c586ad9de4a7b44d  browser/locales/en-US/browser/aboutPrivateBrowsing.ftl
5c53ac764f5939c39e602b22388fc448ae1d8d6ba71c8e6e43e6e8395f5afca4  browser/locales/en-US/browser/aboutLogins.ftl
3bd3c965d1012280aa27fb00aa1023f061d0aa003788a52ed0a0668e4052dc22  browser/locales/en-US/browser/tabbrowser.ftl
418572c91a1e983bd45c3ac36f040d2804279a05bb70a8842e58e53330e06359  browser/locales/en-US/browser/preferences/preferences.ftl
b7989a485268f0c101282d1d88c374f79e5d72a913fbbf8d8a3d53eb825631b4  browser/locales/en-US/browser/profile/default-bookmarks.ftl
1377de7d9be1cee5766c7894baf134877855784f82e139ca5cfafccd8063986b  toolkit/locales/en-US/toolkit/about/aboutAddons.ftl
306ea2da8d894262f0e6ed326c1de551d9d120a7f2e3df46cd797f40ce5bba43  toolkit/locales/en-US/toolkit/about/aboutSupport.ftl
6a0db6dc149d61478649935753656c3d0fdd4a42689c2b2361f071e95103a2df  toolkit/locales/en-US/toolkit/about/aboutProfiles.ftl
2623574d30e072b3ba53bea83c8071237410d8fc3d2641be3b2042645737d441  toolkit/locales/en-US/toolkit/global/handlerDialog.ftl
15a16c9dcec9e4f08b90cf3def663e12f19bb0110012f8ebaf6b6c2028e033ca  toolkit/locales/en-US/toolkit/global/unknownContentType.ftl
5c44a3476af88e6b87050285049a38c752db11eb6b28137957146f916b5fb25e  toolkit/locales/en-US/toolkit/global/profileDowngrade.ftl
```
Open, NOT fixed here: webauthn security-key prompt renders illegibly (strings
verified present + parsing; suspect panel CSS contrast — retest after
restart); context-menu logic scrambling (nsContextMenu.sys.mjs diverges from
vault by 40 diff-lines — needs its own review); these FTL fixes are NOT yet
back-propagated to `patches/` deep-branded-locale masters or the 08_look
snapshot — restoring from those would REINTRODUCE the damage.

## 11. 2026-07-31 (evening) — context menu fix: nsContextMenu.sys.mjs rebased

**Symptom (user screenshot 17:16)**: right-click menu scrambled — every
section shown at once (spelling + link + media + image + video on one
target), "Open Link in New Gorilla Tab" apparently twice.

**Root cause (verified)**: `browser/base/content/nsContextMenu.sys.mjs` was an
OLD-base file. It imported ContextualIdentityService from
`resource://gre/modules/…` — that path is NOT packaged in FF154 (verified:
`ls dist/bin/modules/ContextualIdentityService.sys.mjs` → absent; FF154 moved
it to `moz-src:///toolkit/components/contextualidentity/…`). The lazy getter
throws during `initItems()`; init aborts; every menuitem below the throw stays
visible. The "duplicate" items are the container-tab / etc. variants that are
normally hidden. Old base also lacked FF154's IMAGE_ONLY_PROTOCOLS logic.

**Fix**: replaced the file with the VAULT FF154 copy, then re-applied the one
intentional patch — the `GORILLA: EXCISED` comment-out of
`lazy.GenAI.buildAskChatMenu(…)` (AI strip). Verified
`diff vault tree` now shows ONLY the excision comment block (11 lines).

Deploy: `env -u CLAUDECODE ./mach build faster` (5 s);
`~/.mozilla/ff154-main/startupCache/` flushed.
sha256 post-fix:
`e3f970fad14f622c5ec6ddc79e0d1ebd2fdc5a9346f979e5718a71d1e2a9ee02  browser/base/content/nsContextMenu.sys.mjs`
Back-propagation warning: `patches/` 07.TOOLKIT master and the 07_toolkit
snapshot still carry the OLD-base file — same as the FTL warning above.

## 12. 2026-07-31 (night) — "Gorilla Profile Missing" dialog + .properties tier damage

**Symptom (user screenshot)**: launching from the GNOME app-grid icon showed
"Gorilla Profile Missing / Your Firefox Gorilla profile cannot be loaded".

**Two independent defects, both fixed:**

1. **Stale .desktop Exec** (`~/.local/share/applications/gorilla-unleashed.desktop`):
   all 3 Exec lines pointed `-profile` at
   `…/obj-x86_64-pc-linux-gnu/tmp/profile-default` — destroyed with the gutted
   objdir. Rewrote all 3 to `-profile /home/gorilla/.mozilla/ff154-main`
   (the persistent profile) and dropped `-no-remote` from the main/new-window
   entries so link-handoff reuses the running instance.
   sha256 → `5cb91118abba465d9c0b899ce7230cc548d662b1aa7f0963cf7fe9ae35d82578`.
   NOTE: the vault icon script (`wayland_dual_icon_bug_fixer.sh` /
   `firefox-build-brand-patch brand icons-fix`) regenerates this file — its
   template still writes the STALE tmp-profile Exec; running it will
   reintroduce the bug until the template is updated (vault side untouched
   per policy — flag before next icon-fix run).

2. **.properties string tier — third damage layer** (after CSS tokens, FTL):
   census: 41 of the .properties files differ from vault; most = intentional
   flavor branding (kept per user policy). Actual damage fixed:
   - Redundant brand next to the %S placeholder (renders "Gorilla Unleashed
     Gorilla …"): profileSelection.properties ×3 (profileMissing,
     profileEncryptedButPrefOff, profileNotEncryptedButPrefOn),
     unknownContentType.properties fileType. Restored vanilla wording,
     brand flows via %S. Post-fix adjacency grep: 0.
   - **Double-escaped unicode** (`\\u21e7` renders literal "⇧"):
     platformKeys.properties (unix/win/mac) restored vault-verbatim (no
     branding content), downloads.properties statusSeparator ×2 fixed in
     place. Post-fix `\\uXXXX` grep: 0.
   sha256: profileSelection `ea89f149…45d4e`, unknownContentType
   `c2b3568e…88c63`, downloads `4e30f258…f8ea4`, platformKeys
   unix `ed57017d…7b6cd2` / win `6e97bcf9…d6e44c` / mac `7d173f73…017a9a`.

Deploy: `env -u CLAUDECODE ./mach build faster`; profile startupCache flushed;
`update-desktop-database ~/.local/share/applications` run.
Deliberately NOT fixed: flavor branding in the other ~35 .properties files
(e.g. " Gorilla History" widget labels — note they carry sloppy double
spaces; cosmetic, awaiting user preference).

## 13. OPEN DEFECTS LIST (consolidated; newest first — append here, strike when fixed)

1. ~~popupnotification panels render black-on-black~~ **FIXED — see §14**
   (was: "Set as default browser" prompt 17:53 + webauthn security-key prompt
   ~17:10, body text invisible; strings verified NOT the cause in §10).
2. ~~about:preferences JS errors~~ **FIXED — see §16** (root cause: old-base
   appearance.mjs double-registering sidebar.verticalTabs; the second error
   was a cascade). Residual: sidebar category text invisible until
   hover/selection — re-evaluate AFTER the §16 restart renders the page
   (may need an in-content text-color override in the Look CSS; get fresh
   screenshots first).
3. Vault icon script regenerates .desktop with STALE tmp-profile Exec (§12) —
   update its template before next icons-fix run, else the profile-missing
   dialog returns.
4. ~~Back-propagation~~ **DONE — see §19** (25 masters regenerated, dated
   repairs snapshot cut; the 2026-07-16 tarball alone is no longer sufficient
   — apply the 2026-07-31 REPAIRS tarball LAST).
5. commonDialogs.properties on the differs-list — watch for cross-wired
   titles/fields (the §12 screenshot's odd username/password pairing).
6. Cosmetic: flavor labels with double spaces (" Gorilla History", §12).
7. DB hygiene: fix chroma docs 32/112 (+ source XMLs), review 90/120/150,
   add identifier-existence gate to ingest_lessons.py (mega lesson §4).

## 14. 2026-07-31 (night) — popupnotification black-on-black FIXED (§13 item 1)

**Root cause (found statically, no Browser Toolbox needed)**:
`toolkit/themes/shared/popup.css:9-11` re-declares
`--panel-text-color: MenuText` directly ON the panel element
(`:is(menupopup, panel):where(:not([type="arrow"]))`). An element-level
NORMAL declaration beats an INHERITED `:root !important` value — the same
cascade mechanic documented in §3's mechanics note. On a light GTK theme
MenuText ≈ black, painted over our forced `#000000` panel background.
Arrow panels additionally resolve `light-dark()` to the light branch
(`color-scheme: light dark` at popup.css:33 + light system theme) → dark text.

**Fix (master-redirect.css, new block inserted immediately BEFORE the
"NATIVE CONTEXT MENU & POPUP RESTORATION" section; values verbatim)**:
```css
panel:not([type="arrow"]) {
  --panel-text-color: #00FFFF !important;
  --panel-background-color: #000000 !important;
}
panel[type="arrow"],
panel[type="arrow"]::part(content),
popupnotification,
popupnotificationcontent,
.popup-notification-body,
.popup-notification-description,
panel[type="arrow"] description,
panel[type="arrow"] label,
panel[type="arrow"] .checkbox-label {
  color: #00FFFF !important;
}
panel[type="arrow"] { color-scheme: dark !important; }
```
Design notes: element-level `!important` sidesteps the variable indirection
entirely; `menupopup` is deliberately NOT matched anywhere in the block so
the native context-menu restoration section below is untouched.

**Deploy**: cp Look master → `browser/themes/shared/master-redirect.css`;
`check_css_import_position.py` OK; `env -u CLAUDECODE ./mach build faster`
(5 s); `~/.mozilla/ff154-main/startupCache/` flushed.

**Verify**: `grep -c popupnotification <packaged master-redirect.css>` → 3;
sha256 IDENTICAL across all three copies (Look master = tree = packaged):
`02e60c6788a47115ea0770382869e169aeeee6468d71b94c4e2fccbafb2fcccf`
Visual check owed by user (restart, re-trigger the default-browser prompt;
also re-test the Google security-key sign-in): expect cyan text on black in
both panels.

**§14 addendum (later that night)** — THIRD sighting of the same mechanic,
identified from new user screenshots: the login autocomplete popup
(`#PopupAutoComplete`, "Use a passkey" / "Manage Passwords") renders as a grey
pill with near-invisible text. Source: `toolkit/themes/linux/global/
autocomplete.css:20-23` re-declares `--panel-text-color: FieldText;
--panel-background-color: Field;` ON `panel[type="autocomplete-richlistbox"]`
— element-level again. NO new CSS needed: §14's `panel:not([type="arrow"])`
!important block already matches and outranks it (same specificity, important
vs normal). Screenshots predate the user's restart; awaiting visual
confirmation. IF after restart the popup is black/cyan but still collapsed to
a one-row scrollable box, the HEIGHT is a separate defect (suspect
interaction with the icon-clamp block at master-redirect "POPUP ARTIFACT
OVERRIDES") — reopen as its own §13 item with fresh screenshot.

**Log-check (user-requested, same night)**: predicted flood of "unreachable
code after return statement" CONFIRMED in volume — 277 of 449 lines in
ff154-first-run.log — but source analysis shows ALL 277 are WEB CONTENT
(google.com minified site JS, line 2067); grep for chrome://|resource://|
moz-src sources: **0 hits**. The telemetry-lobotomy .sys.mjs files produce
zero unreachable-code warnings in this log. No action needed; noted so nobody
"fixes" the lobotomy on the strength of web-page noise.

## 15. 2026-07-31 (night) — docs: unpacked-build workflow + check-lessons-first rule into both CLAUDE.mds

At user direction, after verifying the memory tiers document it (lesson
`Firefox_OMNI_JA_Developer_Build_Workflow`, 07.TOOLKIT — present in chroma DB
AND source XML; plus "Smart Compile" in ALL_ICON_LESSONS 2026-07-03 and
`live_patch_injector.py` refs). Changes, no code touched:

1. `/home/gorilla/firefox-main/CLAUDE.md`:
   - CORRECTED a stale rule that contradicted golden rule C9: it still said
     master-redirect.css "CANNOT reach toolkit widgets" — the pre-2026-07-31
     wording that hid the dead-import bug. Now states the import-position
     truth with pointer to GOLDEN_RULES C9/C10.
   - Added persistent-profile note (~/.mozilla/ff154-main; startupCache
     INSIDE the profile dir).
   - New section "UNPACKED DEV BUILD — THE SMART WAY": never `./mach
     package`/`--enable-release`; no omni.ja; dist/bin stays raw dirs/
     symlinks; front-end = build faster (~5 s) + cache flush; instant live
     test = overwrite under dist/bin directly (mirror back or next build
     clobbers); C++ = build binaries.
   - New section "CHECK THE LESSONS FIRST": every breakage is already
     documented — query chroma_fx154 / lesson XMLs / Mega.Lessons / this log
     via memory_tier_extract.py; with the F1 scrub-corruption caveat.
2. `/home/gorilla/Documents/FIREFOX.WORK/FIrefox.154.Work/CLAUDE.md`: compact
   versions of the same two sections.

Note recorded: the workflow lesson XML itself carries F1-class scrub damage
(brand name deleted: `called ""`, `"Tab" -> "Tab"`) — add to DB-hygiene item 7.
sha256: run `sha256sum /home/gorilla/firefox-main/CLAUDE.md
/home/gorilla/Documents/FIREFOX.WORK/FIrefox.154.Work/CLAUDE.md` to fingerprint
current state (files are living docs; hashes change with every doc edit).

## 16. 2026-07-31 (night) — about:preferences init crash fixed (§13 item 2)

**Symptom (user screenshots 18:45)**: Gorilla Settings page renders EMPTY —
blank content pane, sidebar category labels invisible except on
hover/selection.

**Root cause (verified)**: `browser/components/preferences/config/
appearance.mjs` was an OLD-base copy (275 diff-lines vs vault, ZERO GORILLA
markers = no intentional content). It still registered
`{ id: "sidebar.verticalTabs" }` + `sidebar.revamp`, which FF154 upstream
moved to `config/tabs-browsing.mjs:103` → `Preferences.mjs:48` throws
"preference with id 'sidebar.verticalTabs' already added" during page init →
registration chain aborts → later prefs (browser.privatebrowsing.autostart,
registered at main.js:103) never load → both §6 JS errors explained by ONE
defect → panes render empty. Same version-skew class as §11's nsContextMenu.

**Fix**: vault-restore verbatim (diff vs vault now empty).
sha256 `417ee502137bfcbc0d423450033ba7225f34a375f319c88076f7bdf70070267f
browser/components/preferences/config/appearance.mjs`
Deploy: `env -u CLAUDECODE ./mach build faster`; profile startupCache flushed.

**Kept as-is**: `preferences/dialogs/browserLanguages.js` — 54 diff-lines vs
vault but carries 1 intentional GORILLA patch (AMO langpack network-fetch
strip); dialog-scoped, not page-init-critical. If Languages dialog misbehaves
later, rebase it the §11 way (vault base + re-apply the marked block).

**Verify after user restart**: about:preferences should render all panes;
launch log should show NEITHER of the two §6 JS errors. Sidebar label
contrast to be re-judged on the rendered page (see §13 item 2 residual).

## 17. 2026-07-31 (night) — in-content dark-scheme force + common-shared.css rebase

**Symptoms (user screenshots 18:56, post-§16 — page now renders)**: body text
dark-grey-on-black ("Same Gorilla settings, new look!" card, default-browser
card, QR card); sidebar category labels invisible unless selected; giant
unconstrained "POWERED BY DEBIAN" cap image + purple shield art sprawling
over the privacy pane.

**Two root causes:**
1. In-content pages keep vanilla `color-scheme: light dark` (common-shared
   :root) → on the light GTK system theme every `light-dark()` text token
   resolves its NEAR-BLACK branch over our forced-black page backgrounds.
   Affects body text AND `.category-name` labels identically.
2. The Look `common-shared.css` was OLD-BASE (5 hunks vs vault): missing
   FF154's `:where([hidden]) { display: none !important; }` — without it,
   `[hidden]` page elements with author display rules PAINT: that is the
   sprawling hero/promo art.

**Fix — file rebased onto FF154 vanilla, intent preserved (values verbatim):**
- adopted from vault: the `[hidden]` rule + `&:not(.system-font-size)` form;
- kept intentional: 200px `.category-icon` + `.message-bar-icon` sizes (2
  hunks), the 84-line "🦍 ABOUT:ADDONS BRANDING OVERRIDE" tail block;
- NEW appended block: `:root { color-scheme: dark !important; }` for ALL
  in-content pages (tokens then resolve --text-color to the readable
  dark-mode branch).
Method identical to §11/§16 (vault base + re-apply marked intent) — this is
the FOURTH old-base file found today (nsContextMenu, FTL ids, appearance.mjs,
common-shared.css).

**Deploy**: cp Look → `toolkit/themes/shared/in-content/common-shared.css`;
lint OK; `mach build faster` (5 s); profile startupCache flushed.
**Verified**: packaged copy `cmp`-IDENTICAL to source; `:where([hidden])`
present (grep=2: rule + comment).
sha256 (Look = tree):
`f02899dcc28f11c5d61b2cfdfaf6821b82672054474444fa736ca56124426372  common-shared.css`
**User check after restart**: about:preferences body text + unselected
sidebar labels readable; hero art constrained/hidden. If the cap image STILL
sprawls, next suspect is the intentional 480/500px about-logo rules in the
Look preferences.css (lines ~33/88) interacting with the now-working page.

**§17 addendum — design-intent cross-check against the lessons (no change)**:
user pointed at the tiers; verified the ONE-PNG design is fully documented
(`RECOVERED_HISTORY.xml` in 08.Look — 25 provenance-tracked edits from the
2026-05-29/30 sprint incl. change entry 20260530_233206) and that the Look
preferences.css STILL carries every documented value intact:
- ONE image everywhere: `chrome://branding/content/about-logo.png`
  (verified in build: real PNG, 500×500, symlinked live from
  browser/branding/gorilla/content/ — 346,651 bytes)
- `.category-icon` 42px; `moz-promo img` 480px w/auto h, 20px auto margins,
  inside promo card #121214 bg / #2b2b2e border / radius 20 / padding 40;
- paneTabsBrowsing-only fixed decoration ≥1300px: 500×500 at right 40px /
  top 180px, opacity .85;
- `#content { background-image: none !important }` = the DOCUMENTED
  deliberate watermark-hide for this page (change 20260530_233206).
CONCLUSION: the "sprawling cap" in the 18:56 screenshots is the 480px
`moz-promo` image orphaned by the two §16/§17 structural bugs (its card
chrome and text were invisible around it). The legacy text rules
(`label, description… color:#f9f9fb`) predate the FF154 preferences
redesign and no longer reach the new shadow-DOM components — §17's
color-scheme force is the modern replacement, not a conflict.

## 18. 2026-07-31 (late night) — knowledge consolidation into the firefox_154 DB

At user direction. All artifacts, no browser code touched:

1. **Decontaminated 3 source lesson XMLs** (the F1 findings, now fixed at the
   SOURCE tier too): `01.MEDIA/firefox_decodertraits_pref_gate_20260629.xml` +
   `07.TOOLKIT/firefox_rust_compile_pref_mismatch_err_build_005.xml`
   (`media..hardware_only_mode` → `media.gorilla.hardware_only_mode`, the
   tree-verified name) and `07.TOOLKIT/Firefox.OMNI.JA.Developer.Build.Workflow.xml`
   (brand name restored: `called "Gorilla Unleashed"`, examples
   `"Tab" -> "Gorilla Tab"`, with a dated restoration note). Flagged docs
   90/120/150 confirmed FALSE positives (quoted examples / real dir name
   `New..Skills`).
2. **8 new lesson atoms written** per SCHEMA.md (≤250 words, dual-track
   rationale, when_to_recall + wrong_instinct filled):
   08.Look: FF154_Renamed_Tokens_Beat_Legacy_Vars,
   Element_Level_Var_Redeclaration_Beats_Root_Important,
   InContent_Pages_Resolve_Light_Scheme, FTL_Rebrand_Damage_Triad_Repair,
   Preferences_One_PNG_Design_FF154; 07.TOOLKIT:
   Old_Base_File_Skew_Vault_Rebase; 13.JUNK.DRAWER:
   Vanilla_Vault_Plus_Snapshot_Restore, Scrubbed_Identifiers_In_Memory_Tiers.
3. **Contamination gate installed in `ingest_lessons.py`** (§13 item 7 DONE):
   refuses atoms with double-dot identifiers or doubled brand unless the atom
   text is ABOUT the corruption (exemption regex). Proven live: first run
   auto-caught the 3 audit-flagged docs; two were gate false-positives, regexes
   tuned (full-token match, `..Skills` allowlist, `duplicat` stem).
4. **Ingested & verified**: collection `firefox_154` now 178 vectors (170+8),
   idempotent upsert refreshed the repaired docs; recall test
   "urlbar text is black on black…" → new atom ranked #1 (d 0.501); second
   query improved by alias widening (atom #2). Remaining
   `media..hardware` string in DB = 1 doc, the scrub LESSON quoting it
   (by design).
5. **doc-audit toolkit**: `dual-track precheck FIrefox.154.Look` vs restored
   tree → 0 P0 / 0 P1, 6 benign upstream-TODO P2s. AGENT.md's stale
   gutted-tree FF_SRC warning replaced with the 2026-07-31 restored-state
   note.

## 19. 2026-07-31 (late night) — BACK-PROPAGATION: today's fixes made permanent (§13 item 4 DONE)

1. **25 category masters regenerated** as vault-vanilla→repaired-tree unified
   diffs, same naming convention, in place: 21× 08.Look (15 FTL + 6
   .properties incl. all 3 platformKeys) + 3× 07.TOOLKIT (nsContextMenu,
   appearance.mjs, browserLanguages) + browser-shared.css. Special cases:
   `appearance.mjs.patch` is now a ZERO-DELTA marker file (annotated: do NOT
   resurrect the old patch); `master-redirect.css.patch` is a NEW-FILE marker
   (authoritative master = FIrefox.154.Look copy).
2. **New snapshot**: `patches/Future.proof.APPLIED-STATE.2026-07-31.REPAIRS.tar.gz`
   (241 KB) = dir `Future.proof-2026-07-31.repairs/` with files/ (29 verbatim
   tree copies incl. tree CLAUDE.md), per-file-patches/, MANIFEST.txt
   (sha256, same format as 2026-07-16 incl. the `[OK]` annotation the
   verifier strips), README.txt with the restore ORDER: vault → 2026-07-16
   snapshots → Look copies → THIS LAST.
3. **Verified**: manifest-vs-tree = 29/29 OK (fail=0).
4. `Future.proof.INDEX.md` row added; `patch_status.tsv` nsContextMenu row
   updated to APPLIED with rebase note.
Restore procedure memory + Vanilla_Vault_Plus_Snapshot_Restore DB atom now
need the extra final step — updated same session.

## 20. 2026-07-31 (23h) — one-PNG doctrine restored on about:privatebrowsing + 166 more grafts

**User report + tiers check**: PB gorilla blurry vs newtab; suspected second
PNG. CONFIRMED both, with a twist:
- `about-logo-private.png` and `@2x` are BYTE-IDENTICAL duplicates of
  `about-logo.png`/`@2x` (346,651 / 1,033,163 bytes — ~1.4 MB duplicated, the
  doctrine was "satisfied" by file copy). Files left in place (vanilla refs
  may exist); OUR css no longer references them.
- Crispness delta explained by lesson `Crisp_Logo_Never_Upscale_Raster`:
  newtab paints `about-logo.svg` (embeds a 1200×1200 raster) into a 600px box
  (downsample = crisp); PB painted the 500px PNG at a hardcoded
  `background-size: 500px` (1:1, soft under any scaling).

**Fix (Look aboutPrivateBrowsing.css `.logo`, deployed, values verbatim)**:
600×600 box, max-width 95vw / max-height 70vh, `background:
url("chrome://branding/content/about-logo.svg") no-repeat center center;
background-size: contain` — mirrors nova-activity-stream `.logo-and-wordmark`
(and the user's remembered values, which matched the tiers).

**Bonus sweep (toolbox `ftl_graft_missing_messages.py`, tree-wide — the §10
graft had only covered 3 files)**: **166 further missing FF154 message ids
grafted**: newtab.ftl 91(!), viewer.ftl 24, customkeys.ftl 21, onboarding.ftl
19, formAutofill 5, backupSettings 2, features.ftl 2, sidebar/ipProtection 1
each. Parse gate after: 0 Junk tree-wide.
`defaultBrowserNotification.ftl`: missing=0 — the still-empty default-browser
popup body (19:35 screenshot) is NOT a string issue; §14 CSS re-judgement
awaits a restart that actually includes it (§13 item 1 residual re-opened).

**Deploy**: build faster (5 s); profile startupCache flushed.
**Back-propagation kept in lockstep**: repairs snapshot refreshed →
39 files, MANIFEST 39/39 verified, tarball re-cut (339 KB); 9 further
08.Look masters regenerated (newtab/onboarding/viewer/customkeys/etc).

## 21. 2026-07-31 (23h+) — 151/153→154 knowledge migration: 3 page-branding lessons

Continuing the old→154 lesson migration at user direction. Findings + work:

1. **Today's §16 bug was a RECURRENCE of a documented one**:
   `Duplicate_browserLayout_Setting_Group_Registration_Error` (153-era) records
   the same appearance.mjs duplicate-registration crash, fixed the same way
   (vault-restore) — then the 2026-07-16 snapshot re-deployed the old-base
   file and resurrected it. Recorded in the migrated atom as an explicit
   wrong_instinct ("a past fix is not permanent; snapshots can re-deploy fixed
   bugs — repairs snapshot applies LAST").
2. **3 atoms migrated old format → SCHEMA.md form** (old `<concept><title>`
   had NO name attribute — the current ingester silently SKIPPED them; they
   were reachable only via grep, not vector recall):
   `Branding_Internal_UI_Pages_with_Text_and_Logo_Injections` (THE canonical
   one-artwork concept: about-logo.svg/1200px raster + PNG family incl. the
   byte-duplicate -private files; 154-verified per-page values),
   `Completion_of_All_Gorilla_Internal_Page_Brandings` (inheritance-first rule;
   153-era MASTER.CSS.INJECTOR paths flagged OBSOLETE; points at
   ABOUT_PAGES_MEGA_LESSON as the 154 coverage index),
   `Duplicate_browserLayout_...` (both hits recorded). Each carries a
   `<history>` line preserving provenance.
3. **Ingested + verified**: 181 vectors (178+3); no stale duplicates by name
   or source (checked via chroma get); recall test "settings page links dont
   do anything preferences broken" → migrated atom ranked #1 (d 0.472).

Migration tally so far (user estimates ~30% of 151/152/153 knowledge
brought to 154): 8 new atoms (§18) + 3 migrated (§21) + 2 decontaminated
sources + 1 workflow doc repaired; ~40 old-format 08.Look XMLs remain
un-migrated (ingester skips them — grep-only until converted).

## 22. 2026-07-31 (20:22) — post-visual-check round: term graft, dark-scheme pref, promo containment

User verified §17/§20/§21 build: PB logo crisp ✓, newtab perfect ✓, PDF viewer
OK ✓, preferences body text + sidebar readable ✓. Three residuals fixed:

1. **Raw `{-smart-window-brand-name}` on #manageMemories**: FF154-NEW
   PARAMETERIZED term missing from branded `toolkit/branding/brandings.ftl`
   (vanilla defines it with `{ $plural-form -> [true]/[false] }` variants at
   :63). TOOL GAP found: `ftl_graft_missing_messages.py` regexes only match
   `[a-z]`-leading MESSAGES — Fluent TERMS (`-` prefix) were never compared.
   Tree-wide term scan: exactly ONE missing term. Grafted with vanilla's
   parameterized shape, branded values "Gorilla AI Window/Windows".
   brandings.ftl fluent-parse: 0 Junk.
2. **Grey-on-black text in shadow components** (sync/home cards, checkbox
   labels, search engine names — the "still screwed" right-hand side):
   in-content dark tokens are gated behind `@media (prefers-color-scheme:
   dark)`, unreachable by the §17 CSS-level color-scheme force on a LIGHT GTK
   system. Fix at the pref level: `user_pref("ui.systemUsesDarkTheme", 1)` in
   `~/.mozilla/ff154-main/user.js` — flips prefers-color-scheme dark
   product-wide (matches the all-black theme's intent).
3. **Privacy-pane promo image bleeding UNDER later cards**: the FF154 privacy
   promo banner is slim; our 480px `moz-promo img` overflowed it. Fix:
   `moz-promo { overflow: hidden !important }` (Look preferences.css) — image
   clips inside its card; home pane unaffected (card grows to fit). Z-index
   deliberately NOT raised (Z-Index Minimalism rule, VRAM economy on iGPU).
   Searched the tiers per user hint — no pre-existing lesson for this exact
   FF154 breakage (pane only started rendering after §16/§17); the design
   values + z-index rule informed the fix.

Deploy: build faster (5 s); startupCache flushed. Lockstep: snapshot now 41
files (manifest 41/41 OK), tarball re-cut, brandings.ftl master regenerated,
profile user.js captured as `user.js.PROFILE-APPLIED-2026-07-31` in the
snapshot dir. sha256: brandings.ftl `08096292…a325d5`, Look preferences.css
`dd9e6930…3687d8`, profile user.js `e4b07602…f10be`.
TODO next session: extend ftl_graft_missing_messages.py to also compare
`-term` definitions (the §22 tool gap).

## 23. 2026-07-31 (21:03) — full about:-page punch list (user's complete visual sweep)

User swept EVERY about: page and supplied intended designs. The snarky custom
strings were post-07-16 work lost in the unrecoverable window (searched all
tiers — absent); the AUTHOR re-supplied them verbatim in-session, making
their message the spec. Documented lessons supplied the logo values
(Fixing_the_about_welcome/translations_Logo_Sizing, GATHERED_BRAIN_LESSONS).

KEY DIAGNOSIS: the shared watermark `#content { background: about-logo.png
… / 800px }` (common-shared tail) hits EVERY in-content page with a #content
container — 500px PNG at 800px = UPSCALED BLUR (about:addons complaint) and
uninvited bleed-under-cards on about:webrtc.

| Page | Fix (values verbatim) |
|---|---|
| about:addons | watermark URL → about-logo.svg (1200px raster; crisp at 800px). Look + tree common-shared.css |
| about:webrtc | `#content { background: none !important }` appended to toolkit/content/aboutwebrtc/aboutWebrtc.css (author: no gorilla here) |
| about:robots | "Welcome Humans!" → "Welcome Morons!", button label2 → "Don't you DARE to press this button again" (aboutRobots.ftl — file is browser/locales, NOT toolkit) |
| about:studies | noStudies + disabledList → "We do not do studies… We refuse to be test subjects." (aboutStudies.properties) |
| about:translations | blocked-message → the full Bergamot/NMT rant (aboutTranslations.ftl:27); logo 200×200 !important + display:block (about-translations.css, per lesson) |
| about:telemetry | user.js: toolkit.telemetry.enabled/unified/archive + datareporting.healthreport.uploadEnabled + datareporting.policy.dataSubmissionEnabled ALL false; centered 500px svg watermark on body (toolkit/content/aboutTelemetry.css) |
| about:welcome | .brand-logo 300×300 (lesson values); split-screen fox art replaced with 500px-capped gorilla svg on black, inner picture/img hidden (aboutwelcome.css) |

Parse gates: aboutRobots/aboutTranslations 0 Junk. Deploy: build faster;
profile startupCache flushed. Lockstep: snapshot 48 files (manifest 48/48),
tarball re-cut, 3 more 08.Look masters regenerated.
STILL OPEN from the sweep: about:profiling (black page, elements invisible —
does not use common in-content styles; needs its own investigation);
about:studies/telemetry gorilla + text CENTERING to be visually judged after
restart; §13 item 1 (default-browser popup body) unchanged.
Context note: the "10-minute nap" damage incident the user described is
referenced in LESSONS_MASTER.xml — the lost-window (07-16→07-30) work
includes those custom strings; author re-supply is the recovery path.

## 24. 2026-07-31 (21:30) — §23 visual verdicts + two adjustments

USER VERDICTS on the §23 build:
- **about:welcome — APPROVED WITH ENTHUSIASM** ("TWO FOR THE PRICE OF ONE.
  LOVE IT"): the split-screen gorilla + the built-in brand-logo gorilla both
  render; the double-gorilla layout is now INTENTIONAL DESIGN — do not
  "deduplicate" it.
- about:telemetry: gorilla crisp; strings/pref state to re-verify after the
  §23 prefs (screenshot predates restart with them).
- about:studies: custom text PRESENT but black-on-black (select-to-reveal).

FIXES:
1. `toolkit/components/normandy/content/about-studies/about-studies.css`
   (page has its OWN palette outside the in-content token flow — hardcoded
   #737373-class colors): appended force-block — body + study elements
   `color: #00FFFF !important`, links `#35b3ee !important`.
2. `toolkit/content/aboutTelemetry.css`: watermark position
   `center center` → `center bottom 60px` (author spec 21:22).
Deploy: build faster; startupCache flushed; snapshot now 49 files, tarball
re-cut. Verify: restart → about:studies text cyan without selecting;
telemetry gorilla near bottom.

## 25. 2026-07-31 (close of day) — knowledge close-out

Five closing dual-track atoms written + ingested (firefox_154 now **186
vectors**; recall test "text only shows when I select it black page" → new
atom #1 at d 0.547): Shared_Content_Watermark_Hits_Every_Page,
Page_Local_Palettes_Outside_Token_Flow, Dark_Tokens_Need_OS_Level_Pref
(filed under 05.PREFS), Fluent_Terms_Are_Not_Messages,
Author_Memory_Is_A_Recovery_Tier. §22's tool TODO closed:
ftl_graft_missing_messages.py now compares `-`-prefixed TERMS too.
Day total into the DB: 8 (§18) + 3 migrated (§21) + 5 (§25) = 16 atoms,
all schema-conformant, contamination-gated, recall-tested.
This log at close: 749 lines, 25 sections, 36 hash references.
sha256 (BEFORE this §25 entry): 0d455002cdfa7dd56792368450e52a22108b0171f8b44040324c970b72a4c0b9

## 26. 2026-07-31 (late) — notes/ single-source-of-truth reconciliation

User-directed cleanup of the four competing notes artifacts. Doctrine now
stated in each via a common SOURCE-OF-TRUTH banner (events→this log;
inventory→repairs MANIFEST + MAP_IBM; lessons→chroma firefox_154):

1. **AUDIT_REPORT_08.Look.md**: its 2026-07-10 **PASS verdict RETRACTED with
   hindsight** (banner prepended, original preserved) — it scanned the FTL
   set while the sed damage was present; that era's rules couldn't see those
   classes. Current rule state cited (precheck 0 P0/0 P1); fresh audit due
   after next full build.
2. **CSS_FTL_FILES_REGISTRY.md**: marked as the historical 2026-07-01 census
   (2324 files) — pre-restore, non-binding; kept for 153-era breadth record.
3. **firefox_appearance_timeline.md**: "2026-07-31 — THE GREAT RESTORATION"
   chapter appended (the day's arc, pointing here for forensics).
4. **UI_Tweaks_Master_Collection/00_STATUS**: canonical-location correction
   appended — AND the real divergence it exposed was FIXED:
   `new.patches/08.Look/NEW_FILES/.../master-redirect.css` was **128 lines
   stale (187 vs 315)**; re-synced from the Look master, cmp-verified
   identical. Rule recorded: on divergence, the Look copy wins.
   (Other NEW_FILES css copies checked: installing_page, profile_cleanup,
   aboutDialog already synced.)
No stale "CANNOT reach toolkit" wording remains anywhere outside this log's
own quotations (swept Mega.Lessons + the collection).
