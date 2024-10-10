##############################################################################
#
#    Copyright (C) 2015-2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from datetime import datetime
from io import BytesIO
from os import path
from zipfile import ZipFile

from werkzeug.datastructures import Headers
from werkzeug.exceptions import BadRequest, NotFound
from werkzeug.wrappers import Response

from odoo import fields, http
from odoo.http import request

from odoo.addons.web.controllers.main import content_disposition

_logger = logging.getLogger(__name__)


def _get_data(letter):
    # Use the data type that is stored in database
    data = letter.get_pdf()
    if letter.letter_format == "zip":
        fname = fields.Date.today().strftime("%d-%m-%Y") + " letters.zip"
    else:
        fname = f"{letter.get_date('create_date')}-{letter.file_name}"
    return data, fname


def _get_child_correspondence(partner, child):
    sponsorship_ids = child.sponsorship_ids.filtered(
        lambda contract: contract.correspondent_id == partner
        or contract.partner_id == partner
    )
    return (
        request.env["correspondence"]
        .sudo()
        .search(
            [
                ("sponsorship_id", "=", sponsorship_ids[0].id),
            ]
        )
    )


def _fill_archive(buffer, letters, file_path=""):
    with ZipFile(buffer, "a") as archive:
        for letter in letters:
            try:
                data, fname = _get_data(letter)
                if not data:
                    raise ValueError
            except ValueError:
                continue
            full_path = path.join(file_path, fname)
            archive.writestr(full_path, data)


class RestController(http.Controller):
    @http.route("/b2s_image", type="http", auth="public", methods=["GET"])
    def handler_b2s_image(self, uuid=None, disposition=None, **parameters):
        """Handler for `/b2s_image` url for json data.

        It accepts only Communication Kit Notifications.

        """
        if uuid is None:
            raise BadRequest()
        headers = request.httprequest.headers
        self._validate_headers(headers)
        correspondence_obj = request.env["correspondence"].sudo()
        correspondence = correspondence_obj.search([("uuid", "=", uuid)])
        if not correspondence:
            raise NotFound()
        correspondence.email_read = datetime.now()
        disposition = disposition if disposition else "attachment"
        content_type = "application/" + (
            "zip" if correspondence.letter_format == "zip" else "pdf"
        )
        data, fname = _get_data(correspondence)
        headers = Headers([("Content-Disposition", f"{disposition}; filename={fname}")])
        return Response(data or "No data", content_type=content_type, headers=headers)

    @http.route("/b2s_image/child", type="http", auth="user", methods=["GET"])
    # pylint: disable=redefined-builtin
    def handler_b2s_images(self, child_id=None, **parameters):
        partner = request.env.user.partner_id
        zip_buffer = BytesIO()
        if child_id:  # We want to download a single child correspondence
            child = request.env["compassion.child"].browse(int(child_id))
            letters = _get_child_correspondence(partner, child)
            archive_name = f"{child.preferred_name}_correspondence.zip"
            _fill_archive(zip_buffer, letters)
        else:  # We want to download all children correspondence
            children = (
                (
                    partner.contracts_fully_managed
                    + partner.contracts_correspondant
                    + partner.contracts_paid
                )
                .mapped("child_id")
                .sorted("preferred_name")
            )
            archive_name = "children_correspondence.zip"
            for child in children:
                letters = _get_child_correspondence(partner, child)
                file_path = f"{child.preferred_name}_{child.local_id}"
                _fill_archive(zip_buffer, letters, file_path)

        zip_buffer.seek(0)
        zip_data = zip_buffer.read()

        return request.make_response(
            zip_data,
            [
                ("Content-Type", "application/zip"),
                ("Content-Disposition", content_disposition(archive_name)),
            ],
        )

    def _validate_headers(self, headers):
        pass
