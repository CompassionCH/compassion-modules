# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
import requests
import base64
from datetime import datetime, timedelta

from odoo import _
from odoo.exceptions import UserError
from odoo.tools.config import config

_logger = logging.getLogger(__name__)

try:
    import httplib
    import simplejson
except ImportError:
    _logger.warning("Please install httplib and simplejson")


class OnrampConnector(object):
    """ Singleton class to connect to U.S. Onramp in order to send
    messages. """

    # Private instance of the class
    __instance = None

    # Holds the last time a token was retrieved from GMC.
    _token_time = None

    # Holds the token used to authenticate with GMC.
    _token = None

    # Requests Session that will be used accross calls to server
    _session = None

    # Requests headers for sending messages
    _headers = None

    def __new__(cls):
        """ Inherit method to ensure a single instance exists. """
        if OnrampConnector.__instance is None:
            OnrampConnector.__instance = object.__new__(cls)
            connect_url = config.get('connect_url')
            api_key = config.get('connect_api_key')
            if connect_url and api_key:
                OnrampConnector.__instance._connect_url = connect_url
                OnrampConnector.__instance._api_key = api_key
                session = requests.Session()
                session.params.update({
                    'api_key': api_key,
                    'gpid': 'CH'
                })
                OnrampConnector.__instance._session = session
            else:
                raise UserError(
                    _('Please give connect_url and connect_api_key values '
                      'in your Odoo configuration file.'))
        return OnrampConnector.__instance

    def __init__(self):
        """ Get a fresh token if needed. """
        now = datetime.now()
        if not self._token_time or self._token_time + \
                timedelta(hours=1) <= now:
            self._retrieve_token()

    def send_message(self, service_name, message_type, body=None,
                     params=None):
        """ Sends a message to Compassion Connect.
        :param service_name: The service name to reach inside Connect
        :param message_type: GET, POST or PUT
        :param body: Body of the message to send.
        :param params: Optional Dictionary of HTTP Request parameters
                                (put inside the url)

        :returns: A dictionary with the content of the answer to the message.
                  {'code': http_status_code, 'content': response,
                   'Error': error_message, 'request_id': request id header}
        """
        headers = {'Content-type': 'application/json'}
        url = self._connect_url + service_name
        self.log_message(message_type, url, headers, body, self._session)
        if params is None:
            params = dict()
        param_string = self._encode_params(params)
        if message_type == 'GET':
            r = self._session.get(
                url, headers=headers, params=param_string)
        elif message_type == 'POST':
            r = self._session.post(
                url, headers=headers, json=body, params=param_string)
        elif message_type == 'PUT':
            r = self._session.put(
                url, headers=headers, json=body, params=param_string)
        else:
            return {
                'code': 404,
                'Error': 'No valid HTTP verb used'
            }
        status = r.status_code
        result = {
            'code': status,
            'request_id': r.headers.get('x-cim-RequestId'),
        }
        self.log_message(status, 'RESULT', message=r.text)
        try:
            # Receiving some weird encoded strings
            result['content'] = simplejson.JSONDecoder(strict=False).decode(
                r.text.replace('\\\\n', '\n'))
        except ValueError:
            # No json content returned
            result['content'] = r.text
        return result

    def _encode_params(self, params):
        """
        Takes a dictionary and encode it for URL parameters
        :param params: dictionary
        :return: string
        """
        formatted_params = self._session.params.copy()
        for key, value in params.iteritems():
            if isinstance(value, list):
                value = ','.join([str(v) for v in value])
            formatted_params[key] = value

        string_returned = u'&'.join(u'%s=%s' % (k, v) for k, v in
                                    formatted_params.iteritems())
        return string_returned.encode('utf-8')

    def _retrieve_token(self):
        """ Retrieves the token from Connect. """
        client = config.get('connect_client')
        secret = config.get('connect_secret')
        environment = config.get('connect_env', 'core')
        if not client or not secret:
            raise UserError(
                _('Please give connect_client and connect_secret values '
                  'in your Odoo configuration file.'))
        api_client_secret = base64.b64encode("{0}:{1}".format(client, secret))
        params_post = 'grant_type=client_credentials&scope=read+write'
        header_post = {
            "Authorization": "Basic " + api_client_secret,
            "Content-type": "application/x-www-form-urlencoded",
            "Content-Length": 46,
            "Expect": "100-continue",
            "Connection": "Keep-Alive"}
        conn = httplib.HTTPSConnection('api2.compassion.com')
        auth_path = "/{}/connect/token".format(environment)
        conn.request("POST", auth_path, params_post, header_post)
        response = conn.getresponse()
        try:
            self._token = simplejson.loads(response.read())
            self._token_time = datetime.now()
            self._session.headers.update({
                'Authorization': '{token_type} {access_token}'.format(
                    **self._token)})
        except (AttributeError, KeyError):
            raise UserError(
                _('Token validation failed.'))

    @classmethod
    def log_message(cls, type, url, headers=None, message=None, session=None):
        """
        Used to format GMC messages for console log
        :param type: type of request (post/get/etc...)
        :param url: url of request
        :param headers: headers of request
        :param message: content of request
        :param session: session of request
        :return: None
        """
        if headers is None:
            headers = dict()
        if message is None:
            message = '{empty}'
        if session is not None:
            complete_headers = headers.copy()
            complete_headers.update(session.headers)
        else:
            complete_headers = headers
        _logger.info(
            "[%s] %s %s %s",
            type,
            url,
            [(k, v) for k, v in complete_headers.iteritems()],
            simplejson.dumps(message))
