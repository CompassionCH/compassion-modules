# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import http
from odoo.http import request

from odoo.addons.web.controllers.main import content_disposition

from werkzeug.exceptions import BadRequest, NotFound

_logger = logging.getLogger(__name__)


class RestController(http.Controller):

    @http.route('/web/pdf/correspondence', type='http', auth='public', methods=['GET'])
    def generate_correspondence_pdf(self, object_id=None, **parameters):
        if object_id is None:
            raise BadRequest()

        correspondence = request.env['correspondence'].browse(int(object_id))
        binary = correspondence and correspondence.get_image()

        if not binary:
            raise NotFound()

        return request.make_response(
            binary, [('Content-Type', 'application/pdf'),
                     ('Content-Disposition', content_disposition(
                         correspondence.file_name))])
