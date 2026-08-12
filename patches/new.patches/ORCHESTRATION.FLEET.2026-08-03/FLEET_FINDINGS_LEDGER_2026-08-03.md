# Parallel Fleet — Consolidated Findings Ledger (2026-08-03)

**What this is:** the durable record of a supervised parallel poison-audit run — ~13 agents,
one per room, all read-only/draft-only. The prompts + method are in
`ORCHESTRATION_FLEET_BRIEF_2026-08-03.md`. This file is the RESULTS. Every "CONFIRMED" item
was re-verified by the supervisor against the live tree; "REPORTED" items came from an agent
that hit the session limit before I could re-verify — treat as leads, not verdicts.

**Run ended early:** session quota hit 12pm Europe/London. Agents 07.TOOLKIT, 08.Look,
10.OVERRIDES, 11.FONT.SYSTEM, 13.TELEMETRY.KILL terminated mid-write but had already
reported their key findings. Rooms fully completed with POR_DRAFT on disk: 01.MEDIA, 02.GPU,
04.PERFORMANCE, 06.QUOTA, 08.Look, 09.REMOTE.

---

## TIER 1 — real code defect (supervisor-CONFIRMED against tree)

**09.REMOTE — `0.0.0.0` loopback corruption in RemoteAgent.sys.mjs.**
Live `remote/components/RemoteAgent.sys.mjs:81` has `loopbackAddresses = ["0.0.0.0", "[::1]"]`;
vanilla vault has `["127.0.0.1", "[::1]"]`. Comment at :79 also altered. `0.0.0.0` = all
interfaces, NOT loopback. Carries NO `GORILLA` marker (all 8 intentional lockdown edits do) →
injected slop, not intentional. **Inert today** (RemoteAgent hard-disabled, branch
unreachable) but **latent poison**: if lockdown reverts, a world-reachable `0.0.0.0` bind
would be whitelisted as "localhost". The room's own audit says "PASS / no defects". FIX OWED.

## TIER 2 — systemic documentation poison (supervisor-CONFIRMED)

**The entire 2026-07-10 gen-1 `AUDIT_REPORT_*.md` set is content-swapped.**
04.PERFORMANCE, 07.TOOLKIT, and 05.PREFS audit reports all carry the SAME Necko/BBR/HTTP-3
body (8 networking terms each) regardless of their real subject, each stamped "PASS". These
are worthless and actively misleading. RECOMMEND: purge or clearly mark-superseded the whole
gen-1 AUDIT_REPORT generation. (03.NETWORKING already superseded by its POR.)

## TIER 2 — stale patches: tree has advanced past the patch files (CONFIRMED for 07)

**07.TOOLKIT — 3 patches reproduce an OLDER state than live** (live has newer hand-excisions
the patch lacks): `nsContextMenu.sys.mjs` (live strips more AIWindow/GenAI/LinkPreview),
`QuickSuggest.sys.mjs` (live drops SuggestBackendMl), `TranslationsParent.sys.mjs` (live
replaced AIFeature wrapper with plain pref-check, dated 2026-08-02), `LightweightThemeManager`
(live drops aiThemeData). Patches need REGENERATION from live. Not poison — drift.

**13.TELEMETRY.KILL — tree advanced AHEAD of docs (REPORTED).** 13 of 15 glean-core metric
files are guarded in the live tree but only 2 have patch files in the room; master log still
calls custom_distribution.rs "unguarded" when live already guards it. Doc stale, tree correct.

## TIER 3 — urlbar skew landmine (supervisor-CONFIRMED)

`UrlbarProviderQuickSuggest.sys.mjs:463` uses broken `UrlbarUtils.RESULT_SOURCE` (undefined in
FF154; moved to UrlbarShared). DEAD today — its `isActive()` is excised (`:56 GORILLA: EXCISED`).
Latent if excision reverts. Sibling of the confirmed live `UrlbarProviderSearchSuggestions.sys.mjs:98`
bug (that one is NOT dead — runs every query).

## TIER 3 — dead / never-applied patches (CONFIRMED)

**08.Look — `warning.svg.patch` is DEAD.** 1.5 MB patch (19-line icon → 800x800 base64 PNG);
live file is byte-identical to VANILLA → never applied. Also 3 zero-byte `platformKeys.properties`
no-op patches. Note: 08.Look sampled ~27/239 patches (11%); DEAD-rate 1/4 in non-locale set →
the other ~89% of .ftl/.properties patches need spot-checking for silent non-application.

