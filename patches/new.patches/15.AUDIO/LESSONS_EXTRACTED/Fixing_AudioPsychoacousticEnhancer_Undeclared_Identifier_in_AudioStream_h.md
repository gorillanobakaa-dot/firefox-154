# Fixing_AudioPsychoacousticEnhancer_Undeclared_Identifier_in_AudioStream_h

**Source:** Fixing_AudioPsychoacousticEnhancer_Undeclared_Identifier_in_AudioStream_h.xml

## Rationale

The code that manages audio was trying to use a new custom 'AudioPsychoacousticEnhancer' feature, but it forgot to introduce or define what that feature actually was at the beginning of the file, causing the build to fail.

PROBLEM: Compilation of `AudioStream.cpp` failed with `use of undeclared identifier 'AudioPsychoacousticEnhancer'` at line 372 of `AudioStream.h`. The `AudioPsychoacousticEnhancer` class was defined internally within `AudioStream.cpp` but it was used as a member variable `UniquePtr<AudioPsychoacousticEnhancer>` in the `AudioStream` class declaration inside `AudioStream.h` without a forward declaration.

## Execution Logic

SOLUTION: Added a forward declaration `class AudioPsychoacousticEnhancer;` to the top of `AudioStream.h`.

Added `class AudioPsychoacousticEnhancer;` below `class RLBoxSoundTouch;` in `/home/gorilla/firefox-source/dom/media/AudioStream.h` to satisfy the `UniquePtr` declaration.

CODE:
class AudioConfig;
class RLBoxSoundTouch;
class AudioPsychoacousticEnhancer;

PATHS: /home/gorilla/firefox-main/dom/media/AudioStream.h, /home/gorilla/firefox-main/dom/media/AudioStream.cpp

KEYWORDS: AudioPsychoacousticEnhancer, AudioStream, undeclared identifier, forward declaration, compilation error, UniquePtr
