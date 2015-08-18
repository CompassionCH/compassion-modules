.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Compassion Sponsorships Tracking
================================

Module to track the sponsorships.
It is based on a new state : sds_state.
It adds a new kanban, tree and form view to track sponsorships.

Color conventions for SDS Tracking Kanban View :

    0. Blank - Default color
    1. Black - Sponsorships with NO SUB (cancelled, or no_sub)
    2. Red - Sub_rejected sponsorships or sponsorships that are likely to
             become sub_reject.
    3. Yellow - Indicates a higher priority action is required on this
                sponsorship.
    4. Light green - Indicates an action is required on this sponsorship,
                     typically a mailing is to be sent to the sponsor.
                     This is a low priority action.
    5. Green - Sub_accepted sponsorships or sponsorships likely to become
               sub_accept.
    6. Light blue - not used
    7. Blue - Draft sponsorships
    8. Violet - not used
    9. Pink - not used

Usage
=====

To use this module, you need to:

* Go to Sponsorship -> Track sponsorships

Known issues / Roadmap
======================

* Migrate code for V8

Credits
=======

Contributors
------------

* David Coninckx <david@coninckx.com>
* Emanuel Cino <ecino@compassion.ch>

Maintainer
----------

This module is maintained by `Compassion Switzerland <https://www.compassion.ch>`.