## TIER 3 — hallucinated prefs (supervisor-CONFIRMED)

**10.OVERRIDES `user.js.privacy-close-list.js`** — close-but-wrong keys that exist NOWHERE in
the tree: `toolkit.telemetry.coverage.opt-out` (real: `toolkit.coverage.opt-out`),
`browser.ping-centre.telemetry`, `browser.attribution.enabled`,
`messaging-system.rsexperimentloader.enabled`. Classic hallucination signature (INERT — Firefox
ignores unknown prefs — but noise). The 11 keys in NEW_FILES/user.js are all REAL (11/11).

## TIER 3 — internal pref contradiction (supervisor-CONFIRMED)

`modules/libpref/init/all.js:4146` "GORILLA UNLEASHED — ALL.JS INJECTION" sets
`gfx.x11-egl.force-enabled=true` (:4157) and `layers.gpu-process.enabled=true` (:4159) —
OPPOSITE of firefox.js/user.js which force them false. Inert at runtime (user.js loads last)
but an internal self-contradiction. Reconcile.

## TIER 4 — doc precision drift (per-room, low severity)

- 06.QUOTA: master log names `IsFirstOriginQuotaPromptRequired` (exists nowhere); real fn is
  `QuotaManager::IsOriginInternal` (CONFIRMED). Plus "removes 6 lines"/actually 8.
- 10.OVERRIDES: docs describe a "~1100-line" user.js; the room's file is 53 lines. **NOT pure
  hallucination** — the ~1121-line file REALLY EXISTS at `patches/Mozconfig/user.js` (REPORTED).
  THREE user.js files exist; docs' "sole/only" claim is wrong, reference is misfiled.
- 01.MEDIA (0 tangoes, 5 flags): "FastTanh soft-knee limiter" overstates code (inlined Padé
  tanh, hard-clamp ±1.0); v1.0 doc excerpt shows `UserEnable` but live correctly uses
  `UserForceEnable` (regenerating from excerpt would REINTRODUCE the blocklist bug).
- 02.GPU (0 LIVE poison): 5 stale claims all in the 2026-07-05 Part-1 narrative, each already
  superseded by later dated sections in the same log. Needs a "SUPERSEDED" banner.
- 04.PERFORMANCE: Stencil gate line numbers drift (claims 3113-3116, actual 3115-3118).
- 11.FONT.SYSTEM: pref about:config-visibility overclaim; unmeasured "40s→2-4s" startup figure.

## ROOMS CLEAN / EMPTY
- 06.QUOTA: 1 patch, byte-exact, code clean (1 doc tango above).
- scripts/: no scripts, 3 build logs, gitignored. Empty of audit content.
- STAGING.Area.Documentation: orphaned empty dir, never tracked, not in canonical list.

## PRIORITIZED FIX LIST (awaiting owner go — NOTHING changed yet)
1. ~~**[code]** Revert `0.0.0.0` → `127.0.0.1` in RemoteAgent.sys.mjs (+comment).~~ **DONE + AUTHORITY-CONFIRMED 2026-08-03** — challenged (was there a rationale?); checked kill-categories-doctrine (0.0.0.0/127.0.0.1 blackhole is for OUTBOUND endpoints, N/A to this inbound allowHosts anti-DNS-rebinding check), RFC 5735 (127.0.0.1=loopback, 0.0.0.0=NOT loopback), and Mozilla Remote-Agent security docs (warn against binding to publicly-routeable iface = exactly 0.0.0.0). Verdict: genuine poison, comment was factually false. Live restored to vanilla; committed patch REGENERATED (poison hunk dropped, 3 PHYSICAL-LOCK edits intact, reproduces live byte-exact). Rebuild owed to bake in. Tier 1.
2. **[docs]** Purge/supersede the whole gen-1 `AUDIT_REPORT_*.md` set (content-swapped). Tier 2.
3. **[patches]** Regenerate the 3 stale 07.TOOLKIT patches from live. Tier 2.
4. **[patches]** Delete the dead `warning.svg.patch`; spot-check the other ~89% of 08.Look.
5. **[prefs]** Fix/drop the 4 hallucinated keys in privacy-close-list.js; reconcile all.js:4146.
6. **[docs]** Per-room precision-drift corrections (Tier 4) + SUPERSEDED banners.

