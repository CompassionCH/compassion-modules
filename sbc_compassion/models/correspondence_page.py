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
from pdf2image import convert_from_bytes
from PIL import Image

from odoo import api, fields, models

from ..tools.onramp_connector import SBCConnector
from .correspondence_text_box import PAGE_HEIGHT_PX, PAGE_WIDTH_PX

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
        "correspondence", ondelete="cascade", required=True, readonly=False, index=True
    )
    original_page_url = fields.Char()
    cloudinary_original_page_url = fields.Char(
        compute="_compute_cloudinary_url", store=True
    )
    final_page_url = fields.Char()
    cloudinary_final_page_url = fields.Char(
        compute="_compute_cloudinary_url", store=True
    )
    original_page_image = fields.Binary(compute="_compute_original_page_image")
    final_page_image = fields.Binary(compute="_compute_final_page_image")
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
            "The pages already exists in database.",
        ),
        (
            "final_page_url",
            "unique(final_page_url)",
            "The pages already exists in database.",
        ),
    ]

    def _compute_page_image(self, image_type="original"):
        cloudinary_url_field = f"cloudinary_{image_type}_page_url"
        image_field = f"{image_type}_page_image"
        url_field = f"{image_type}_page_url"
        for page in self:
            cloudinary_url = getattr(page, cloudinary_url_field)
            page_url = getattr(page, url_field)
            image = False
            # A cropped image slices a stack of pages in equal parts, which is
            # wrong when the pages don't have the same height: the page of the
            # document is used first.
            connect_first = bool(cloudinary_url and "c_crop" in cloudinary_url)
            if connect_first:
                image = page._get_connect_image(page_url)
            if not image and cloudinary_url:
                image = page._get_cloundinary_image(cloudinary_url)
            if not image and not connect_first:
                image = page._get_connect_image(page_url)
            if (
                not image
                and page.correspondence_id.direction == "Beneficiary To Supporter"
            ):
                image = page.template_id.background
            # The computed field must always be assigned
            setattr(page, image_field, image or False)

    def _get_connect_image(self, page_url):
        if not page_url:
            return False
        image = SBCConnector(self.env).get_letter_image(page_url, {"dpi": 96})
        # Connect returns the body of an error as it is: only keep real images
        try:
            Image.open(BytesIO(base64.b64decode(image or b""))).verify()
        except Exception:
            _logger.warning(
                "Connect did not return an image for %s: %r",
                page_url,
                base64.b64decode(image or b"")[:200],
            )
            return False
        return image

    def _compute_original_page_image(self):
        self._compute_page_image("original")

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
                if page.correspondence_id.direction == "Supporter To Beneficiary":
                    page_template = modulo_page
                elif (
                    page.original_page_url
                    or page.page_index
                    <= page.correspondence_id.overlay_source_nbr_pages
                ):
                    # Extra scanned page of the child or page of the source
                    # PDF: no text box over it
                    page_template = template.page_ids.browse()
                else:
                    page_template = template.additional_page_id or modulo_page
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
        if self.page_index <= letter.overlay_source_nbr_pages:
            return self._fetch_pdf_page_image(
                letter.with_context(bin_size=False).overlay_source_pdf, 150
            )
        if letter.direction == "Supporter To Beneficiary" and not letter.kit_identifier:
            if self.template_id.background:
                return self.template_id.background
            else:
                # Fetch from sponsor pdf
                return self._fetch_sponsor_pdf_image()
        image_field = (
            "final_page_image"
            if letter.sponsor_needs_final_letter
            else "original_page_image"
        )
        if not getattr(self, image_field):
            self._compute_page_image(image_field.replace("_page_image", ""))
        return getattr(self, image_field)

    @api.model
    def fetch_image_width(self, image):
        """
        Used by the PDF report: width in px at which the image is printed so
        that it fits on one A4 page. The width must be absolute, because a
        percentage resolves to the natural size of the image in wkhtmltopdf,
        which makes large images overflow on the next page. Images that are
        higher than A4 are shrunk, the others keep the full page width.
        """
        if not image:
            return PAGE_WIDTH_PX
        try:
            width, height = Image.open(BytesIO(base64.b64decode(image))).size
        except Exception:
            _logger.warning("Could not read the size of a page image", exc_info=True)
            return PAGE_WIDTH_PX
        if not width or not height:
            return PAGE_WIDTH_PX
        # Keep a small margin so that rounding never pushes it onto a new page
        max_width = (PAGE_HEIGHT_PX - 2) * width / height
        return round(min(PAGE_WIDTH_PX, max_width), 1)

    def _fetch_sponsor_pdf_image(self):
        self.ensure_one()
        return self._fetch_pdf_page_image(
            self.correspondence_id.sponsor_letter_scan, 96
        )

    def _fetch_pdf_page_image(self, pdf, dpi):
        """Image of the page of a PDF corresponding to this letter page."""
        self.ensure_one()
        if pdf:
            pdf_data = base64.b64decode(pdf)
            image = convert_from_bytes(
                pdf_data, dpi, first_page=self.page_index, last_page=self.page_index
            )[0]
            return self.env["import.letters.history"].create_preview(image)
        return False

    def _get_cloundinary_image(self, cloudinary_url):
        if not cloudinary_url:
            return False
        try:
            response = requests.get(cloudinary_url, timeout=3)
        except requests.RequestException:
            # Fall back to the next image source instead of failing the PDF
            _logger.warning("Could not download %s", cloudinary_url, exc_info=True)
            return False
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
        # Pages added to hold overflowing text are not part of the letter image
        letter_pages = self.correspondence_id.page_ids
        scanned_pages = letter_pages.filtered("original_page_url") or letter_pages
        if not cloudinary_url or self not in scanned_pages:
            return False
        scanned_index = list(scanned_pages).index(self) + 1
        if cloudinary_url.endswith("p1.jpg"):
            return cloudinary_url.replace("p1.jpg", f"p{scanned_index}.jpg")
        response = requests.get(cloudinary_url, timeout=3)
        if not response.ok:
            return False
        width, total_height = Image.open(BytesIO(response.content)).size
        height = total_height // len(scanned_pages)
        y_start = (scanned_index - 1) * height
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

    def set_text(self, field, text):
        """Make sure the text is split into paragraphs"""
        self.ensure_one()
        paragraphs = text.split(BOX_SEPARATOR)
        for index, paragraph in enumerate(paragraphs):
            if index < len(self.paragraph_ids):
                self.paragraph_ids[index][field] = paragraph
            else:
                self.paragraph_ids.create(
                    {
                        field: paragraph,
                        "sequence": index,
                        "page_id": self.id,
                    }
                )
        return self.write({field: text})

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
