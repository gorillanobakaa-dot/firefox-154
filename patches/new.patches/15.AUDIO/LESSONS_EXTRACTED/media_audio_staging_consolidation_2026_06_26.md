# media_audio_staging_consolidation_2026_06_26

**Source:** media_audio_staging_consolidation_2026_06_26.xml

## Rationale

The Firefox Unleashed Zero CPU media/audio staging directory had accumulated 7 orphaned
    duplicate files at the root patches/ level, and 4 separate disconnected documentation
    files with no cross-referencing. This caused version drift between sessions and made it
    impossible to reliably identify which AudioStream.cpp was canonical. All files were
    consolidated into a single authoritative directory with one master documentation file.

## Execution Logic

CANONICAL DIRECTORY:
    /home/gorilla/Documents/FIrefox.153.Work/GitHub_Staging/Firefox_Unleashed_Zero_CPU/patches/01_Media_Audio_Video/

    CANONICAL FILES (as of 2026-06-26):
    - AudioStream.cpp      : DSP v2 source (Jun 25 22:10, 35737 bytes) — SINGLE SOURCE OF TRUTH
    - AudioStream.h        : DSP v2 header
    - PDMFactory.cpp       : Hardware-only factory (Jun 25, 31623 bytes, newest version)
    - DecoderTraits.cpp    : Codec and container blocking
    - FFmpegVideoDecoder.cpp: VA-API hardware decode + 16-frame pool hard lock
    - RemoteVideoDecoder.cpp: Zero-copy IPC layer
    - CubebUtils.cpp       : Audio backend (no bugs, reference impl)
    - MASTER_DOCUMENTATION.md: v3.0 — ALL prior docs merged here (577 lines)
    - PDMFactory_upstream.cpp: Reference upstream mozilla-central (DO NOT MODIFY)
    - RemoteMediaDataDecoder_upstream.cpp: Reference upstream (DO NOT MODIFY)
    - ARCHIVE_DSP_TRIAL_AND_ERROR_HISTORY.md: Extended 1084-line archive with unique hardware diagrams

    DEPRECATED (still present, do not use as reference):
    - *.txt copies: plain text duplicates of .cpp files
    - BUG_FIXES_REPORT.md/.txt: content merged into MASTER_DOCUMENTATION.md
    - sugestions for Audio.Stream.txt: old v1 AudioStream source code

    ACTIONS PERFORMED (2026-06-26 ~15:57 BST):
    1. Copied canonical AudioStream.cpp + .h from root patches/ into 01_Media_Audio_Video/
    2. Merged 4 documentation files into single MASTER_DOCUMENTATION.md v3.0
    3. Deleted 7 stale files from root patches/: AudioStream.cpp, AudioStream.h,
       MASTER_DOCUMENTATION_Jun22.md, BUG_FIXES_REPORT_Jun22.md,
       DSP_TRIAL_AND_ERROR_HISTORY.md, DSP_HISTORY_v1_18h35.md,
       suggestions_AudioStream_Jun25.txt
    4. Moved extended DSP history (1084 lines, unique content) to
       ARCHIVE_DSP_TRIAL_AND_ERROR_HISTORY.md in 01_Media_Audio_Video/

    DEPLOYED TARGET (unchanged):
    /home/gorilla/Documents/FIrefox.153.Work/patches/dom/media/AudioStream.cpp
    (diff vs canonical: ZERO — verified Jun 25)

    ROOT patches/ DIRECTORY STRUCTURE (after cleanup):
    patches/
      01_Media_Audio_Video/     - ALL audio/video patches + MASTER_DOCUMENTATION
      02_Networking_UDP_TCP/    - Networking patches
      03_Graphics_GPU_Acceleration/ - Graphics patches
      04_Performance_GC_Timeouts/   - JS/GC patches
      assets/                   - mozconfig, README, shared assets
      surgical_v2_overrides/    - CSS overrides
      ui_tweaks/                - UI CSS files

    RULE: Never create standalone doc files in root patches/ or other locations.
    ALL media/audio documentation MUST append to 01_Media_Audio_Video/MASTER_DOCUMENTATION.md.
