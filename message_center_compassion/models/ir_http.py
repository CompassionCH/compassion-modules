##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Yannick Vaucher, Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

import requests
from werkzeug.exceptions import Unauthorized

from odoo import models
from odoo.http import request
from odoo.tools import config

_logger = logging.getLogger(__name__)

try:
    from jwt import JWT, jwk
except ImportError:
    _logger.error("Please install python jwt")


class IrHTTP(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _auth_method_oauth2(cls):
        client_id = cls._oauth_validation()
        cls._validate_client_user(client_id)

    @classmethod
    def _oauth_validation(cls):
        cert_url = config.get("connect_token_cert")
        if request.httprequest.method == "GET":
            mode = "read"
        if request.httprequest.method == "POST":
            mode = "write"

        # Get public certificate of issuer for token validation
        try:
            token_data = request.httprequest.headers.get("Authorization")
            access_token = token_data.split()[1]
            _logger.debug("Received access token: %s", access_token)
            cert = requests.get(cert_url)
            key_json = cert.json()["keys"][0]
        except (ValueError, AttributeError):
            # If any error occurs during token and certificate retrieval,
            # we put a wrong certificate, and jwt library will fail
            # to decrypt the token, leading to unauthorized error.
            key_json = {}

        public_key = jwk.RSAJWK.from_dict(key_json)
        jwt_decoded = JWT().decode(
            access_token, key=public_key, algorithms=["RS256"], do_verify=True
        )
        # validation
        # is scope read or write in scopes ?
        scope = jwt_decoded.get("scope")
        if scope and mode not in scope:
            raise Unauthorized()
        client_id = jwt_decoded.get("client_id") or jwt_decoded.get("ClientID")
        _logger.debug("TOKEN CLIENT IS -----------------> " + client_id)
        return client_id

    @classmethod
    def _validate_client_user(cls, client_id):
        """
        Validates that the client_id received in the token is a Odoo
        user. This will change the current user in the session.
        :param client_id: token client id
        :return: res.user record
        """
        user = request.env["res.users"].sudo().search([("login", "=", client_id)])
        if user:
            request.uid = user.id
        else:
            raise Unauthorized()
        return user
