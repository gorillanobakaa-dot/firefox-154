=================================================================
  new.patches  —  Gorilla Unleashed Firefox 154  (2026-07-16)
=================================================================

WHAT THIS IS
  Every change you made, as .patch files, in the SAME folders as
  old.patches. 13 folders. That's it.

  Each folder = one topic:
    01.MEDIA            video/audio codec (hardware H.264)
    02.GPU             graphics / zero-copy / compositor
    03.NETWORKING      connection tuning
    04.PERFORMANCE     build-compat + Stencil
    05.PREFS           prefs (all.js, firefox.js, mozconfig...)
    06.QUOTA           storage quota
    07.TOOLKIT         addons / urlbar / suggest
    08.Look            theme + branding + locales (the big one)
    09.REMOTE          marionette / remote agent
    10.OVERRIDES       user.js (goes to the PROFILE, not source)
    11.FONT.SYSTEM     bundled fonts
    12.MOZAMBIQUE.DRILL normandy / nimbus kill
    13.TELEMETRY.KILL  MemoryTelemetry + Glean CPU kill (NEW this session)

  Inside each folder:
    *.patch        one per changed file (path is in the filename,
                   with __ instead of /)
    NEW_FILES/     brand-new files (logos, fonts) that get copied in,
                   not patched (there was nothing to patch against)

HOW IT WAS MADE
  Compared your firefox-main against the clean SafetyVault copy
  (the untouched Firefox 154). VERIFIED: all 316 patches apply
  cleanly onto that clean copy.

HOW TO APPLY (to a fresh Firefox 154 tree)
  cd <fresh-firefox-154>
  for p in <this-folder>/*/*.patch; do patch -p1 < "$p"; done
  # then copy each NEW_FILES/ tree into the source
  # then copy 10.OVERRIDES/NEW_FILES/user.js into the profile

NOTE: 13.TELEMETRY.KILL patches to third_party/rust/glean-core also
      need .cargo-checksum.json (included) or the build rejects them.
