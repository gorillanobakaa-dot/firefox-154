"""
Firefox 154 project rules for `dual-track precheck`.

MIGRATED 2026-07-30 from doc-audit/doc_audit.py's run_precheck_rules(). Those
rules were the best part of that script and they are Firefox-specific, so they
live here rather than in the shared tool: dual-track also documents a kernel
patch set, a Go TUI and a Python search utility, none of which have vendored
Rust crates or a Necko stack.

The tool finds this file by walking up from whatever you point it at, so it
applies automatically to anything under FIrefox.154.Work/.

CONTRACT
    rules(infos, collect) -> None
        infos    — list of dicts from analyze_file(): ref, name, path, language,
                   lines, code_lines, complexity, sha256, content
        collect  — call collect.add(severity, track_a, track_b, remediation,
                   effort=None); severity is one of P0/P1/P2/P3

Both tracks are mandatory on every finding. `track_a` must be readable by
someone who has never seen a compiler — a physical analogy, no jargon. `track_b`
must name the file and the mechanism. A defect only a developer can understand
fails this project's philosophy just as surely as an undocumented patch.

The generic TODO/FIXME rule is NOT repeated here — dual-track applies it to
every project already, and duplicating it would double-report.
"""

import importlib.util
import os
import re
from pathlib import Path

FF_SRC = Path(os.environ.get("FF_SRC", "/home/gorilla/firefox-main"))

# Reuse the SINGLE CSS @import-position validator (the same one the git hook and
# build_gorilla.sh call). One implementation, three callers — never a second
# copy of the check, which is precisely how the 400 KB / 12-tools overflow was
# missed elsewhere. If the validator is absent, the CSS rule simply no-ops
# rather than guessing.
_CSS_SCAN = None
_v = Path(__file__).parent / "patches" / "lint" / "check_css_import_position.py"
if _v.exists():
    _spec = importlib.util.spec_from_file_location("css_import_check", _v)
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    _CSS_SCAN = _mod.scan

# Directories that must all be present before this file believes it is looking at
# a mozilla-central checkout.
_TREE_MARKERS = ("browser", "netwerk", "dom", "toolkit")


def _tree_is_usable(root: Path) -> bool:
    """Is FF_SRC a real source tree, or just a directory that happens to exist?

    WHY THIS GUARD EXISTS. The original rule tested only `FF_SRC.exists()` and
    then concluded "the patch target is missing, upstream must have moved it".
    Run against the tree on 2026-07-30 that produced 61 P1 defects from 60
    patches — very nearly one per patch — because the tree had been reduced to
    devtools/, js/, mozglue/, testing/, tools/ and the objdir. `mach` was gone
    and so were browser/, dom/, netwerk/ and intl/. The directory existed; the
    source did not.

    A rule that flags everything is worse than no rule: it teaches the reader to
    skip the defects section, which is where the real findings live. An absent
    tree means "cannot check", and "cannot check" must never be reported as
    "found a problem".
    """
    return root.exists() and all((root / m).is_dir() for m in _TREE_MARKERS)


def _added(content):
    """The '+' side of a diff only. Old values live on '-' lines."""
    return [l[1:] for l in content.splitlines()
            if l.startswith('+') and not l.startswith('+++')]


def _target(content):
    m = re.search(r'^\+\+\+ [ab]/(.+)$', content, re.MULTILINE)
    return m.group(1).strip() if m else None


