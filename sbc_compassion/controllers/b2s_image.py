##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from datetime import datetime

from odoo import http, fields
from odoo.http import request

from werkzeug.exceptions import BadRequest, NotFound
from werkzeug.wrappers import Response
from werkzeug.datastructures import Headers

_logger = logging.getLogger(__name__)


class RestController(http.Controller):

    @http.route('/b2s_image', type='http', auth='public', methods=['GET'])
    # We don't want to rename parameter id because it's used by our sponsors
    def handler_b2s_image(self, id=None):  # pylint: disable=redefined-builtin
        """ Handler for `/b2s_image` url for json data.

        It accepts only Communication Kit Notifications.

        """
        if id is None:
            raise BadRequest()
        headers = request.httprequest.headers
        self._validate_headers(headers)
        correspondence_obj = request.env['correspondence'].sudo()
        correspondence = correspondence_obj.search([('uuid', '=', id)])
        if not correspondence:
            raise NotFound()
        data = correspondence.get_image()
        correspondence.email_read = datetime.now()
        headers = Headers()
        if correspondence.letter_format == 'zip':
            fname = fields.Date.today() + ' letters.zip'
            headers.add(
                'Content-Disposition', 'attachment',
                filename=fname)
            response = Response(data, content_type='application/zip',
                                headers=headers)
        else:
            headers.add(
                'Content-Disposition', 'attachment',
                filename=correspondence.file_name)
            response = Response(data, content_type='application/pdf',
                                headers=headers)
        return response

    def _validate_headers(self, headers):
        pass
