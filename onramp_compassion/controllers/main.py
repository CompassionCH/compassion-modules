# -*- coding: utf-8 -*-
#
#    Author: Yannick Vaucher
#    Copyright 2015 Camptocamp SA
#
from datetime import datetime
import logging

from openerp import http
from openerp.http import request

_logger = logging.getLogger(__name__)
_onramp_logger = logging.getLogger('ONRAMP')


class RestController(http.Controller):

    @http.route('/onramp', type='json', auth='oauth2', methods=['POST'])
    def handler_onramp(self, token=None):
        """ Handler for `/onramp` url for json data.

        It accepts only Communication Kit Notifications.

        """
        now = datetime.strftime(datetime.now(), '%Y-%m-%dT%H:%M:%S')
        if request.httprequest.method == 'POST':
            # TODO check if headers are correct and message type is ok,
            #      then process update commkit in a private method.
            print request.jsonrequest
            return {
                "ConfirmationId": "e0f05e27-97af-47d0-b162-5e935052aab7",
                "Timestamp": now,
                "Message": "Your message was successfully received."
            }
        else:
            return {
                "ErrorId": "156b633d-2fe7-48ca-94e8-fbe0b8cd560a",
                "ErrorTimestamp": now,
                "ErrorClass": "BusinessException",
                "ErrorCategory": "InputValidationError",
                "ErrorCode": "ESB4000",
                "ErrorMessage": "Request Invalid: Request contains invalid "
                "json.",
                "ErrorRetryable": False,
                "ErrorModule": "REST OnRamp",
                "ErrorSubModule": "Rest OnRamp Request Checking",
                "ErrorMethod": "RequestIsValidJson",
                "ErrorLoggedInUser": "",
                "RelatedRecordId": ""
            }
