# STATUS: DORMANT branded-locale MASTERS — kept, not live, not superseded

**What this is:** 189 branded locale files (`.ftl` + `.properties`) carrying Gorilla Unleashed
branding — a *comprehensive* ("deep") localized-rebrand set.

**Verified 2026-07-22 (evidence, not a guess):**
- **Branded masters, real work product** — Gorilla branding is present (e.g. `downloads.properties`).
- **NOT superseded by the canonical patch stack** — only **1 of 189** basenames overlap
  `new.patches/08.Look`. These are 188 *distinct* files the shipping stack does not contain.
- **NOT wired to the live pipeline** — the current rebrand scripts
  (`branding-tools/rebrand_154.sh` / `finish_rebranding.sh`) drive `new.patches/08.Look`, not
  this folder. Nothing live references it (only an *archived* `deploy.sh` did).

**Conclusion:** this is a **more thorough branded-locale set that did NOT ship** in the last
build (which brands via the smaller `08.Look` set). So it's **dormant masters** — neither the
live source nor redundant clutter.

**Decision: KEEP, uncompressed** (browsable) — it's branded work product with future value.
Do **not** delete or mistake it for the deployed locales.

**If you ever want the deep localized rebrand:** this is the master set. Wire it into the
rebrand pipeline (point the locale source here, regenerate the `08.Look` diffs from it), rather
than re-doing the branding by hand.
