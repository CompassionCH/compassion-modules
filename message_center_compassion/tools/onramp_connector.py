##############################################################################
#
#    Copyright (C) 2015-2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import json
import logging
import urllib
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

    # For accessing odoo system parameters
    _res_config = None

    def __new__(cls, env):
        """ Inherit method to ensure a single instance exists. """
        if OnrampConnector.__instance is None:
            OnrampConnector.__instance = object.__new__(cls)
            res_config = env["res.config.settings"]
            connect_url = config.get("connect_url")
            api_key = res_config.get_param("connect_api_key")
            if connect_url and api_key:
                cls._connect_url = connect_url
                cls._res_config = res_config
                session = requests.Session()
                session.params.update({"api_key": api_key, "gpid": res_config.get_param('connect_gpid')})
                cls._session = session
            else:
                raise UserError(
                    _(
                        "Please give connect_url and connect_api_key values "
                        "in your Odoo configuration file."
                    )
                )
        return OnrampConnector.__instance

    def __init__(self, env):
        """ Get a fresh token if needed. """
        now = datetime.now()
        if not self._token_time or self._token_time + timedelta(hours=1) <= now:
            self._retrieve_token(env)

    def send_message(self, service_name, message_type, body=None, params=None, headers=None, full_url=False):
        """ Sends a message to Compassion Connect.
        :param service_name: The service name to reach inside Connect
        :param message_type: GET, POST, PUT or GET_RAW.
                             GET_RAW is a special type used to fetch files and binary data that should be returned
                             as it is.
        :param body: Body of the message to send.
        :param params: Optional Dictionary of HTTP Request parameters
                                (put inside the url)
        :param headers: Optional headers for the request
        :param full_url: Optional boolean to indicate the service_name is a full url that should be called as it is.

        :returns: A dictionary with the content of the answer to the message.
                  {'code': http_status_code, 'content': response,
                   'Error': error_message, 'request_id': request id header}
        """
        if headers is None:
            headers = {"Content-type": "application/json"}
        url = self._connect_url + service_name if not full_url else service_name
        log_body = body if body and len(body) < 500 else body and (body[:500] + "...[truncated]")
        self.log_message(message_type, url, headers, log_body, self._session, params)
        if message_type in ("GET", "GET_RAW"):
            r = self._session.get(url, headers=headers, params=params)
        elif message_type == "POST":
            r = self._session.post(url, headers=headers, json=body, params=params)
        elif message_type == "PUT":
            r = self._session.put(url, headers=headers, json=body, params=params)
        else:
            return {"code": 404, "Error": "No valid HTTP verb used"}
        if message_type == "GET_RAW":
            # Simply return the result
            return r.content
        status = r.status_code
        result = {
            "code": status,
            "request_id": r.headers.get("cf-request-id"),
            "raw_content": r.content
        }
        log_body = r.text if r.text and len(r.text) < 500 else r.text and (r.text[:500] + "...[truncated]")
        self.log_message(status, "RESULT", message=log_body)
        try:
            # Receiving some weird encoded strings
            result["content"] = json.JSONDecoder(strict=False).decode(
                r.text.replace("\\\\n", "\n")
            )
        except ValueError:
            # No json content returned
            result["content"] = r.text
        return result

    def _retrieve_token(self, env):
        """ Retrieves the token from Connect. """
        self._token_time = datetime.now()
        self._session.headers.update(self.get_gmc_token(env))

    @classmethod
    def get_gmc_token(cls, env):
        """
        Class method that fetches a token from GMC OAuth server.
        :return: dict: Authorisation header.
        """
        client = env["res.config.settings"].get_param("connect_client")
        secret = env["res.config.settings"].get_param("connect_secret")
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
    def log_message(cls, req_type, url, headers=None, message=None, session=None, params=None):
        """
        Used to format GMC messages for console log
        :param req_type: type of request (post/get/etc...)
        :param url: url of request
        :param headers: headers of request
        :param message: content of request
        :param session: session of request
        :param params: params of request
        :return: None
        """
        if headers is None:
            headers = dict()
        if message is None:
            message = "{empty}"
        if params is None:
            params = dict()
        if session is not None:
            complete_headers = headers.copy()
            complete_headers.update(session.headers)
            if session.params:
                params.update(session.params)
        else:
            complete_headers = headers
        if params:
            url += "?" + urllib.parse.urlencode(params)
        _logger.debug(
            "[%s] %s %s %s",
            req_type,
            url,
            [(k, v) for k, v in complete_headers.items()],
            json.dumps(message),
        )
