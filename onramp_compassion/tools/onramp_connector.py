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
import httplib
import simplejson
import requests
import base64
from datetime import datetime, timedelta

from onramp_logging import ONRAMP_LOGGER

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
        self._connect_url = config.get('connect_url')
        self._api_key = config.get('connect_api_key')
        if not self._connect_url or not self._api_key:
            raise Warning(
                _('Missing configuration'),
                _('Please give connect_url and connect_api_key values '
                  'in your Odoo configuration file.'))
        if not self._token_time or self._token_time+timedelta(hours=1) <= now:
            self._retrieve_token()

    def send_letter_image(self, image_data, image_type):
        """ Sends an image of a Letter to Onramp U.S. Image Upload Service.
        See http://developer.compassion.com/docs/read/compassion_connect2/
            service_catalog/Image_Submission

        Returns the uploaded image URL.
        """
        headers = self._get_authorization_header({
            'Content-type': 'image/{0}'.format(image_type)})
        params = {'api_key': self._api_key, 'doctype': 's2bletter'}
        url = self._connect_url+'images'
        ONRAMP_LOGGER.info(
            "[POST] %s %s %s",
            url,
            [(k, v) for k, v in headers.iteritems()],
            '{image binary data not shown}')
        r = requests.post(
            url, params=params, headers=headers,
            data=image_data)
        letter_url = False
        status = r.status_code
        if status == 201:
            letter_url = r.text
        else:
            raise Warning(
                _("Error while uploading letter image to GMC."),
                r.text)
        return letter_url

    def send_message(self, service_name, message_type, body):
        """ Sends a message to Compassion Connect.
        :param service_name: The service name to reach inside Connect
        :param message_type: GET, POST or PUT
        :param body: Body of the message to send.

        :returns: A dictionary with the content of the answer to the message.
        """
        headers = self._get_authorization_header({
            'Content-type': 'application/json'})
        params = {'api_key': self._api_key}
        url = self._connect_url + service_name
        status = 200
        result = False
        ONRAMP_LOGGER.info(
            "[%s] %s %s %s",
            message_type,
            url,
            [(k, v) for k, v in headers.iteritems()],
            simplejson.dumps(body))
        if message_type == 'GET':
            r = requests.get(
                url, params=params, headers=headers, data=body)
            status = r.status_code
            result = r.text
        elif message_type == 'POST':
            r = requests.post(
                url, params=params, headers=headers,
                data=body)
            status = r.status_code
            try:
                result = r.json()
                result['request_id'] = r.headers.get('x-cim-RequestId')
            except ValueError:
                result = {
                    'error': r.text}
        return status, result

    def _get_authorization_header(self, _headers=None):
        """ Returns the authorization header in dict format. """
        if _headers is None:
            _headers = dict()
        _headers['Authorization'] = '{token_type} {access_token}'.format(
            **self._token)
        return _headers

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
        params_post = 'grant_type=client_credentials&scope=read+write'
        header_post = {"Authorization": "Basic " + api_client_secret,
                       "Content-type": "application/x-www-form-urlencoded",
                       "Content-Length": 46,
                       "Expect": "100-continue",
                       "Connection": "Keep-Alive"}
        conn = httplib.HTTPSConnection('api2.compassion.com')
        conn.request("POST", "/core/connect/token", params_post, header_post)
        response = conn.getresponse()
        self._token = simplejson.loads(response.read())
