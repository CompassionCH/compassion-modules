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
import simplejson as json
import logging

from openerp import http, exceptions
from openerp.http import request

_logger = logging.getLogger(__name__)

# Put any authorized sender here. Its address must be part of the headers
# in order to handle a request.
AUTHORIZED_SENDERS = ['CHTest', 'CISalesforce', 'CISFDC']


class RestController(http.Controller):

    @http.route('/onramp', type='json', auth='oauth2', methods=['POST'])
    def handler_onramp(self, token=None):
        """ Handler for `/onramp` url for json data.
        """
        headers = request.httprequest.headers
        self._validate_headers(headers)
        message_type = request.httprequest.headers['x-cim-MessageType']
        result = {
            "ConfirmationId": request.uuid,
            "Timestamp": request.timestamp,
        }
        action_connect = request.env['gmc.action.connect'].sudo(
            request.uid).search([('connect_schema', '=', message_type)])
        if action_connect:
            action = action_connect.action_id
            request.env['gmc.message.pool'].sudo(request.uid).create({
                'request_id': request.uuid,
                'action_id': action.id,
                'headers': json.dumps(dict(headers.items())),
                'content': json.dumps(request.jsonrequest)
            })
            result.update({
                "code": 200,
                "Message": "Your message was successfully received."
            })
        else:
            result.update({
                "code": 501,
                "Message": "Unknown message type"
            })
        return result

    def _validate_headers(self, headers):
        if headers.get('x-cim-FromAddress') not in AUTHORIZED_SENDERS:
            raise exceptions.AccessDenied()
        company_obj = request.env['res.company'].sudo(request.uid)
        companies = company_obj.search([])
        country_codes = companies.mapped('partner_id.country_id.code')
        if headers.get('x-cim-ToAddress') not in country_codes:
            raise AttributeError("This message is not for me.")
