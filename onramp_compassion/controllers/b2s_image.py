# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import logging
import base64

from openerp import http
from openerp.http import request

from werkzeug.wrappers import Response

_logger = logging.getLogger(__name__)


class RestController(http.Controller):

    @http.route('/b2s_image', type='http', auth='public', methods=['GET'])
    def handler_b2s_image(self):
        """ Handler for `/b2s_image` url for json data.

        It accepts only Communication Kit Notifications.

        """
        headers = request.httprequest.headers
        self._validate_headers(headers)
        correspondence_obj = request.env['sponsorship.correspondence'].sudo()
        test = correspondence_obj.browse(10)
        response = Response(base64.b64decode(test.letter_image.datas),
                            mimetype='application/pdf')
        _logger.info("A sponsor requested a child letter image !")
        return response

    def _validate_headers(self, headers):
        pass
