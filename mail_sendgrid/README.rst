.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

========
SendGrid
========

This module integrates the basic functionality of
`SendGrid <https://sendgrid.com/>`_ with Odoo. It can send transactional emails
through SendGrid, using templates defined on the
`SendGrid web interface <https://sendgrid.com/templates>`_. It also supports
substitution of placeholder variables in these templates. The list of available
templates can be fetched automatically.

Configuration
=============

You can add the following system parameters to configure the usage of SendGrid:

* ``mail_sendgrid.substitution_prefix`` Any symbol or character used as a 
  prefix for `SendGrid Substitution Tags <https://sendgrid.com/docs/API_Reference/SMTP_API/substitution_tags.html>`_.
  ``{`` is used by default.
* ``mail_sendgrid.substitution_suffix`` Any symbol or character used as a 
  suffix for `SendGrid Substitution Tags <https://sendgrid.com/docs/API_Reference/SMTP_API/substitution_tags.html>`_.
  ``}`` is used by default.
* ``mail_sendgrid.send_method`` Use value 'sendgrid' to override the traditional STMP server used to send e-mails with sendgrid.
  Use any other value to disable traditional e-mail sending. By default, SendGrid will co-exist with traditional system
  (two buttons for sending either normally or with SendGrid).

Usage
=====

In order to use this module, the following variables have to be defined in the
server command-line options (or in a configuration file):

- ``sendgrid_api_key`` A valid API key obtained from the
  `SendGrid web interface <https://app.sendgrid.com/settings/api_keys>`_ with
  full access for the ``Mail Send`` permission and read access for the
  ``Template Engine`` permission.

Optionally, the following configuration variables can be set as well:

- ``sendgrid_test_address`` Destination email address for testing purposes.
  You can use ``odoo@sink.sendgrid.net``, which is an address that
  will simply receive and discard all incoming email.

Known issues / Roadmap
======================

* Use SendGrid with massmailing
* Extends the features from SendGrid

Credits
=======

Maintainer
----------

This module is maintained by
`Compassion Switzerland <https://www.compassion.ch>`_.
