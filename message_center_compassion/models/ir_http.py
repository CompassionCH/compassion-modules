# -*- coding: utf-8 -*-
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

from odoo import models
from odoo.http import request
from odoo.tools import config
from werkzeug.exceptions import Unauthorized

_logger = logging.getLogger(__name__)

try:
    import jwt
    import simplejson
    from jwt.algorithms import RSAAlgorithm
except ImportError:
    _logger.error("Please install python jwt and simplejson")


class IrHTTP(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _auth_method_oauth2_legacy(cls):
        # TODO Remove this OAuth method when no more used
        valid_issuers = [
            'https://esther.ci.org',
            'http://services.compassionuk.org/',
            'globalaccess-stage.ci.org',
            'globalaccess-test.ci.org',
            'globalaccess.ci.org',
        ]
        if request.httprequest.method == 'GET':
            mode = 'read'
        if request.httprequest.method == 'POST':
            mode = 'write'

        try:
            token_data = request.httprequest.headers.get('Authorization')
            access_token = token_data.split()[1]
            _logger.info("Received access token: %s", access_token)
        except ValueError:
            # If any error occurs during token and certificate retrieval,
            # we don't allow to go any further
            _logger.error("Error during token validation", exc_info=True)
            raise Unauthorized()

        # Don't verify signature and audience
        options = {
            'verify_signature': False,
            'verify_aud': False
        }
        jwt_decoded = jwt.decode(access_token, options=options)
        # Manual validation of issuer
        if jwt_decoded.get('iss') not in valid_issuers:
            raise Unauthorized()
        # is scope read or write in scopes ?
        scope = jwt_decoded.get('scope')
        if scope and mode not in scope:
            raise Unauthorized()
        client_id = jwt_decoded.get('client_id') or jwt_decoded.get('ClientID')
        _logger.info("TOKEN CLIENT IS -----------------> " + client_id)
        user = request.env['res.users'].sudo().search(
            [('login', '=', client_id)])
        if user:
            request.uid = user.id
        else:
            raise Unauthorized()

    @classmethod
    def _auth_method_oauth2(cls):
        client_id = cls._oauth_validation()
        cls._validate_client_user(client_id)

    @classmethod
    def _oauth_validation(cls):
        issuer = config.get('connect_token_issuer')
        cert_url = config.get('connect_token_cert')
        if request.httprequest.method == 'GET':
            mode = 'read'
        if request.httprequest.method == 'POST':
            mode = 'write'

        # Get public certificate of issuer for token validation
        try:
            token_data = request.httprequest.headers.get('Authorization')
            access_token = token_data.split()[1]
            _logger.info("Received access token: %s", access_token)
            cert = requests.get(cert_url)
            key_json = simplejson.dumps(cert.json()['keys'][0])
        except ValueError:
            # If any error occurs during token and certificate retrieval,
            # we put a wrong certificate, and jwt library will fail
            # to decrypt the token, leading to unauthorized error.
            key_json = {}

        public_key = RSAAlgorithm.from_jwk(key_json)
        jwt_decoded = jwt.decode(
            access_token, key=public_key, algorithms=['RS256'],
            audience=issuer+'/resources', issuer=issuer
        )
        # validation
        # is scope read or write in scopes ?
        scope = jwt_decoded.get('scope')
        if scope and mode not in scope:
            raise Unauthorized()
        client_id = jwt_decoded.get('client_id') or jwt_decoded.get('ClientID')
        _logger.info("TOKEN CLIENT IS -----------------> " + client_id)
        return client_id

    @classmethod
    def _validate_client_user(cls, client_id):
        """
        Validates that the client_id received in the token is a Odoo
        user. This will change the current user in the session.
        :param client_id: token client id
        :return: res.user record
        """
        user = request.env['res.users'].sudo().search(
            [('login', '=', client_id)])
        if user:
            request.uid = user.id
        else:
            raise Unauthorized()
        return user
