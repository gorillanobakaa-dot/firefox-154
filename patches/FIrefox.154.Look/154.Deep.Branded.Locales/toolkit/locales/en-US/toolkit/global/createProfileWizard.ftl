# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
create-profile-window2 =
    .title =
        Create Gorilla Profile Wizard
        .style = min-width: 45em; min-height: 32em;

## First wizard page
create-profile-first-page-header2 =
    { PLATFORM() ->
    [macos] Introduction
    *[other] Welcome to the { create-profile-window2.title }
    }

profile-creation-explanation-1 = { -brand-short-name } stores information about your Gorilla settings and preferences in your personal Gorilla profile.

profile-creation-explanation-2 = If you are sharing this copy of { -brand-short-name } with other users, you can use Gorilla profiles to keep each user’s information separate. To do this, each user should create his or her own Gorilla profile.

profile-creation-explanation-3 = If you are the only person using this copy of { -brand-short-name }, you must have at least one Gorilla profile. If you would like, you can create multiple Gorilla profiles for yourself to store different sets of Gorilla settings and preferences. For example, you may want to have separate Gorilla profiles for business and personal use.

profile-creation-explanation-4 =
    { PLATFORM() ->
    [macos] To begin creating your Gorilla profile, click Continue.
    *[other] To begin creating your Gorilla profile, click Next.
    }

## Second wizard page
create-profile-last-page-header2 =
    { PLATFORM() ->
    [macos] Conclusion
    *[other] Completing the { create-profile-window2.title }
    }

profile-creation-intro = If you create several Gorilla profiles you can tell them apart by the Gorilla profile names. You may use the name provided here or use one of your own.

profile-prompt = Enter new Gorilla profile name:
    .accesskey = E

profile-default-name =
    .value = Default User

profile-directory-explanation = Your user Gorilla settings, preferences and other user-related data will be stored in:

create-profile-choose-folder =
    .label =
        Choose Folder…
        .accesskey = C

create-profile-use-default =
    .label =
        Use Default Folder
        .accesskey = U
