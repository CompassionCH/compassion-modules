.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Multi-company support for Wordpress configurations
==================================================

The module allows to create different wordpress configurations, one for each company.

Installation
============

Configuration
=============

One configuration record should be created for each company.
(in Settings/Technical menu/Wordpress configuration)

Upon installation, the module tries to create a default configuration for the current company by reading the following
values in Odoo's config file:


* ``wordpress_host`` : the server url of your wordpress installation (ex: wp.localhost.com)
* ``wordpress_user`` : a wordpress user which have read/write access to the childpool
* ``wordpress_pwd`` : the password of the wordpress user

Credits
=======

Contributors
------------

* Favre Cyril

Maintainer
----------

This module is maintained by `Compassion Switzerland <https://www.compassion.ch>`.
