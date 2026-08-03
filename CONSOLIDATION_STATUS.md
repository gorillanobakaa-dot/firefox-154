> # ⚠️ SUPERSEDED — 2026-07-22
> This is an **earlier snapshot (2026-07-17) of the SAME consolidation effort**, not a
> competing plan. It predates the vanity-prefix rename and the restructure into
> `dispatchers/ modules/ patch-tools/ …`.
>
> **Live record / source of truth:**
> `gorilla-firefox-toolkit/CONSOLIDATION_STATE.md`.
>
> **Why the paths here are dead:** the toolkit it describes
> (`~/Documents/gorilla-firefox-toolkit`, `~/Documents/firefox/gorilla-firefox-toolkit`,
> the `gorilla` router + `gorilla_*.py` modules) was renamed function-first
> (git commit `0adbbf5`) and now lives at
> `FIREFOX.WORK/gorilla-firefox-toolkit/`.
>
> **Still-live nugget preserved from this doc** (feeds the OPEN patch-workflow question in
> canon): the decision that **file-copy `deploy` is legacy and git-apply (`patch-mgr apply`)
> is canonical → `firefox-main`** — corroborated by git commits `0f99de9` (“deprecate
> file-copy”) and `53d204f` (“retire port + deploy”). Per the memory rule this must still be
> **brain-confirmed** before `deploy.sh` is retired.
>
> Kept (not deleted) as a dated record. Read canon to resume.

---

# Script Consolidation — Where We're At

**Last updated:** 2026-07-17. **Break point / resume note.**

Full detail lives in two files — read these to resume:
- **Plan (target):** `Second.Brain/docs/SCRIPT_CONSOLIDATION_BLUEPRINT.md`
- **Journal (what was done, entries 1–10):** `Second.Brain/docs/CONSOLIDATION_ACTIVITY_LOG.md`

---

## The goal
Collapse ~203 scattered scripts → ~10-ish clean tools. Scope = **Firefox 154 only**
(Microsoft, LEX/legal, Kernel, rental, brain, hwdiag, model-forensics stay SEPARATE).
Model: one `gorilla` command with subcommands; backup = git history, not vault copies.

## What exists now: `~/Documents/gorilla-firefox-toolkit/` (git repo, 7 commits)

One `gorilla` launcher (a router) fronting three command groups:

| Group | Module | Commands |
|---|---|---|
| **build** | `modules/gorilla_build.py` (adopted from `setup_orchestrator.py`) | patch, check, vault-repair, fonts, user-fonts, gpu-bypass, build, diagnose, forensics, crypto-audit, pref-audit, setup, validate, cargo-fix, preflight, clang-fix (17) |
| **brand** | `modules/gorilla_brand.py` (adopted from `branding_engine.py`) | rebrand, wayland-fix, live-patch, gen-icons, shim, map-svgs, recon, dark-mode, ghost (9) |
| **patch-mgr** | `patches/scripts/patch_manager.py` (dispatched, not bundled) | init, status, **apply**, build, rollback, diff, export, upgrade, preflight, verify (10) |

Run: `cd ~/Documents/gorilla-firefox-toolkit && ./gorilla --help`

## Key decisions locked
- **Patch workflow = git (`patch_manager`)**, canonical. File-copy `patch` is legacy;
  `deploy` and `port` were **retired**.
- **`patch-mgr apply`** git-applies the 316 `new.patches/*.patch` diffs + copies `NEW_FILES/`
  (mirror paths; `mozconfig` → `browser/config/mozconfig`). Idempotent. Verified: all 316
  diffs already applied to `~/firefox-main`.
- Patch tools **stay in `patches/`** (they compute paths from their own location).

## Done ✅
- Deleted `ablation_pipeline.py` (superseded by `janitor.py`) + a stale janitor README.
- Built `gorilla-build`, `gorilla-brand`, and the `patch-mgr` git workflow (incl. `apply` + NEW_FILES).

## Still TODO (blueprint order)
1. **`gorilla-icons`** — reconcile the merged `Dash.And.App.grid.Icon.fixer.py` (canonical,
   fuzz-trim + SVG route) with `brand`'s older `wayland-fix`/`gen-icons`.
2. **`gorilla-ui`** — Vertical_Tabs_Excision, mass_dark_mode, firefox_unleashed, revert_sidebar.
3. **`gorilla-prefs`** — `firefox_pref_unleashed.py` (the pref *setter*).
4. **`gorilla-audit`** — gecko-audit, patch_drift_analyzer, structural_brace_checker, doc-audit.
5. Retire the now-superseded originals in vault/brain once each tool is verified.

## Open flags / caveats
- **patches repo is LOCAL-ONLY:** `patch_manager.py` + `patches/scripts/` are uncommitted/
  untracked in the `github.com/gorillanobakaa-dot/firefox.154` repo. Not pushed to remote
  on purpose — commit/push when ready.
- Everything verified at `--help` / dry-run level — **no full Firefox compile driven yet.**
- `preflight-clang21.py` had 3 drifted copies; the toolkit uses the `Start.over.GITHUB` root
  one — confirm it's newest before retiring the others.
- Originals are all still in place (nothing retired yet beyond ablation + the stale README).
