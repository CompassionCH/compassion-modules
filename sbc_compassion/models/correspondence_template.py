##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import base64
import json
import logging
import os.path
import subprocess
import tempfile

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import config

_logger = logging.getLogger(__name__)

try:
    import numpy
    import cv2
except ImportError:
    _logger.warning("Please install numpy, and cv2 to use SBC module")


class Style:
    """ Defines a few colors for drawing on the result picture
    (names from wikipedia).
    The color order is BGR"""

    pattern_color_sq = (34, 139, 34)  # green (forest)
    pattern_color_pt = (0, 128, 0)  # green (html/css color)
    pattern_color_key = (0, 204, 239)  # yellow (munsell)
    qr_color = (168, 24, 0)  # blue (Pantone)
    lang_color = (0, 97, 232)  # Spanish orange
    # defines scaling for circles radius
    radius_scale = 120


class CorrespondenceTemplate(models.Model):
    """ This class defines a template used for Supporter Letters and holds
    all information relative to position of metadata in the Template, like for
    instance where the QR Code is supposed to be, where the language
    checkboxes will be found, where the pattern will be, etc...

    Template images should be in 300 DPI
    """

    _name = "correspondence.template"
    _description = "Correspondence template"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char(required=True, translate=True)
    type = fields.Selection(
        [("s2b", "S2B Template"), ("b2s", "B2S Layout"), ], required=True, default="s2b"
    )
    active = fields.Boolean(default=True)
    layout = fields.Selection(
        [
            ("CH-A-1S11-1", "Layout 1"),
            ("CH-A-2S01-1", "Layout 2"),
            ("CH-A-3S01-1", "Layout 3"),
            ("CH-A-4S01-1", "Layout 4"),
            ("CH-A-5S01-1", "Layout 5"),
            ("CH-A-6S11-1", "Layout 6"),
        ]
    )
    template_image = fields.Binary(compute="_compute_template_image")
    page_width = fields.Integer(help="Width of the template in pixels")
    page_height = fields.Integer(help="Height of the template in pixels")
    usage_count = fields.Integer(compute="_compute_usage_count")
    page_ids = fields.One2many(
        "correspondence.template.page",
        "template_id",
        "Pages",
        required=True,
        copy=True,
        readonly=False,
    )
    additional_page_id = fields.Many2one(
        "correspondence.template.page",
        "Additional page",
        help="Template used in case the S2B text is too long to fit on the "
             "standard two-sided page.",
        readonly=False,
    )

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################

    @api.multi
    def _compute_usage_count(self):
        for template in self:
            template.usage_count = self.env["correspondence"].search_count(
                [("template_id", "=", template.id)]
            )

    @api.multi
    def _compute_template_image(self):
        for template in self:
            template.template_image = template.page_ids[:1].background

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################

    def get_template_size(self, resize_factor=1.0):
        """ Returns the width and height of the template in a numpy array. """
        wh = numpy.array([self.page_width, self.page_height])
        wh *= resize_factor
        return wh

    def generate_pdf(self, pdf_name, header, text, image_data, background_list=None):
        """
        Generate a pdf file
        This function is nearly as generic as it should be to be implemented
        directly to generate PDF for any template, text and image
        We save every text to a temp txt file to avoid having to escape all
        characters that could potentially be problematic
        :param pdf_name: path and name of the pdf file to write on
        :param header: tuple of text for the headers to display
                       (first value is for front pages, second for back pages)
        :param text: a dict of {type of text ('Original' or 'Translation'):
                                list of text boxes}
        :param image_data: a list of base64 images to display
        :param background_list: an optional list of page background images
                                if not specified, it will be taken from
                                the template.
        """
        self.ensure_one()

        temp_img = []
        temp_header = []
        temp_text = []
        if background_list is None:
            background_list = []
        overflow_template = False

        pages = self.mapped("page_ids") - self.additional_page_id
        template_list = []
        image_list = []
        page_count = 0
        for i, page in enumerate(pages):
            page_count += 1
            header_index = i % 2
            try:
                background = background_list[i]
            except (TypeError, IndexError):
                background = page.background
            if background:
                temp_img.append(
                    tempfile.NamedTemporaryFile(prefix="img_", suffix=".jpg")
                )
                temp_img[-1].write(base64.b64decode(background))
                temp_img[-1].flush()
                background_file = temp_img[-1].name
            else:
                background_file = False
            header_data = []
            page_header = page.header_box_id
            if page_header and len(header) >= header_index:
                header_file = tempfile.NamedTemporaryFile(
                    "w", prefix="header_", suffix=".txt"
                )
                header_file.write(header[header_index])
                header_file.flush()
                header_data = [header_file.name]
                header_data.extend(page_header.get_json_repr())
                temp_header.append(header_file)
            text_list = []
            for text_box in page.text_box_ids:
                text_list.append(text_box.get_json_repr())
            image_boxes = []
            for image_box in page.image_box_ids:
                image_boxes.append(image_box.get_json_repr())
            template_list.append([background_file, header_data, text_list, image_boxes])
        if background_list:
            # An original document is provided. We want
            # to complete the PDF document with the remaining pages
            # and provide an overflow template in case the text is longer
            # and we should add pages for additional translation.
            if len(background_list) > len(pages):
                for i in range(len(pages), len(background_list)):
                    bf = tempfile.NamedTemporaryFile(prefix="img_", suffix=".jpg")
                    bf.write(base64.b64decode(background_list[i]))
                    bf.flush()
                    temp_img.append(bf)
                    template_list.append([bf.name, [], [], []])
            additional_page = self.env.ref("sbc_compassion.b2s_additional_page")
            bf_name = False
            if additional_page.background:
                bf = tempfile.NamedTemporaryFile(prefix="img_", suffix=".jpg")
                bf.write(base64.b64decode(additional_page.background))
                bf.flush()
                bf_name = bf.name
                temp_img.append(bf)
            text_list = []
            for text_box in additional_page.text_box_ids:
                text_list.append(text_box.get_json_repr())
            overflow_template = [bf_name, [], text_list, image_boxes]
        elif self.additional_page_id:
            # We are generating a new PDF (S2B case). We provide
            # an overflow template using the template
            add_background = tempfile.NamedTemporaryFile(prefix="img_", suffix=".jpg")
            add_background.write(base64.b64decode(self.additional_page_id.background))
            add_background.flush()
            temp_img.append(add_background)
            text_list = []
            for text_box in self.additional_page_id.text_box_ids:
                text_list.append(text_box.get_json_repr())
            overflow_template = [add_background.name, header_data, text_list, []]

        text_list = []
        for t_type, t_boxes in list(text.items()):
            for txt in t_boxes:
                temp_text.append(
                    tempfile.NamedTemporaryFile("w", prefix=t_type + "_", suffix=".txt")
                )
                temp_text[-1].write(txt)
                temp_text[-1].flush()
                text_list.append([temp_text[-1].name, t_type])

        for image in image_data:
            ifile = tempfile.NamedTemporaryFile(prefix="img_", suffix=".jpg")
            ifile.write(base64.b64decode(image))
            ifile.flush()
            image_list.append(ifile.name)
            temp_img.append(ifile)

        generated_json = {
            "images": image_list,
            "templates": template_list,
            "texts": text_list,
            # The output should at least contain 2 pages
            "original_size": max(2, len(background_list)),
            "overflow_template": overflow_template,
            "lang": self.env.lang,
            "prevent_overflow": self.type == "b2s",
        }

        json_val = json.dumps(generated_json).replace(" ", "")

        std_err_file = open(self.path_to("stderr.txt"), "w")

        php_command_args = ["php", self.path_to("pdf.php"), pdf_name, json_val]
        if config.get("php_debug"):
            # Allow php debugging with Xend
            os.environ["XDEBUG_CONFIG"] = "PHPSTORM"
            php_command_args.extend(
                [
                    "-dxdebug.remote_enable=1",
                    "-dxdebug.remote_mode=req",
                    "-dxdebug.remote_port=9000",
                    "-dxdebug.remote_host=127.0.0.1",
                ]
            )
        proc = subprocess.Popen(php_command_args, stderr=std_err_file)
        proc.communicate()

        # Clean temp files
        for img in temp_img:
            img.close()
        for h in temp_header:
            h.close()
        for t in temp_text:
            t.close()
        std_err_file.close()

        # Read and return output
        try:
            pdf_file = open(pdf_name, "rb")
            res = pdf_file.read()
            pdf_file.close()
            os.remove(pdf_file.name)
        except FileNotFoundError:
            _logger.error("Cannot read PDF made by FPDF.")
            res = False
        return res

    # path of the FPDF folder
    _absolute_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "FPDF/"
    )

    # create path to the subfolder of FPDF
    def path_to(self, filename, folder=""):
        if folder == "":
            return os.path.join(self._absolute_path, filename)
        return os.path.join(self._absolute_path, folder + "/" + filename)
