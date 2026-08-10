# quarantine

## mozinfo.json.rogue-srcroot-2026-08-02.bak
Was at `/home/gorilla/firefox-main/mozinfo.json` (source ROOT). Created 2026-08-02 20:46 by
preflight tooling. **It broke every `./mach build`.**

`python/mozbuild/mozbuild/base.py` walks cwd + parents looking for `mozinfo.json` — "if we find
a mozinfo.json, we are in the objdir". Finding it at the source root made mach compute
topobjdir == topsrcdir and raise:
`BadEnvironmentException: The object directory appears to be the same as your source directory`.

Worse, the failure was INVISIBLE: mach then deadlocked on exit (its Glean dispatcher thread parks
on a crossbeam channel and never shuts down, so interpreter exit blocks in Thread.join()), so the
buffered error never flushed — the build presented as a silent 0-CPU stall for 95 minutes.

The LEGITIMATE mozinfo.json lives in `obj-x86_64-pc-linux-gnu/mozinfo.json` and is untouched.
Vanilla vault has no source-root mozinfo.json (confirmed) — this file was never upstream.
Restore only if some tool proves it needs it AND it is placed outside the source root.

## gfx_config_gfxConfigManager.cpp.patch.REVERTED-compositor-artifacts-2026-08-10.bak
Was `02.GPU/gfx_config_gfxConfigManager.cpp.patch`. Added an UNCONDITIONAL
`mFeatureWrCompositor->UserForceEnable(...)` — the WebRender native Wayland
compositor (NativeLayerRootWayland, one wl_subsurface per layer) could never be
turned off, by any pref. Cause of the 2026-08-10 artifacts: red/green flashes,
previous tab's image ghosting onto the next tab, corrupted chrome UI, plus
`meta_wayland_buffer_process_damage: assertion 'buffer->resource' failed` in
gnome-shell's journal. It also silently invalidated the 2026-08-09 user.js A/B
test (commenting the pref out disabled nothing — this hunk won).
Reverted from the live tree 2026-08-10; `MOZ_LOG=WidgetCompositor:5` went from
449 NativeLayer lines to 0 after removal. The same force-enable existed a second
time as firefox.js defaults (`gfx.webrender.compositor` + `.force-enabled`) —
removed from `05.PREFS/browser_app_profile_firefox.js.patch` the same day.
To re-test the zero-copy overlay path later: set
`gfx.webrender.compositor.force-enabled=true` in user.js — upstream code
honours it; no rebuild needed. Do not resurrect this patch.

## appearance.mjs.patch.DEAD-noop-2026-08-04.bak
Was `07.TOOLKIT/browser_components_preferences_config_appearance.mjs.patch`. Malformed ("only
garbage was found in the patch input") AND a no-op: vanilla == live for
`browser/components/preferences/config/appearance.mjs` (cmp identical 2026-08-04), so it applies
to nothing. Removed from the shipped patch set. If an appearance.mjs change was intended, it was
never captured as a valid patch — redo from a real edit, don't resurrect this file.
