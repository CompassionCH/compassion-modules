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

from openerp import http
from openerp.http import request

from werkzeug.exceptions import BadRequest, NotFound
from werkzeug.wrappers import Response
from werkzeug.datastructures import Headers

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
        correspondence_obj = request.env['correspondence'].sudo()
        if user is not None:
            correspondence_obj = correspondence_obj.sudo(user)
        correspondence = correspondence_obj.search([('uuid', '=', id)])
        if not correspondence:
            raise NotFound()
        data = correspondence.get_image(user)
        headers = Headers()
        headers.add(
            'Content-Disposition', 'attachment',
            filename=correspondence.letter_image.name)
        if correspondence.letter_format == 'zip':
            response = Response(data, content_type='application/zip',
                                headers=headers)
        else:
            response = Response(data, content_type='application/pdf',
                                headers=headers)
        return response

    def _validate_headers(self, headers):
        pass
