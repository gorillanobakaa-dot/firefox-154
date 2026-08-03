# Agent Instructions — Gorilla Unleashed Firefox 154 (patches working directory)

The full rules for any AI or human agent working in this directory live in
[`CLAUDE.md`](./CLAUDE.md). This file exists so tools that read a generic
`AGENTS.md` see the same source of truth — do NOT duplicate rules here; if you
change policy, edit `CLAUDE.md` and both this file and `GEMINI.md` will still
be correct (they only point).

## The short version (read `CLAUDE.md` for the full rules)

1. **Source-tree rules are mandatory.** Before touching any source under
   `/home/gorilla/firefox-main/`, read `/home/gorilla/firefox-main/CLAUDE.md`.
   That file lists media/GFX/CSS/locale/build invariants proven by real bugs.
2. **Reference machine:** Sony VAIO SVE14A3AJ — Intel HD 4000 (Ivy Bridge),
   i965 VA-API, **16 GiB DDR3L UMA-shared with the GPU** (verified from GNOME
   Settings > About, 2026-07-16), Debian 13 Trixie, Wayland/GNOME 48.
   **Distribution audience is much weaker** (~4 GB DDR3, HDD, no SSD) — the
   *audience* the build is aimed at, not the reference machine it runs on.
3. **Naming discipline:** never invent new "gorilla-*" file/folder/constant/marker
   names. Name things by function. See the *Naming discipline* section in `CLAUDE.md`.
4. **Documentation:** one dual-track pair (LAYMAN + DEVELOPER) plus one AUDIT per
   patch topic, generated with `doc-audit/doc_audit.py`. Read `doc-audit/AGENT.md`
   before writing. Never invent performance numbers.
5. **Tone:** no flattery. State results, not sales copy. "Not measured" beats
   estimating silently.

Everything else — the top-3 rules agents keep forgetting, key file locations,
build/launch quirks — is in `CLAUDE.md`.
