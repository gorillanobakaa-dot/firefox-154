# Offline Pre-Check: 01-media

*Generated 2026-07-16 19:33:48 by doc_audit.py (rule-based, no model involved).*

## File Inventory

| File | Lang | Lines | Complexity | SHA256 (16) |
|---|---|---|---|---|
| dom_media_AudioStream.cpp.patch | patch | 263 | 25 | `5f2c409d9cb8af62` |
| dom_media_AudioStream.h.patch | patch | 21 | 3 | `805df79bfd479119` |
| dom_media_CubebUtils.cpp.patch | patch | 28 | 4 | `ee45504effcb9ec2` |
| dom_media_DecoderTraits.cpp.patch | patch | 103 | 19 | `e174a0b284dcf9d6` |
| dom_media_ipc_RemoteVideoDecoder.cpp.patch | patch | 82 | 13 | `1f052c8f9797d73c` |
| dom_media_mediacapabilities_MediaCapabilities.cpp.patch | patch | 34 | 9 | `83dd09febd24234e` |
| dom_media_mediasource_MediaSource.cpp.patch | patch | 15 | 2 | `491d1f41c3d3e242` |
| dom_media_moz.build.patch | patch | 13 | 3 | `20caf84e87b9ac0f` |
| dom_media_platforms_PDMFactory.cpp.patch | patch | 214 | 33 | `73b023c3dd25b5e1` |
| dom_media_platforms_ffmpeg_FFmpegVideoDecoder.cpp.patch | patch | 72 | 10 | `6003c42f11b6da8a` |
| dom_media_webaudio_AudioContext.cpp.patch | patch | 73 | 12 | `22d3b13f56ea6e64` |
| dom_media_webaudio_AudioDestinationNode.cpp.patch | patch | 36 | 8 | `fbd32688e586afd0` |
| dom_media_webaudio_DynamicsCompressorNode.cpp.patch | patch | 28 | 3 | `86291ff29395ae3d` |
| dom_media_webcodecs_VideoDecoder.cpp.patch | patch | 26 | 4 | `c05353e81b989d38` |
| dom_media_webcodecs_VideoEncoder.cpp.patch | patch | 26 | 4 | `16fbed5eb7400362` |
| dom_media_webcodecs_WebCodecsUtils.cpp.patch | patch | 13 | 5 | `88b177c1b50afde2` |
| dom_media_webrtc_jsapi_DefaultCodecPreferences.cpp.patch | patch | 24 | 3 | `521f4dc4d07b98fe` |
| dom_media_webrtc_libwebrtcglue_VideoConduit.cpp.patch | patch | 21 | 1 | `6b53a0c8ce5dff6a` |
| dom_media_webrtc_libwebrtcglue_WebrtcVideoCodecFactory.cpp.patch | patch | 95 | 15 | `6f0a73c6268d1d35` |
| gfx_thebes_gfxPlatformGtk.cpp.patch | patch | 28 | 4 | `dc7625ca9de2994e` |

## Rule Findings (1)

### 🟡 P2-001 — P2
- **Track A:** A sticky note saying 'finish this later' was left inside the machine.
- **Track B:** dom_media_webaudio_AudioContext.cpp.patch: added lines contain 1 TODO/FIXME markers.
- **Remediation:** Resolve or convert to a tracked item in PATCH.READINESS.txt.
