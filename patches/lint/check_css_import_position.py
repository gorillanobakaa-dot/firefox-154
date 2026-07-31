#!/usr/bin/env python3
# =============================================================================
# check_css_import_position.py
#
# ONE deterministic gate for a real, expensive defect:
#   an @import (or @charset) placed AFTER a style rule is SILENTLY DROPPED by
#   the CSS parser. It is not an error; the line just does nothing.
#
# This is exactly how the Gorilla Firefox theme broke: the master-redirect
# @import was appended to the END of toolkit/themes/shared/global-shared.css
# (line 441, after 66 rule blocks). The parser dropped it, so every
# chrome://global/skin widget — every input field, dropdown, text control —
# never received the theme, and rendered with the OS's default field colour
# against the black chrome. The artefact was untraceable for weeks.
#
# WHY THIS SCRIPT AND NOT "just an instruction". The brain already carried the
# rule that caused it — "always append CSS, never overwrite" (true for style
# RULES, fatal for @import). Advisory rules get ignored by context-lost or
# non-Claude agents. This gate sits BELOW the agent layer: the git hook and the
# build both call it, so it binds every agent (Claude, Gemini, Kiro, Bob, agy)
# regardless of which instruction file that agent did or did not read.
#
# Per the CSS spec (CSS Cascade / @import): @import must precede all other rules
# except @charset and @layer-STATEMENTS (`@layer a, b;` with no block). @charset
# must be the very first thing. Anything after the first ruleset / @namespace /
# blocked at-rule that is an @import or @charset is invalid-position.
#
# Exit 0 = clean. Exit 1 = a violation was found (gates the commit/build).
# Exit 2 = the self-test failed (the gate itself is broken — treat as blocking).
#
# Model-agnostic, no node/network dependency. Deterministic. CC0.
# =============================================================================
import sys
from pathlib import Path


def strip_comments(css: str) -> str:
    """Remove /* ... */ comments but keep byte/line count stable by replacing
    each comment with same-length whitespace (newlines preserved), so reported
    line numbers still match the original file."""
    out = []
    i, n = 0, len(css)
    in_str = None  # quote char if inside a string
    while i < n:
        c = css[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(css[i + 1]); i += 2; continue
            if c == in_str:
                in_str = None
            i += 1; continue
        if c in "\"'":
            in_str = c; out.append(c); i += 1; continue
        if c == "/" and i + 1 < n and css[i + 1] == "*":
            j = css.find("*/", i + 2)
            if j == -1:
                j = n - 2
            block = css[i:j + 2]
            # preserve newlines so line numbers do not shift
            out.append("".join(ch if ch == "\n" else " " for ch in block))
            i = j + 2; continue
        out.append(c); i += 1
    return "".join(out)


def line_of(css: str, offset: int) -> int:
    return css.count("\n", 0, offset) + 1


def scan(css: str):
    """Single-pass top-level scan. @import/@charset is legal only while the
    prelude is open; the prelude closes at the first ruleset, @namespace, or any
    blocked/other at-rule. Bare @layer statements keep it open."""
    stripped = strip_comments(css)
    violations = []
    prelude_open = True
    i, n = 0, len(stripped)
    in_str = None
    depth = 0
    stmt_start = 0

    def stmt_keyword(frag):
        low = frag.lstrip().lower()
        if low.startswith("@charset"):
            return "@charset"
        if low.startswith("@import"):
            return "@import"
        if low.startswith("@layer") and "{" not in frag:
            return "@layer-stmt"
        return "other"

    while i < n:
        c = stripped[i]
        if in_str:
            if c == "\\" and i + 1 < n:
                i += 2; continue
            if c == in_str:
                in_str = None
            i += 1; continue
        if c in "\"'":
            in_str = c; i += 1; continue
        if c == "{":
            if depth == 0:
                # a blocked statement (ruleset or @media/@supports/@layer{})
                frag = stripped[stmt_start:i]
                kw = stmt_keyword(frag + "{")
                if kw in ("@import", "@charset") and not prelude_open:
                    off = stmt_start + frag.lower().find(kw)
                    violations.append((line_of(css, off), kw))
                # a blocked at-rule or ruleset closes the prelude unless it is a
                # bare @layer statement (which has no block, so we're not here)
                prelude_open = False
            depth += 1; i += 1; continue
        if c == "}":
            depth -= 1
            if depth == 0:
                stmt_start = i + 1
            i += 1; continue
        if c == ";" and depth == 0:
            frag = stripped[stmt_start:i]
            kw = stmt_keyword(frag)
            if kw in ("@import", "@charset"):
                if not prelude_open:
                    off = stmt_start + frag.lower().find(kw)
                    violations.append((line_of(css, off), kw))
            elif kw == "@layer-stmt":
                pass  # allowed, prelude stays open
            else:
                prelude_open = False  # @namespace or any other statement
            stmt_start = i + 1
            i += 1; continue
        i += 1
    return violations


def check_file(path: Path):
    try:
        css = path.read_text(encoding="utf-8", errors="surrogateescape")
    except Exception as e:  # noqa: BLE001
        return [(0, f"unreadable: {e}")]
    return scan(css)


def selftest() -> bool:
    good = '@charset "utf-8";\n@layer a, b;\n@import url("x.css");\n@namespace html "y";\n:root { color: red; }\n'
    bad = ':root { color: red; }\n#thing { padding: 1px; }\n@import url("master-redirect.css");\n'
    edge_comment = '/* @import url("in-a-comment.css"); */\n@import url("real.css");\nbody{color:#000}\n'
    ok = True
    if scan(good):
        print("SELFTEST FAIL: valid prelude flagged:", scan(good)); ok = False
    v = scan(bad)
    if not v or v[0][0] != 3:
        print("SELFTEST FAIL: late @import not caught at line 3:", v); ok = False
    if scan(edge_comment):
        print("SELFTEST FAIL: @import inside a comment false-positived:", scan(edge_comment)); ok = False
    if ok:
        print("SELFTEST OK: valid prelude passes, late @import at line 3 caught, commented @import ignored.")
    return ok


def main(argv):
    if "--selftest" in argv:
        return 0 if selftest() else 2
    files = [a for a in argv[1:] if not a.startswith("-")]
    if not files:
        print("usage: check_css_import_position.py [--selftest] FILE.css ...", file=sys.stderr)
        return 0
    total = 0
    for f in files:
        p = Path(f)
        if p.suffix != ".css":
            continue
        for line, kw in check_file(p):
            total += 1
            print(f"{f}:{line}: ERROR {kw} is after a style rule — the CSS parser "
                  f"will SILENTLY DROP it. Move it into the leading @import block "
                  f"(only @charset and bare @layer statements may precede it).",
                  file=sys.stderr)
    if total:
        print(f"\n{total} invalid-position @import/@charset finding(s). This is the "
              f"defect that broke the theme's input fields — refusing.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
