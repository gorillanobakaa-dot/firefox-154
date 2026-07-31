# Doc-Audit Agent — Operating Instructions

> ## ⚠️ 2026-07-30: USE `dual-track`, NOT `doc_audit.py`
>
> `doc_audit.py` and `dual_track.py` were two attempts at the same thing. They have
> been **merged into one tool**, and nothing was dropped. Use:
>
> ```sh
> export FF_SRC=/home/gorilla/Documents/FIREFOX.WORK/Firefox.Scripts.Vault.Docs/SafetyVault.Firefox/firefox-main
> dual-track precheck  <topic-dir> --output-dir <topic-dir>
> dual-track code prep <topic-dir> --output-dir <topic-dir> --format all
> #   ... fill the three .filled.json files ...
> dual-track code render <topic-dir> --output-dir <topic-dir> --format all --validate
> ```
>
> `dual-track` is on `PATH` and works from any project. **Topic directories are
> first-class** — pass the folder, and all its files are documented as ONE unit,
> per the "one pair + one audit per topic, never per file" rule below.
>
> **`FF_SRC` update 2026-07-31:** `/home/gorilla/firefox-main` has been RESTORED
> (vault rsync + Future.proof applied-state overlays + FIrefox.154.Look copies;
> 115/115 manifest SHAs verified; full build succeeded same day). Point `FF_SRC`
> at `/home/gorilla/firefox-main` again — it is the patched, buildable tree.
> The vault path above remains valid as the VANILLA baseline only (it contains
> zero patches; never verify patch targets against it expecting gorilla code).
> Verified: `dual-track precheck patches/FIrefox.154.Look` with the restored
> tree → 0 P0 / 0 P1 (6 benign upstream-TODO P2s).
> *(The paragraph this replaces described the 2026-07-30 gutted-tree state.)*
>
> **What the merge changed, all of it gains:**
> - Rule findings and model findings are now **labelled separately** in Section D
>   (`found by rule` / `found by review`), and rules always come first.
> - The quality score is **computed from the document**, not self-awarded. It is
>   **track-aware** — an audit is no longer marked down for having no glossary.
> - Section E always prints **Not verified**, and an audit that lists nothing there
>   is called out. Hiding your limits now costs you the gate.
> - Claim sourcing (`stated_in_input` vs `model_inference`, with quoted evidence)
>   applies to every track.
> - Firefox's rules live in `../.dual-track-rules.py` and are found automatically.
>   The generic TODO rule is builtin; only Firefox-specific rules are in that file.
> - `--payload` (paste into any free chat AI) and model calls (`--call-model`,
>   `--allow-local`) are preserved unchanged, including the rule that a local
>   Ollama model is never reached without an explicit opt-in.
>
> `doc_audit.py` is kept in this folder as the reference implementation. Do not
> extend it; extend `dual-track`. Everything below still describes the standard
> correctly — only the commands have changed.

**Who reads this:** any AI agent (Claude Code, Gemini, a local Ollama model) asked to
document or audit a patch topic of the custom Firefox build — or a human
doing it by hand. Same rules either way.

**Version:** 1.0 · 2026-07-16
**Toolkit:** this folder (`doc-audit/`) — 4 files, nothing else needed.

---

## Mission

Every patch topic (`patches/new.patches/NN.TOPIC/`) gets exactly **three** living documents:

| Output | Audience | Voice |
|---|---|---|
| `NN-topic.LAYMAN.md` | everyone | storyteller — analogies, zero jargon, warm |
| `NN-topic.DEVELOPER.md` | maintainers/forkers/auditors | audit-grade — WHY before HOW, exact lines |
| `NN-topic.AUDIT.md` | release decisions | IBM Sections A–F, P0–P3, readiness % |

One pair + one audit per **topic**, never per file. Outputs live in
`patches/DOCS.dual-track/`. The proof-of-style reference pair is
`13-telemetry-kill.LAYMAN.md` / `.DEVELOPER.md` in that folder — match it.

## The Workflow (in order, no skipping)

