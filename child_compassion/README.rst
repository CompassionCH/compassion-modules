.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

===================
Compassion Children
===================

Setup child and projects related objects for using with TCPT R4.
Contains Beneficiary, Beneficiary Lifecycle, ICP, ICP Lifecycle,
Child Holds and Global Child Pool management, Field Office,
Household, and other related objects...

Installation
============

This module depends on message_center_compassion to manage
messages with GMC Connect. You need to add pyquery, requests,
timezonefinder pytz libraries

- sudo pip install pyquery requests timezonefinder pytz

Configuration
=============

You need to add "Manage sponsorships" access rights to the users
who will have access to Beneficiary and ICP data.

Demand Planning:

You can add in the system settings default values for weekly demand and
resupply quantities by setting the following keys:

- `child_compassion.default_demand`
- `child_compassion.default_resupply`

To get weather information about each project location, you'll need to add an
API key from opernweathermap.com to the odoo.conf file.
`openweathermap_api_key = AAAAAAAAAAA`

Usage
=====

To use this module, you need to:

* Go to Sponsorship -> Children

Known issues / Roadmap
======================

* Implement mappings and messages for R4
* Tests for R4

Credits
=======

Contributors
------------

* Emanuel Cino <ecino@compassion.ch>
* Cyril Sester <cyril.sester@outlook.com>
* Kevin Cristi <kcristi@compassion.ch>
* David Coninckx <david@coninckx.com>

Maintainer
----------

This module is maintained by `Compassion Switzerland <https://www.compassion.ch>`.
