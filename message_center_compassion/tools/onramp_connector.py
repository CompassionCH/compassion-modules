##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import json
import logging
from datetime import datetime, timedelta
from json.decoder import JSONDecodeError

import requests

from odoo import _
from odoo.exceptions import UserError
from odoo.tools.config import config

_logger = logging.getLogger(__name__)


class OnrampConnector(object):
    """ Singleton class to connect to U.S. Onramp in order to send
    messages. """

    # Private instance of the class
    __instance = None

    # Holds the last time a token was retrieved from GMC.
    _token_time = None

    # Requests Session that will be used across calls to server
    _session = None

    # Requests headers for sending messages
    _headers = None

    def __new__(cls):
        """ Inherit method to ensure a single instance exists. """
        if OnrampConnector.__instance is None:
            OnrampConnector.__instance = object.__new__(cls)
            connect_url = config.get("connect_url")
            api_key = config.get("connect_api_key")
            if connect_url and api_key:
                OnrampConnector.__instance._connect_url = connect_url
                OnrampConnector.__instance._api_key = api_key
                session = requests.Session()
                session.params.update({"api_key": api_key, "gpid": config.get('connect_gpid')})
                OnrampConnector.__instance._session = session
            else:
                raise UserError(
                    _(
                        "Please give connect_url and connect_api_key values "
                        "in your Odoo configuration file."
                    )
                )
        return OnrampConnector.__instance

    def __init__(self):
        """ Get a fresh token if needed. """
        now = datetime.now()
        if not self._token_time or self._token_time + timedelta(hours=1) <= now:
            self._retrieve_token()

    def send_message(self, service_name, message_type, body=None, params=None):
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
        headers = {"Content-type": "application/json"}
        url = self._connect_url + service_name
        self.log_message(message_type, url, headers, body, self._session)
        if message_type == "GET":
            r = self._session.get(url, headers=headers, params=params)
        elif message_type == "POST":
            r = self._session.post(url, headers=headers, json=body, params=params)
        elif message_type == "PUT":
            r = self._session.put(url, headers=headers, json=body, params=params)
        else:
            return {"code": 404, "Error": "No valid HTTP verb used"}
        status = r.status_code
        result = {
            "code": status,
            "request_id": r.headers.get("cf-request-id"),
        }
        self.log_message(status, "RESULT", message=r.text)
        try:
            # Receiving some weird encoded strings
            result["content"] = json.JSONDecoder(strict=False).decode(
                r.text.replace("\\\\n", "\n")
            )
        except ValueError:
            # No json content returned
            result["content"] = r.text
        return result

    def _retrieve_token(self):
        """ Retrieves the token from Connect. """
        self._token_time = datetime.now()
        self._session.headers.update(self.get_gmc_token())

    @classmethod
    def get_gmc_token(cls):
        """
        Class method that fetches a token from GMC OAuth server.
        :return: dict: Authorisation header.
        """
        client = config.get("connect_client")
        secret = config.get("connect_secret")
        provider = config.get("connect_token_server")
        if not client or not secret or not provider:
            raise UserError(
                _(
                    "Please give connect_client, connect_secret, "
                    "connect_token_server in your Odoo configuration file."
                )
            )
        params_post = "grant_type=client_credentials&scope=connect/read-write"
        header_post = {
            "Content-type": "application/x-www-form-urlencoded",
        }
        response = requests.post(
            provider, data=params_post, auth=(client, secret), headers=header_post
        )
        try:
            token = response.json()
            return {"Authorization": "{token_type} {access_token}".format(**token)}
        except (AttributeError, KeyError, JSONDecodeError):
            _logger.error("GMC token retrieval error: %s",
                          response.text, exc_info=True)
            raise UserError(_("Token validation failed."))

    @classmethod
    def log_message(cls, req_type, url, headers=None, message=None, session=None):
        """
        Used to format GMC messages for console log
        :param req_type: type of request (post/get/etc...)
        :param url: url of request
        :param headers: headers of request
        :param message: content of request
        :param session: session of request
        :return: None
        """
        if headers is None:
            headers = dict()
        if message is None:
            message = "{empty}"
        if session is not None:
            complete_headers = headers.copy()
            complete_headers.update(session.headers)
        else:
            complete_headers = headers
        _logger.debug(
            "[%s] %s %s %s",
            req_type,
            url,
            [(k, v) for k, v in complete_headers.items()],
            json.dumps(message),
        )
