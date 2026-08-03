#!/usr/bin/env python3
"""
doc_audit.py — Unified Dual-Track Documentation + IBM-Style Audit Tool
===========================================================================

The child of two parents:
  * Second.Brain/documentation_agent/doc_generator.py
      -> JSON-schema prompts, deterministic Markdown renderers,
         multi-model failover (Claude -> Gemini -> local Ollama), zero pip deps.
  * IBM.Templates.Script.Audit/project2 (run_audit.py + unified_audit.py)
      -> offline rule-based pre-check, PROMPT_PAYLOAD generation (works with
         NO model at all), IBM Sections A-F, P0-P3 severity, readiness score.

Modes
-----
  precheck  Offline only. Scan a topic folder, run rule checks, write PRECHECK report.
  payload   Offline only. Write self-contained PROMPT_PAYLOAD_*.txt files you can
            paste into ANY chat AI (free web Claude/Gemini/local). No API key needed.
  doc       Call a model, generate <topic>.LAYMAN.md + <topic>.DEVELOPER.md.
  audit     Call a model, generate <topic>.AUDIT.md (IBM Sections A-F).
  full      precheck + doc + audit.
  render    Take a JSON reply you pasted back from any AI and render it to Markdown.
            (payload -> paste into free AI -> save JSON -> render. Zero cost.)

Usage
-----
  python3 doc_audit.py precheck --target ../patches/new.patches/13.TELEMETRY.KILL
  python3 doc_audit.py payload  --target ../patches/new.patches/01.MEDIA --output ./out
  python3 doc_audit.py doc      --target <topic-dir> --model auto
  python3 doc_audit.py render   --from-json reply.json --kind layman --topic 01-media

Environment (only needed for doc/audit/full):
  ANTHROPIC_API_KEY / GEMINI_API_KEY, or a local Ollama server.

License: CC0 1.0 Universal (Public Domain).
"""

import os
import re
import sys
import json
import hashlib
import argparse
import datetime
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE_PATH = HERE / "MASTER_TEMPLATE.md"
PROJECT_NAME = "Gorilla Unleashed Firefox 154"
FF_SRC = Path(os.environ.get("FF_SRC", "/home/gorilla/firefox-main"))

SOURCE_EXT = ['.cpp', '.cc', '.c', '.h', '.hpp', '.rs', '.js', '.mjs', '.ts',
              '.py', '.css', '.ftl', '.patch', '.sh', '.build']
IGNORE_DIRS = ['.git', 'node_modules', '__pycache__', 'obj-', 'build', 'dist', 'reference']
MAX_FILE_KB = 400

# ─────────────────────────────────────────────────────────────────────────────
#  SCANNER  (from project2/unified_audit.py)
# ─────────────────────────────────────────────────────────────────────────────

def find_source_files(root: Path):
    if root.is_file():
        return [root]
    files = []
    for ext in SOURCE_EXT:
        for p in sorted(root.rglob(f"*{ext}")):
            if not any(part in IGNORE_DIRS for part in p.parts):
                files.append(p)
    return files


def analyze_file(p: Path):
    content = p.read_text(encoding='utf-8', errors='ignore')
    lines = content.splitlines()
    code = sum(1 for l in lines if l.strip() and not l.strip().startswith(('//', '#', ';', '*')))
    complexity = len(re.findall(r'\b(if|for|while|switch|match|catch)\b', content)) + 1
    return {
        'name': p.name, 'path': str(p), 'language': p.suffix.lstrip('.'),
        'lines': len(lines), 'code_lines': code, 'complexity': complexity,
        'sha256': hashlib.sha256(content.encode()).hexdigest()[:16],
        'content': content,
    }

# ─────────────────────────────────────────────────────────────────────────────
#  OFFLINE RULE-BASED PRE-CHECK  (generalized from unified_audit.py)
# ─────────────────────────────────────────────────────────────────────────────

def _patch_added_lines(content):
    return [l[1:] for l in content.splitlines()
            if l.startswith('+') and not l.startswith('+++')]


