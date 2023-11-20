##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from werkzeug.exceptions import BadRequest, NotFound, Unauthorized

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class RestController(http.Controller):
    @http.route("/web/pdf/correspondence/<int:object_id>", type="http", methods=["GET"])
    def generate_correspondence_pdf(self, object_id, api_key=None):
        if not object_id:
            raise BadRequest()
        if not api_key or api_key != request.env[
            "ir.config_parameter"
        ].sudo().get_param("sbc_translation.api_key"):
            raise Unauthorized()

        correspondence = request.env["correspondence"].sudo().browse(object_id).exists()
        if not correspondence:
            raise NotFound()
        binary = correspondence and correspondence.get_image()
        if not binary:
            raise NotFound()

        return request.make_response(
            binary,
            [
                ("Content-Type", "application/pdf"),
            ],
        )
