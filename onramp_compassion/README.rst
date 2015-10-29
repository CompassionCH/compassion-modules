.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

OnRamp Compassion
=================

This module adds a route for listening to OnRamp messages call from
Compassion using REST message using authentification with a oauth2 token.

You need to send a message of type POST to address /onramp
with Authorization: Bearer <token> to pass the oauth2 authentification method
token must be provided by api2.compassion.com
plus with Content-Type: application/json
containing a body with json data.

Current supported messages are only Communication Kit Notifications
http://developer.compassion.com/docs/read/compassion_connect2/service_catalog/SupporterBeneficiary_Communication_Status


Installation
============
- 

Configuration
=============
-
    
Usage
=====
To use this module, you need to:

* send POST messages to address /onramp

Known issues / Roadmap
======================

* Contracts and Sponsorships will be better differenciated.

Credits
=======

Contributors
------------

* Emanuel Cino <ecino@compassion.ch>
* Yannick Vaucher <yannick.vaucher@camp2camp.ch>

Maintainer
----------

This module is maintained by `Compassion Switzerland <https://www.compassion.ch>`.