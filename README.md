# Gorilla Unleashed — Firefox 154

A telemetry-stripped, hardware-accelerated, low-RAM rebuild of Firefox for old
and low-end Linux laptops — the machines that get thrown away while they still
have years of life in them.

> **🧸 In plain language:** this is Firefox with the phone-home, the background
> "services," and the bloat taken out, and the old machine's real hardware (its
> video chip, its graphics) switched back *on*. It runs well on a 2 GB laptop.
> Everything we changed is here as a **patch** (a small, readable description of
> the exact change) with a document next to it explaining, in both plain English
> and developer terms, *what* it does and *why*. Nothing is hidden.
>
> **💻 For developers:** a reproducible patch set against `mozilla-firefox`
> nightly (154.0a1), plus a one-command builder. Every patch is
> `diff -u`-format, applies with fuzz tolerance, and ships with a dual-track
> (layman + developer) MASTER log and an A–F readiness audit per subsystem.

## One command

```sh
git clone https://github.com/gorillanobakaa-dot/firefox.154.git
cd firefox.154
./recreate.sh
```

`recreate.sh` clones a fresh Firefox source, lays this patch set onto it, copies
the tuned build config, compiles it, and (optionally) wraps the result into an
installable `.deb` — with a proper big Gorilla icon on your desktop. Grab a
coffee: the download and the compile each take a while.

## What's in here

| Path | What it is |
|---|---|
| `recreate.sh` | the one-command builder (clone → patch → build → `.deb`) |
| `patches/` | the change set: `NN.TOPIC/` folders of `.patch` files + `apply.sh` |
| `patches/NN.TOPIC/MASTER_PROJECT_LOG_*.md` | dual-track documentation + A–F audit for each subsystem |
| `scripts/` | build wrapper, `.deb` packager, Microsoft-fonts helper |
| `mozconfig` | the tuned clang-21 build configuration |
| `deb_template/` | packaging skeleton (control, desktop entry, icon) |

## The subsystems

`01.MEDIA` H.264-only hardware decode + audio DSP · `02.GPU` un-blocklist the
Intel HD 4000 · `03.NETWORKING` kernel-matched TCP/DNS tuning · `04.PERFORMANCE`
`05.PREFS` baked defaults · `06.QUOTA` · `07.TOOLKIT` AI/ML seam removal ·
`08.Look` the theme + branding · `09.REMOTE` automation lockdown ·
`10.OVERRIDES` · `11.FONT.SYSTEM` · `12.MOZAMBIQUE.DRILL` experiment kill ·
`13.TELEMETRY.KILL` glean neutralised · `14.EGRESS.LOCKDOWN`.

Read any room's `MASTER_PROJECT_LOG_*.md` for the full story of that subsystem —
both tracks, every value, every reason.

## Hardware target

Tuned on and for era-2012 Intel hardware (Ivy Bridge / Intel HD 4000, the Sony
VAIO SVE14A3AJ reference machine), Debian 13 + Wayland. The audio DSP and codec
policy are compiled for that class of hardware; see `01.MEDIA` before deploying a
built binary to a very different machine.

## Fonts

The build can bundle Microsoft fonts (Segoe UI, Yu Gothic, Consolas) using the
established **ttf-ms-win-auto** method — sourced from Microsoft's own Windows
evaluation edition, the same approach mainstream Linux distributions use. See
`scripts/fonts-microsoft.sh` and `patches/11.FONT.SYSTEM/`.

## Why this exists

Open source gave the world the recipe but forgot to teach people how to cook.
Publishing code is not access if only engineers can read it. So every change here
carries a plain-language explanation next to the developer detail — the
documentation is a first-class part of the product, meant to be readable by the
person who owns the laptop, not just the person who compiles the browser.

*Not affiliated with Mozilla. "Firefox" is a trademark of the Mozilla Foundation;
this is an unofficial modified build.*