def _patch_target(content):
    m = re.search(r'^\+\+\+ [ab]/(.+)$', content, re.MULTILINE)
    return m.group(1).strip() if m else None


def run_precheck_rules(infos):
    """Returns list of defect dicts (id, severity, track_a, track_b, remediation)."""
    defects, n = [], {'P0': 0, 'P1': 0, 'P2': 0, 'P3': 0}

    def add(sev, track_a, track_b, remediation):
        n[sev] += 1
        defects.append({'id': f"{sev}-{n[sev]:03d}", 'severity': sev,
                        'track_a': track_a, 'track_b': track_b,
                        'remediation': remediation})

    patches = [i for i in infos if i['name'].endswith('.patch')]
    names = {i['name'] for i in infos}

    # R1: vendored Rust crate edited without a checksum patch alongside (build rejects it)
    rust_patches = [i for i in patches if 'third_party_rust' in i['name']
                    and 'cargo-checksum' not in i['name']]
    if rust_patches and not any('cargo-checksum' in x for x in names):
        add('P1',
            "A sealed factory part was modified, but the seal-inspection sticker was not "
            "updated. The factory will refuse the part at the door.",
            f"Vendored crate patches present ({rust_patches[0]['name']}, ...) with no "
            f".cargo-checksum.json patch in the same topic. mach build verifies per-file "
            f"SHA256 against the checksum manifest.",
            "Add the matching .cargo-checksum.json.patch; also delete stale "
            "libglean_core-*.rlib / .fingerprint/* / libgkrust.a before rebuilding.")

    for i in patches:
        added = _patch_added_lines(i['content'])

        # R2: patch target must exist in the live tree
        tgt = _patch_target(i['content'])
        if tgt and FF_SRC.exists() and not (FF_SRC / tgt).exists():
            add('P1',
                f"A repair instruction points at a room that does not exist in the "
                f"current building ({tgt}).",
                f"{i['name']}: target path {tgt} missing under {FF_SRC}. Upstream moved "
                f"or renamed it; patch will not apply.",
                "Re-locate the code in the new tree and regenerate the patch.")

        # R3: TODO/FIXME landing in added lines
        todos = [l for l in added if re.search(r'\b(TODO|FIXME|XXX|HACK)\b', l)]
        if todos:
            add('P2',
                "A sticky note saying 'finish this later' was left inside the machine.",
                f"{i['name']}: added lines contain {len(todos)} TODO/FIXME markers.",
                "Resolve or convert to a tracked item in PATCH.READINESS.txt.")

    # R4: inherited Necko rules from unified_audit.py (fire only when files present)
    for i in infos:
        if i['name'].startswith('netwerk') or 'Http' in i['name'] or 'nsHost' in i['name']:
            # For .patch files judge only the ADDED lines (old values live on '-' lines)
            c = "\n".join(_patch_added_lines(i['content'])) \
                if i['name'].endswith('.patch') else i['content']
            if 'HttpConnectionUDP' in i['name'] and 'SetRecvBufferSize' in c \
                    and 'SetSendBufferSize' not in c:
                add('P1',
                    "The incoming loading dock was widened, but the outgoing dock kept "
                    "its narrow default door — uploads bottleneck.",
                    f"{i['name']}: InitCommon() sets recv buffer but never SO_SNDBUF.",
                    "Add mSocket->SetSendBufferSize(33554432) next to the recv call.")
            m = re.search(r'NEGATIVE_RECORD_LIFETIME\s*=?\s*(\d+)', c)
            if m and int(m.group(1)) > 15:
                add('P3',
                    f"Failed address lookups are remembered too long ({m.group(1)}s).",
                    f"{i['name']}: NEGATIVE_RECORD_LIFETIME = {m.group(1)}.",
                    "Reduce to 15 seconds for dynamic signaling servers.")
    return defects

# ─────────────────────────────────────────────────────────────────────────────
#  JSON SCHEMAS  (from documentation_agent, upgraded to per-TOPIC scope)
# ─────────────────────────────────────────────────────────────────────────────

