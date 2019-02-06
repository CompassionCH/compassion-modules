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

from odoo.http import request
from odoo import models
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
    def _auth_method_oauth2(self):
        self._oauth_validation(
            'globalaccess.ci.org',
            'https://globalaccessidp.ci.org/core/.well-known/jwks'
        )

    @classmethod
    def _auth_method_oauth2_stage(self):
        self._oauth_validation(
            'globalaccess-stage.ci.org',
            'https://globalaccessidp-stage.ci.org/core/.well-known/jwks'
        )

    @classmethod
    def _oauth_validation(self, issuer, cert_url):
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
            # we don't allow to go any further
            _logger.error("Error during token validation", exc_info=True)
            raise Unauthorized()

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
        user = request.env['res.users'].sudo().search(
            [('login', '=', client_id)])
        if user:
            request.uid = user.id
        else:
            raise Unauthorized()
