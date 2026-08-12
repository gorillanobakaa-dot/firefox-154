# Poison Autopsy — Lesson Template (dual-track, IBM-style, GitHub-annotated)

**Purpose:** the fixed structure a poison-autopsy lesson MUST follow. Fired by the
poison-autopsy protocol (see memory `poison-autopsy-protocol`) whenever a piece of code is
**proven poisoned beyond reasonable doubt** — i.e. confirmed across all three tiers: the tree
(what changed), the doctrine/memory tier (was it intended?), and the governing authority (is it
correct?). Produces one artifact carrying BOTH tracks + code snippets, ingested to chroma_fx154.

Do NOT fire this for suspicions, drift, or single-tier hunches. Only for a proven kill.

---

## Required sections (every autopsy fills all of them)

### 0. Header
- Concept name (kebab or Pascal), category (NN.TOPIC), date, file:line, severity (P0–P3),
  one-line verdict.

### 1. Situation on the ground  *(dual-track)*
- **Human:** what part of the browser this is, in plain language — what a user would call it.
- **Developer:** the file, the function, the subsystem, how it's reached at runtime.

### 2. What the code looked like  *(GitHub-annotated diff)*
- The BEFORE (poisoned) and the vanilla/correct, as fenced code blocks with `-`/`+` and inline
  `// ←` annotations pointing at the exact poisoned token.

### 3. What it PROMISED to do  *(the disguise)*
- Quote the comment / doc / claim verbatim. State what it *told the reader* it did. This is where
  poison hides — a plausible, often internally-consistent story.

### 4. What it ACTUALLY did  *(the reality)*
- The real behaviour, mechanism-level. Name the exact gap between promise and reality.

### 5. How it happened  *(provenance)*
- Sed-rebrand? graft? mechanical family-swap? The signature (e.g. one-char-family swap with a
  consistent comment edit = classic disguise). Note absence/presence of provenance markers.

### 6. Intended effect vs. reality  *(the two-column truth)*
- A table: | What it was meant to achieve | What it achieved in reality |

### 7. The proof — all three tiers  *(this is what earns "beyond reasonable doubt")*
- **Tree:** the vanilla-vs-live diff. **Doctrine:** which memory rule applies / is ruled out.
  **Authority:** the governing body (RFC / W3C / Mozilla docs / MP4RA / vendor spec) quoted, with
  URL. If any tier is unchecked, it is NOT beyond reasonable doubt — do not fire.

### 8. The fix — how we sealed it  *(dual-track + GitHub diff)*
- The exact edit (fenced diff). What value changed, from → to. Whether it restores vanilla or
  installs a hardened value. Whether a provenance marker was added (restores-to-vanilla = none;
  new hardening = `// GORILLA OVERRIDE:` marker).

### 9. Rationale  *(why THIS fix, not another)*
- Why the chosen value is correct by the authority. What was considered and rejected.

### 10. Verification  *(falsifiable)*
- The command(s) that prove the fix: `cmp` vs vanilla, grep for residual poison (want 0), patch
  regeneration reproducing live byte-exact, symbol-grep, etc. Include expected output.

### 11. Blast radius & what was NOT checked  *(honesty clause)*
- Reachability today (dead code? live path?), rebuild owed?, and an explicit "not verified" list.

---

## Style contract (non-negotiable)
- **Dual-track:** Human track uses physical-life analogies, zero unexplained jargon; Developer
  track is exact (paths, lines, values). Same truth, two languages — neither is dumbed down.
- **GitHub-flavored:** fenced diffs with `-`/`+`, inline `// ←` arrows on the poisoned token.
- **Evidence-anchored:** every claim carries file:line, a command, or an authority URL. No anchor
  → write "not verified". Never estimate silently.
- **IBM-audit rigor:** severity rated; intended-vs-real table mandatory; verification commands
  mandatory; limits stated as prominently as findings.

## Output
Two forms of the SAME content:
1. A `.xml` atom (chroma_fx154 schema: name/category/date/aliases/symptoms/when_to_recall/
   wrong_instinct/human_rationale/execution_logic/related/verified) with the autopsy inside
   human_rationale + execution_logic and code snippets XML-escaped. THIS is the chroma payload.
2. Optionally a rendered `.md` twin alongside it for human reading.
Ingest the atom: `Firefox.154.Lessons/` via `ingest_lessons.py` (vector_env python).