1. **Pre-check first, always.**
   `python3 doc_audit.py precheck --target <topic-dir>`
   The rule findings (missing checksum patches, dead patch targets, unsigned hunks,
   TODOs) go into SECTION D of the audit *before* any model opinion.

2. **Ground the model.** If verified numbers exist (perf results, before/after CPU %,
   boot times), put them in a small text file and pass `--context <file>`. The template
   forbids the model from inventing numbers: **no measurement supplied → the doc must
   say "not measured."** This rule is absolute.

3. **Generate.**
   - With an API key or local Ollama: `doc_audit.py full --target <topic-dir> --output ../patches/DOCS.dual-track`
   - With NOTHING (no key, no GPU): `doc_audit.py payload --target <topic-dir>`,
     paste the payload into any free chat AI, save its JSON reply, then
     `doc_audit.py render --from-json reply.json --kind layman --topic NN-topic`.
   - If YOU are a capable agent (e.g. Claude Code) doing this inline: skip the script's
     model call, but you MUST still (a) run the precheck, (b) follow the JSON schemas
     in `doc_audit.py` as your content checklist, and (c) match the rendered
     section order exactly, so hand-written and generated docs are indistinguishable.

4. **Quality gate.** Score the rendered Markdown against the checklist in
   `MASTER_TEMPLATE.md` (structure 20 · rigor 25 · visual 20 · separation 15 ·
   task-orientation 10 · modularity 10). **< 85 → fix and re-score, don't ship.**

5. **File it.** Outputs go INSIDE the topic folder itself
   (`patches/new.patches/NN.TOPIC/NN-topic.{LAYMAN,DEVELOPER,AUDIT,PRECHECK}.md`
   + `NN-topic.PRECHECK.json`), so docs travel with the patches they describe.
   Always pass `--output <topic-dir>` — never the central `DOCS.dual-track/` folder.
   The precheck rules (SOURCE_EXT list) exclude `.md`/`.json`, so re-running precheck
   on a doc-populated topic folder is safe.
   If the audit found P0/P1 defects, mirror them into `patches/PATCH.READINESS.txt`.

## Hard Rules (learned the expensive way — do not relearn them)

- **Reference machine RAM is 16 GiB DDR3L, UMA-shared with the HD 4000 GPU**
  (verified 2026-07-16 from GNOME Settings > About). Distribution AUDIENCE is
  ~4 GB DDR3 / HDD. A doc that says "8 GB UMA" is repeating a stale old value
  and is wrong; a doc that conflates the reference machine (16 GiB) with the
  distribution audience (~4 GB) is also wrong. Name both explicitly.
- GPU process stays **ForceDisabled on Wayland**; VA-API runs in **RDD**, not GPU process.
- Vendored Rust edits are invisible to the build until `.cargo-checksum.json` is updated
  AND stale `.rlib`/fingerprint/`libgkrust.a` artifacts are deleted.
- Microsoft fonts: legal to **use**, illegal to **redistribute** — docs must carry the
  binary-distribution caveat (see `patches/new.patches/11.FONT.SYSTEM/README.fonts.md`).
- Honesty over marketing: what does NOT work gets the same font size as what does.
- Never "simply", never "just".

## Where Everything Lives

| Thing | Path |
|---|---|
| Topics (input AND output) | `patches/new.patches/01.MEDIA` … `13.TELEMETRY.KILL` — docs live alongside the patches they describe |
| Style reference pair | `patches/new.patches/13.TELEMETRY.KILL/13-telemetry-kill.{LAYMAN,DEVELOPER}.md` (once moved from `DOCS.dual-track/`) |
| Pristine tree (patch truth) | `Firefox.Scripts.Vault.Docs/SafetyVault.Firefox/firefox-main` — verified intact 2026-07-30 (path corrected: there is no `.backup` suffix) |
| Live tree | `/home/gorilla/firefox-main` — **incomplete as of 2026-07-30**, see the notice at the top. Set `FF_SRC` to the vault tree instead. |
| Mandatory build rules | `/home/gorilla/firefox-main/CLAUDE.md`, `patches/GOLDEN_RULES.md` |

---
*This agent definition is itself dual-track by construction: a human can follow it as a
checklist; a model can follow it as a system prompt. That is the point.*
