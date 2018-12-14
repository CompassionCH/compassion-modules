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

from odoo.http import request
from odoo import models, _
from odoo.exceptions import UserError
from werkzeug.exceptions import Unauthorized

try:
    import jwt
except ImportError:
    raise UserError(_("Please install python jwt"))

logger = logging.getLogger(__name__)

VALID_ISSUERS = [
    'https://esther.ci.org',
    'http://services.compassionuk.org/',
    'globalaccess-stage.ci.org',
    'globalaccess-test.ci.org',
]


class IrHTTP(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _auth_method_oauth2(self):
        if request.httprequest.method == 'GET':
            mode = 'read'
        if request.httprequest.method == 'POST':
            mode = 'write'
        token_data = request.httprequest.headers.get('Authorization')
        if not token_data:
            raise Unauthorized()
        token_authorization = token_data.split()[0]
        if token_authorization != 'Bearer':
            raise Unauthorized()
        access_token = token_data.split()[1]

        # Token validation
        options = {
            # not sure why, you might need to do that if token is not encrypted
            'verify_signature': False,
            'verify_aud': False
        }
        jwt_decoded = jwt.decode(access_token, options=options)
        # validation
        # is the iss = to Compassions IDP ?
        if jwt_decoded.get('iss') not in VALID_ISSUERS:
            raise Unauthorized()
        # is scope read or write in scopes ?
        scope = jwt_decoded.get('scope')
        if scope and mode not in scope:
            raise Unauthorized()
        client_id = jwt_decoded.get('client_id') or jwt_decoded.get('ClientID')
        logger.info("TOKEN CLIENT IS -----------------> " + client_id)
        user = request.env['res.users'].sudo().search(
            [('login', '=', client_id)])
        if user:
            request.uid = user.id
        else:
            raise Unauthorized()
