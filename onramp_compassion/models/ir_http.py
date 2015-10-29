# -*- coding: utf-8 -*-
#
#    Author: Yannick Vaucher
#    Copyright 2015 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
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
        if not request.env['res.users'].sudo().search(
                [('login', '=', client_id)]):
            raise Unauthorized()
