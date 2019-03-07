.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

==================
GMC Message Center
==================

Message Center that offers a queue of messages that have to be sent
to GMC and a queue of messages received from GMC.

This module adds a route for listening to OnRamp messages call from Compassion
using REST message using authentification with a oauth2 token.

Installation
============

To install this module, you need to install dependencies:

* install python-requests (sudo apt-get install python-requests)
* install jwt (sudo pip install pyjwt)

Configuration
=============

To configure this module, you need to:

* add settings in .conf file of Odoo
* connect_url = <url to entry point of GMC Onramp>
* connect_api_key = <api key for using GMC messages services>
* connect_client = <username for token requests>
* connect_secret = <password for token requests>
* connect_token_server = <base URL of token server>
* connect_token_endpoint = <endpoint for fetching token>
* connect_token_issuer = <issuer name of the token>
* connect_token_cert = <full URL of the public key of the token server>

To allow incoming messages you must setup a user with required access rights
and with login = <username sent by GMC in tokens> and password = <password
sent by GMC in tokens>

In order to manage messages, setup a user with the "GMC Manager" access
rights.

Usage
=====

To use this module, you need to:

* Go to Message Center

Known issues / Roadmap
======================

* Test for R4

Credits
=======

Contributors
------------

* Emanuel Cino <ecino@compassion.ch>
* Cyril Sester <cyril.sester@outlook.com>
* David Coninckx <david@coninckx.com>

Maintainer
----------

This module is maintained by `Compassion Switzerland <https://www.compassion.ch>`.