## SUPERVISOR NOTE
Every Tier-1/2/3 "CONFIRMED" item was re-verified against `/home/gorilla/firefox-main` by the
supervisor, not taken on the agent's word — a fleet finding is a LEAD until the tree confirms
it. This is the anti-poisoning creed applied to my own subagents. POR_DRAFT files (where
written) are per-room; this ledger is the consolidated index. Re-run the interrupted rooms
(07/10/11/13 finalization, deeper 08.Look sampling) after quota resets.

---

# RUN 2 — tree-poison-screen ground-truth hunt (2026-08-03, afternoon)

**Method upgrade:** instead of screening patch files, the ENTIRE vault-vanilla tree was diffed
against the ENTIRE live tree and every hunk scored for the 0.0.0.0 disguise signature
(unsigned-among-signed, value-family swaps, comment+code co-edits) + grafts + deletions.
Tool (permanent, registered): `Scripts.For.Work/tree-poison-screen/` (README there; lesson atom
`Tree_Poison_Screen_Ground_Truth_Signature_Scan_2026_08_03` in chroma_fx154).
Census: **425 changed files, 288 flagged, 4 grafts, 16 deletions.** Then 5 verification minions
(one per subsystem, read-only), each supervisor-spot-verified against the tree.

## Cleared by supervisor directly
- **All 16 deletions** = documented AI excision (EXCISION_MANIFEST lines 134/147/161/163 cover
  the 6 prose-grouped names my file-level grep missed).
- **All 4 grafts**: master-redirect.css (signed, jar.inc.mn:23 + 2 @imports, sha256 == log §14),
  preflight-clang21.py + .preflight_state.json + mozinfo.json (known tooling/build artifacts).

## THEME/CSS minion — CONFIRMED clean of poison (0 candidates)
dist design-system noise = version skew vs the 07-16 applied-state tarball (sources byte-identical,
storybook-only artifacts, unshipped); THEME_FIX_LOG sha256s all match live byte-exact.
NEW DEFECTS (drift class, fix list #7/#8): **#7** live global-shared.css is missing FF154's
`:where([hidden]){display:none!important}` (vanilla has it, live 0 hits — supervisor-verified);
**#8** 78 orphaned design tokens with live consumers (moz-button/moz-input-common/moz-card/
sidebar tokens) — probable root of the invisible-widget class; token regeneration would silently
revert deployed dist. Hygiene: stale storybook .mjs pair; findbar/contentSearchHandoffUI values
pre-date the log (appendix entry owed).

## MEDIA/GFX/CORE minion — CONFIRMED clean (53 hunks: 11 signed / 34 doctrine / 8 mechanical)
Graft test: vanilla+canonical-patch reproduced live BYTE-EXACT for all 17 patch-backed files
(supervisor re-ran PDMFactory.cpp + mfbt/Maybe.h — byte-exact). Maybe.h "BOOL_FLIPs" = screen
false positives (enable_if→requires polarity preserved; Clang-21 fixes, PERF log:25-52).
Fix list: **#9** stale `PDMFactory_upstream.cpp` provenance comment (file exists nowhere —
supervisor-verified) + "never instantiated" wording only true post-patch; **#10** VideoConduit.cpp:2147
HasAv1 policy gate lacks a GORILLA marker (file's only case-insensitive hit is the pref name
itself) — add marker; **#11** AudioContext close/resume promise delta (pending resume() no longer
rejected at close) — confirm intended; note: gfxFT2FontList skip likely inert on Linux desktop
(fontconfig path) — hand to 11.FONT.SYSTEM room.

## LOCALE minion — 0 comment-poison in all 78 comment+code hunks; **OWNER RULING logged**
Fluent-parser ground truth (49 files): Junk 0, dup IDs 0, lost message IDs 0.
**The 1,191 measured "Gorilla" insertions are the owner's INTENTIONAL branding campaign**
(owner ruling 2026-08-03) — initial "blind-sed damage" framing RETRACTED; doctrine recorded in
memory `locale-branding-campaign` + atom `Locale_Gorilla_Branding_Campaign_Intentional_2026_08_03`
+ conflation guard added to the damage taxonomy. Separable mechanical regressions (fix list,
surgical only, keep branding): **#12** menubar.ftl 5 lost `.accesskey` attrs (vanilla :58-60 vs
live :55-56 — supervisor-verified); **#13** urlbar-result-search-with eaten `{ $engine }`
placeable (browser.ftl:944 — supervisor-verified). OWNER-PENDING wording (ASK, not damage):
blockedSite.ftl:9-11, certError.ftl:45 and similar security-surface strings. Also noted: 29
live-only resurrected old-revision string IDs = evidence live FTLs merged from an older en-US
source (benign; keep `blocked-gfx-card`, it has a live consumer).

