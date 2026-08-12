# 16.SNAPSHOT.DELTA.2026-08-12 — completeness sweep

Auto-generated 2026-08-12 by diffing the LIVE build tree (~/firefox-main,
the source of .deb BuildID 20260811184252) against the vault vanilla
snapshot (SafetyVault.Firefox/firefox-main, 2026-07-10).

- One `.patch` per changed source file that had NO patch in categories
  01–14 (locale name-purge, Look CSS, branding/gorilla files, misc).
  New files appear as `--- /dev/null` patches.
- `DELETED_FILES.manifest.txt` — 434 files the fork REMOVES from the
  vanilla tree (the AI excision: third_party/llama.cpp, genai/aiwindow
  components). Apply with:
      xargs -a DELETED_FILES.manifest.txt -d '\n' rm -f --
- Excluded as junk: .preflight_state.json, package-lock.json.

Categories 01–14 remain the curated, documented patch set; this folder
guarantees the snapshot rebuilds the exact shipped tree even where
curation lagged. Fold these into proper categories at leisure.
