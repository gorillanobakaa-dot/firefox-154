# SOP — Room-Clearing & Poison Audit (for the next Fable / any agent)

*Written 2026-08-01 after clearing the WEBRTC and prefs "rooms." This is the
Method of Operation for taking a folder full of mixed real-work-and-Gemini-slop,
separating the two, immortalising the real work in the firefox_154 DB, and
cleaning up — WITHOUT overclaiming what was actually verified.*

> **Read this first, and read it honestly.** The whole project exists because a
> previous AI overclaimed ("telemetry gated!", "patch active!") when it wasn't.
> Do not become the next one. Speed is not rigour. This SOP tells you how to be
> fast AND how to say plainly where fast stops.

---

## The MO (the room-clearing metaphor, made concrete)

For each target folder: **move in → ID tangoes → keep friendlies → lead them to
the fortress → POR → document (IBM dual-track) + .patch → clean → next target.**

### Phase 1 — RECON (map before you read)
- `find`/`du`/`ls` for structure, sizes, dates. Do NOT read 280 files.
- Semantic-recall the firefox_154 DB for what's already known (avoid re-deriving).
- Grep for the contamination signature: docs *claiming* a pref/patch/gate is
  active. Those claims are the first thing to verify.

### Phase 2 — ID TANGOES (contamination-triage — know its limits, below)
- For every factual claim in a doc (a pref value, a line number, a "patch X is
  active"), **verify against the live tree, not the doc.** Docs lie; the tree
  and the running binary don't.
- Grep the claimed key/value/line. If it doesn't match, it's suspect.

### Phase 3 — KEEP FRIENDLIES / verify they're real
- A "friendly" is real work that survives verification against the tree.
- 2026-08-01 example: the WEBRTC folder's every claim (hardware_only_mode pref
  at StaticPrefList:12746, the two .cpp guards, vainfo H264-yes/VP8-no) checked
  out true → real → keep. Not everything is poison.

### Phase 4 — LEAD TO THE FORTRESS (immortalise in firefox_154 DB)
- Consolidate the verified knowledge into an atom-schema `.xml` in the right
  `NN.CATEGORY/` folder. Ingest with `ingest_lessons.py` (vector_env python).
- The DB is the fortress: it can't be silently poisoned the way loose docs were.

### Phase 5 — POR (post-operation report)
- A short `.md` in the topic dir: tangoes neutralised, friendlies extracted,
  actions taken, **what is still owed**. Be specific with file:line + values.

### Phase 6 — DOCUMENT (IBM dual-track) + .patch
- Update/create LAYMAN + DEVELOPER + AUDIT docs. Generate `.patch` files for any
  tree changes so they're reproducible and travel with the topic.

### Phase 7 — CLEAN + NEXT
- Only after the knowledge is in the fortress AND the POR is written, the loose
  source folder can be archived/deleted. Then move to the next room.

---

## THE POISON-DETECTION METHOD — and exactly what it does NOT do

This is the part the human specifically challenged, and rightly. Be honest about it.

### The two signals that are FAST and RELIABLE-ish
1. **Existence check.** Does the pref/symbol/file actually exist in this FF
   version? `grep -E "^- name: KEY$" StaticPrefList.yaml` or grep the quoted key
   across `modules/ browser/ toolkit/ dom/ netwerk/` (`.cpp .h .mjs .js .yaml`).
2. **Policy-contradiction check.** Does a value contradict an ESTABLISHED policy
   you already hold? (2026-08-01: `vp8_enabled=true` contradicts the hardware-only
   H.264 policy — caught ONLY because the WEBRTC context was loaded that session.)

### The SAFETY ASYMMETRY that makes triage tolerable
- Setting a **nonexistent** pref via `pref()` is **INERT** — Firefox ignores
  unknown keys. So a hallucinated key that slips through does no harm.
- The **dangerous** class is a **REAL pref set to a WRONG value** (like
  `vp8_enabled=true`). That's the only class that actually breaks things, and it's
  the only class the policy-contradiction check reliably catches.
- Therefore: existence-triage is enough to keep the binary SAFE, but NOT enough
  to make it CORRECT.

### What this method DOES NOT DO (say this out loud, every time)
- It does **NOT** validate that a value is correct, current, or optimal against
  Mozilla's documentation. That is separate, slow, human-grade work (the project
  author spent ~2 months doing exactly this by hand against the FF docs).
- It does **NOT** detect a real pref whose value is subtly wrong but doesn't
  contradict a policy you happen to hold.
- It does **NOT** detect a pref removed/renamed between FF versions unless the
  existence check happens to miss it.
- **grep is false-positive AND false-negative prone.** 2026-08-01 proofs:
  (a) a crude sweep flagged REAL prefs (`app.update.enabled`, `pocket.enabled`)
  as "unverified" because they register at runtime, not in the grepped paths;
  (b) a grep for the excluded poison keys matched the AUDIT COMMENT that named
  them, faking a red flag. **Always check WHERE a match is, not just that it
  matched.**

### The honest label for the output
"Adopted N prefs" after triage means **"N real prefs that passed a shallow
screen,"** NOT "N validated prefs." Do not write "validated," "audited-correct,"
or "poison removed" as if it were the human's 2-month validation. Write
"contamination-screened; values not doc-validated" unless you actually did the
doc pass.

### When to STOP and defer to the human baseline
- If a human-validated artifact exists (e.g. `config/firefox.js` = the 2-month
  work), your job is **drift/contamination triage against it**, not re-derivation.
- You cannot cleanly separate "human-validated pref" from "Gemini-injected-later
  pref" without the original validation record. If that record isn't available,
  SAY SO and treat the human artifact as authority, flagging only values that
  fail existence or contradict a known policy.

---

## The one-line creed
**Verify against the tree, not the doc. Existence keeps it safe; only the doc
pass makes it correct. Never call a fast screen a validation.**
