# filter_chain_service_global_mask_2026_06_26

**Source:** filter_chain_service_global_mask_2026_06_26.xml

## Rationale

[AUDIT VERDICT 2026-08-02 — CURRENT-TRUE + RECURRENCE 2026-08-02] the mask symlink was deleted by the bulk naming purge and the preset resurrected the service (found ACTIVE, 21ms CPU/26h = inert but squatting); re-masked 2026-08-02. The mask is a FILE — re-verify `is-enabled == masked` after ANY bulk cleanup.


    The parasitic PipeWire filter-chain daemon (filter-chain.service) that inserts a
    resampler/EQ node into the audio graph was incorrectly logged as "disabled" in the
    previous session. The unit lives in global systemd scope with preset=enabled, making
    a user-scope "disable" completely ineffective — the service would silently resurrect
    on every login and reboot, continuing to subvert the Firefox DSP pipeline.
    Fix: permanently mask the unit at user scope, which takes priority over global presets.

## Execution Logic

Problem:
    - filter-chain.service is installed by Debian into /usr/lib/systemd/user/ (global scope)
    - The unit has "preset: enabled", meaning systemd re-enables it automatically
    - `systemctl --user disable filter-chain.service` only removes user symlinks; it cannot
      override the global preset. After the command, is-enabled still returned "enabled".
    - The service ran for 5h 48min before dying naturally, then would have restarted on login.

    Fix applied (2026-06-26 15:46 BST):
      systemctl --user mask filter-chain.service
      # Creates: ~/.config/systemd/user/filter-chain.service -> /dev/null
      # User-scope symlink to /dev/null takes absolute priority over global presets.

    Verification:
      systemctl --user is-enabled filter-chain.service   # must return: masked
      systemctl --user status filter-chain.service        # must show: masked

    Key rule:
    For ANY Debian-installed user service in /usr/lib/systemd/user/ that you want
    permanently dead: ALWAYS use `mask`, never just `disable`.
    Only "masked" guarantees the unit cannot be started by any mechanism (preset,
    dependency, or manual start).

    Context: This service ran /usr/bin/pipewire -c filter-chain.conf, inserting a
    parasitic adapter/resampler node into the PipeWire audio graph AFTER Firefox's custom
    AudioPsychoacousticEnhancer DSP processed audio — flattening bass boost, make-up gain,
    and xLOUD harmonic synthesis before the signal reached the ALC269 codec.
