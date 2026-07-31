# ABOUT: PAGES — CONSOLIDATED KNOWLEDGE + MEMORY-TIER AUDIT (2026-07-31)

**Purpose**: one place answering "what have we ever done to each `about:` page,
and can the recorded knowledge be trusted?" Commissioned after (a) the CSS
theme audit found convincing-but-wrong entries, and (b) a prior agent (Gemini)
corrupted work and seeded vector DBs with plausible garbage.

**Method (computed, not narrated)**: every mention of the 46 pages listed on
`about:about` was mechanically extracted from three memory tiers —
1. **DB**: `SECOND.BRAIN/Chroma.DB.and.Brain.xml/Firefox.154.Lessons/chroma_fx154/chroma.sqlite3`
   (collection `firefox_154`, 170 docs) ← **this is the Firefox-specific database**
2. **XML**: the 345 source lesson XMLs beside it (13 category folders)
3. **MD**: all .md/.txt under `patches/` (Mega.Lessons, new.patches,
   FIrefox.154.Look/notes, DOCS.dual-track) + Icon GATHERED_BRAIN_LESSONS

Raw verbatim snippets (deduplicated, attributed): **`ABOUT_PAGES_EVIDENCE.md`**
(generated file, ~310 KB, same directory). This document holds the coverage
index and the AUDIT VERDICTS. Extractor: session scratchpad `extract_about.py`
/ `audit_about.py` (logic described inline below so it can be re-run).

---

## 1. Coverage index (which pages have recorded history)

| Page | Snippets | Sources | Page | Snippets | Sources |
|---|---|---|---|---|---|
| about:config | 95 | 45 | about:memory | 12 | 7 |
| about:preferences | 55 | 22 | about:networking | 12 | 8 |
| about:support | 50 | 17 | about:cache | 11 | 3 |
| about:translations | 36 | 12 | about:processes | 9 | 5 |
| about:welcome | 33 | 9 | about:telemetry | 8 | 5 |
| about:home | 29 | 9 | about:logins | 6 | 4 |
| about:addons | 25 | 13 | about:unloads | 5 | 3 |
| about:newtab | 21 | 10 | about:studies | 4 | 4 |
| about:buildconfig | 18 | 5 | about:checkerboard | 3 | 3 |
| about:certificate | 18 | 7 | about:glean / logging / license / mozilla / pdf / downloads | 3 ea | 3 ea |
| about:url-classifier | 14 | 4 | about:profiles / serviceworkers / webrtc | 2 ea | 2 ea |
| about:policies | 13 | 5 | about:debugging | 1 | 1 |

**No recorded work in any tier** (13 pages): about:about, compat, credits,
firefoxview, inference, keyboard, loginsimportreport, logo, privatebrowsing¹,
profiling, protections, rights, robots, sync-log, webauthn.
¹ about:privatebrowsing has CSS work under the *filename* `aboutPrivateBrowsing.css`
(copy map, THEME_FIX_LOG §2) and FTL damage (finding F2) — the `about:` string
extractor doesn't catch filename-only references; treat "no mention" as
"no `about:`-keyed mention", not "never touched".

---

## 2. AUDIT FINDINGS — same defect class as the CSS stylesheet

### F1 — The naming-scrub CORRUPTED database entries (CONFIRMED, 2 docs; 4 more flagged)

Scan: regex `[A-Za-z]\w*\.\.[A-Za-z]` (mangled identifiers) + doubled-word scan
over all 170 DB docs. Result **6/170 flagged**:

| DB doc | Signature | Verdict |
|---|---|---|
| `firefox_decodertraits_pref_gate_20260629` (id 32) | `media..hardware_only_mode` | **CORRUPT** — real pref is `media.gorilla.hardware_only_mode` (StaticPrefList.yaml:12746, verified in tree 2026-07-31). The de-vanity scrubber deleted "gorilla" from inside the pref name. An agent trusting this doc would create/query a nonexistent pref. |
| `firefox_rust_compile_pref_mismatch_err_build_005` (id 112) | `media..hardware_only_mode` | **CORRUPT** — same mangling. Bitter irony: this doc is ITSELF a lesson about pref-name mismatches. |
| `FTL_Never_Touch_l10n_name` (id 3) | "Gorilla Gorilla" | **NOT corrupt** — scanner false-positive: the doc legitimately *describes* the doubled-text symptom. Confirms the F2 bug was a known lesson. |
| `Consolidated_Historical_Lessons` (id 90) | "Unleashed Unleashed" | REVIEW — likely same scrub/dup class, unconfirmed. |
| `tree` (id 120), `llm_paths` (id 150) | `New..S` | REVIEW — mangled path names (scrubbed component), unconfirmed. |

**Implication**: identifiers (pref names, paths, constants) inside DB docs are
NOT trustworthy verbatim — the 17,000-occurrence naming cleanup ran through
them. Words survive; exact identifiers may be silently mangled. Always re-grep
the tree before using an identifier from the DB. The source XMLs (id 32 ←
`01.MEDIA/firefox_decodertraits_pref_gate_20260629.xml`) must be checked for
the same mangling before any re-ingestion.

### F2 — LIVE UI BUG traced: "Gorilla Gorilla" in 8 deployed FTL files (508 lines)

The doubled brand string seen in the bookmarks toolbar on 2026-07-31 is not a
CSS issue — it is baked into the restored deep-branded locales, and DB doc id 3
(`FTL_Never_Touch_l10n_name`) documented the mechanism in advance: blind
`sed s/Firefox/Gorilla/` rebrands double visible strings (and in the worst
class corrupt `data-l10n-name` attributes → invisible panels).

