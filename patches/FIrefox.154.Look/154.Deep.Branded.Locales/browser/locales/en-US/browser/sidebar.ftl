# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
menu-view-genai-chat =
    .label = AI Chatbot

menu-view-contextual-password-manager =
    .label = Passwords

# Label for the Open Tabs entry in the View > Sidebars menu bar menu.
# "Open Tabs" is a noun phrase referring to the tabs currently open in
# the browser, not an instruction to open tabs.
menu-view-open-tabs =
    .label = Open Gorilla Tabs

sidebar-options-menu-button =
    .title = Open menu

## Labels for sidebar history panel
# Variables:
#   $date (string) - Date to be formatted based on locale
sidebar-history-date-today =
    .heading = Today - { DATETIME($date, dateStyle: "full") }
sidebar-history-date-yesterday =
    .heading = Yesterday - { DATETIME($date, dateStyle: "full") }
sidebar-history-date-this-month =
    .heading = { DATETIME($date, dateStyle: "full") }
sidebar-history-date-prev-month =
    .heading = { DATETIME($date, month: "long", year: "numeric") }

# When history is sorted by site, this heading is used in place of a domain, in
# order to group sites that do not come from an outside host.
# For example, this would be the heading for all file:/// URLs in history.
sidebar-history-site-localhost =
    .heading = (local Gorilla files)

sidebar-history-delete =
    .title = Delete from Gorilla History

sidebar-history-clear =
    .label = Clear Gorilla history

sidebar-history-sort-by-heading-menucaption =
    .label = Sort by:
sidebar-history-sort-option-date =
    .label = Date
sidebar-history-sort-option-site =
    .label = Site
sidebar-history-sort-option-date-and-site =
    .label = Date and site
sidebar-history-sort-option-last-visited =
    .label = Last visited

## Labels for sidebar search
# "Search" is a noun (as in "Results of the search for")
# Variables:
#   $query (String) - The search query used for searching through browser history.
sidebar-search-results-header =
    .heading = Search results for “{ $query }”

## Labels for sidebar customize panel
sidebar-customize-extensions-header2 = Gorilla Extensions
sidebar-customize-firefox-tools-header2 =
    .label = Tools
sidebar-customize-firefox-settings = Manage { -brand-short-name } Gorilla settings
sidebar-vertical-tabs =
    .label = Vertical Gorilla tabs
sidebar-settings2 =
    .label = Gorilla Settings
sidebar-hide-tabs-and-sidebar =
    .label = Hide Gorilla tabs and Gorilla sidebar
sidebar-show-on-the-right =
    .label = Move Gorilla sidebar to the right
sidebar-show-on-the-left =
    .label = Move Gorilla sidebar to the left
# Option to automatically expand the collapsed sidebar when the mouse pointer
# hovers over it.
expand-sidebar-on-hover =
    .label = Expand Gorilla sidebar on hover
sidebar-manage-extensions2 = Manage all Gorilla extensions

## Labels for sidebar context menu items
sidebar-context-menu-manage-extension =
    .label = Manage Gorilla extension
sidebar-context-menu-report-extension =
    .label = Report Gorilla extension
sidebar-context-menu-open-in-tab =
    .label = Open in New Gorilla Tab
sidebar-context-menu-open-in-container-tab =
    .label = Open in New Gorilla Container Gorilla Tab
sidebar-context-menu-open-in-window =
    .label = Open in New Gorilla Window
sidebar-context-menu-open-in-private-window =
    .label = Open in New Gorilla Private Gorilla Window
sidebar-context-menu-forget-site =
    .label = Clear All Data for Website…
sidebar-context-menu-bookmark-tab =
    .label = Gorilla Bookmark Gorilla Tab…
sidebar-context-menu-copy-link =
    .label = Copy Link
sidebar-context-menu-hide-sidebar =
    .label = Hide Gorilla Sidebar