def rules(infos, collect):
    patches = [i for i in infos if i['name'].endswith('.patch')]
    names = {i['name'] for i in infos}
    tree_ok = _tree_is_usable(FF_SRC)

    # Say out loud that a whole class of checking was skipped. Silence would let
    # a report look clean when it was merely incomplete, and "no findings"
    # must never be confusable with "not checked".
    if not tree_ok:
        missing = [m for m in _TREE_MARKERS if not (FF_SRC / m).is_dir()]
        collect.add(
            'P2',
            "The patches could not be checked against the real Firefox source, "
            "because that source is not on this machine right now. Everything "
            "below still applies, but nobody has confirmed these repairs still "
            "match the building they were written for.",
            f"FF_SRC={FF_SRC} is not a usable mozilla-central checkout "
            f"(missing: {', '.join(missing)}). Patch-target verification (R2) "
            f"was SKIPPED for all {len(patches)} patch(es).",
            "Restore or re-clone the source tree, set FF_SRC to it, and re-run "
            "the pre-check before trusting any readiness score.")

    # R1 — a vendored Rust crate edited without its checksum manifest patch.
    # mach build verifies per-file SHA256 against .cargo-checksum.json and
    # rejects the crate outright, so this fails the build rather than misbehaving
    # at runtime. That is why it is P1 and not a style note.
    rust_patches = [i for i in patches
                    if 'third_party_rust' in i['name']
                    and 'cargo-checksum' not in i['name']]
    if rust_patches and not any('cargo-checksum' in x for x in names):
        collect.add(
            'P1',
            "A sealed factory part was modified, but the seal-inspection sticker "
            "was not updated. The factory will refuse the part at the door — "
            "nothing subtle happens, the build simply stops.",
            f"Vendored crate patches present ({rust_patches[0].get('ref', rust_patches[0]['name'])}, "
            f"{len(rust_patches)} total) with no .cargo-checksum.json patch in the "
            f"same topic. mach build verifies per-file SHA256 against the checksum "
            f"manifest.",
            "Add the matching .cargo-checksum.json.patch. Also delete stale "
            "libglean_core-*.rlib, .fingerprint/* and libgkrust.a before rebuilding, "
            "or the old artefact is silently reused.",
            effort="30min")

    for i in patches:
        # R2 — the patch aims at a file that is not in the live tree any more.
        # Only checkable when the source tree is actually present; asserting a
        # missing target without the tree to check against would be a guess.
        tgt = _target(i['content'])
        if tgt and tree_ok and not (FF_SRC / tgt).exists():
            collect.add(
                'P1',
                f"A repair instruction points at a room that does not exist in "
                f"the current building ({tgt}). Upstream moved or renamed it, so "
                f"the repair cannot be carried out.",
                f"{i.get('ref', i['name'])}: target path {tgt} is missing under "
                f"{FF_SRC}. The patch will not apply.",
                "Re-locate the code in the new tree and regenerate the patch "
                "against it.",
                effort="1h")

    # R4 — Necko rules, inherited from unified_audit.py. These fire only when the
    # relevant files are in scope, so they cost nothing on unrelated topics.
    for i in infos:
        if not (i['name'].startswith('netwerk') or 'Http' in i['name']
                or 'nsHost' in i['name']):
            continue
        body = ("\n".join(_added(i['content']))
                if i['name'].endswith('.patch') else i['content'])
        ref = i.get('ref', i['name'])

        if ('HttpConnectionUDP' in i['name'] and 'SetRecvBufferSize' in body
                and 'SetSendBufferSize' not in body):
            collect.add(
                'P1',
                "The incoming loading dock was widened but the outgoing dock kept "
                "its narrow default door, so uploads bottleneck while downloads "
                "got faster. Half a fix reads as a whole one in a benchmark that "
                "only measures downloads.",
                f"{ref}: InitCommon() calls SetRecvBufferSize but never "
                f"SO_SNDBUF/SetSendBufferSize.",
                "Add mSocket->SetSendBufferSize(33554432) next to the recv call.",
                effort="10min")

        m = re.search(r'NEGATIVE_RECORD_LIFETIME\s*=?\s*(\d+)', body)
        if m and int(m.group(1)) > 15:
            collect.add(
                'P3',
                f"When a web address fails to resolve, the failure is remembered "
                f"for {m.group(1)} seconds. For a server that moves around, that "
                f"means staying broken longer than necessary after it comes back.",
                f"{ref}: NEGATIVE_RECORD_LIFETIME = {m.group(1)} (>15).",
                "Reduce to 15 seconds for dynamic signalling servers.",
                effort="5min")

    # R5 — CSS @import/@charset placed after a style rule. The parser SILENTLY
    # DROPS it: no error, the line just does nothing. This broke the theme's
    # input fields for weeks (master-redirect @import appended to the end of
    # global-shared.css). P0 because a dropped theme-delivery import ships a
    # visibly broken UI while every artefact looks present and correct.
    if _CSS_SCAN is not None:
        for i in infos:
            if not i['name'].endswith('.css'):
                continue
            for line, kw in _CSS_SCAN(i.get('content', '') or ''):
                collect.add(
                    'P0',
                    f"A theme instruction ({kw}) was pinned to the bottom of the "
                    f"stylesheet instead of the top. CSS ignores it there — like "
                    f"stapling the cover page to the back of a report — so the "
                    f"whole theme it was meant to pull in never loads.",
                    f"{i.get('ref', i['name'])}:{line}: {kw} appears after a style "
                    f"rule. Per the CSS spec it must precede all rules except "
                    f"@charset and bare @layer statements, or the parser drops it.",
                    f"Move the {kw} into the leading import block at the top of the "
                    f"file. Verify with patches/lint/check_css_import_position.py.",
                    effort="2min")
