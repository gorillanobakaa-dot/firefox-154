# 🦍 Lesson: Ultimate High-Resolution Gorilla SVG Injection (PIL Dynamic Resampling)

## 🧑‍🏫 Layperson Overview (The "Why it was blurry and how we fixed it" story)
When you use a browser, you see warning icons (like yellow triangles) or faint watermarked backgrounds (like the one in `about:config`). We wanted to replace all of these with our custom Gorilla logo.

**The First Attempt (The Blurry Gorilla):** 
At first, we took a standard Gorilla logo file (about 32 Kilobytes in size, roughly 256x256 pixels) and wrapped it in a "container" to trick the browser into thinking it was a standard browser icon. It worked! The Gorilla showed up everywhere. BUT... when the browser tried to stretch that 256-pixel image to fill a massive 800-pixel background, it looked like a blown-up, pixelated mess. It was incredibly blurry.

**The Solution (The 8-Megabyte Motherlode):** 
To fix the blurriness, we needed a much bigger, higher-quality image. We dug into our vault and found the master source file: a staggering 8-Megabyte logo with a resolution of 2598 by 2626 pixels. It's massive! 
But if we forced the browser to load an 8MB image every time it showed a warning, the browser would become incredibly slow and bloated. 

**The Magic Trick (Python to the Rescue):** 
Instead of manually messing with photo editing software, we wrote a tiny automated robot script using Python. This script:
1. Opens the gigantic 8MB master image.
2. Carefully and smoothly shrinks it down to *exactly* 800 by 800 pixels using a high-quality shrinking method (called "Lanczos").
3. Translates that perfectly crisp 800x800 image into a long string of text (called base64).
4. Packages that text string directly into a new browser icon file (`warning.svg` and `background.svg`).

**The CSS Fix (Making Room for the Gorilla):** 
Finally, the browser's style rules (CSS) were originally designed for a tiny little 32-pixel triangle. So, it was only showing the top-left corner of our giant Gorilla. We went into the CSS files and changed the rules: we told the browser to make the box 400x400 pixels wide and to shrink the Gorilla *just enough* so the whole thing fits perfectly inside the box without getting cut off.

**The Result:** Crystal clear, razor-sharp Gorilla logos everywhere, without slowing down the browser!

## 👩‍💻 Developer Details
- **The Challenge:** Scaling a standard 256x256 base64 PNG up to 800px within an SVG wrapper caused severe interpolation artifacts (blurriness).
- **The Asset:** Located `canonical_about_logo.png` (2598x2626, 8MB) in `/home/gorilla/Documents/mozilla-central-24949d57b331/browser/branding/gorilla/REAL_GORILLA_ICONS/content/`.
- **The Technique (Python PIL Resampling):** To prevent embedding an 8MB base64 payload into the UI thread, we utilized Python's Pillow (`PIL`) library to dynamically downsample the asset to exactly 800x800 pixels using Lanczos resampling (the highest quality anti-aliasing filter). We then buffered the output to an in-memory byte stream, encoded it to base64, and injected it into an SVG payload template.

### The Python Script
(See `generate_crisp_svgs.py` in this directory)

- **CSS Scaling Adjustments:** Because the SVG intrinsic size is now 800x800, standard CSS (`background-size: auto`) results in severe cropping. In `toolkit/components/aboutconfig/content/aboutconfig.css`, we overrode the defaults:
  - `.config-background` -> `background-size: contain; width: 400px; height: 400px;`
  - `.title` -> `background-size: 8em; min-height: 8em; padding-inline-start: 9em;`

- **Live deployment:** Pushed the modified SVGs to `/usr/lib/gorilla-unleashed/chrome/toolkit/` (in `skin/classic/global/icons/warning.svg` and `content/global/aboutconfig/background.svg`), pushed `aboutconfig.css`, and executed `live_patch_injector.py` to blast the startup caches.

## 📂 Paths
- **Source asset:** `/home/gorilla/Documents/mozilla-central-24949d57b331/browser/branding/gorilla/REAL_GORILLA_ICONS/content/canonical_about_logo.png` (8MB)
- **Replaced files (and backups):** 
  - `toolkit/themes/shared/icons/warning.svg`
  - `toolkit/components/aboutconfig/content/background.svg`
  - `toolkit/components/aboutconfig/content/aboutconfig.css`
- **Live installed paths:** 
  - `/usr/lib/gorilla-unleashed/chrome/toolkit/skin/classic/global/icons/warning.svg`
  - `/usr/lib/gorilla-unleashed/chrome/toolkit/content/global/aboutconfig/background.svg`
  - `/usr/lib/gorilla-unleashed/chrome/toolkit/content/global/aboutconfig/aboutconfig.css`

## 🔑 Key Lesson
**Don't rely on browser CSS scaling for base64 raster embeddings in SVGs.** If you start with a low-res base64, CSS upscaling causes interpolation blur. If you start with an ultra-high-res base64, it bloats the DOM/UI thread. The sweet spot is a script that dynamically downsamples the master canonical asset to the exact intrinsic boundary size of your target SVG wrapper.
