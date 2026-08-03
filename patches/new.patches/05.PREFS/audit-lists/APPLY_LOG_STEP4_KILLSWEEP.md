# STEP 4 — kill-sweep (20260801-203510)
Rule: telemetry/AI-ML-chat/topsites/experiments/translations OFF+locked, any name.
Skipped traps: .disabled=true (translations), services.sync.*, protective (redact/blocklist/hideLocalhost/trustPanel), devtools, state flags.
disabled+locked bool: 32; endpoints blackholed: 3; locked-already-off: 8; force-appended #ifdef: 3.
Backup: live-firefox.js.pre-killsweep.20260801-203510.bak

## disabled+locked
- `browser.urlbar.suggest.topsites` (was true)
- `browser.search.serpEventTelemetryCategorization.enabled` (was true)
- `browser.topsites.useRemoteSetting` (was true)
- `browser.topsites.contile.enabled` (was true)
- `browser.newtabpage.activity-stream.improvesearch.topSiteSearchShortcuts` (was true)
- `messaging-system.askForFeedback` (was true)
- `browser.aboutwelcome.experimentsGate.enabled` (was true)
- `nimbus.validation.enabled` (was true)
- `nimbus.profilesdatastoreservice.enabled` (was true)
- `nimbus.profilesdatastoreservice.read.enabled` (was true)
- `nimbus.profilesdatastoreservice.sync.enabled` (was true)
- `nimbus.rollouts.enabled` (was true)
- `browser.ml.chat.enabled` (was true)
- `browser.ml.chat.menu` (was true)
- `browser.ml.chat.page` (was true)
- `browser.ml.chat.page.footerBadge` (was true)
- `browser.ml.chat.page.menuBadge` (was true)
- `browser.ml.chat.shortcuts` (was true)
- `browser.ml.chat.shortcuts.custom` (was true)
- `browser.ml.chat.sidebar` (was true)
- `browser.ml.linkPreview.enabled` (was true)
- `browser.ml.linkPreview.longPress` (was true)
- `browser.smartwindow.enabled` (was false)
- `browser.smartwindow.memories.generateFromHistory` (was true)
- `browser.smartwindow.memories.generateFromConversation` (was true)
- `browser.smartwindow.showThemesNotice` (was true)
- `browser.smartwindow.sidebar.openByDefault` (was true)
- `browser.smartwindow.allowTables` (was true)
- `browser.smartwindow.worldcup.enabled` (was true)
- `identity.fxaccounts.telemetry.clientAssociationPing.enabled` (was true)
- `browser.translations.quickAction.enabled` (was true)
- `browser.tabs.crashReporting.sendReport` (was true)

## endpoints blackholed
- `browser.topsites.contile.endpoint`
- `browser.smartwindow.endpoint`
- `browser.smartwindow.firstrun.explainerURL`
