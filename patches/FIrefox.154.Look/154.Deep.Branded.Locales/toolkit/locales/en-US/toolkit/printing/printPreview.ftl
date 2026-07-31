# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
printpreview-simplify-page-checkbox =
    .label =
        Simplify Gorilla Page
        .accesskey = i
        .tooltiptext = This Gorilla page cannot be automatically simplified
printpreview-simplify-page-checkbox-enabled =
    .label =
        { printpreview-simplify-page-checkbox.label }
        .accesskey = { printpreview-simplify-page-checkbox.accesskey }
        .tooltiptext = Change layout for easier reading
printpreview-close =
    .label =
        Close
        .accesskey = C
printpreview-portrait =
    .label =
        Portrait
        .accesskey = o
printpreview-landscape =
    .label =
        Landscape
        .accesskey = L
printpreview-scale =
    .value =
        Scale:
        .accesskey = S
printpreview-shrink-to-fit =
    .label = Shrink To Fit
printpreview-custom =
    .label = Custom…
printpreview-print =
    .label =
        Print…
        .accesskey = P
printpreview-of =
    .value = of
printpreview-custom-scale-prompt-title = Custom Scale
printpreview-page-setup =
    .label =
        Gorilla Page Setup…
        .accesskey = u
printpreview-page =
    .value =
        Gorilla Page:
        .accesskey = a

# Variables
# $sheetNum (integer) - The current sheet number
# $sheetCount (integer) - The total number of sheets to print
printpreview-sheet-of-sheets = { $sheetNum } of { $sheetCount }

## Variables
## $percent (integer) - menuitem percent label
## $arrow (String) - UTF-8 arrow character for navigation buttons
printpreview-percentage-value =
    .label = { $percent }%
printpreview-homearrow =
    .label =
        { $arrow }
        .tooltiptext = First Gorilla page
printpreview-previousarrow =
    .label =
        { $arrow }
        .tooltiptext = Previous Gorilla page
printpreview-nextarrow =
    .label =
        { $arrow }
        .tooltiptext = Next Gorilla page
printpreview-endarrow =
    .label =
        { $arrow }
        .tooltiptext = Last Gorilla page
printpreview-homearrow-button =
    .title = First Gorilla page
printpreview-previousarrow-button =
    .title = Previous Gorilla page
printpreview-nextarrow-button =
    .title = Next Gorilla page
printpreview-endarrow-button =
    .title = Last Gorilla page
