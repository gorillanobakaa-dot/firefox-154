# Pref-Validation Pipeline — Full Architecture (design of record)

**Date:** 2026-08-01 · **Author:** Fable5/ultracode with the project owner
**Status legend:** [BUILT] working + tested · [BUILDABLE] cheap, not yet wired · [DESIGNED] real
work, spec'd not built · [HUMAN] cannot be fully automated.

## The core defect this fixes
The old pipeline collapsed **five orthogonal questions** into one "REAL" verdict. They are
separate decisions and must be decided separately:

1. **EXISTS** — is the string in Firefox source?  (searchfox — we had this)
2. **IMPLEMENTED** — does production code actually *read* it?  (consumer analysis — NEW)
3. **ALIVE** — is Mozilla's intent supported/permanent, or killswitch/experimental/dying?
4. **EFFECTIVE** — does changing it measurably do the claimed thing?
5. **SAFE** — is the effect useful, non-redundant, non-regressing, non-conflicting?

A searchfox hit answers only #1. "REAL, keep" off #1 alone was the bug.

## The classifier axes (each independent; a pref gets a value on each)

### A. Firefox source reality  [BUILT: sfpref] [BUILT: sfconsumers] [BUILDABLE: type/default/gating]
- EXISTS?  -> sfpref (searchfox `text:`) : REAL / FAKE(+nearest name)
- CONSUMED?  -> sfconsumers : DEFINED_AND_CONSUMED / TEST_ONLY / DEFINED_UNUSED
- TYPE+RANGE?  -> StaticPrefList.yaml `type:` field -> WRONG_TYPE / INVALID_VALUE  [BUILDABLE]
- GATING?  -> StaticPrefList `#if` / `do_not_use_directly` / mirror -> NIGHTLY_ONLY /
  BUILD_GATED / PLATFORM_GATED / ESR_UNAVAILABLE  [BUILDABLE]
- DEFAULT?  -> objdir `dist/bin/greprefs.js` effective default vs proposed value ->
  EFFECTIVE_CHANGE / REDUNDANT_DEFAULT / OVERRIDES_SAFER_DEFAULT  [BUILDABLE, local]

### B. Normative status  [BUILT: sfstandards seed] [DESIGNED: extended families]
- CONCEPT real + CURRENT/LEGACY?  Source FAMILIES (not one API):
  IETF (rfc-editor JSON: obsoleted_by) · W3C/WHATWG · ECMA/TC39 (proposal stage/withdrawn) ·
  Unicode + CLDR (i18n/Intl) · **IANA registries** (an RFC may DEFINE a thing the registry
  marks provisional/deprecated/reserved — a distinct check) · Khronos (WebGL/GLSL) ·
  WebGPU/WGSL · CA/Browser Forum + Mozilla Root Store (PKI) · ISO/IEC + MPEG + AOM
  (codecs — status is NOT enough: patents/OS-decoder/build-config decide shipping) · OpenType (fonts).
- **CORRECTION (the important one):** classify the BEHAVIOR the pref VALUE produces, not the
  technology it names. obsolete-tech is not auto-drop:
    - "enable obsolete protocol = true"          -> DROP/REJECT
    - "disable obsolete-protocol fallback = true" -> KEEP (this is the hardening)
    - "control migration from obsolete mechanism" -> TEMPORARY/lifecycle-dependent
    - "no-op compatibility pref"                   -> DROP

### C. Mozilla lifecycle & intent  [DESIGNED]
- searchfox blame -> introducing commit -> Bugzilla bug -> status/resolution + removal/deprecation
  bugs + code comments/annotations + release notes.
- States: SUPPORTED_CONTROL / EXPERIMENTAL_GATE / TEMPORARY_KILLSWITCH / ROLLBACK_PREF /
  MIGRATION_ONLY / DEBUG_OR_TEST / DEPRECATED / PENDING_REMOVAL.
- Cost: Bugzilla API is rate-limited + the read is interpretive. Semi-automatable.

### D. Runtime effect  [DESIGNED scaffold + HUMAN assertions]
- clean profile + target-pref-alone vs control profile, on Release/ESR where possible; measure.
- Per-CATEGORY assertion (no generic "does the claim hold"):
  network prefs -> tshark egress diff · web-API prefs -> `typeof navigator.X` / feature probe ·
  perf -> load-time delta. Detects SILENTLY_IGNORED / restart-required / MISSING_DEPENDENCY.
- Honest limit: the assertion encodes the CLAIM; claims are human-authored per pref.

### E. Dependency & conflict  [DESIGNED, hard]
- graph from source consumers + conditional branches: REQUIRES / MUTUALLY_EXCLUSIVE /
  SHADOWED_BY / OVERRIDES / NO_EFFECT_WHEN / BREAKS_UI_CONTROL. Individually-valid prefs can
  form an invalid config. Requires real source analysis; not cheap.

### F. Security / threat model  [HUMAN]
- per pref: claimed threat · protected asset · attacker capability · mitigation path ·
  residual risk · known regressions · already-provided-elsewhere?
- SECURITY_MITIGATION / PRIVACY_MITIGATION / DATA_MINIMIZATION / FINGERPRINTING_TRADEOFF /
  PERFORMANCE_ONLY / COSMETIC / UNSUBSTANTIATED_CLAIM. "More restrictive" != "more secure".

## Source hierarchy = FAMILIES, not sequential gates
Normative status · Firefox source reality · Mozilla lifecycle · Runtime effect · Security value ·
Config interaction · Expert curation (arkenfox/Betterfox — LEADS only) · Untrusted crowd
(GitHub user.js/blogs/AI lists — LEAD GENERATION ONLY, never acceptance).

## Final output states (union)
KEEP · KEEP_CONDITIONALLY · POLICY_PINNING_ONLY · REDUNDANT_DEFAULT · WRONG_NAME · RENAMED ·
INVALID_VALUE · FABRICATED · REMOVED · DEFINED_UNUSED · TEST_ONLY · BUILD_GATED · PLATFORM_GATED ·
NIGHTLY_ONLY · ESR_UNAVAILABLE · INERT · SHADOWED · MISSING_DEPENDENCY · LEGACY · DEPRECATED ·
EXPERIMENTAL · TEMPORARY · UNSUBSTANTIATED · SECURITY_THEATER · FINGERPRINTING_TRADEOFF ·
HIGH_BREAKAGE · REJECT.

## Recommended build order (cheap+high-value first)
1. [DONE] consumer analysis (sfconsumers) — kills the "string exists = real" error.
2. type/value + default-comparison + gating (all local/cheap; REDUNDANT_DEFAULT drops the most noise).
3. extend sfstandards families (IANA registry check is the highest-leverage add).
4. Mozilla lifecycle (Bugzilla) — separates killswitch/rollback from permanent control.
5. runtime harness scaffold (per-category), threat-model template — human-in-the-loop.
6. dependency/conflict graph — last, hardest.

## Tools
`Scripts.For.Work/searchfox-tools/`: sfpref.py (EXISTS) · sfconsumers.py (CONSUMED) ·
sfstandards.py (normative). pref_provenance.py = SUPERSEDED (GitHub-count, anti-signal).
