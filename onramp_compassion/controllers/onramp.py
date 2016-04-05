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
AUTHORIZED_SENDERS = ['CHTest', 'CISalesforce', 'CISFDC']

# Only those message types will be accepted (checked in the header)
MESSAGE_TYPES = {
    'CommKitNotification':
        'http://schemas.ci.org/ci/messaging/communications/2015/08/'
        'CommunicationUpdates',
    'FinalCommKit':
        'http://schemas.ci.org/ci/messaging/communications/2015/09/'
        'SBCStructured',
    'ReservationNotification':
        'http://schemas.ci.org/ci/messaging/communications/2015/08/'
        'Notification'}


class RestController(http.Controller):

    @http.route('/onramp', type='json', auth='oauth2', methods=['POST'])
    def handler_onramp(self, token=None):
        """ Handler for `/onramp` url for json data.

        It accepts only Communication Kit Notifications.

        """
        headers = request.httprequest.headers
        self._validate_headers(headers)
        message_type = request.httprequest.headers['x-cim-MessageType']

        # CommKit (contains either a list of commkits or a single commkit)
        if message_type in (MESSAGE_TYPES['CommKitNotification'],
                            MESSAGE_TYPES['FinalCommKit']):
            json_data = request.jsonrequest
            updates = json_data.get('Responses', [json_data])
            for commkit_data in updates:
                if 'CompassionSBCId' not in commkit_data:
                    raise AttributeError(
                        "Body does not contain a valid CommKit Data")
            correspondence_obj = request.env[
                'correspondence'].sudo(request.uid)
            correspondence_obj.process_commkit_notifications(updates, headers)

        # TODO [Release 4]: Reservation Notification Messages
        elif message_type == MESSAGE_TYPES['ReservationNotification']:
            return {
                'code': 501,
                "ConfirmationId": request.uuid,
                "Timestamp": request.timestamp,
                "Message":
                    "Your message was successfully received "
                    "but we are not processing reservations yet."
            }
        return {
            'code': 200,
            "ConfirmationId": request.uuid,
            "Timestamp": request.timestamp,
            "Message": "Your message was successfully received.",
        }

    def _validate_headers(self, headers):
        if headers.get('x-cim-MessageType') not in MESSAGE_TYPES.values():
            raise AttributeError("Unknown MessageType")
        if headers.get('x-cim-FromAddress') not in AUTHORIZED_SENDERS:
            raise exceptions.AccessDenied()
        if headers.get('x-cim-ToAddress') != 'CH':
            raise AttributeError("This message is not for me.")