Damage census (verified `grep -c 'Gorilla Gorilla'`, 2026-07-31):

| File (under firefox-main) | Doubled lines |
|---|---|
| browser/locales/en-US/browser/preferences/preferences.ftl | **252** ← about:preferences |
| browser/locales/en-US/browser/browser.ftl | **171** ← browser chrome incl. bookmarks toolbar |
| toolkit/locales/en-US/toolkit/about/aboutAddons.ftl | **66** ← about:addons |
| browser/locales/en-US/browser/aboutPrivateBrowsing.ftl | 11 ← about:privatebrowsing |
| browser/locales/en-US/browser/menubar.ftl | 4 |
| browser/locales/en-US/browser/appmenu.ftl | 2 |
| browser/locales/en-US/browser/sanitize.ftl | 1 |
| browser/locales/en-US/browser/profile/default-bookmarks.ftl | 1 |

Also present: gratuitous insertions where the vanilla string never contained
"Firefox" (`menubar.ftl:267 "Gorilla Bookmark Current Gorilla Gorilla Tab…"`).
**Checked and clean**: zero corrupted `data-l10n-name`/`data-l10n-id`
attributes (regex sweep) — the invisible-panel failure class is absent.

**Fix strategy (per lesson id 3, NOT yet executed)**: for each of the 8 files,
restore the vanilla file from the vault and re-apply brand substitution ONLY
where the vanilla visible text contains "Firefox"; never inside `{ }`
placeables or any attribute. Do not sed the damaged files in place — the
gratuitous insertions make pattern-repair unreliable.

### F3 — Pref-name claim verdicts (every suspect from the about:-page snippets)

Method: candidate pref-shaped identifiers extracted from all snippets, checked
against StaticPrefList.yaml + all.js + firefox.js + profile user.js, then
tree-wide grep for the misses.

| Claimed identifier | Verdict | Evidence |
|---|---|---|
| `media..hardware_only_mode` | **CORRUPT** (F1) | real: StaticPrefList.yaml:12746 |
| `network.http.http3.support-version1` | **NONEXISTENT** — no hit anywhere in tree or patch dirs | networking docs claim; do not "restore" it |
| `media.hardware_decode_policy.strict` / `.allowed_codecs` | **NONEXISTENT** — design fiction, never implemented; actual policy is compiled-in (PDMFactory.cpp) + `media.gorilla.hardware_only_mode` | tree-wide grep 0 hits |
| `media.hardware-video-decoding.failed` | REAL | gfxPlatform.cpp:953,3063 (our dead-coded kill switch) |
| `gfx.bundled_fonts.skip_system_scan` | REAL | gfxPlatformFontList.cpp:791 (11.FONT.SYSTEM applied via snapshot) |
| `media.cubeb.backend` | REAL | tree hit (dom/media) |
| `media.rdd.process.enabled` (dotted) | SPELLING UNVERIFIED — grep dots match hyphens; canonical form likely `media.rdd-process.enabled` | re-check before use |
| `extensions.css`, `media.rdd.process.en`, `network.http.http3.initial_` | scanner artifacts (filename / snippet truncation), not claims | — |

### F4 — The pattern, named

Same signature as the CSS defect (legacy `--toolbar-field-color` looking right
while FF154 consumers read `--toolbar-field-text-color`): **an entry that is
locally plausible, syntactically valid, and wrong in exactly one identifier.**
Neither eyeballing nor vector-similarity search catches it — only mechanical
existence checks against the tree do. Standing rule: any identifier lifted
from memory tiers gets one `grep` in the tree before it is used or re-taught.

---

## 3. Verification & fingerprints (audit-log convention)

```bash
# DB is where it says, collection + doc count
sqlite3 ~/Documents/SECOND.BRAIN/Chroma.DB.and.Brain.xml/Firefox.154.Lessons/chroma_fx154/chroma.sqlite3 \
  "SELECT name FROM collections; SELECT count(*) FROM embedding_metadata WHERE key='chroma:document';"
# → firefox_154 / 170
# corrupt pref in doc 32, real pref in tree
sqlite3 <same-db> "SELECT string_value FROM embedding_metadata WHERE id=32 AND key='chroma:document';" | grep -o 'media\.\.[a-z_]*'
grep -n 'media.gorilla.hardware_only_mode' /home/gorilla/firefox-main/modules/libpref/init/StaticPrefList.yaml
# FTL damage census
grep -rc 'Gorilla Gorilla' /home/gorilla/firefox-main/browser/locales /home/gorilla/firefox-main/toolkit/locales 2>/dev/null | grep -v ':0'
```

sha256 at authoring time (re-run `sha256sum` on both files to detect tampering):
- `ABOUT_PAGES_EVIDENCE.md` — recorded in THEME_FIX_LOG_2026-07-31.md appended entry
- this file — recorded in THEME_FIX_LOG_2026-07-31.md appended entry

## 4. Open actions (none started — awaiting go-ahead)

1. Repair the 8 FTL files per F2 strategy (vault-restore + careful re-brand).
2. Fix DB docs 32 & 112 (+ their source XMLs) — restore `media.gorilla.` pref
   name; review docs 90/120/150.
3. Extend this audit's grep-before-trust rule to any future DB ingestion
   (add an identifier-existence check to `ingest_lessons.py`).
