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
    from jwt.exceptions import JWTDecodeError
except ImportError as e:
    _logger.error("Please install python jwt")
    raise e


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
        elif request.httprequest.method == "POST":
            mode = "write"
        else:
            mode = None

        # We iterate over the various certificates provider
        found_right_certificate = False
        jwt_decoded = None
        for one_cert_url in cert_url.split(','):
            one_cert_url = one_cert_url.strip()
            access_token = None

            # Get public certificate of issuer for token validation
            try:
                token_data = request.httprequest.headers.get("Authorization")
                access_token = token_data.split()[1]
                cert = requests.get(one_cert_url)
                keys_json = cert.json()["keys"]
            except (ValueError, AttributeError):
                # If any error occurs during token and certificate retrieval,
                # we put a wrong certificate, and jwt library will fail
                # to decrypt the token, leading to unauthorized error.
                keys_json = []

            for key_json in keys_json:
                try:
                    public_key = jwk.RSAJWK.from_dict(key_json)
                    jwt_decoded = JWT().decode(
                        access_token, key=public_key, algorithms={"RS256"}, do_verify=True
                    )
                except JWTDecodeError:
                    continue

                # If we did not encounter an error before, it means the certificate allowed to correctly decode the
                # access token so we hopefully found a matching certificate
                if jwt_decoded:
                    found_right_certificate = True
                    break

            if found_right_certificate:
                break

        if not found_right_certificate:
            raise Unauthorized()

        # validation
        # is scope read or write in scopes ?
        scope = jwt_decoded.get("scope")
        if scope and mode not in scope:
            raise Unauthorized()
        client_id = jwt_decoded.get("client_id") or jwt_decoded.get("ClientID")
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
