# Audit lists — regenerated 2026-08-01 (durable re-run)
Source: config/firefox.js (1613 unique prefs) vs searchfox firefox-main (Nightly).
Method: batch namespace-enumerate (382 namespaces) + per-pref `text:` rescue on 109 misses.
Authority: searchfox. GitHub count NOT used (anti-signal — see PREF_AUDIT_FINAL_2026-08-01.md).

| bucket | count |
|---|---|
| REAL (batch enumerate) | 1504 |
| REAL (rescued by per-pref text:) | 21 |
| **REAL total** | **1525** |
| ABSENT from mozilla-central | 88 |
| ...of which present in OUR local build | 23 |

Files: all_prefs.txt · real.txt · absent.txt (annotated: in-local-build + nearest real names).
Prior (lost, scratchpad) run for comparison: 1504 batch + 18 rescued = 1522 REAL, ~82 absent, 9 in-build.
Next: classify absent.txt into DROP / FIX(rename) / FABRICATED, apply to config/firefox.js.

## Verification addendum (same day)
The 65 ABSENT-and-not-IN_LOCAL_BUILD prefs were re-checked against the generated
`dist/include/mozilla/StaticPrefList_*.h` accessor headers (67 files, 441,645 bytes,
positive control media.ffmpeg.vaapi.force-surface-zero-copy found): **0 hits**.
So the 65 are confirmed absent from our build through all three channels
(objdir greprefs.js · local browser/app/profile/firefox.js · static accessors).
Note: the thin `StaticPrefs_*.h` wrappers (~420 B each) contain NO pref names —
grepping those (as pref_provenance.py did) silently false-negatives. Use StaticPrefList_*.h.
Notable confirmed-inert: media.ffmpeg.vaapi-drm-display.enabled — currently SET in the
active patches/new.patches/10.OVERRIDES/NEW_FILES/user.js (line is a no-op in our build).
