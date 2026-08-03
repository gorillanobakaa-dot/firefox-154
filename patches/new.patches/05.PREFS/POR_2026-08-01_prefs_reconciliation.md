# POR — Prefs Reconciliation & Lock-Down (2026-08-01)

**Operation:** clear the prefs/config room — ID Gemini poison, adopt the canonical
fuller config into the build, lock the critical subset, immortalize in the DB.
**Auditor:** Fable 5 / ultracode. **Authorization:** author (adopt-canonical + lock-critical).

## Tangoes neutralized (Gemini poison)
1. MASTER_PROJECT_LOG claimed "weather locked to 0.0.0.0 dummy endpoints" — FALSE (no 0.0.0.0 anywhere; only weather.featureGate=false). Hallucination.
2. MASTER_PROJECT_LOG cited fake line numbers (firefox.js 2435-2440, StaticPrefList 12681 vs real 12746).
3. config/firefox.js carried `media.peerconnection.video.vp8_enabled=true` — CONTRADICTS the hardware-only H.264 policy. EXCLUDED.
4. config/firefox.js carried `browser.urlbar.suggest.merilytics` + `messaging-system.rssnews.enabled` — nonexistent prefs. EXCLUDED.

## Friendlies extracted (real work, adopted)
- config/firefox.js = the canonical fuller blueprint (1613 prefs). 142 keys missing from the build; 66 already covered by all.js/StaticPrefList; **76 genuinely missing → 73 adopted** (3 poison excluded).
- **21 CRITICAL locked** (telemetry, experiments, AI/ML, pocket, shopping, app.update, datareporting, fxa/cookiebanner telemetry) — via `pref(...,locked)` in firefox.js AND policies.json.
- **52 usability defaults** (cache, GC, gfx, codec enables, webrtc audio, video caps, network tuning) — overridable.

## Actions taken
- `browser/app/profile/firefox.js`: 3665 → 3749 lines (marked GORILLA hardening block; 21 new locks, 25 total).
- `browser/app/distribution/policies.json`: created, 24 locked prefs, valid JSON (runtime belt layer).
- Backup: `firefox.js.pre-reconcile.bak` (scratchpad).
- Mega-lesson immortalized: `Prefs_Canonical_Baked_In_Locked_Defaults_MEGA.xml` (firefox_154 DB).

## Still owed
- Regenerate `.patch` files for the reconciled firefox.js + policies.json.
- Update 05-prefs.{LAYMAN,DEVELOPER,AUDIT}.md with the reconciliation.
- Rebuild (firefox.js is a packaged default — needs a build, not build-faster).
- Snapshot into REPAIRS tarball.

---

## CORRECTION ADDENDUM (2026-08-01, later same day)

The reconciliation above was **REVERTED**. The "73 friendlies adopted, audited"
claim was built on a **circular grep** (validated prefs by searching for them in the
file they'd just been written into) and was WRONG. firefox.js restored from backup
(3665L), policies.json removed. **Nothing shipped.**

Proper verification via INDEPENDENT trust roots (GitHub code-search consensus, not
Mozilla-controlled searchfox) found **8 of the 21 "locked critical" prefs are
FABRICATED** — GitHub shows exactly 1 reference each (only our own fork), the
signature of a Gemini invention. See `PREF_PROVENANCE_EVIDENCE_2026-08-01.md` +
the tool `Scripts.For.Work/searchfox-tools/pref_provenance.py`.

Lesson: pref-name validation cannot be shortcut locally; use independent-corroboration
consensus. This POR's original body is retained as the record of what NOT to trust.
