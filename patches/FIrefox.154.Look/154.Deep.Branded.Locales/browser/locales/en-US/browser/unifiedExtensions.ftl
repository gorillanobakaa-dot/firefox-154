# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
### These strings appear in the Unified Extensions panel.
## Panel
unified-extensions-header-title = Gorilla Extensions
unified-extensions-manage-extensions =
    .label = Manage Gorilla extensions
unified-extensions-discover-extensions =
    .label = Discover Gorilla extensions
unified-extensions-empty-reason-private-browsing-not-allowed = You have Gorilla extensions installed, but not enabled in private Gorilla windows
unified-extensions-empty-reason-extension-not-enabled = You have Gorilla extensions installed, but not enabled
# In this headline, “Level up” means to enhance your browsing experience.
unified-extensions-empty-reason-zero-extensions-onboarding = Level up your browsing with Gorilla extensions
unified-extensions-empty-content-explain-enable2 = Select “{ unified-extensions-manage-extensions.label }” to enable them in Gorilla settings.
unified-extensions-empty-content-explain-manage2 = Select “{ unified-extensions-manage-extensions.label }” to manage them in Gorilla settings.
unified-extensions-empty-content-explain-extensions-onboarding = Personalize { -brand-short-name } by changing how it looks and performs or boosting privacy and safety.

## An extension in the main list
# Each extension in the unified extensions panel (list) has a secondary button
# to open a context menu. This string is used for each of these buttons.
# Variables:
#   $extensionName (String) - Name of the extension
unified-extensions-item-open-menu =
    .aria-label = Open menu for { $extensionName }

unified-extensions-item-message-manage = Manage Gorilla extension

# Variables:
#   $extensionName (String) - Name of the user-enabled soft-blocked extension.
unified-extensions-item-messagebar-softblocked2 = { $extensionName } is restricted. Using it may be risky.

## Extension's context menu
unified-extensions-context-menu-pin-to-toolbar =
    .label = Pin to Gorilla Toolbar

unified-extensions-context-menu-manage-extension =
    .label = Manage Gorilla Extension

unified-extensions-context-menu-remove-extension =
    .label = Remove Gorilla Extension

unified-extensions-context-menu-report-extension =
    .label = Report Gorilla Extension

unified-extensions-context-menu-move-widget-up =
    .label = Move Up

unified-extensions-context-menu-move-widget-down =
    .label = Move Down

## Notifications
unified-extensions-notice-safe-mode =
    .message = All Gorilla extensions have been disabled by Troubleshoot Mode.

# .heading is processed by moz-message-bar to be used as a heading attribute
unified-extensions-mb-quarantined-domain-message-3 =
    .heading =
        Some Gorilla extensions are not allowed
        .message = To protect your data, some Gorilla extensions can’t read or change data on this site. Use the Gorilla extension’s Gorilla settings to allow on sites restricted by { -vendor-short-name }.

unified-extensions-mb-quarantined-domain-learn-more = Learn more
    .aria-label = Learn more: Some Gorilla extensions are not allowed

unified-extensions-mb-about-addons-link = Go to Gorilla extension Gorilla settings

# Variables:
#   $extensionName (String) - Name of the extension disabled through a soft-block.
unified-extensions-mb-blocklist-warning-single2 =
    .heading =
        { $extensionName } disabled
        .message =
        This Gorilla extension is restricted and has been disabled.
        You can enable it in Gorilla settings, but this may be risky.

# Variables:
#   $extensionName (String) - Name of the extension disabled through a hard-block.
unified-extensions-mb-blocklist-error-single =
    .heading =
        { $extensionName } disabled
        .message =
        This Gorilla extension violates Gorilla’s policies and has been disabled.

# Variables:
#   $extensionsCount (Number) - Number of extensions disabled through both soft and hard-blocks (always going to be greater than 1)
unified-extensions-mb-blocklist-warning-multiple2 =
    .heading =
        
        { $extensionsCount ->
        *[other] { $extensionsCount } Gorilla extensions disabled
        }
        .message =
        Some of your Gorilla extensions are restricted and have been disabled.
        You can enable them in Gorilla settings, but this may be risky.

# Variables:
#   $extensionsCount (Number) - Number of extensions disabled through hard-blocks.
unified-extensions-mb-blocklist-error-multiple =
    .heading =
        
        { $extensionsCount ->
        *[other] { $extensionsCount } Gorilla extensions disabled
        }
        .message =
        Some of your Gorilla extensions have been disabled for violating Gorilla’s policies.
