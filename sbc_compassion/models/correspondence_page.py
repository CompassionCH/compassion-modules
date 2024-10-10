##############################################################################
#
#    Copyright (C) 2014-2024 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Stephane Eicher, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
import html
import logging
from io import BytesIO

import requests
from PIL import Image

from odoo import _, api, fields, models

from ..tools.onramp_connector import SBCConnector

_logger = logging.getLogger(__name__)

BOX_SEPARATOR = "#BOX#"
PAGE_SEPARATOR = "#PAGE#"


class CorrespondencePage(models.Model):
    """This class defines a page used for in sponsorship correspondence"""

    _inherit = "compassion.mapped.model"
    _name = "correspondence.page"
    _description = "Letter page"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    correspondence_id = fields.Many2one(
        "correspondence", ondelete="cascade", required=True, readonly=False
    )
    original_page_url = fields.Char()
    cloudinary_original_page_url = fields.Char(
        compute="_compute_cloudinary_url", store=True
    )
    final_page_url = fields.Char(compute="_compute_cloudinary_url", store=True)
    cloudinary_final_page_url = fields.Char()
    original_page_image = fields.Binary(
        compute="_compute_original_page_image", store=True
    )
    final_page_image = fields.Binary(compute="_compute_final_page_image", store=True)
    paragraph_ids = fields.One2many(
        "correspondence.paragraph", "page_id", "Paragraphs", copy=True
    )
    template_id = fields.Many2one(
        "correspondence.template.page", compute="_compute_template_page"
    )
    original_text = fields.Text(default="")
    english_text = fields.Text(default="")
    translated_text = fields.Text(default="")
    page_index = fields.Integer(compute="_compute_page_index")

    _sql_constraints = [
        (
            "original_page_url",
            "unique(original_page_url)",
            _("The pages already exists in database."),
        ),
        (
            "final_page_url",
            "unique(final_page_url)",
            _("The pages already exists in database."),
        ),
    ]

    def _compute_page_image(self, image_type="original"):
        cloudinary_url_field = f"cloudinary_{image_type}_page_url"
        image_field = f"{image_type}_page_image"
        url_field = f"{image_type}_page_url"
        for page in self:
            if getattr(page, cloudinary_url_field):
                setattr(
                    page,
                    image_field,
                    page._get_cloundinary_image(getattr(page, url_field)),
                )
            if not getattr(page, image_field) and getattr(page, url_field):
                connector = SBCConnector(self.env)
                setattr(
                    page,
                    image_field,
                    connector.get_letter_image(getattr(page, url_field), {"dpi": 96}),
                )
            if (
                not getattr(page, image_field)
                and page.correspondence_id.direction == "Beneficiary To Supporter"
            ):
                setattr(page, image_field, page.template_id.background)

    @api.depends("original_page_url", "cloudinary_original_page_url")
    def _compute_original_page_image(self):
        self._compute_page_image("original")

    @api.depends("final_page_url", "cloudinary_final_page_url")
    def _compute_final_page_image(self):
        self._compute_page_image("final")

    def _compute_page_index(self):
        for page in self:
            letter = page.correspondence_id
            page.page_index = next(
                (i for i, cp in enumerate(letter.page_ids, 1) if cp == page), 0
            )

    def _compute_template_page(self):
        """
        This method determines the appropriate template page for each page in the
        correspondence based on the page index and the direction of the correspondence.
        """
        for page in self:
            template = page.correspondence_id.template_id
            try:
                # Attempt to get the template page based on the page index
                page_template = template.page_ids[page.page_index - 1]
            except IndexError:
                # Handle case where page index exceeds the number of template pages
                new_index = (page.page_index - 1) % 2
                modulo_page = template.page_ids[new_index : new_index + 1]
                page_template = (
                    modulo_page
                    if page.correspondence_id.direction == "Supporter To Beneficiary"
                    else template.additional_page_id or modulo_page
                )
            page.template_id = page_template

    def fetch_image(self):
        """
        Used by the PDF report of the correspondence in order to get the correct image
        of the page (Original or Final).
        It also ensures an image is available and tries to fetch it from Persistence
        in case it's missing.
        """
        self.ensure_one()
        letter = self.correspondence_id
        if letter.direction == "Supporter To Beneficiary" and not letter.kit_identifier:
            return self.template_id.background
        image_field = (
            "final_page_image"
            if letter.sponsor_needs_final_letter
            else "original_page_image"
        )
        if not getattr(self, image_field):
            self._compute_page_image(image_field.replace("_page_image", ""))
        return getattr(self, image_field)

    def _get_cloundinary_image(self, cloudinary_url):
        if not cloudinary_url:
            return False
        response = requests.get(cloudinary_url)
        return base64.b64encode(response.content) if response.ok else False

    @api.depends(
        "correspondence_id.cloudinary_original_letter_url",
        "correspondence_id.cloudinary_final_letter_url",
    )
    def _compute_cloudinary_url(self):
        for page in self:
            page.cloudinary_original_page_url = page._get_cloudinary_url(
                page.correspondence_id.cloudinary_original_letter_url
            )
            page.cloudinary_final_page_url = page._get_cloudinary_url(
                page.correspondence_id.cloudinary_final_letter_url
            )

    def _get_cloudinary_url(self, cloudinary_url):
        """
        Returns the cloudinary url with the correct crop so that the page is displayed
        """
        if not cloudinary_url:
            return False
        if cloudinary_url.endswith("p1.jpg"):
            return cloudinary_url.replace("p1.jpg", f"p{str(self.page_index)}.jpg")
        response = requests.get(cloudinary_url)
        if not response.ok:
            return False
        width, total_height = Image.open(BytesIO(response.content)).size
        height = total_height // len(self.correspondence_id.page_ids)
        y_start = (self.page_index - 1) * height
        crop_operator = f"c_crop,h_{height},w_{width},x_0,y_{y_start}"
        url_parts = cloudinary_url.split("upload/")
        return f"{url_parts[0]}upload/{crop_operator}/{url_parts[1]}"

    def sync_text_from_paragraphs(self):
        _fields = ["original_text", "english_text", "translated_text"]
        for page in self:
            page.write(
                {
                    field: BOX_SEPARATOR.join(
                        page.mapped("paragraph_ids").mapped(
                            lambda paragraph, _field=field: paragraph[_field] or ""
                        )
                    )
                    for field in _fields
                }
            )
        return True

    @api.model
    def json_to_data(self, json, mapping_name=None):
        odoo_data = super().json_to_data(json, mapping_name)
        odoo_fields = ("original_text", "english_text", "translated_text")
        if isinstance(odoo_data, dict):
            odoo_data = [odoo_data]
        for field in odoo_fields:
            for page_data in odoo_data:
                if field in page_data:
                    page_data[field] = html.unescape(
                        BOX_SEPARATOR.join(page_data[field])
                    )
        return odoo_data
