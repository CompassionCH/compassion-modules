# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Yannick Vaucher, Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import jwt

from openerp.http import request
from openerp import models
from werkzeug.exceptions import Unauthorized


class IrHTTP(models.AbstractModel):
    _inherit = 'ir.http'

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
        if jwt_decoded.get('iss') != 'https://idsrv3.com':
            raise Unauthorized()
        # is scope read or write in scopes ?
        if mode not in jwt_decoded.get('scope'):
            raise Unauthorized()
        client_id = jwt_decoded.get('client_id')
        user = request.env['res.users'].sudo().search(
            [('login', '=', client_id)])
        if user:
            request.uid = user.id
        else:
            raise Unauthorized()
