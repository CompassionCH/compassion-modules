##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo.addons.web.controllers.main import content_disposition
from werkzeug.exceptions import BadRequest, NotFound

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class RestController(http.Controller):
    @http.route("/web/pdf/correspondence/<int:object_id>", type="http", methods=["GET"])
    def generate_correspondence_pdf(self, object_id, translator_id=None):
        if not object_id or not translator_id:
            raise BadRequest()

        translator = request.env["translation.user"].sudo().browse(int(translator_id)).exists()
        correspondence = request.env["correspondence"].sudo(translator.user_id.id).browse(object_id).exists()
        binary = correspondence and correspondence.get_image()

        if not binary:
            raise NotFound()

        return request.make_response(
            binary,
            [
                ("Content-Type", "application/pdf"),
                ("Content-Disposition", content_disposition(correspondence.file_name)),
            ],
        )
