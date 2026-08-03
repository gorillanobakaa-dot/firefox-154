# Gemini Agent Instructions — Gorilla Unleashed Firefox 154

The single source of truth for agent rules in this directory is
[`CLAUDE.md`](./CLAUDE.md). This `GEMINI.md` exists only so Gemini CLI picks up
the same rules automatically — do NOT edit rules here; edit `CLAUDE.md` and this
pointer stays correct.

## Read these, in this order

1. [`CLAUDE.md`](./CLAUDE.md) — this directory's rules, hardware target, naming
   discipline, top-3 forgotten rules, doc-audit toolkit pointer.
2. [`/home/gorilla/firefox-main/CLAUDE.md`](/home/gorilla/firefox-main/CLAUDE.md)
   — mandatory rules for any source-tree edit (media, GFX, CSS, locale, build).
   Each rule is anchored to a real bug that has already burned this project.
3. [`doc-audit/AGENT.md`](./doc-audit/AGENT.md) — if you are asked to document or
   audit a patch topic.

## Non-negotiables (excerpt — full list in `CLAUDE.md`)

- Reference machine truth (verified 2026-07-16 from GNOME About): Sony VAIO
  SVE14A3AJ, Intel HD 4000 (Ivy Bridge), i965 VA-API, **16 GiB DDR3L
  UMA-shared with the GPU**, Wayland/GNOME 48. Distribution AUDIENCE is
  weaker (~4 GB DDR3, HDD) — that is who the build is FOR, not what it runs on.
- Never invent new "gorilla-*" file/folder/constant/marker names. Name things by
  function. 17,000+ prior occurrences had to be forensically removed; the
  cleanup scripts live in `Second.Brain/Firefox.154.Documentation/Doc.Tooling.Scripts/`.
- Never invent measured performance numbers. If no verified measurement was
  supplied, the output says "not measured".
- Tone: no flattery, no unearned superlatives. State results, not sales copy.