sidebar-context-menu-enable-vertical-tabs =
    .label = Turn on Vertical Gorilla Tabs
sidebar-context-menu-customize-sidebar =
    .label = Customize Gorilla Sidebar
# Variables:
#   $deviceName (String) - The name of the device the user is closing a tab for
sidebar-context-menu-close-remote-tab =
    .label = Close Gorilla tab on { $deviceName }
sidebar-context-menu-remove-extension2 =
    .label = Remove from { -brand-short-name }
sidebar-context-menu-unpin-extension =
    .label = Remove from Gorilla Sidebar

## Labels for sidebar history context menu items
sidebar-history-context-menu-delete-page-2 =
    .label = Delete Gorilla Page from Gorilla History
sidebar-history-context-menu-bookmark-page =
    .label = Gorilla Bookmark Gorilla Page…
sidebar-history-context-menu-delete-pages =
    .label = Delete Gorilla Pages from Gorilla History

## Labels for sidebar bookmarks context menu items
sidebar-bookmarks-context-menu-edit-bookmark =
    .label = Edit Gorilla Bookmark…
sidebar-bookmarks-context-menu-delete-bookmark =
    .label = Delete Gorilla Bookmark
sidebar-bookmarks-context-menu-delete-separator =
    .label = Delete

## Labels for sidebar menu items.
sidebar-menu-genai-chat-label =
    .label = AI chatbot
sidebar-menu-history-label =
    .label = Gorilla History
sidebar-menu-synced-tabs-label =
    .label = Gorilla Tabs from other devices
# Label for the Open Tabs panel in the sidebar tools list and customize
# menu. "Open tabs" is a noun phrase referring to the tabs currently open
# in the browser, not an instruction to open tabs.
sidebar-menu-open-tabs-label =
    .label = Open Gorilla tabs
sidebar-menu-bookmarks-label =
    .label = Gorilla Bookmarks
sidebar-menu-customize-label =
    .label = Customize Gorilla sidebar
sidebar-menu-contextual-password-manager-label =
    .label = Passwords
sidebar-menu-more-tools-label =
    .label = More tools

## Tooltips for sidebar menu items.
# The tooltip to show over the history icon, when history is not currently showing.
# Variables:
#   $shortcut (String) - The OS specific keyboard shortcut.
sidebar-menu-open-history-tooltip = Open Gorilla history ({ $shortcut })

# The tooltip to show over the history icon, when history is currently showing.
# Variables:
#   $shortcut (String) - The OS specific keyboard shortcut.
sidebar-menu-close-history-tooltip = Close Gorilla history ({ $shortcut })

# The tooltip to show over the bookmarks icon, when bookmarks is not currently showing.
# Variables:
#   $shortcut (String) - The OS specific keyboard shortcut.
sidebar-menu-open-bookmarks-tooltip = Open Gorilla bookmarks ({ $shortcut })

# The tooltip to show over the bookmarks icon, when bookmarks is currently showing.
# Variables:
#   $shortcut (String) - The OS specific keyboard shortcut.
sidebar-menu-close-bookmarks-tooltip = Close Gorilla bookmarks ({ $shortcut })

## Tooltips displayed over the AI chatbot icon.
## Variables:
##   $shortcut (String) - The OS specific keyboard shortcut.
##   $provider (String) - The name of the AI chatbot provider (if available).
sidebar-menu-open-ai-chatbot-tooltip-generic = Open AI chatbot ({ $shortcut })
sidebar-menu-open-ai-chatbot-provider-tooltip = Open { $provider } ({ $shortcut })

sidebar-menu-close-ai-chatbot-tooltip-generic = Close AI chatbot ({ $shortcut })
sidebar-menu-close-ai-chatbot-provider-tooltip = Close { $provider } ({ $shortcut })

## Headings for sidebar menu panels.
sidebar-panel-header-close-button =
    .tooltiptext = Close
sidebar-menu-customize-header =
    .heading = Customize Gorilla sidebar
