.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

SendGrid
========

This module integrates the basic functionality of
`SendGrid <https://sendgrid.com/>`_ with Odoo. It can send transactional emails
through SendGrid, using templates defined on the
`SendGrid web interface <https://sendgrid.com/templates>`_. It also supports
substitution of placeholder variables in these templates. The list of available
templates can be fetched automatically.

Usage
=====

In order to use this module, the following variables have to be defined in the
server configuration file:

- ``sendgrid_api_key`` A valid API key obtained from the
  `SendGrid web interface <https://app.sendgrid.com/settings/api_keys>`_ with
  full access for the ``Mail Send`` permission and read access for the
  ``Template Engine`` permission.
- ``sendgrid_from_address`` The sender address that will be shown for emails
  sent through SendGrid.

Optionally, the following configuration variables can be set as well:

- ``sendgrid_production_mode`` If set to ``1`` (or any other value), the module
  will run in production mode and send emails to their true destination
  address. Otherwise, all emails will be sent to ``sendgrid_test_address``.
- ``sendgrid_test_address`` Destination email address for testing purposes. By
  default, this is set to ``odoo@sink.sendgrid.net``, which is an address that
  will simply receive and discard all incoming email.

Credits
=======

Maintainer
----------

This module is maintained by
`Compassion Switzerland <https://www.compassion.ch>`_.
