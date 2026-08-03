# AI-Excision Script Collection — Operator's Manual

**What this is.** Ten Python scripts that performed the structural removal of Mozilla's AI stack
(aiwindow / genai / ml / llama.cpp / mozinference) from Firefox 154, plus one CSS/JS self-heal. They
are **not throwaway.** They are (a) the byte-exact record of every source edit made, (b) a re-apply
tool if the tree is restored from the vanilla vault, and (c) worked examples of the *surgical patcher*
pattern (see the lesson atom `Surgical_Patcher_Script_Pattern_Assert_Once`).

**Why they exist as scripts at all** (not hand-edits): a hand-edit across ~40 files is unverifiable and
unrepeatable. A script that asserts each change matched *exactly once* turns "I think I changed the
right thing" into a proof, and turns "redo it after a restore" from a day into a second. The prior
Gemini tenure hand-edited and shimmed; that is why it cratered. These scripts are the antidote.

---

## The shared design contract (every script obeys this)

1. **`rep(path, old, new, label)` asserts exactly one match.** If `old` appears 0 or 2+ times, the
   script prints `FAIL [label] path: N matches (want 1)` and `sys.exit(1)` **before writing anything**.
   Drift (an edit already applied, or the file changed upstream) aborts loudly instead of silently
   corrupting. This is the single most important property.
2. **Fail-before-write, all-or-nothing per run.** An assert that trips leaves the tree untouched from
   that point on. A half-applied run is impossible for the assert-guarded edits.
3. **Backup before delete/move.** `delete_file()` copies to `aiwindow-originals/` (or `tier2/`) first;
   directory moves go to `/home/gorilla/firefox-main.excised-*` (out of tree, not `rm`). Nothing is
   ever truly destroyed — reversal is always possible.
4. **Brace-matched extraction for structural blocks.** Where a whole function / object literal / dead
   block must go, the script walks braces from an anchor (`remove_object`, the `#initSuggestions`
   removal, the `canOpenAsSmartWindow` JSDoc+body cut) with a length sanity-check, rather than a
   fragile multi-line string match.
5. **Self-verifying tail.** Several scripts end by grepping the tree for surviving references and
   printing "remaining consumers (want NONE)" — the script proves its own completeness.
6. **Human-readable provenance in every edit.** Replacements carry `// GORILLA OVERRIDE: <why>` per the
   Open Source Philosophy — the edits explain themselves to a future reader.

---

## Run order (only relevant for a from-vanilla re-apply)

The live tree is already fully excised; these ran once in this order. On a vanilla restore, run them
in sequence — each asserts its preconditions, so a wrong order aborts safely rather than corrupting.

| # | Script | Lines | Scope | Idempotent? | Reversal |
|---|---|---|---|---|---|
| 1 | `mozambique_tier1_seam_removal.py` | 460 | 32 window-chrome seam edits (Ctrl+N, menus, tabbrowser transparency, hooks) | No (asserts-once → 2nd run aborts) | re-apply each `rep` inverse; originals in git/vault |
| 2 | `mozambique_tier1b_ask_button.py` | 56 | ask-button markup + 2 selector lists | No | same |
| 3 | `mozambique_tier2_module_seams.py` | 872 | SessionStore ×6, urlbar, firefoxview chats (del), Smartbar (del), UITour, sidebar, ASRouter targeting, theme engine | No | `aiwindow-originals/tier2/` holds deleted files |
| 4 | `mozambique_tier2b_continuation.py` | 454 | resumes tier2 after the promo-message anchor fix (brace-matched `remove_object`) | No | same |
| 5 | `mozambique_phasec_endgame.py` | 282 | 3 live-crash fixes + genai seams + **dir moves out of tree** + DIRS drop | No | dirs at `firefox-main.excised-ai-aiwindow-genai.2026-08-02/` |
| 6 | `mozambique_phasec2_genai_ftl.py` | 87 | retire `preview/genai.ftl` (jar + Localization + document `<link>`) | No | — |
| 7 | `mozambique_phasec3_glean_index.py` | 66 | deregister aiwindow/genai `metrics.yaml` from glean `metrics_index.py` + chatbot shortcut | No | — |
| 8 | `mozambique_phasec4_startup_categories.py` | 115 | startup categories, ModelHubProvider, TranslationsParent.AIFeature→plain-pref, aichat sidebar | No | — |
| 9 | `mozambique_tier3_ml_residue.py` | 115 | TranslationsFeature standalone, PlacesSemanticHistoryManager finalize-first, prefs panes, locked prefs | No | — |
| 10 | `customize_palette_selfheal.py` | 64 | **NOT AI** — nightly customize null-palette self-heal (separate upstream bug) | Yes-ish (idempotent guards) | remove the guards |

**Companion (not in this dir but part of the same effort):** the phantom-customize CSS fix
(`#customization-container[hidden]{display:none!important}` in customizeMode.css) and the tab-groups
lockout + dead-code strip in `tabgroup-menu.js` were applied inline (not scripted); see the manifest.

---

## How to re-apply after a vanilla tree restore

```
cd /home/gorilla/firefox-main
for s in tier1_seam_removal tier1b_ask_button tier2_module_seams tier2b_continuation \
         phasec_endgame phasec2_genai_ftl phasec3_glean_index phasec4_startup_categories \
         tier3_ml_residue ; do
  python3 <THIS_DIR>/mozambique_$s.py || { echo "ABORTED at $s"; break; }
done
# then the inline fixes (customizeMode.css hidden rule, tabgroup-menu groups-off) per EXCISION_MANIFEST.md
# then: config.status (from objdir) + make -C obj-*/faster   (see the build atoms — mach hangs)
```
If any script aborts with `FAIL [... ] want 1`, the tree is not pristine vanilla at that spot — inspect
before forcing. **Never** edit a script to make an assert pass; that defeats the whole safety model.

## The verification that must follow ANY re-apply
- `config.status` from the objdir (surfaces backend errors in ~11s; `mach build faster` hangs — see
  `Mach_Build_Output_Limited_Under_AI_Agent`, `Component_Dir_Four_Hidden_Anchors`).
- Symbol-grep the relinked `libxul.so`: `LlamaRunner|llama_|ggml_|mozinference|SmartTabGrouping` must
  all be 0, and dead Glean categories `smart_window|genai.chatbot` must be 0.
- Fresh-profile headless boot + a windowed GUI pass (headless misses interactive handlers — see
  `GUI_Runtime_Forensics_Monitor_Breadcrumb_StackInject`). Purge `startupCache` between runs
  (`StartupCache_Stale_Bytecode_Invalidates_On_BuildID_Only`).

## Related tooling (documented elsewhere, same session)
- **searchfox-tools/** (`sfmedia.py`, `sfpref.py`, `sfstandards.py`, `sfconsumers.py`) — the five-axis
  validation suites; standards/authority-backed identifier checking.
- **dsp-ab-lab.py** — measure→simulate→listen audio A/B lab.
- **run_build_and_capture.sh** — patched build wrapper (unsets CLAUDECODE, uses PIPESTATUS).
- Canonical registry of ALL scripts: `Scripts.For.Work/SCRIPT_INVENTORY.md`.
- Full narrative: `../SESSION_CHRONICLE_2026-07-31_to_08-03.md`.
