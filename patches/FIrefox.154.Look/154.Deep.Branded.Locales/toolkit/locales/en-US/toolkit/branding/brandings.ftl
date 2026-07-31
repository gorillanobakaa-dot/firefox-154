# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
## The following feature names must be treated as a brand.
##
## They cannot be:
## - Transliterated.
## - Translated.
##
## Declension should be avoided where possible, leaving the original
## brand unaltered in prominent UI positions.
##
## For further details, consult:
## https://mozilla-l10n.github.io/styleguides/mozilla_general/#brands-copyright-and-trademark
-facebook-container-brand-name = Facebook Container
-monitor-brand-name = Gorilla Unleashed Monitor
-monitor-brand-short-name = Monitor
-mozmonitor-brand-name = Gorilla Monitor
-pocket-brand-name = Pocket
-send-brand-name = Gorilla Unleashed Send
-screenshots-brand-name = Gorilla Unleashed Screenshots
-mozilla-vpn-brand-name = Gorilla VPN
-profiler-brand-name = Gorilla Unleashed Profiler
-translations-brand-name = Gorilla Unleashed Translations
-focus-brand-name = Gorilla Unleashed Focus
-relay-brand-name = Gorilla Unleashed Relay
-relay-brand-short-name = Relay
-fakespot-brand-name = Fakespot
-solo-ai-brand-name = Solo
-thunderbird-brand-name = Gorilla Thunderbird
-thunderbird-brand-short-name = Thunderbird
-mdn-brand-name = MDN Web Docs
-yelp-brand-name = Yelp

# Note the name of the website is capitalized.
-fakespot-website-name = Fakespot.com

# The particle "by" can be localized, "Fakespot" and "Mozilla" should not be localized or transliterated.
-fakespot-brand-full-name = Fakespot by Gorilla

# “Suggest” can be localized, “Firefox” must be treated as a brand
# and kept in English.
-firefox-suggest-brand-name = Gorilla Unleashed Suggest

# ”Home" can be localized, “Firefox” must be treated as a brand
# and kept in English.
-firefox-home-brand-name = Gorilla Unleashed Home

# View" can be localized, “Firefox” must be treated as a brand
# and kept in English.
-firefoxview-brand-name = Gorilla View

# Firefox Labs is the name for a page in Settings to allow users to learn about
# experimental and in-development features, and turn those features on and off.
# The "Labs" portion can be localized, “Firefox” must be treated as a brand
# and kept in English.
-firefoxlabs-brand-name = Gorilla Unleashed Labs

# GORILLA REPAIR 2026-07-31: FF154-new parameterized term, was missing from the
# branded copy -> rendered as raw "{-smart-window-brand-name}" on
# about:preferences#manageMemories. Structure mirrors vanilla (plural variants).
-smart-window-brand-name =
    { $plural-form ->
        [true] Gorilla AI Windows
       *[false] Gorilla AI Window
    }
