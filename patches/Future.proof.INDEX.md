# Gorilla Unleashed FF154 — Applied-State Snapshots (2026-07-16)

Full-file copies of the **currently applied** patches, taken from the live
`/home/gorilla/firefox-main` working tree and SHA-verified. These supersede
`old.patches/`, whose backups were frequently STALE vs the tree.

Why full copies (not `git diff`): the Day-0 commit is the git ROOT with most
patches baked in, so `git diff HEAD` cannot cleanly extract them.

> **RELOCATED 2026-08-03 (single-source-of-truth reorganisation):** the tarballs
> no longer live in this repo. Both `Future.proof.APPLIED-STATE.*.tar.gz` (and
> `merged-docs-backup-2026-08-02.tar.gz`) moved to
> `~/Documents/FIREFOX.WORK/Firefox.Scripts.Vault.Docs/Applied.State.Archive/`
> (see `ARCHIVE.INDEX.md` there). The 2026-07-31 repairs set's canonical form is
> the in-repo dir `Future.proof-2026-07-31.repairs/` — completed 2026-08-03 with
> the 2 files only its tarball had (`aboutprofiling.css`, `warning.svg`).

| Snapshot | files | notes |
|---|---|---|
| 2026-07-16_03_networking_snapshot | 8 | see MANIFEST.txt |
| 2026-07-16_04_performance_snapshot | 4 | see MANIFEST.txt |
| 2026-07-16_05_prefs_snapshot | 5 | see MANIFEST.txt |
| 2026-07-16_06_quota_snapshot | 3 | see MANIFEST.txt |
| 2026-07-16_07_toolkit_snapshot | 19 | see MANIFEST.txt |
| 2026-07-16_08_look_snapshot | 320 | see MANIFEST.txt |
| 2026-07-16_09_remote_snapshot | 2 | see MANIFEST.txt |
| 2026-07-16_10_overrides_snapshot | 1 | see MANIFEST.txt |
| 2026-07-16_11_font_system_snapshot | 5 | see MANIFEST.txt |
| 2026-07-16_12_mozambique_drill_snapshot | 3 | see MANIFEST.txt |
| 2026-07-16_gpu_snapshot | 4 | see MANIFEST.txt |
| 2026-07-16_media_snapshot | 21 | see MANIFEST.txt |
| 2026-07-16_snapshot | 9 | see MANIFEST.txt |
| **Future.proof-2026-07-31.repairs** (own tarball: APPLIED-STATE.2026-07-31.REPAIRS.tar.gz) | 29 | 2026-07-31 repair campaign — FTL decontamination, nsContextMenu/appearance.mjs rebases, .properties fixes, token/panel CSS, in-content rebase. APPLY LAST, after the 2026-07-16 set + Look copies. Audit trail: THEME_FIX_LOG_2026-07-31.md |

## Not retired
- `old.patches/08.Look` — KEPT as possible source masters (branding assets
  differ from tree in unclear direction). Its applied state IS captured in
  `2026-07-16_08_look_snapshot`.

## Coverage notes
- Telemetry/CSS/GPU edits from today: `2026-07-16_snapshot`
- BUG H (gfxPlatformGtk.cpp): in media snapshot; BUG I (gfxConfigManager.cpp): in today's snapshot
- user.js: PROFILE-applied copy captured (backup differed by 1173 lines — both kept)
- `_old.patches_root_files/`: deploy.sh + MAP_IBM.md preserved

## Safe to retire from old.patches (superseded, verified)
01.MEDIA, 02.GPU, 03.NETWORKING, 04.PERFORMANCE, 05.PREFS, 06.QUOTA,
07.TOOLKIT, 09.REMOTE, 10.OVERRIDES, 11.FONT.SYSTEM, 12.MOZAMBIQUE.DRILL
(Keep 08.Look.)