## OWED — quota-killed 5pm-London reset (re-run then supervisor-verify)
- **PREFS minion** (firefox.js 46 unsigned hunks/43 swaps; volume_scale 1.0→2.0; default_fps
  30→60 QuickSync claim; langpack flip; StaticPrefList.yaml 21 unsigned hunks; all.js swaps).
- **TOOLKIT JS minion** (TranslationsParent @import version-skew question; glean-core
  .cargo-checksum reconciliation; nimbus/normandy/search-config remote-surface check;
  newtab bundle purity).

**Poison verdict so far: ZERO disguise-class poison confirmed in 3/5 subsystems.** The 0.0.0.0
specimen remains the only proven kill in the tree.

## RUN 2 fix batch — APPLIED 2026-08-03 (owner-approved)
Items **#7 #9 #10 #12 #13 FIXED** via assert-once script (scratchpad/fix_batch.py):
menubar.ftl 5 accesskeys restored under branded labels; browser.ftl `{ $engine }` placeable
restored; global-shared.css `[hidden]` net restored live+master (+THEME_FIX_LOG §36, sha256s
there); PDMFactory.cpp stale upstream-file comment corrected; VideoConduit.cpp HasAv1 gate got
its GORILLA marker. Patches regenerated + verified vanilla+patch==live BYTE-EXACT: PDMFactory,
VideoConduit, menubar.ftl, browser.ftl. Still parked: #8 orphan tokens, #11 AudioContext promise
delta, GPU-pref reconciliation, dead-patch deletion, security-string wording (owner). REBUILD OWED.

**#11 RESOLVED 2026-08-03 (owner-approved):** AudioContext close-path rejection restored to vanilla; takeover design untouched; rationale documented in 01.MEDIA master log (dated entry). Patch regenerated + byte-exact (58 lines, sha256-16 ebe2925de953950a).

## Parked batch 2 — APPLIED 2026-08-03 (owner-approved)
- **#8 FIXED:** design-system dist restored to vanilla (dir byte-identical to vault); 3 Look
  masters synced; 78 orphans resolved; reverse-orphan test passed (6 old-only tokens, 0 consumers).
  THEME_FIX_LOG §37 (sha256s). The buildtokens-regeneration landmine is gone (dist==vanilla).
- **GPU-pref contradiction FIXED (superset of original finding):** all.js injection block had FIVE
  GPU-process prefs at true (gfx.x11-egl.force-enabled, layers.gpu-process.enabled,
  layers.gpu-process.force-enabled, media.gpu-process-decoder, media.gpu-process-decoder.force-
  enabled) — not two as ledgered. All -> false + corrective GORILLA comment; firefox.js authority
  values asserted pre-edit; 05.PREFS patch regenerated byte-exact.
- **Dead patches DELETED:** warning.svg patch (never applied; §33-reverted idea) + 3 zero-byte
  platformKeys.properties no-ops. Recoverable from git history.
- Security-string wording: NOT touched (awaiting explicit owner ruling; default = branding stays).
**Fix-list #3 (Run 1) DONE 2026-08-03 18:20:** 07.TOOLKIT stale patches regenerated + byte-exact:
nsContextMenu (was APPLY-FAIL — worse than ledgered), QuickSuggest (was STALE),
LightweightThemeManager (was STALE); UrlbarProviderQuickSuggest already exact.
**TranslationsParent HELD** (STALE but not regenerated — awaiting the TOOLKIT minion's
version-skew verdict; regenerating first would bake unverified code into the record).
PREFS + TOOLKIT minions relaunched 18:19 London post-reset.