LAYMAN_SCHEMA = """LAYMAN_SCHEMA — respond with valid JSON only:
{
  "title": "Plain-English title (storyteller style, may be playful)",
  "big_picture": "2-3 paragraphs: what this topic does in the real world and why it matters on old hardware",
  "main_characters": [{"name": "TechnicalName", "plain_english": "...", "analogy": "physical-world comparison"}],
  "how_it_works": [{"step": 1, "title": "...", "explanation": "plain English with analogies, states what was actually done"}],
  "quirky_things": [{"title": "...", "explanation": "the surprising/counterintuitive bits"}],
  "real_world_impact": {"battery_cpu_ram": "...", "speed": "...", "your_privacy": "...", "your_internet": "..."},
  "kill_switch_explained": {"what_happened": "...", "without_it": "...", "real_life_analogy": "..."},
  "open_source_angle": "why being able to read this change matters (surveillance/trust angle, Snowden ok)",
  "glossary": [{"term": "...", "definition": "plain English"}]
}"""

DEVELOPER_SCHEMA = """DEVELOPER_SCHEMA — respond with valid JSON only:
{
  "title": "Technical title",
  "files": ["repo-relative paths actually touched"],
  "module_summary": "one paragraph: what this patch group does, mechanism, measured result if supplied",
  "architecture": {"pattern": "...", "trust_boundary": "...", "attack_surface": "...", "dependencies": ["..."]},
  "kill_switches": [{"location": "file/function", "type": "hard|soft|runtime_guard", "condition": "...",
                     "effect": "...", "reversible": true, "notes": "verified numbers if supplied"}],
  "performance_profile": {"cpu": "...", "memory": "...", "io": "...", "timer_interval": "...",
                          "measured_table": [{"component": "...", "before": "...", "after": "...", "mechanism": "..."}]},
  "security_analysis": {"user_profiling": "...", "targeting": "...", "trust_chain": "...", "abuse_potential": "..."},
  "implementation_flow": [{"step": 1, "function": "...", "description": "...", "side_effects": "..."}],
  "technical_debt": [{"item": "...", "severity": "low|medium|high|accepted", "recommendation": "..."}],
  "what_breaks_if_removed": "...",
  "testing_notes": "concrete verification steps with commands",
  "changelog_notes": "development history if evident from material"
}"""

AUDIT_SCHEMA = """AUDIT_SCHEMA — respond with valid JSON only:
{
  "target": "topic name",
  "status": "PASS|FAIL",
  "executive_summary_layman": "Track A: plain-English summary with one physical metaphor",
  "technical_summary_developer": "Track B: architecture, trade-offs, exact mechanisms",
  "defects": [{"id": "P1-001", "severity": "P0|P1|P2|P3", "track_a": "...", "track_b": "file, line, code context",
               "remediation": "actionable step", "effort": "e.g. 30min"}],
  "readiness": {"score_percent": 0, "done": ["..."], "blockers": ["..."], "todo": ["..."]},
  "expansion_plan": [{"target": "file/function", "tweak": "...", "phase": "0|1|2", "impact": "..."}],
  "positive_observations": ["..."],
  "verification_commands": ["shell commands proving the claims"]
}"""

# ─────────────────────────────────────────────────────────────────────────────
#  PAYLOAD BUILDER
# ─────────────────────────────────────────────────────────────────────────────

def load_master_template():
    return TEMPLATE_PATH.read_text(encoding='utf-8')


def build_payload(topic_name, infos, schema, extra_context=""):
    meta, code = [], []
    for i in infos:
        meta.append(f"- {i['name']}  [{i['language']}, {i['lines']} lines, "
                    f"complexity {i['complexity']}, sha {i['sha256']}]")
        body = i['content']
        if len(body) > MAX_FILE_KB * 1024:
            body = body[:MAX_FILE_KB * 1024] + "\n... [TRUNCATED]"
        code.append(f"### FILE: {i['name']}\n```{i['language']}\n{body}\n```")
    t = load_master_template()
    t = t.replace("[TARGET_DIRECTORY]", topic_name).replace("[PROJECT_NAME]", PROJECT_NAME)
    t = t.replace("{files_count}", str(len(infos)))
    t = t.replace("{target_files_metadata}", "\n".join(meta))
    t = t.replace("{source_code_files}", "\n\n".join(code))
    if extra_context:
        t += f"\n\nADDITIONAL VERIFIED CONTEXT (measured numbers you may cite):\n{extra_context}\n"
    return t + f"\n\n{schema}\n"

