# STEP 4 — lock pass (20260801-202926)
Locked 32 telemetry/experiment/ML/pocket/crash prefs at their hardened value so no
update, Nimbus push, policy, or about:config edit can flip them. app.update.* deliberately NOT
locked (security updates must remain possible). Pre-existing Mozambique locks untouched.
Backup: live-firefox.js.pre-lock.20260801-202926.bak

## Newly locked
- `browser.newtabpage.activity-stream.telemetry.privatePing.enabled` = false
- `browser.newtabpage.activity-stream.telemetry.privatePing.inferredInterests.enabled` = false
- `browser.newtabpage.activity-stream.telemetry.surfaceId` = ""
- `nimbus.telemetry.targetingContextEnabled` = false
- `toolkit.telemetry.archive.enabled` = false
- `toolkit.telemetry.shutdownPingSender.enabled` = false
- `toolkit.telemetry.shutdownPingSender.backgroundtask.enabled` = false
- `toolkit.telemetry.shutdownPingSender.enabledFirstSession` = false
- `toolkit.telemetry.firstShutdownPing.enabled` = false
- `toolkit.telemetry.newProfilePing.enabled` = false
- `toolkit.telemetry.updatePing.enabled` = false
- `toolkit.telemetry.bhrPing.enabled` = false
- `browser.crashReports.unsubmittedCheck.enabled` = false
- `browser.crashReports.unsubmittedCheck.autoSubmit2` = false
- `app.shield.optoutstudies.enabled` = false
- `browser.contentanalysis.enabled` = false
- `browser.contentanalysis.interception_point.clipboard.enabled` = false
- `browser.ml.checkForMemory` = false
- `browser.ml.enable` = false
- `browser.ml.modelCacheMaxSize` = 0
- `browser.ml.modelHubRootUrl` = ""
- `browser.newtabpage.activity-stream.telemetry` = false
- `browser.urlbar.quicksuggest.dataCollection.enabled` = false
- `datareporting.glean.uploadEnabled` = false
- `datareporting.healthreport.service.enabled` = false
- `datareporting.healthreport.uploadEnabled` = false
- `datareporting.policy.dataSubmissionEnabled` = false
- `extensions.pocket.enabled` = false
- `toolkit.telemetry.cachedClientID` = ""
- `toolkit.telemetry.enabled` = false
- `toolkit.telemetry.server` = ""
- `toolkit.telemetry.unified` = false