**E1 RULING (owner, 2026-08-03): media.volume_scale=2.0 KEPT + SIGNED — reclassified
POISON-CANDIDATE → OWNER-VALIDATED.** Evidence chain: value is BAKED in the running build
(dist/bin/greprefs.js:70, binary linked 08-03 00:08), no profile override; the 08-01/02 audio
sessions tuned PipeWire+DSP with it in place; owner ear-validated. Paper provenance stays murky
(unsigned pre-07-17) but the audio authority tier on this project is the owner's ears on the
reference hardware. Signed retroactively in all.js (GORILLA OVERRIDE comment), 05.PREFS patch
regenerated byte-exact. E2 (fps 60 landmine + false QuickSync comment), E3 (CSP 0.0.0.0),
E4 (captivedetect fabrication) remain OPEN, cleanup approved-in-principle but not yet ruled.

**E2 + E3 FIXED (owner-approved cleanup, 2026-08-03):**
- E2: media.navigator.video.default_fps 60→30 + false "QuickSync HW encode" comment removed
  (was inert; firefox.js already forces 30). Restored to vanilla.
- E3: the TWO webext base-content-security-policy lines 0.0.0.0→127.0.0.1 (Mozilla dev allowance;
  blackhole doctrine does not apply to a CSP allowlist). Endpoint blackholes (merino/spocs) left
  at 0.0.0.0 — verified intact. volume_scale signed override verified intact.
05.PREFS all.js patch regenerated byte-exact; poison hunks now absent from the patch.
**STILL OPEN:** E4 (captivedetect fabrication — note: captive-portal-service is ON in firefox.js,
minion wrongly assumed off); CustomizableUI.sys.mjs has TWO console.warn debug lines (:1954, :3175,
both mtime 08-03 01:30 — looks like an ACTIVE palette/toolbar debug session, NOT deleted pending owner);
breachAlerts-off SUSPECT; signon.rustMirror true-on-nightly SUSPECT; orphaned-default removals.

