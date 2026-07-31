# ⚠️ STATUS: HISTORICAL — trial-and-error record. Read this first.

**Kept ON PURPOSE** as a "what we tried / what NOT to do" reference. This folder is the
UI/theme experimentation archive — an elaborate "zero-CPU UI architecture" (ghost shims,
SVG→text glyphs, mass physical asset ablation, theme injection). It is **NOT current
guidance.** Most of it was **superseded or never shipped.**

## What actually made it into the last build (verified 2026-07-22 against the canonical
## `new.patches/08.Look` stack + the deployed `~/firefox-main` tree):

| Technique described here | Reality in the last build |
|---|---|
| **`master-redirect.css` theme injection** | ✅ **APPLIED — this is the ONE that survived.** Live at `new.patches/08.Look/NEW_FILES/browser/themes/shared/master-redirect.css` (187 lines). The current canonical UI method. |
| **63-byte / 0-byte "ghost shim" mass ablation** (called a *core* method in `UI_Tweaks_Mega_Lesson.md`) | ❌ **essentially NOT applied** — 0 sixty-three-byte SVGs, exactly 1 zero-byte SVG in `firefox-main`. The wholesale ablation never shipped. |
| **SVG → text/unicode-glyph icons** (`svg_to_text_icons`) | ❌ **ABANDONED** — shipped once, **user-rejected, reverted** (brain lesson `Glyph_Nav_Controls_Abandoned`). Do NOT rebuild; recolor native SVGs instead. |
| the branding *scripts* catalogued in `scripts.path.md` / `Redundancy_Analysis_Report.md` | 🔁 **consolidated** into the toolkit (`gorilla-firefox-toolkit/`, run via `fx brand`); `scripts.path.md` itself self-declares SUPERSEDED (2026-07-18). |

## Why keep it then?
- **Trial-and-error is knowledge.** The record of *what didn't work and why* (the "invisible
  window" bug from naive FTL regex, the CPU cost of CSS `display:none` vs real excision, the
  user-rejection of text-glyph nav) is exactly what stops us repeating those mistakes.
- Every lesson here is also **twinned in the Chroma brain** (findable via `pfind --brain`).

## If you want the *current* way to do UI/branding
→ `fx brand` (dark-mode / shim / gen-icons / wayland-fix) + the `master-redirect.css` above.
This folder is the museum; the toolkit is the workshop.

---

## 2026-07-31 update (canonical-location correction)
The table above named `new.patches/08.Look/NEW_FILES/.../master-redirect.css
(187 lines)` as the live canonical copy. **As of 2026-07-31 the AUTHORITATIVE
master is `patches/FIrefox.154.Look/master-redirect.css` (315 lines** — token
renames, panel/autocomplete fixes, native-menu restoration). The NEW_FILES
copy was found 128 lines stale and has been re-synced from the Look master;
if they ever diverge again, the Look copy wins. Event ledger:
`notes/THEME_FIX_LOG_2026-07-31.md`.

