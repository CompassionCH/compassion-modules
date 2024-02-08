To configure this module, you need to:

- add settings in .conf file of Odoo
- connect_url = \<url to entry point of GMC Onramp\>
- connect_api_key = \<api key for using GMC messages services\>
- connect_client = \<username for token requests\>
- connect_secret = \<password for token requests\>
- connect_token_server = \<base URL of token server\>
- connect_token_cert = \<comma-separated list of full URLs of the public
  keys of the token server\>

To allow incoming messages you must setup a user with required access
rights and with login = \<username sent by GMC in tokens\> and password
= \<password sent by GMC in tokens\>

In order to manage messages, setup a user with the "GMC Manager" access
rights.