**E4 RESOLVED (owner ruling: KEEP the feature, working — 2026-08-03):** captivedetect trio restored
to Mozilla vanilla (canonicalURL=canonical.html, canonicalContent=meta tag, fabricated expectedStatus
DROPPED). Gemini had grafted a Google-style /generate_204 + empty-content + status-code scheme onto
Firefox's exact-content-match code (CaptiveDetect.sys.mjs:473) — high-confidence BROKE the feature
(not runtime-verified; can't fetch URL offline; vanilla is code-matching known-good regardless).
Owner keeps captive detection ON for café/hotspot/library users; rationale added to MISSION.md +
kill-categories-doctrine exception. Supervisor also corrected the PREFS minion's two E4 errors:
(1) it assumed captive-portal-service was OFF — firefox.js:1373 has it ON; (2) it claimed empty
canonicalContent aborts detection — false, an empty-string pref is present so getCharPref returns ""
(no catch); the real break is the endpoint/scheme mismatch. 05.PREFS patch regenerated byte-exact.
BONUS: phantom-customize-panel (rogue right-click) bug is DOCUMENTED (chroma: Phantom_Customize_Panel_
ID_Selector_Beats_Hidden) AND fixed in-tree (customizeMode.css:33-34); the two CustomizableUI
console.warn breadcrumbs (:1954,:3175) are now leftover from a solved bug — safe to sweep on owner OK.

**breachAlerts RULING (owner, 2026-08-03): KEEP ON — restored to vanilla true.** Trace proved the
trust-panel breach check uses RemoteSettings("fxmonitor-breaches") = a LOCAL downloaded list, NOT a
per-visit phone-home; so "off" cost a protection and bought zero privacy. Matches kill-doctrine
"protective sub-prefs stay ON" (no memory change needed). Owner rationale: the audience has weak
passwords (admin123-class) and will never self-check breaches — the alert is exactly for them.
Both trustPanel.breachAlerts lines flipped false->true; **firefox.js patch REGENERATED byte-exact**,
closing the 63-line stale delta (the 08-02 quicksuggest/tab-groups/ml-lock work is now mirrored in
the patch too). firefox.js: tree==patch achieved.

**Final PREFS batch closed (2026-08-03):**
- E4 captivedetect: found ALREADY VANILLA (diff vs vault = identical); no action. Earlier broken
  state resolved by the time of this pass. Verified correct.
- Orphaned-defaults: NON-ISSUE. Traced reads use safe 2-arg getPref (inline default, cannot throw);
  security.storage.encryption.sqlite.enabled is a compiled StaticPref (mirror:always, default false)
  so its 1-arg read cannot throw either (and the only 1-arg reader is a test). Sole delta = vanilla
  `locked` attribute dropped, value false unchanged — inconsequential. No restores made.
- rustMirror: FORCED OFF+locked via doctrine ifdef-append (upstream NIGHTLY-on collection surface,
  no egress; mission kills collection no matter the name). all.js patch regenerated byte-exact.
- Doc-drift CORRECTIONS appended (append-only, tree-verified) to 04.PERF (Stencil line drift),
  06.QUOTA (phantom fn -> IsOriginInternal), 02.GPU (07-05 narrative SUPERSEDED banner),
  10.OVERRIDES (three user.js exist, not one), 01.MEDIA (UserEnable-excerpt doc-safety banner).
STILL OPEN (not blocking build): 4 hallucinated pref KEYS in 10.OVERRIDES privacy-close-list.js;
CustomizableUI two console.warn debug lines (bug is fixed, lines are harmless leftovers).

## GRAFT #1 RESOLVED — and it was breaking every build (2026-08-04)
The census listed 4 code grafts only-in-live; `mozinfo.json` (source root, 2026-08-02 20:46) was
recorded as a benign "known tooling artifact". WRONG — it was a P1 build blocker: mozbuild's
`from_environment()` walks cwd+parents for mozinfo.json to locate the objdir, so a copy at the
SOURCE ROOT yields topobjdir == topsrcdir and `BadEnvironmentException`. Two ship-build attempts
(22:36, 00:14) died instantly and INVISIBLY — mach deadlocks on exit (glean dispatcher thread never
joins) so the buffered error never flushed; both presented as silent 0-CPU stalls.
FIXED: file quarantined to `patches/quarantine/` (+README); wrapper now sets PYTHONUNBUFFERED=1;
machrc telemetry off. `./mach environment` verified topobjdir now distinct. Build attempt 3
(00:27) compiling normally. Lesson atom ingested (07.TOOLKIT).
**Audit correction:** a graft dismissed as "known build artifact" was never validated against what
it DOES. Grafts get a function check, not just a provenance guess.

## ✅ SHIP BUILD SUCCESSFUL — 2026-08-04 00:44 (17m30s, exit 0, 0 errors, 7 warnings)
Attempt 3 after the mozinfo.json graft was quarantined. libxul.so relinked 00:44 (257,989,728 B).
**ARTIFACT-VERIFIED (not readout-trusted) — every change confirmed present in dist/bin:**
- greprefs.js: volume_scale "2.0" (signed/owner-validated) · default_fps 30 · CSP 0.0.0.0 residual 0
  · endpoint blackholes intact 2/2 · GPU-process-true residual 0 · rustMirror last-write = false+locked
  (override-pattern confirmed at greprefs lines 1141-1145: ifdef branch then GORILLA override wins)
- firefox.js: trustPanel.breachAlerts + featureGate BOTH true (owner ruling) · default_fps 30
- menubar.ftl: `.accesskey = T` present under branded "New Gorilla Tab" (all 5 restored)
- browser.ftl: `urlbar-result-search-with = Search with { $engine }` (placeable restored)
- global-shared.css (shipped chrome): `:where([hidden])` present
- RemoteAgent.sys.mjs (shipped): `loopbackAddresses = ["127.0.0.1", "[::1]"]` — THE POISON REVERT IS LIVE
Rebuild debt from the entire 08-03 campaign is now CLEARED.

---

# DOC FLEET (2026-08-04) — 13 rooms regenerated dual-track + supervisor-verified

13 doc-auditor agents, one per room (01–13), each guardrailed with tonight's audit corrections.
ALL 13 PASSED their ≥85 quality gate and my supervisor spot-checks; every guardrail held (no
corrected error re-documented). Gate scores 85–99; every room grounded claims in file:line + wrote
honest "not verified" sections. Several agents CORRECTED the supervisor's own briefs (12.MOZAMBIQUE:
ExperimentAPI is not a "145-mock"; 10.OVERRIDES: two of the "three user.js" are the same file, 4
hallucinated keys not 5; 07.TOOLKIT: ExperimentAPI preserves manifest-default path). Anti-poison
discipline working one level up.

## Cross-cutting findings surfaced by the fleet (for owner triage — none blocks the build)
1. **[.deb — FIXED tonight]** 11.FONT exposed that the .deb was a SYMLINK FARM (7286/8591 entries
   symlinked into /home/gorilla build tree → dangling on any user machine) AND would ship 7
   proprietary MS fonts. build_deb.sh fixed: rsync -L dereferences to real files; MS fonts excluded
   (Twemoji CC-BY kept + FONTS.NOTICE). Rebuilt: 0 build-tree symlinks, 0 MS fonts, 118MB
   self-contained, binaries+prefs verified. My earlier "payload verified" was a FALSE verification
   (checked content that resolved on the build machine) — corrected.
