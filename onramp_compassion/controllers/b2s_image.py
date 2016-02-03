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

from openerp import fields, http, _
from openerp.http import request

from werkzeug.exceptions import BadRequest, NotFound
from werkzeug.wrappers import Response

_logger = logging.getLogger(__name__)


class RestController(http.Controller):

    @http.route('/b2s_image', type='http', auth='public', methods=['GET'])
    def handler_b2s_image(self, id=None, user=None):
        """ Handler for `/b2s_image` url for json data.

        It accepts only Communication Kit Notifications.

        """
        if id is None:
            raise BadRequest()
        headers = request.httprequest.headers
        self._validate_headers(headers)
        correspondence_obj = request.env['sponsorship.correspondence'].sudo()
        if user is not None:
            correspondence_obj = correspondence_obj.sudo(user)
        correspondence = correspondence_obj.search([('uuid', '=', id)])
        if not correspondence:
            raise NotFound()
        correspondence.write({
            'last_read': fields.Datetime.now(),
            'read_count': correspondence.read_count + 1,
        })
        data = base64.b64decode(correspondence.letter_image.datas)
        message = _("The sponsor requested the child letter image.")
        if user is not None:
            message = _("User requested the child letter image.")
        correspondence.message_post(message, _("Letter downloaded"))
        response = Response(data, mimetype='application/pdf')
        return response

    def _validate_headers(self, headers):
        pass
