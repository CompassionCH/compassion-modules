# -*- coding: utf-8 -*-
#
#    Author: Yannick Vaucher
#    Copyright 2015 Camptocamp SA
#
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
        print request.jsonrequest
        return {
            'code': 200,
            "ConfirmationId": request.uuid,
            "Timestamp": request.timestamp,
            "Message": "Your message was successfully received.",
        }
