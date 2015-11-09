# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import logging
import requests
import base64
from datetime import datetime, timedelta

from openerp import _
from openerp.exceptions import Warning
from openerp.tools.config import config

logger = logging.getLogger(__name__)


class OnrampConnector(object):
    """ Singleton class to connect to U.S. Onramp in order to send
    messages. """

    # Private instance of the class
    __instance = None

    # Holds the last time a token was retrieved from GMC.
    _token_time = None

    # Holds the token used to authenticate with GMC.
    _token = None

    def __new__(cls):
        """ Inherit method to ensure a single instance exists. """
        if OnrampConnector.__instance is None:
            OnrampConnector.__instance = object.__new__(cls)
        return OnrampConnector.__instance

    def __init__(self):
        """ Get a fresh token if needed. """
        now = datetime.now()
        if not self._token_time or self._token_time+timedelta(hours=1) <= now:
            self._retrieve_token()

    def send_message(self, service_name, message_type, body):
        """ Sends a message to Compassion Connect.
        :param service_name: The service name to reach inside Connect
        :param message_type: GET, POST or PUT
        :param body: Body of the message to send.

        :returns: A dictionary with the content of the answer to the message.
        """
        connect_url = config.get('connect_url')
        api_key = config.get('connect_api_key')
        if not connect_url or not api_key:
            raise Warning(
                _('Missing configuration'),
                _('Please give connect_url and connect_api_key values '
                  'in your Odoo configuration file.'))

        headers = {
            'Content-type': 'application/json',
            'Authorization': '{token_type} {access_token}'.format(
                **self._token),
        }
        params = {'api_key': api_key}
        status = 200
        result = False
        if message_type == 'GET':
            r = requests.get(
                connect_url, params=params, headers=headers, data=body)
            status = r.status_code
            result = r.text
        elif message_type == 'POST':
            r = requests.post(
                connect_url, params=params, headers=headers,
                data=body)
            status = r.status_code
            result = r.json()
            result['request_id'] = r.headers.get('x-cim-RequestId')
        return status, result

    def _retrieve_token(self):
        """ Retrieves the token from Connect. """
        client = config.get('connect_client')
        secret = config.get('connect_secret')
        if not client or not secret:
            raise Warning(
                _('Missing configuration'),
                _('Please give connect_client and connect_secret values '
                  'in your Odoo configuration file.'))
        api_client_secret = base64.b64encode("{0}:{1}".format(client, secret))
        params_post = {
            'grant_type': 'client_credentials',
            'scope': 'read+write'}
        header_post = {"Authorization": "Basic " + api_client_secret,
                       "Content-type": "application/x-www-form-urlencoded",
                       "Content-Length": 46,
                       "Expect": "100-continue",
                       "Connection": "Keep-Alive"}
        self._token = requests.post(
            'https://api2.compassion.com/core/connect/token',
            params=params_post, headers=header_post).json()
