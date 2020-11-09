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

from werkzeug.datastructures import Headers
from werkzeug.exceptions import BadRequest, NotFound
from werkzeug.wrappers import Response

from odoo import http, fields
from odoo.http import request

_logger = logging.getLogger(__name__)


class RestController(http.Controller):
    @http.route("/b2s_image", type="http", auth="public", methods=["GET"])
    # We don't want to rename parameter id because it's used by our sponsors
    # pylint: disable=redefined-builtin
    def handler_b2s_image(self, id=None, disposition=None, file_type=None, **parameters):
        """ Handler for `/b2s_image` url for json data.

        It accepts only Communication Kit Notifications.

        """
        if id is None:
            raise BadRequest()
        headers = request.httprequest.headers
        self._validate_headers(headers)
        correspondence_obj = request.env["correspondence"].sudo()
        correspondence = correspondence_obj.search([("uuid", "=", id)])
        if not correspondence:
            raise NotFound()
        correspondence.email_read = datetime.now()
        headers = Headers()
        disposition = disposition if disposition else "attachment"
        if correspondence.letter_format == "zip":
            if file_type == "pdf":
                data = correspondence.generate_original_pdf()
                fname = correspondence.file_name
            else:
                data = correspondence.get_image()
                fname = fields.Date.today().strftime("%d-%m-%Y") + " letters.zip"
            headers.add("Content-Disposition", disposition, filename=fname)
            response = Response(data, content_type="application/zip", headers=headers)
        else:
            data = correspondence.get_image()
            headers.add(
                "Content-Disposition", disposition, filename=correspondence.file_name
            )
            response = Response(data, content_type="application/pdf", headers=headers)
        return response

    def _validate_headers(self, headers):
        pass
