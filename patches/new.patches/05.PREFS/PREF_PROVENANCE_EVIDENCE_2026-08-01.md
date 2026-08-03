# Pref Provenance Evidence — independent (non-Mozilla) verification — 2026-08-01

Method: `pref_provenance.py` — GitHub code-search consensus (independent trust root)
cross-checked with arkenfox/Betterfox + local build accessors. Vindicates the rollback.

## The 21 prefs that had been (wrongly) locked into firefox.js — verdict

### REAL (independently corroborated, keep IF build-defined)
| pref | GitHub refs |
|---|--:|
| app.update.enabled | 2756 |
| browser.newtabpage.activity-stream.telemetry | 1764 (+arkenfox) |
| browser.newtabpage.activity-stream.feeds.telemetry | 1484 (+arkenfox) |
| datareporting.healthreport.service.enabled | 1440 |
| toolkit.telemetry.cachedClientID | 1220 |
| browser.pocket.enabled | 388 |
| browser.shopping.experience2023.enabled | 328 |
| app.update.background.enabled | 255 |
| browser.shopping.experience2023.autoOpen.enabled | 211 |
| browser.newtabpage.activity-stream.telemetry.structuredIngestion.endpoint | 135 |
| browser.pocket.api | 98 |
| browser.ml.chat.hideFromLabs | 43 |
| nimbus.enabled | 24 |

### FABRICATED / wrong-name (GitHub = 1 → only our own fork = Gemini invention)
- browser.ml.audioTranscription.enabled
- browser.ml.backend.onnx.enabled
- browser.ml.textRecognition.enabled
- browser.ml.textTranslation.enabled
- browser.monitor.feature
- cookiebanners.reportingSite.telemetry.enabled
- datareporting.glean.enabled
- identity.fxaccounts.telemetry.clientAssertionJwt

**8 of 21 fabricated.** A real pref has thousands of independent witnesses; an
invented one has exactly one — the corrupted source. This is why searchfox alone
(Mozilla-controlled) was insufficient, and why the fast local adoption was reverted.
