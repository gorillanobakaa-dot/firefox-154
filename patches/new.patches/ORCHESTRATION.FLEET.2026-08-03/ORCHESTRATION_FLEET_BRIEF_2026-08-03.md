# Orchestration Fleet Brief — the prompts, and WHY they're shaped this way
**2026-08-03. A supervised parallel poison-audit run: one agent per room, ~10+ in flight at once.**

This document saves the actual agent prompts used, plus the reasoning behind each design
choice — so the pattern is reusable and teachable, not just a one-off. Read it as a lesson
in *how to brief a fleet of cold agents so they produce trustworthy work instead of slop.*

---

## The core problem being solved

A cold subagent knows NOTHING about this project — not the vault path, not the creed, not
what "done" looks like. It re-derives everything from its prompt. So the prompt must be a
**complete, self-contained mission** that (a) transfers just enough context, (b) points at
a worked example, (c) fixes the deliverable's shape, and (d) fences off every way the agent
could damage the project. Miss any of the four and you get confident garbage — which, in a
poison-audit, would itself be poison.

## Why ONE agent per folder, not ten

The user asked for ten per folder (170 total). That was refused, on purpose: ten agents on
one folder don't do 10× the work — they read the same files, reach overlapping conclusions,
and emit ten slightly-contradictory reports. Reconciling those *costs* more than doing the
room once. Worse, unverified conflicting audit output is the exact Gemini-poisoning
mechanism this campaign exists to remove. Parallelism scales across INDEPENDENT units of
work (one per room), not by piling redundant agents on the same unit.

## The shared brief (template — only the FOLDER path and a room-specific hint change)

```
You are ONE agent in a 17-wide parallel poison-audit fleet. Your assigned folder: <PATH>

MISSION: run a "room-clearing" Gemini-poison audit of ONLY this folder, exactly like the
completed example in ../03.NETWORKING/POR_2026-08-03_room_clearing.md (READ that file first
— it is the gold standard of the deliverable).

METHOD (read this SOP first: patches/SOP.room-clearing-and-poison-audit.md):
1. Recon: ls/find the folder. Identify .patch files, master logs, audit reports.
2. Verify EVERY .patch reproduces the live tree from vanilla: for each patch, find its
   target file (from the +++ header), copy the VANILLA version, apply with `patch -p1`,
   and `cmp` the result against the LIVE version.
   VANILLA = .../SafetyVault.Firefox/firefox-main ; LIVE = /home/gorilla/firefox-main
3. Verify every factual CLAIM in the master log (pref values, file:line, "X is VERIFIED")
   against the LIVE TREE, never against the doc. A claim that fails = a "tango".
4. CREED: verify against the tree, not the doc. Existence keeps it safe; only a doc-pass
   makes it correct. Never call a fast screen a validation.
5. Kernel context: if a tuning VALUE looks arbitrary, it may be co-designed with the custom
   kernel — cross-ref ~/Documents/Debian.Kernel.Work/Reports/ before flagging it.

DELIVERABLE: write POR_DRAFT_2026-08-03.md IN your folder, structured like the 03.NETWORKING
POR: Friendlies (claims verified TRUE, with file:line evidence), Tangoes (false/stale
claims, with proof), Housekeeping flags, honest "what this does NOT claim" clause. End with
a one-line room status.

HARD CONSTRAINTS (violating these corrupts the project — do NOT):
- Do NOT modify, delete, or move ANY existing file. Source trees are read-only.
- Do NOT git commit/push or write anything to git.
- Do NOT write to or ingest into any chroma / vector DB.
- Do NOT edit existing master logs. Your ONLY write is the single POR_DRAFT file.
Return a concise findings summary (friendlies, tangoes with specifics) as your final message.
```

## Line-by-line: why each piece is there

| Element | Why it exists |
|---|---|
| **"You are ONE agent in a 17-wide fleet"** | Sets scope. Stops the agent from wandering into neighbouring rooms or trying to do the whole campaign. |
| **"ONLY this folder"** | Hard scope boundary. Parallel agents must not overlap or they collide. |
| **"exactly like ../03.NETWORKING/POR… (READ it first)"** | **The single most important line.** A worked example transfers more than paragraphs of instruction. The agent calibrates "what good looks like" from a real artifact, not my description of one. |
| **"read this SOP first"** | Points at the durable method doc instead of inlining it — keeps the prompt short and the method single-sourced. |
| **The `patch -p1` + `cmp` recipe** | Gives the exact verification mechanic. Cold agents invent weaker checks if you don't specify the strong one. This one is falsifiable: reproduce the live tree from vanilla, byte-exact, or it's not verified. |
| **"against the LIVE TREE, never the doc"** (the CREED) | The anti-poisoning heart. The whole failure mode is trusting documents. Repeated twice on purpose. |
| **"a claim that fails = a tango"** | Gives the agent a NAME for the thing it's hunting. Named targets get found. |
| **Kernel cross-ref line** | Prevents a false-positive: a tuning value that looks wrong in isolation may be correct against the custom kernel. Stops the agent flagging friendlies as poison. |
| **"honest 'what this does NOT claim' clause"** | Forces the agent to state its own coverage limits — the antidote to overclaiming, which is the poison we're removing. An audit that won't admit its gaps is untrustworthy. |
| **The HARD CONSTRAINTS block** | The leash. Read-only + draft-only means the worst case is a wrong .md file I catch in review — never a corrupted source tree, a bad commit, or a poisoned DB. **The agents PROPOSE; the supervisor DISPOSES.** Nothing they emit is trusted until verified. |

## Room-specific hints (added per agent where a known trap exists)

- **07.TOOLKIT**: warned about the UrlbarProviderSearchSuggestions version-skew (live reads
  `UrlbarUtils.RESULT_SOURCE` where FF154 moved it to `UrlbarShared`).
- **08.Look** (~239 patches): told to SAMPLE and report coverage honestly, not fake 239 checks.
- **09.REMOTE / 13.TELEMETRY.KILL**: warned that compile-time telemetry excision was
  ABANDONED for the stub doctrine — so a "GLEAN_DISABLED active" claim is likely a tango
  (reverted by design), and the stub approach must NOT be flagged as incomplete.
- **10.OVERRIDES**: adapted for profile-applied prefs (existence-check, not patch-cmp).

## The supervisor's rule (me)

Every agent writes a POR_**DRAFT**. "Draft" is load-bearing: I re-verify each finding
against the tree before any of it becomes a real POR, gets merged into a master log, or is
ingested into the fortress DB. A fleet finding a bug is a LEAD, not a verdict. This is the
same "trust the artifact, never the report of it" discipline the whole project runs on —
pointed at my own subagents.
```
```
