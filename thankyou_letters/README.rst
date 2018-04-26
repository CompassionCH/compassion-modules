.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Thank You Letters
=================

Adds everything needed for thank you letters.

Configuration
=============

By default, three donation configurations are set:

* Small gifts (< 100CHF)
* Standard gifts (100 - 999 CHF)
* Large gifts (1000 CHF)

You can customize the limits by setting the three system parameters:

* thankyou_letters.small
* thankyou_letters.standard
* thankyou_letters.large

One example template comes installed and is the same for the 3 donation types.
You can however create other ones and attach them in the communication config
(Sales -> Partner Communications -> Communication Config)

In order to get a summary of the donations, activate the CRON sending it and
add a system parameter to set a User ID receiving the summary by e-mail:

* thankyou_letters.summary_user_id (1 for instance = admin)

You can as well edit the report layout for printing by changing the report
thankyou_letters.donation

Don't forget to create Success Stories to include them in your thank you
donations.

Known issues / Roadmap
======================

* Test invoices amount generates the correct thank you configuration
* Test invoices unreconcile removes from the thank you letter
* Test new invoices reconcile merge in the same letter and updates the configuration
* Test success sentences are set in texts

Credits
=======

Contributors
------------

* Emanuel Cino <ecino@compassion.ch>

Maintainer
----------

This module is maintained by `Compassion Switzerland <https://www.compassion.ch>`.
