from io import BytesIO

from werkzeug.exceptions import NotFound

from odoo import fields, http
from odoo.http import content_disposition, request

from odoo.addons.sbc_compassion.controllers.b2s_image import _fill_archive


class B2sLettersController(http.Controller):
    @http.route("/b2s_image/letters", type="http", auth="public", methods=["GET"])
    def handler_b2s_letters(self, letter_uuid=None, **kwargs):
        """Zip of all letters of the communication the given letter belongs to."""
        letter = (
            request.env["correspondence"]
            .sudo()
            .search([("uuid", "=", letter_uuid)], limit=1)
            if letter_uuid
            else None
        )
        if not letter or not letter.communication_id:
            raise NotFound()
        letters = letter.communication_id.get_objects()
        if letters._name != "correspondence":
            raise NotFound()
        stored_zip = letter.communication_id._get_letters_zip()[:1]
        if stored_zip:
            data = stored_zip.raw
        else:
            buffer = BytesIO()
            _fill_archive(buffer, letters)
            data = buffer.getvalue()
        if request.env.user.share:
            letters.write({"email_read": fields.Datetime.now()})
        fname = fields.Date.today().strftime("%d-%m-%Y") + " letters.zip"
        return request.make_response(
            data,
            [
                ("Content-Type", "application/zip"),
                ("Content-Disposition", content_disposition(fname)),
            ],
        )