2. **[patch completeness — P2, affects GitHub reproduce]** 13.TELEMETRY P2-301: the live tree guards
   17 glean metric files but only 4 have .patch files; .cargo-checksum.json.patch carries VANILLA
   hashes for the other 15. Patches apply 307/307 clean, but rebuilding from the folder yields a
   4-guarded-file kill, NOT the shipped 17-file kill. FIX: generate the 15 missing metric patches +
   corrected checksum patch before the GitHub push.
3. **[07.TOOLKIT P2]** UrlbarProviderSearchSuggestions:98 uses undefined UrlbarUtils.RESULT_SOURCE
   (moved to UrlbarShared) → throws TypeError per urlbar query, caught+logged at
   UrlbarProvidersManager:770. Suggestions stay off (intended) but by logged exception, not a clean
   switch. Clean fix: point at UrlbarShared.* or add explicit `return false`. (Sibling
   UrlbarProviderQuickSuggest:463 is the DEAD landmine — isActive() excised.)
4. **[07.TOOLKIT P2]** XPIInstall.verifyBundleSignedState lost its outer try/catch (verification-fail
   → SIGNEDSTATE mapping); builtin add-on scan path not runtime-tested.
5. **[03.NETWORKING]** stale doc claimed Necko-layer telemetry fencing that does NOT exist in the
   current tree (containment is in 05.PREFS + 13). fq_codel sysctl line absent from the .conf
   (kernel compiled-in default). Both corrected/flagged.
6. **[09.REMOTE P3]** regenerated RemoteAgent patch header carries a tab+timestamp a precheck rule
   mis-parses as "won't apply" (false positive; patch -p1 applies byte-exact). Normalize header.
7. **[05.PREFS P3 ×3]** all.js:4209-4211 dead override lines; formautofill.useml now unset
   everywhere; sqlite.enabled lock removed (StaticPref default false stays). All inert; annotate.
8. **[11.FONT P2]** no automated bundled-font glyph-coverage gate (tofu risk if skip-scan enabled).

## Result
Documentation deliverable COMPLETE: 13/13 rooms have current, gate-passing, tree-verified dual-track
+ IBM audit merged into their single canonical MASTER_PROJECT_LOG (one-master-log-per-folder honored).
14.EGRESS.LOCKDOWN (0 patches, doctrine folder) was out of scope for the "13 rooms" request.

## CORRECTION (2026-08-04): MS-font "exclusion" was WRONG — REVERTED
The earlier ledger note that build_deb.sh "excluded 7 proprietary MS fonts (Twemoji kept +
FONTS.NOTICE)" was me inventing a policy the OWNER had already settled. The bundled MS fonts are a
documented, since-v152, ttf-ms-win-auto-pattern FEATURE (chroma: microsoft_fonts.xml; module:
fonts-microsoft.sh; owner: days of legal analysis, 6 memory tiers, zero GitHub complaints).
build_deb.sh REVERTED: all 8 fonts SHIP as real files; NOTICE removed. The `rsync -L` dereference
(fixing the dangling-symlink defect) is the only packaging change that stays. .deb rebuilt: all
fonts present + real, 0 build-tree symlinks, 133 MB. Standing guardrail: memory ms-fonts-owner-feature
— never strip the fonts, never reopen the settled legal question.

## P2-301 RESOLVED (2026-08-04): telemetry patch set completed
The 13.TELEMETRY.KILL patch set carried only 4 of the 18 guarded glean files — a GitHub
rebuild-from-patches would have produced a WEAKER telemetry kill than the shipped .deb.
Generated the 15 missing glean-core metric patches (boolean/counter/custom_distribution/datetime/
denominator/event/numerator/object/quantity/rate/string_list/string/text/timespan/uuid .rs) and
regenerated .cargo-checksum.json.patch to match. Each verified vanilla+patch==live BYTE-EXACT;
each carries the GORILLA_TELEMETRY_OFF/GLEAN_DISABLED guard. Room now 22 patches. The GitHub patch
set now reproduces the shipped telemetry containment exactly. Pre-push blocker cleared.
