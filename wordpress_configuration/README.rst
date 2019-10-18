.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Multi-company support for Wordpress configurations
==================================================

The module allows to create different wordpress configurations for each company.

Installation
============

Configuration
=============

In "Settings", the "wordpress configuration" menu item has been added to the technical menu.
One record should be created for each company.

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
