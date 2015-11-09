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
import logging

from openerp import http, exceptions
from openerp.http import request

_logger = logging.getLogger(__name__)

# Put any authorized sender here. Its address must be part of the headers
# in order to handle a request.
AUTHORIZED_SENDERS = ['CHTest', 'CISalesforce']

# Only those message types will be accepted (checked in the header)
MESSAGE_TYPES = {
    'CommKitNotification':
        'http://schemas.ci.org/ci/services/communications/2015/09/'
        'SBCStructured'}


class RestController(http.Controller):

    @http.route('/onramp', type='json', auth='oauth2', methods=['POST'])
    def handler_onramp(self, token=None):
        """ Handler for `/onramp` url for json data.

        It accepts only Communication Kit Notifications.

        """
        headers = request.httprequest.headers
        self._validate_headers(headers)
        if request.httprequest.headers['x-cim-MessageType'] == MESSAGE_TYPES[
                'CommKitNotification']:
            updates = request.jsonrequest.get('CommunicationUpdates')
            if updates and isinstance(updates, list):
                correspondence_obj = request.env[
                    'sponsorship.correspondence'].sudo(request.uid)
                correspondence_obj.process_commkit_notifications(
                    updates, headers)
            else:
                raise AttributeError()
        return {
            'code': 200,
            "ConfirmationId": request.uuid,
            "Timestamp": request.timestamp,
            "Message": "Your message was successfully received.",
        }

    def _validate_headers(self, headers):
        if headers.get('x-cim-MessageType') not in MESSAGE_TYPES.values():
            raise AttributeError()
        if headers.get('x-cim-FromAddress') not in AUTHORIZED_SENDERS:
            raise exceptions.AccessDenied()
        if headers.get('x-cim-ToAddress') != 'CH':
            raise AttributeError()
