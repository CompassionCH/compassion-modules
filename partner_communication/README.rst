.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Partner Communication
=====================

Module to configure the communication with sponsors / partners.
It adds a model in order to define some communications and how to
send them to the partner (by e-mail or by printed letter)

Configuration
=============

You can add a system parameter to use a default e-mail address to be the
sender of your communications :

* ``partner_communication.default_from_address``
  email address which sends the letters to sponsors.

Usage
=====

You cannot use this module standalone. You can inherit it, add some config
rules and send communications to partners from your code, by using the
provided method in the communication_config class.

Known issues / Roadmap
======================

Credits
=======

Contributors
------------

* Emanuel Cino <ecino@compassion.ch>

Maintainer
----------

This module is maintained by `Compassion Switzerland <https://www.compassion.ch>`.