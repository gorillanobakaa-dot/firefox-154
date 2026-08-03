# MEDIA/GFX standards & identifier audit — 2026-08-02
# Tool: searchfox-tools/sfmedia.py (commit d5ec866) | scope: 01.MEDIA + 02.GPU (25 patches)
# Ground truth: vanilla vault + MP4RA + IANA video.csv + RFC-editor + pci.ids (offline)

# sfmedia scan — 62 distinct tokens from ['patches/new.patches/01.MEDIA', 'patches/new.patches/02.GPU']

   0x1002                                               STANDARD
       STANDARD: PCI-SIG vendor ID | PCI-SIG assignment | current | pci.ids: 1002 = Advanced Micro Devices [AMD/ATI]
   0x10de                                               STANDARD
       STANDARD: PCI-SIG vendor ID | PCI-SIG assignment | current | pci.ids: 10de = NVIDIA Corporation
   0x8086                                               STANDARD
       STANDARD: PCI-SIG vendor ID | PCI-SIG assignment | current | pci.ids (offline, 2026-08-02): 8086 = Intel Corporation
   AgnosticDecoderModule.h                              MOZ-VANILLA+DOC-ONLY
       MOZ-VANILLA: [dom/media/platforms/agnostic/AgnosticDecoderModule.cpp:5:#include "AgnosticDecoderModule.h"]
       DOC-ONLY: appears only in comments — verify as documentation
   AudioPsychoacousticEnhancer::AudioPsychoacousticEnhancer OURS
       OURS: [dom/media/AudioStream.cpp:224:AudioPsychoacousticEnhancer::AudioPsychoacousticEnhancer() = default;]
   AudioPsychoacousticEnhancer::Init                    OURS
       OURS: [dom/media/AudioStream.cpp:226:void AudioPsychoacousticEnhancer::Init(uint32_t aSampleRate, uint32_t aChannels) {]
   AudioPsychoacousticEnhancer::Process                 OURS
       OURS: [dom/media/AudioStream.cpp:243:void AudioPsychoacousticEnhancer::Process(AudioDataValue* aBuffer, uint32_t aFrames) {]
   AudioPsychoacousticEnhancer::UpdateGains             OURS
       OURS: [dom/media/AudioStream.cpp:234:void AudioPsychoacousticEnhancer::UpdateGains(float /* aVolumePercent */) {]
   AudioStream::Init                                    MOZ-VANILLA+DOC-ONLY
       MOZ-VANILLA: [dom/media/AudioStream.cpp:242:nsresult AudioStream::Init(AudioDeviceInfo* aSinkInfo)]
       DOC-ONLY: appears only in comments — verify as documentation
   CANPLAY_MAYBE                                        STANDARD+DOC-ONLY
       STANDARD: WHATWG HTML: canPlayType() -> 'maybe' | WHATWG | current | dom/media/mediaelement/HTMLMediaElement.cpp
       DOC-ONLY: appears only in comments — verify as documentation
   CANPLAY_NO                                           STANDARD
       STANDARD: WHATWG HTML: canPlayType() -> '' | WHATWG | current | vanilla HTMLMediaElement.cpp maps CANPLAY_NO -> empty string
   CC_TYPE                                              MOZ-VANILLA
       MOZ-VANILLA: [dom/media/gtest/moz.build:195:if CONFIG["CC_TYPE"] in ("clang", "clang-cl"):]
   CodecSupport::Unsupported                            MOZ-VANILLA
       MOZ-VANILLA: [dom/media/mediacapabilities/MediaCapabilities.cpp:373:      return CodecSupport::Unsupported;]
   ColorSpace2::BT709                                   MOZ-VANILLA
       MOZ-VANILLA: [dom/media/gtest/TestMP4Demuxer.cpp:1014:  EXPECT_EQ(info.mColorPrimaries, Some(gfx::ColorSpace2::BT709));]
   CubebUtils::GetFirstStream                           MOZ-VANILLA
       MOZ-VANILLA: [dom/media/CubebInputStream.cpp:89:    CubebUtils::ReportCubebStreamInitFailure(CubebUtils::GetFirstStream());]
   CubebUtils::GetVolumeScale                           MOZ-VANILLA
       MOZ-VANILLA: [dom/media/MediaTrackGraph.cpp:3391:      mGlobalVolume(CubebUtils::GetVolumeScale())]
   CubebUtils::PreferredSampleRate                      MOZ-VANILLA
       MOZ-VANILLA: [dom/media/MediaTrackGraph.cpp:2475:          : static_cast<TrackRate>(CubebUtils::PreferredSampleRate(]
   EncodeSupport::SoftwareEncode                        MOZ-VANILLA
       MOZ-VANILLA: [dom/media/gtest/TestWebrtcCodecFactory.cpp:83:              media::EncodeSupportSet{media::EncodeSupport::SoftwareEncode});]
   FEATURE_AV1_HW_DECODE                                MOZ-VANILLA
       MOZ-VANILLA: [widget/gtk/GfxInfo.cpp:1534:      {nsIGfxInfo::FEATURE_AV1_HW_DECODE, CODEC_HW_DEC_AV1,]
   FEATURE_AV1_HW_ENCODE                                MOZ-VANILLA
       MOZ-VANILLA: [widget/gtk/GfxInfo.cpp:1536:      {nsIGfxInfo::FEATURE_AV1_HW_ENCODE, CODEC_HW_ENC_AV1,]
   FEATURE_BLOCKED_PLATFORM_TEST                        MOZ-VANILLA+DOC-ONLY
       MOZ-VANILLA: [gfx/thebes/gfxPlatformGtk.cpp:268:    } else if (status == nsIGfxInfo::FEATURE_BLOCKED_PLATFORM_TEST) {]
       DOC-ONLY: appears only in comments — verify as documentation
   FEATURE_FAILURE_GORILLA_NO_HW_CODEC                  OURS
       OURS: [widget/gtk/GfxInfo.cpp:1494:        aFailureId = "FEATURE_FAILURE_GORILLA_NO_HW_CODEC";]
   FEATURE_H264_HW_DECODE                               MOZ-VANILLA
       MOZ-VANILLA: [widget/gtk/GfxInfo.cpp:1522:      {nsIGfxInfo::FEATURE_H264_HW_DECODE, CODEC_HW_DEC_H264,]
   FEATURE_H264_HW_ENCODE                               MOZ-VANILLA
       MOZ-VANILLA: [widget/gtk/GfxInfo.cpp:1524:      {nsIGfxInfo::FEATURE_H264_HW_ENCODE, CODEC_HW_ENC_H264,]
   FEATURE_HEVC_HW_DECODE                               MOZ-VANILLA
       MOZ-VANILLA: [widget/gtk/GfxInfo.cpp:1538:      {nsIGfxInfo::FEATURE_HEVC_HW_DECODE, CODEC_HW_DEC_HEVC,]
   FEATURE_HEVC_HW_ENCODE                               MOZ-VANILLA
       MOZ-VANILLA: [widget/gtk/GfxInfo.cpp:1540:      {nsIGfxInfo::FEATURE_HEVC_HW_ENCODE, CODEC_HW_ENC_HEVC,]
   FEATURE_STATUS_OK                                    MOZ-VANILLA+DOC-ONLY
       MOZ-VANILLA: [gfx/thebes/gfxPlatformGtk.cpp:164:  } else if (status != nsIGfxInfo::FEATURE_STATUS_OK) {]
       DOC-ONLY: appears only in comments — verify as documentation
   FEATURE_VP8_HW_DECODE                                MOZ-VANILLA
       MOZ-VANILLA: [widget/gtk/GfxInfo.cpp:1526:      {nsIGfxInfo::FEATURE_VP8_HW_DECODE, CODEC_HW_DEC_VP8,]
   FEATURE_VP8_HW_ENCODE                                MOZ-VANILLA
       MOZ-VANILLA: [widget/gtk/GfxInfo.cpp:1528:      {nsIGfxInfo::FEATURE_VP8_HW_ENCODE, CODEC_HW_ENC_VP8,]
   FEATURE_VP9_HW_DECODE                                MOZ-VANILLA
       MOZ-VANILLA: [widget/gtk/GfxInfo.cpp:1530:      {nsIGfxInfo::FEATURE_VP9_HW_DECODE, CODEC_HW_DEC_VP9,]
   FEATURE_VP9_HW_ENCODE                                MOZ-VANILLA
       MOZ-VANILLA: [widget/gtk/GfxInfo.cpp:1532:      {nsIGfxInfo::FEATURE_VP9_HW_ENCODE, CODEC_HW_ENC_VP9,]
   Feature::DMABUF                                      MOZ-VANILLA
       MOZ-VANILLA: [gfx/thebes/gfxPlatformGtk.cpp:112:    if (gfxConfig::IsEnabled(Feature::DMABUF)) {]
   FeatureState::GetValue                               MOZ-VANILLA+DOC-ONLY
       MOZ-VANILLA: [gfx/config/gfxFeature.cpp:18:FeatureStatus FeatureState::GetValue() const {]
       DOC-ONLY: appears only in comments — verify as documentation
   InitPromise::CreateAndReject                         MOZ-VANILLA
       MOZ-VANILLA: [dom/media/ogg/OggDemuxer.cpp:209:    return InitPromise::CreateAndReject(NS_ERROR_OUT_OF_MEMORY, __func__);]
   LogLevel::Debug                                      MOZ-VANILLA
       MOZ-VANILLA: [dom/media/imagecapture/ImageCapture.h:17:    MOZ_LOG_FMT(GetICLog(), mozilla::LogLevel::Debug, __VA_ARGS__)]
   MOZ_ASSERT                                           MOZ-VANILLA
       MOZ-VANILLA: [dom/media/imagecapture/CaptureTask.cpp:42:  MOZ_ASSERT(NS_IsMainThread());]
   MOZ_LOG                                              MOZ-VANILLA
       MOZ-VANILLA: [dom/media/imagecapture/ImageCapture.h:17:    MOZ_LOG_FMT(GetICLog(), mozilla::LogLevel::Debug, __VA_ARGS__)]
   MP4Decoder::IsH264                                   MOZ-VANILLA
       MOZ-VANILLA: [dom/media/mp4/MP4Demuxer.cpp:327:  if (videoInfo && MP4Decoder::IsH264(mInfo->mMimeType)) {]
   MatroskaDecoder::IsSupportedType                     MOZ-VANILLA
       MOZ-VANILLA: [dom/media/webm/MatroskaDecoder.cpp:113:bool MatroskaDecoder::IsSupportedType(const MediaContainerType& aContainerType,]
   OggDecoder::IsSupportedType                          MOZ-VANILLA
       MOZ-VANILLA: [dom/media/ogg/OggDecoder.cpp:15:bool OggDecoder::IsSupportedType(const MediaContainerType& aContainerType) {]
   PlatformDecoderModule::CreateDecoderPromise          MOZ-VANILLA
       MOZ-VANILLA: [dom/media/platforms/AllocationPolicy.cpp:198:                RefPtr<PlatformDecoderModule::CreateDecoderPromise> p =]
   Preferences::GetBool                                 MOZ-VANILLA
       MOZ-VANILLA: [dom/media/MediaTrackGraph.cpp:3527:  if (Preferences::GetBool("media.audiograph.single_thread.enabled", true)) {]
   StaticPrefs::media_gorilla_hardware_only_mode        OURS
       OURS: [dom/media/CubebUtils.cpp:504:  if (StaticPrefs::media_gorilla_hardware_only_mode()) {]
   WebMDecoder::IsSupportedType                         MOZ-VANILLA
       MOZ-VANILLA: [dom/media/webm/WebMDecoder.cpp:79:bool WebMDecoder::IsSupportedType(const MediaContainerType& aContainerType) {]
   WebrtcVideoConduit::HasAv1                           MOZ-VANILLA
       MOZ-VANILLA: [dom/media/webrtc/jsapi/DefaultCodecPreferences.cpp:15:  return WebrtcVideoConduit::HasAv1() &&]
   YUVColorSpace::BT709                                 MOZ-VANILLA
       MOZ-VANILLA: [dom/media/utils/PerformanceRecorder.cpp:68:      case gfx::YUVColorSpace::BT709:]
   av01                                                 STANDARD
       STANDARD: AOM 'AV1 Codec ISO Media File Format Binding' + MP4RA | Alliance for Open Media (2018) | current | MP4RA codecs registry (checked 2026-08-02): registered, AV1-ISOBMFF
   clang                                                MOZ-VANILLA
       MOZ-VANILLA: [dom/media/mediasink/VideoSink.cpp:7:// clang-format off]
   fix                                                  MOZ-VANILLA+DOC-ONLY
       MOZ-VANILLA: [dom/media/imagecapture/ImageCapture.cpp:118:  // check MediaStreamTrack.enable before bug 910249 is fixed.]
       DOC-ONLY: appears only in comments — verify as documentation
   gcc                                                  MOZ-VANILLA
       MOZ-VANILLA: [dom/media/MockCubeb.cpp:545:  // Note [[maybe_unused]] could silence this but then gcc warns about]
   hev1                                                 STANDARD
       STANDARD: ISO/IEC 14496-15 (NALu structured video in ISOBMFF) + MP4RA | MPEG (ISO/IEC JTC1/SC29); codec = ITU-T H.265 | ISO/IEC 23008-2 | current | MP4RA: NALu Video, ObjectType 0x23; param sets MAY be in-band
   hvc1                                                 STANDARD
       STANDARD: ISO/IEC 14496-15 + MP4RA | MPEG; codec = ITU-T H.265 | ISO/IEC 23008-2 | current | MP4RA: NALu Video, ObjectType 0x23; param sets ONLY in sample entry
   media.hardware-video-decoding.failed                 PREF-REAL
       PREF-REAL: DYNAMIC (C++ callsite) [gfx/thebes/gfxPlatform.cpp:953:        "media.hardware-video-decoding.failed");]
   media.rdd-ffmpeg.enabled                             PREF-REAL+DOC-ONLY
       PREF-REAL: DECLARED [modules/libpref/init/StaticPrefList.yaml:12530:- name: media.rdd-ffmpeg.enabled]
       DOC-ONLY: appears only in comments — verify as documentation
   mozilla/StaticPrefs_media.h                          MOZ-VANILLA+DOC-ONLY
       MOZ-VANILLA: [dom/media/ogg/OggDecoder.cpp:9:#include "mozilla/StaticPrefs_media.h"]
       DOC-ONLY: appears only in comments — verify as documentation
   video/                                               MOZ-VANILLA
       MOZ-VANILLA: [dom/media/ogg/OggDemuxer.cpp:113:  if (aRole.Find("audio/main") != -1 || aRole.Find("video/main") != -1) {]
   video/ogg                                            STANDARD
       STANDARD: IANA media-types registry | Xiph.Org / IETF | REGISTERED | IANA video.csv (checked 2026-08-02): RFC 5334 + RFC 7845
   video/webm                                           STANDARD*
       STANDARD*: NONE — de-facto convention | Google / WebM Project (2010) | UNREGISTERED (de-facto, universally shipped) | IANA video.csv (2026-08-02): absent from registry
   video/x-webm                                         STANDARD*
       STANDARD*: NONE — unregistered x- alias (RFC 6648 deprecates x- prefix) | legacy server convention | UNREGISTERED; absent from vanilla Firefox | vault grep 2026-08-02: 0 hits in vanilla; OURS-DEFENSIVE dead-belt
   vp09                                                 STANDARD
       STANDARD: WebM Project 'VP Codec ISO Media File Format Binding' + MP4RA | Google / WebM Project | current | MP4RA: ObjectType 0xB1; string vp09.PP.LL.DD[+5 optional], first 4 mandatory
   vp8                                                  STANDARD
       STANDARD: WebM/Matroska codec ID V_VP8 (RFC 9559); bitstream RFC 6386 | Google (On2 lineage) | current | canPlayType 'video/webm; codecs=vp8'; RFC 9559 = Matroska (IETF CELLAR, Oct 2024)
   vp9                                                  STANDARD
       STANDARD: WebM/Matroska codec ID V_VP9 (RFC 9559); bitstream = Google spec, no RFC | Google | current | RFC 9559 Matroska + WebM Project container guidelines

# SEMANTIC PAIR RULES
  [PAIR-OK] dom_media_DecoderTraits.cpp.patch: hev1/hvc1 both gated
  [PAIR-OK] dom_media_DecoderTraits.cpp.patch: vp09(ISOBMFF)/vp9(WebM) both gated

# verdict summary: {'STANDARD': 12, 'MOZ-VANILLA': 40, 'OURS': 6, 'PREF-REAL': 2, 'STANDARD*': 2}

# no invented/unprovenanced tokens — patch layer is clean