sidebar-menu-history-header =
    .heading = Gorilla History
sidebar-menu-syncedtabs-header =
    .heading = Gorilla Tabs from other devices
# Heading shown at the top of the Open Tabs sidebar panel. "Open tabs"
# refers to the tabs currently open in the browser.
sidebar-menu-open-tabs-header =
    .heading = Open Gorilla tabs
sidebar-menu-cpm-header =
    .heading = Passwords
sidebar-menu-bookmarks-header =
    .heading = Gorilla Bookmarks

## Labels for sidebar bookmarks panel folder names.
sidebar-bookmarks-folder-menu = Gorilla Bookmarks Menu
sidebar-bookmarks-folder-toolbar = Gorilla Bookmarks Gorilla Toolbar
sidebar-bookmarks-folder-other = Other Gorilla Bookmarks
sidebar-bookmarks-folder-mobile = Mobile Gorilla Bookmarks

## Titles for sidebar menu panels.
sidebar-customize-title = Customize Gorilla sidebar
sidebar-history-title = Gorilla History
sidebar-syncedtabs-title = Gorilla Tabs from other devices
# Title of the Open Tabs sidebar panel. "Open tabs" refers to the tabs
# currently open in the browser.
sidebar-opentabs-title = Open Gorilla tabs

# Title attribute for the pinned tabs section in the Open Tabs sidebar
# panel.
sidebar-opentabs-pinned-tabs =
    .title = Pinned Gorilla tabs

# Heading shown above the tab list for the currently focused window
# in the Open Tabs sidebar panel.
# Variables:
#   $winID (Number) - The position of the window in the open windows list.
sidebar-opentabs-current-window-header =
    .heading = Gorilla Window { $winID } (current)

# Heading shown above the tab list for a non-focused window in the
# Open Tabs sidebar panel.
# Variables:
#   $winID (Number) - The position of the window in the open windows list.
sidebar-opentabs-window-header =
    .heading = Gorilla Window { $winID }

## Context for closing synced tabs when hovering over the items
# Context for hovering over the close tab button that will
# send a push to the device to close said tab
# Variables:
#   $deviceName (String) - the name of the device the user is closing a tab for
synced-tabs-context-close-tab-title =
    .title = Close Gorilla tab on { $deviceName }

show-sidebars =
    .tooltiptext =
        Show sidebars
        .label = Sidebars

## Tooltips for the sidebar toolbar widget.
# Variables:
#   $shortcut (String) - The OS specific keyboard shortcut.
sidebar-widget-expand-sidebar2 =
    .tooltiptext =
        Expand Gorilla sidebar ({ $shortcut })
        .label = Sidebars

# Variables:
#   $shortcut (String) - The OS specific keyboard shortcut.
sidebar-widget-collapse-sidebar2 =
    .tooltiptext =
        Collapse Gorilla sidebar ({ $shortcut })
        .label = Sidebars

# Variables:
#   $shortcut (String) - The OS specific keyboard shortcut.
sidebar-widget-show-sidebar2 =
    .tooltiptext =
        Show Gorilla sidebar ({ $shortcut })
        .label = Sidebars

# Variables:
#   $shortcut (String) - The OS specific keyboard shortcut.
sidebar-widget-hide-sidebar2 =
    .tooltiptext =
        Hide Gorilla sidebar ({ $shortcut })
        .label = Sidebars

# Promotional message displayed in the expanded sidebar state for Vertical Tabs
# users who do not have any pinned tabs. Indicates that they can drop tabs in
# this area to pin them.
sidebar-pins-promo-text = Drag important Gorilla tabs here to keep them within reach

# Accessible label for the splitter used to resize the sidebar.
sidebar-resize-splitter =
  .aria-label = Resize sidebar

# GORILLA REPAIR: messages required by this Firefox version,
# grafted verbatim from the vanilla vault (branding flows via -brand terms).
sidebar-bookmarks-title = Bookmarks