# ─────────────────────────────────────────────────────────────────────────────
#  MODEL CALLERS  (from doc_generator.py, model names refreshed)
# ─────────────────────────────────────────────────────────────────────────────

def _post_json(url, headers, data, timeout=600):
    req = urllib.request.Request(url, data=json.dumps(data).encode(),
                                 headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return json.loads(res.read().decode())


def call_anthropic(prompt, model="claude-sonnet-5"):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    r = _post_json("https://api.anthropic.com/v1/messages",
                   {"x-api-key": key, "anthropic-version": "2023-06-01",
                    "content-type": "application/json"},
                   {"model": model, "max_tokens": 8192,
                    "messages": [{"role": "user", "content": prompt}]})
    return r["content"][0]["text"]


def call_gemini(prompt, model="gemini-2.5-flash"):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY not set")
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent?key={key}")
    r = _post_json(url, {"content-type": "application/json"},
                   {"contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"responseMimeType": "application/json"}})
    return r["candidates"][0]["content"]["parts"][0]["text"]


def call_ollama(prompt, model="gemma4:latest"):
    r = _post_json("http://localhost:11434/api/chat",
                   {"content-type": "application/json"},
                   {"model": model, "stream": False,
                    "messages": [{"role": "user", "content": prompt}],
                    "options": {"num_predict": 8192}})
    return r["message"]["content"]


def strip_fences(raw):
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    return raw.strip()


def query_model(prompt, choice, ollama_model, allow_local=False):
    # MODEL-FIRST by design. The local Ollama model is an EMERGENCY fallback for a
    # human running the script alone with no API quota left — it is NOT a normal
    # channel. When a model/agent drives the script (the common case) the local
    # model must NEVER be reached: a cloud model that starts the script should
    # finish with a cloud model, not silently hand the job to a weak local model.
    # Local is opt-in ONLY, via `--allow-local` or GORILLA_ALLOW_LOCAL_MODEL=1.
    allow_local = allow_local or os.environ.get("GORILLA_ALLOW_LOCAL_MODEL") == "1"

    chain = []
    if choice == "auto":
        if os.environ.get("ANTHROPIC_API_KEY"):
            chain.append(("anthropic", "claude-sonnet-5"))
        if os.environ.get("GEMINI_API_KEY"):
            chain.append(("gemini", "gemini-2.5-flash"))
    elif "claude" in choice or "opus" in choice or "sonnet" in choice:
        chain = [("anthropic", choice)]
    elif "gemini" in choice:
        chain = [("gemini", choice)]
    elif "ollama" in choice or "gemma" in choice or "llama" in choice or "qwen" in choice:
        # An explicitly-named local model is itself an opt-in to local.
        allow_local = True
        chain = [("ollama", choice)]
    else:
        chain = [("anthropic", choice)]  # treat unknown as a cloud model name

    if allow_local and not any(p == "ollama" for p, _ in chain):
        chain.append(("ollama", ollama_model))

    if not chain:
        raise RuntimeError(
            "No cloud model channel available (no ANTHROPIC_API_KEY / GEMINI_API_KEY, "
            "and no cloud --model given). The local model is EMERGENCY-ONLY and is not "
            "used unless you pass --allow-local or set GORILLA_ALLOW_LOCAL_MODEL=1. "
            "Set an API key or choose a cloud --model.")

    errors = []
    for provider, model in chain:
        try:
            print(f"   🤖 {provider} / {model} ...")
            fn = {"anthropic": call_anthropic, "gemini": call_gemini,
                  "ollama": call_ollama}[provider]
            return json.loads(strip_fences(fn(prompt, model)))
        except Exception as e:
            errors.append(f"{provider}/{model}: {e}")
            print(f"   ⚠️  failed ({e}); trying next channel")
    raise RuntimeError("All model channels failed:\n  " + "\n  ".join(errors))

# ─────────────────────────────────────────────────────────────────────────────
#  RENDERERS  (deterministic Markdown; structure cannot drift)
# ─────────────────────────────────────────────────────────────────────────────

def _today():
    return datetime.date.today().isoformat()


def render_layman(d, topic):
    L = [f"# 🧍 {d.get('title', topic)} — Plain English Guide",
         f"\n> *Topic `{topic}` of the {PROJECT_NAME} build · Written for everyone · {_today()}*",
         "\n---\n", "## 🌍 The Big Picture\n", d.get("big_picture", ""), ""]
    chars = d.get("main_characters", [])
    if chars:
        L += ["## 🎭 The Main Characters\n",
              "| Name | What It Is | Real-World Comparison |", "|---|---|---|"]
        L += [f"| **{c.get('name','')}** | {c.get('plain_english','')} | {c.get('analogy','')} |"
              for c in chars] + [""]
    steps = d.get("how_it_works", [])
    if steps:
        L.append("## 🔢 How It Works — Step by Step\n")
        for s in steps:
            L += [f"### Step {s.get('step','')}: {s.get('title','')}\n",
                  s.get("explanation", ""), ""]
    for q in d.get("quirky_things", []):
        if not any("Quirky" in x for x in L):
            L.append("## 🤔 Quirky Things Worth Knowing\n")
        L += [f"### ⚠️ {q.get('title','')}\n", q.get("explanation", ""), ""]
    imp = d.get("real_world_impact", {})
    if imp:
        L.append("## 💻 What Does This Mean For YOU?\n")
        for label, key in [("🔋 Battery, Speed & Memory", "battery_cpu_ram"),
                           ("⚡ Speed", "speed"), ("🕵️ Your Privacy", "your_privacy"),
                           ("🌐 Your Internet", "your_internet")]:
            if imp.get(key):
                L += [f"### {label}\n", imp[key], ""]
    ks = d.get("kill_switch_explained", {})
    if any(ks.values()):
        L += ["## 🔴 The Kill Switch — Explained\n",
              f"**What it is:** {ks.get('what_happened','')}\n",
              f"**Without it:** {ks.get('without_it','')}\n",
              f"**Think of it like:** {ks.get('real_life_analogy','')}\n"]
    if d.get("open_source_angle"):
        L += ["## 🌐 Open Source & Why It Matters To You\n", d["open_source_angle"], ""]
    gl = d.get("glossary", [])
    if gl:
        L.append("## 📖 Glossary (Plain English Dictionary)\n")
        L += [f"**{g.get('term','')}** — {g.get('definition','')}\n" for g in gl]
    L += ["---",
          f"*Human Track. Its Developer Track twin (`{topic}.DEVELOPER.md`) covers the "
          f"same changes in technical detail. Neither is a simplified copy of the other — "
          f"they are the same truth in two languages.*"]
    return "\n".join(L)


def render_developer(d, topic):
    L = [f"# {d.get('title', topic)} — Developer Track",
         f"\n> **Topic:** `{topic}` · **Files:** {', '.join(f'`{f}`' for f in d.get('files', []))}",
         f"> **Generated:** {_today()}", "\n---\n",
         "## Module Summary\n", d.get("module_summary", ""), "", "## Architecture\n"]
    a = d.get("architecture", {})
    L += [f"- **Pattern:** {a.get('pattern','')}",
          f"- **Trust Boundary:** {a.get('trust_boundary','')}",
          f"- **Attack Surface:** {a.get('attack_surface','')}"]
    if a.get("dependencies"):
        L.append(f"- **Dependencies:** {', '.join(f'`{x}`' for x in a['dependencies'])}")
    L.append("")
    kss = d.get("kill_switches", [])
    if kss:
        L.append("## Kill Switches\n")
        for k in kss:
            rev = "reversible" if k.get("reversible") else "**NOT reversible**"
            L += [f"### `{k.get('location','')}` — {k.get('type','').upper()} ⚠️\n",
                  f"- **Condition:** {k.get('condition','')}",
                  f"- **Effect:** {k.get('effect','')}",
                  f"- **Reversibility:** {rev}"]
            if k.get("notes"):
                L.append(f"- **Notes:** {k['notes']}")
            L.append("")
    p = d.get("performance_profile", {})
    if p:
        L.append("## Performance Profile\n")
        tbl = p.get("measured_table", [])
        if tbl:
            L += ["| Component | Before | After | Mechanism |", "|---|---|---|---|"]
            L += [f"| {r.get('component','')} | {r.get('before','')} | "
                  f"{r.get('after','')} | {r.get('mechanism','')} |" for r in tbl] + [""]
        for label, key in [("CPU", "cpu"), ("Memory", "memory"), ("I/O", "io"),
                           ("Timer Interval", "timer_interval")]:
            if p.get(key):
                L.append(f"- **{label}:** {p[key]}")
        L.append("")
    s = d.get("security_analysis", {})
    if any(s.values()):
        L.append("## Security Analysis\n")
        for label, key in [("User Profiling", "user_profiling"), ("Targeting", "targeting"),
                           ("Trust Chain", "trust_chain"), ("Abuse Potential", "abuse_potential")]:
            if s.get(key):
                L += [f"### {label}\n", s[key], ""]
    fl = d.get("implementation_flow", [])
    if fl:
        L.append("## Implementation Flow\n")
        for st in fl:
            L.append(f"{st.get('step','')}. **`{st.get('function','')}`** — "
                     f"{st.get('description','')}")
            if st.get("side_effects"):
                L.append(f"   *Side effects:* {st['side_effects']}")
        L.append("")
    debt = d.get("technical_debt", [])
    if debt:
        L.append("## Technical Debt\n")
        icon = {"low": "🟡", "medium": "🟠", "high": "🔴", "accepted": "🟢"}
        for t in debt:
            L += [f"{icon.get(t.get('severity','low'),'🟡')} "
                  f"**{t.get('severity','').upper()}** — {t.get('item','')}",
                  f"  - *Recommendation:* {t.get('recommendation','')}", ""]
    for title, key in [("Impact If Removed / Disabled", "what_breaks_if_removed"),
                       ("Testing Notes", "testing_notes"),
                       ("Changelog Notes", "changelog_notes")]:
        if d.get(key):
            L += [f"## {title}\n", d[key], ""]
    L += ["---", f"*Developer Track. Human Track twin: `{topic}.LAYMAN.md`.*"]
    return "\n".join(L)


SEV_EMOJI = {'P0': '🔴', 'P1': '🟠', 'P2': '🟡', 'P3': '🟢',
             'Critical': '🔴', 'High': '🟠', 'Medium': '🟡', 'Low': '🟢'}


def render_audit(d, topic, infos=None, precheck=None):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    files = ", ".join(i['name'] for i in infos) if infos else "see payload"
    L = [f"# IBM-Style Audit Report: {topic}", "",
         "## SECTION A: DOCUMENT CONTROL", "",
         "| Attribute | Value |", "|---|---|",
         f"| **Target Category** | {topic} |",
         f"| **Files Scanned** | {files} |",
         f"| **Baseline** | Firefox 154 (mozilla-central) |",
         f"| **Date / Time** | {now} |",
         f"| **Audit Status** | {d.get('status','N/A')} |", "",
         "## SECTION B: EXECUTIVE SUMMARY (Track A — Layman)", "",
         d.get("executive_summary_layman", ""), "",
         "## SECTION C: TECHNICAL SUMMARY (Track B — Developer)", "",
         d.get("technical_summary_developer", ""), "",
         "## SECTION D: DETECTED DEFECTS", ""]
    defects = list(d.get("defects", []))
    if precheck:
        defects = precheck + defects
    if defects:
        for f in defects:
            sev = f.get('severity', 'P3')
            L += [f"### {SEV_EMOJI.get(sev,'🔵')} {f.get('id','')} — {sev}",
                  f"- **Track A (Layman):** {f.get('track_a','')}",
                  f"- **Track B (Technical):** {f.get('track_b','')}",
                  f"- **Remediation:** {f.get('remediation','')}"]
            if f.get("effort"):
                L.append(f"- **Effort:** {f['effort']}")
            L.append("")
    else:
        L += ["*No defects detected by rules or model.*", ""]
    r = d.get("readiness", {})
    L += ["## SECTION E: PRODUCTION READINESS ASSESSMENT", ""]
    score = r.get("score_percent")
    if score is not None:
        light = "🟢" if score >= 90 else ("🟡" if score >= 70 else "🔴")
        L.append(f"- **Overall readiness:** {light} {score}%")
    for label, key, box in [("Done", "done", "x"), ("Blockers", "blockers", " "),
                            ("To Do", "todo", " ")]:
        items = r.get(key, [])
        if items:
            L.append(f"- **{label}:**")
            L += [f"  - [{box}] {it}" for it in items]
    L.append("")
    exp = d.get("expansion_plan", [])
    if exp:
        L += ["## SECTION F: PHASED EXPANSION PLAN", ""]
        for e in exp:
            L += [f"### Phase {e.get('phase','?')} — `{e.get('target','')}`",
                  f"- **Tweak:** {e.get('tweak','')}",
                  f"- **Expected impact:** {e.get('impact','')}", ""]
    pos = d.get("positive_observations", [])
    if pos:
        L += ["## POSITIVE OBSERVATIONS", ""] + [f"- ✅ {x}" for x in pos] + [""]
    vc = d.get("verification_commands", [])
    if vc:
        L += ["## VERIFICATION COMMANDS", "", "```bash"] + vc + ["```", ""]
    return "\n".join(L)


def render_precheck(topic, infos, defects):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    L = [f"# Offline Pre-Check: {topic}", f"\n*Generated {now} by doc_audit.py "
         f"(rule-based, no model involved).*\n",
         "## File Inventory\n",
         "| File | Lang | Lines | Complexity | SHA256 (16) |", "|---|---|---|---|---|"]
    L += [f"| {i['name']} | {i['language']} | {i['lines']} | {i['complexity']} "
          f"| `{i['sha256']}` |" for i in infos]
    L += ["", f"## Rule Findings ({len(defects)})", ""]
    if defects:
        for f in defects:
            L += [f"### {SEV_EMOJI.get(f['severity'],'🔵')} {f['id']} — {f['severity']}",
                  f"- **Track A:** {f['track_a']}", f"- **Track B:** {f['track_b']}",
                  f"- **Remediation:** {f['remediation']}", ""]
    else:
        L.append("*All offline rules passed.*")
    return "\n".join(L)

# ─────────────────────────────────────────────────────────────────────────────
#  TOPIC HELPERS + MAIN
# ─────────────────────────────────────────────────────────────────────────────

def topic_slug(target: Path):
    # "13.TELEMETRY.KILL" -> "13-telemetry-kill"
    return re.sub(r'[^a-z0-9]+', '-', target.name.lower()).strip('-')


def collect(target: Path):
    files = find_source_files(target)
    if not files:
        sys.exit(f"[!] No source/patch files under {target}")
    return [analyze_file(f) for f in files]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["precheck", "payload", "doc", "audit", "full", "render"])
    ap.add_argument("--target", type=Path, help="Topic folder or single file")
    ap.add_argument("--output", type=Path, default=Path("./out"))
    ap.add_argument("--model", default="auto",
                    help="auto | claude-* | gemini-* | any ollama model name")
    ap.add_argument("--ollama-model", default="gemma4:latest")
    ap.add_argument("--allow-local", action="store_true",
                    help="EMERGENCY ONLY: permit the local Ollama model as a fallback. "
                         "Off by default — the script is model-first and will not touch "
                         "a local model unless you (a human with no quota left) opt in.")
    ap.add_argument("--context", type=Path,
                    help="Optional file of verified numbers/notes to ground the model")
    ap.add_argument("--from-json", type=Path, help="(render) JSON reply from any AI")
    ap.add_argument("--kind", choices=["layman", "developer", "audit"],
                    help="(render) which schema the JSON follows")
    ap.add_argument("--topic", help="(render) topic slug, e.g. 01-media")
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    if args.mode == "render":
        if not (args.from_json and args.kind and args.topic):
            sys.exit("render needs --from-json, --kind and --topic")
        d = json.loads(strip_fences(args.from_json.read_text(encoding='utf-8')))
        out = args.output / f"{args.topic}.{args.kind.upper()}.md"
        if args.kind == "audit":
            # Auto-merge precheck defects if a sibling PRECHECK.json exists
            pj = args.output / f"{args.topic}.PRECHECK.json"
            pre = json.loads(pj.read_text(encoding='utf-8')) if pj.exists() else None
            out.write_text(render_audit(d, args.topic, precheck=pre), encoding='utf-8')
            if pre:
                print(f"[i] Merged {len(pre)} precheck defect(s) from {pj.name}")
        else:
            fn = {"layman": render_layman, "developer": render_developer}[args.kind]
            out.write_text(fn(d, args.topic), encoding='utf-8')
        print(f"[+] Rendered: {out}")
        return

    if not args.target or not args.target.exists():
        sys.exit("[!] --target missing or does not exist")
    topic = topic_slug(args.target)
    infos = collect(args.target)
    extra = args.context.read_text(encoding='utf-8') if args.context and args.context.exists() else ""
    print(f"[*] Topic: {topic}  ({len(infos)} files)")

    precheck_defects = run_precheck_rules(infos)

    if args.mode in ("precheck", "full"):
        out = args.output / f"{topic}.PRECHECK.md"
        out.write_text(render_precheck(topic, infos, precheck_defects), encoding='utf-8')
        (args.output / f"{topic}.PRECHECK.json").write_text(
            json.dumps(precheck_defects, indent=2), encoding='utf-8')
        print(f"[+] Pre-check ({len(precheck_defects)} findings): {out}")
        if args.mode == "precheck":
            return

    if args.mode == "payload":
        for kind, schema in [("LAYMAN", LAYMAN_SCHEMA), ("DEVELOPER", DEVELOPER_SCHEMA),
                             ("AUDIT", AUDIT_SCHEMA)]:
            p = args.output / f"PROMPT_PAYLOAD.{topic}.{kind}.txt"
            p.write_text(build_payload(topic, infos, schema, extra), encoding='utf-8')
            print(f"[+] Payload: {p}")
        print("[i] Paste a payload into any AI, save its JSON reply, then run:")
        print(f"    python3 {Path(__file__).name} render --from-json reply.json "
              f"--kind layman --topic {topic}")
        return

    if args.mode in ("doc", "full"):
        for kind, schema, renderer in [("LAYMAN", LAYMAN_SCHEMA, render_layman),
                                       ("DEVELOPER", DEVELOPER_SCHEMA, render_developer)]:
            print(f"[*] Generating {kind} track ...")
            data = query_model(build_payload(topic, infos, schema, extra),
                               args.model, args.ollama_model, args.allow_local)
            out = args.output / f"{topic}.{kind}.md"
            out.write_text(renderer(data, topic), encoding='utf-8')
            (args.output / f"{topic}.{kind}.json").write_text(
                json.dumps(data, indent=2), encoding='utf-8')
            print(f"[+] {out}")

    if args.mode in ("audit", "full"):
        print("[*] Generating AUDIT ...")
        data = query_model(build_payload(topic, infos, AUDIT_SCHEMA, extra),
                           args.model, args.ollama_model, args.allow_local)
        out = args.output / f"{topic}.AUDIT.md"
        out.write_text(render_audit(data, topic, infos, precheck_defects), encoding='utf-8')
        (args.output / f"{topic}.AUDIT.json").write_text(
            json.dumps(data, indent=2), encoding='utf-8')
        print(f"[+] {out}")


if __name__ == "__main__":
    main()
