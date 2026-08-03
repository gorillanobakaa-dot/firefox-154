# doc-audit — One Toolkit, Two Ancestors

*Dual-track, per the project's open-source philosophy (`00.Open.Source.Philosophy`).*

---

## 🧍 Human Track

This little folder is the child of two older projects:

- The **documentation robot** (`Second.Brain/documentation_agent`) — great at explaining
  code in two languages at once (plain English + developer), but it only looked at one
  file at a time and needed an AI on tap.
- The **IBM-style inspector** (`IBM.Templates.Script.Audit/project2`) — great at strict,
  checklist-driven inspections with severity grades and "is this ready to ship?" scores,
  but its reports were mostly written by hand-fed prompts.

This toolkit merges them. Point it at one of the 13 patch topics and it can:

1. **Inspect offline** — no AI, no internet: it checks the patches against rules learned
   from real bugs (like "you edited a sealed Rust crate but forgot the checksum sticker").
2. **Write the paperwork** — a plain-English guide, a developer guide, and a formal audit
   report, all from the same facts.
3. **Work with zero budget** — if you have no API key, it writes a `PROMPT_PAYLOAD` text
   file you paste into any free chat AI; paste the answer back and it formats it perfectly.

Four files is the whole thing. Your brain holds seven; we left you three spare. 🧠

```
doc_audit.py     the tool
MASTER_TEMPLATE.md   the rules + hardware truth it feeds the AI
AGENT.md             the instructions any AI (or human) follows
README.md            this file
```

**Quickest start (no AI needed):**
```bash
cd /home/gorilla/Documents/FIrefox.154.Work/doc-audit
python3 doc_audit.py precheck --target ../patches/new.patches/13.TELEMETRY.KILL
```

---

## 👩‍💻 Developer Track

**Pipeline:** `scan → offline rules → payload(MASTER_TEMPLATE + diffs + JSON schema) →
model (Claude→Gemini→Ollama failover, or manual paste) → deterministic MD renderers`.
JSON-in/Markdown-out means section structure cannot drift between topics or models.

| Mode | Needs a model? | Produces |
|---|---|---|
| `precheck` | no | `<topic>.PRECHECK.md` (inventory + rule findings, P0–P3) |
| `payload` | no | 3× `PROMPT_PAYLOAD.<topic>.{LAYMAN,DEVELOPER,AUDIT}.txt` |
| `doc` | yes | `<topic>.LAYMAN.md` + `<topic>.DEVELOPER.md` (+ raw `.json`) |
| `audit` | yes | `<topic>.AUDIT.md` — IBM Sections A–F; precheck findings merged into D |
| `full` | yes | all of the above |
| `render` | no | Markdown from any AI's pasted JSON reply (`--from-json --kind --topic`) |

Key flags: `--context <file>` injects verified measurements (the template forbids the
model from inventing numbers without it); `--model auto|claude-*|gemini-*|<ollama-name>`;
`--ollama-model` (default `gemma4:latest`); `FF_SRC` env var overrides the live-tree path
used by the dead-patch-target rule.

**Offline rules implemented** (each traces to a real bug from this project):
vendored-crate edit without `.cargo-checksum.json` patch (P1) · patch target missing in
live tree (P1) · TODO/FIXME in added lines (P2) · inherited Necko checks: missing `SO_SNDBUF` in `HttpConnectionUDP`,
`NEGATIVE_RECORD_LIFETIME > 15` (fire only when those files are in scope).

Zero pip dependencies — stdlib `urllib` only, same as both ancestors.

**Claude Code integration:** `.claude/agents/doc-auditor.md` registers a subagent whose
system prompt defers to `AGENT.md`. Invoke by asking Claude Code to "use the doc-auditor
agent on 03.NETWORKING".

**Quality gate:** rendered docs must score ≥85/100 on the checklist in
`MASTER_TEMPLATE.md` (inherited from `HOW_TO_GET_IBM_QUALITY_DOCS.md`). Below 85 →
iterate, don't ship.
