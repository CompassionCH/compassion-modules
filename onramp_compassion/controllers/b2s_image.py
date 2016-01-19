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

from openerp import fields, http
from openerp.http import request

from werkzeug.wrappers import Response

_logger = logging.getLogger(__name__)


class RestController(http.Controller):

    @http.route('/b2s_image', type='http', auth='public', methods=['GET'])
    def handler_b2s_image(self, id):
        """ Handler for `/b2s_image` url for json data.

        It accepts only Communication Kit Notifications.

        """
        headers = request.httprequest.headers
        self._validate_headers(headers)
        correspondence_obj = request.env['sponsorship.correspondence'].sudo()
        correspondence = correspondence_obj.search([('uuid', '=', id)])
        correspondence.last_read = fields.Datetime.now()
        correspondence.read_count += 1
        data = base64.b64decode(correspondence.letter_image.datas)
        response = Response(data, mimetype='application/pdf')
        _logger.info("A sponsor requested a child letter image !")
        return response

    def _validate_headers(self, headers):
        pass
