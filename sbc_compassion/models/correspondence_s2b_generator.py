##############################################################################
#
#    Copyright (C) 2016-2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
import logging
from io import BytesIO

from wand.exceptions import PolicyError

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

try:
    from PyPDF2 import PdfFileReader, PdfFileWriter
    from wand.image import Image
except ImportError:
    _logger.debug("Please install wand to use SBC module")


class CorrespondenceS2bGenerator(models.Model):
    """Generation of S2B Letters with text."""

    _name = "correspondence.s2b.generator"
    _description = "Correspondence Generator"
    _inherit = "correspondence.metadata"
    _order = "date desc"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    state = fields.Selection(
        [("draft", "Draft"), ("preview", "Preview"), ("done", "Done")], default="draft"
    )
    name = fields.Char(required=True)
    date = fields.Datetime(default=fields.Datetime.now)
    image_ids = fields.Many2many(
        "ir.attachment", string="Attached images", readonly=False
    )
    template_id = fields.Many2one(required=True, domain=[("type", "=", "s2b")])
    background = fields.Image(related="template_id.template_image")
    selection_domain = fields.Char(
        default=[
            ("partner_id.category_id", "=", "Correspondance by Compassion"),
            ("state", "=", "active"),
            ("child_id", "!=", False),
        ]
    )
    sponsorship_ids = fields.Many2many(
        "recurring.contract", string="Sponsorships", required=True, readonly=False
    )
    language_id = fields.Many2one(
        "res.lang.compassion",
        "Language",
        readonly=False,
        default=lambda s: s.env.ref("advanced_translation.lang_compassion_english").id,
        required=True,
    )
    body = fields.Text(
        required=True,
        help="You can use the following tags to replace with values :\n\n"
        "* %child%: child name\n"
        "* %age%: child age (1, 2, 3, ...)\n"
        "* %firstname%: sponsor firstname\n"
        "* %lastname%: sponsor lastname\n",
    )
    letter_ids = fields.One2many(
        "correspondence", "generator_id", "Letters", readonly=False
    )
    nb_letters = fields.Integer(compute="_compute_nb_letters")
    preview_image = fields.Image(readonly=True)
    preview_pdf = fields.Binary(readonly=True)
    filename = fields.Char(compute="_compute_filename")
    month = fields.Selection("_get_months")

    def _compute_nb_letters(self):
        for generator in self:
            generator.nb_letters = len(generator.letter_ids)

    @api.model
    def _get_months(self):
        return self.env["compassion.child"]._get_months()

    def _compute_filename(self):
        for generator in self:
            generator.filename = generator.name + ".pdf"

    @api.constrains("image_ids")
    def check_attached_images(self):
        # Only jpg images are allowed
        for generator in self:
            for image in generator.image_ids:
                if image.mimetype != "image/jpeg":
                    raise ValidationError(
                        _("Only JPG images are allowed as attached images.")
                    )

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.onchange("selection_domain")
    def onchange_domain(self):
        if self.selection_domain:
            self.sponsorship_ids = self.env["recurring.contract"].search(
                safe_eval(self.selection_domain)
            )

    @api.onchange("month")
    def onchange_month(self):
        if self.month:
            domain = safe_eval(self.selection_domain)
            month_select = ("child_id.birthday_month", "=", self.month)
            index = 0
            for search_filter in domain:
                if search_filter[0] == "child_id.birthday_month":
                    index = domain.index(search_filter)
            if index:
                domain[index] = month_select
            else:
                domain.append(month_select)
            self.selection_domain = str(domain)

    def preview(self):
        """Generate a picture for preview."""
        pdf = self._get_pdf(self.sponsorship_ids[:1])[0]
        if self.template_id.layout == "CH-A-3S01-1":
            # Read page 2
            in_pdf = PdfFileReader(BytesIO(pdf))
            output_pdf = PdfFileWriter()
            out_data = BytesIO()
            output_pdf.addPage(in_pdf.getPage(1))
            output_pdf.write(out_data)
            out_data.seek(0)
            pdf = out_data.read()

        try:
            with Image(blob=pdf, resolution=96) as pdf_image:
                preview = base64.b64encode(pdf_image.make_blob(format="jpeg"))
        except PolicyError as error:
            _logger.error(
                "ImageMagick policy error. Please add following line to "
                "/etc/Image-Magick-<version>/policy.xml: "
                '<policy domain="coder" rights="read|write" '
                'pattern="PDF" />',
            )
            raise UserError(
                _(
                    "Please allow ImageMagick to write PDF files."
                    " Ask an IT admin for help."
                )
            ) from error
        except TypeError as error:
            raise UserError(
                _(
                    "There was an error while generating the PDF of the letter. "
                    "Please check FPDF logs for more information."
                )
            ) from error

        pdf_image = base64.b64encode(pdf)

        return self.write(
            {
                "state": "preview",
                "preview_image": preview,
                "preview_pdf": pdf_image,
            }
        )

    def edit(self):
        """Generate a picture for preview."""
        return self.write({"state": "draft"})

    def generate_letters(self):
        """
        Launch S2B Creation job
        :return: True
        """
        self.with_delay().generate_letters_job()
        return True

    def generate_letters_job(self):
        """
        Create S2B Letters
        :return: True
        """
        try:
            letters = self.env["correspondence"]
            for sponsorship in self.sponsorship_ids:
                text = self._get_text(sponsorship)
                vals = {
                    "sponsorship_id": sponsorship.id,
                    "store_letter_image": False,
                    "template_id": self.template_id.id,
                    "direction": "Supporter To Beneficiary",
                    "source": self.source,
                    "original_language_id": self.language_id.id,
                    "original_text": text,
                }
                if self.image_ids:
                    vals["original_attachment_ids"] = [
                        (
                            0,
                            0,
                            {
                                "datas": atchmt.datas,
                                "name": atchmt.name,
                                "res_model": letters._name,
                            },
                        )
                        for atchmt in self.image_ids
                    ]
                letters += letters.create(vals)

            letters.create_text_boxes()
            self.letter_ids = letters

            # If the operation succeeds, notify the user
            message = "Letters have been successfully generated."
            self.env.user.notify_success(message=message)
            return self.write({"state": "done", "date": fields.Datetime.now()})

        except Exception as error:
            # If the operation fails, notify the user with the error message
            error_message = str(error)
            self.env.user.notify_danger(message=error_message)

        return True

    def open_letters(self):
        letters = self.letter_ids
        return {
            "name": letters._description,
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "res_model": letters._name,
            "context": self.env.context,
            "domain": [("id", "in", letters.ids)],
            "target": "current",
        }

    def _get_text(self, sponsorship):
        """Generates the text given a sponsorship."""
        self.ensure_one()
        sponsor = sponsorship.correspondent_id
        child = sponsorship.child_id
        keywords = {
            "%child%": child.preferred_name,
            "%age%": str(child.age),
            "%firstname%": sponsor.firstname or sponsor.name,
            "%lastname%": sponsor.firstname and sponsor.lastname or "",
        }
        text = self.body
        for keyword, replacement in list(keywords.items()):
            text = text.replace(keyword, replacement)

        return text

    def _get_pdf(self, sponsorship):
        """Generates a PDF given a sponsorship."""
        self.ensure_one()
        sponsor = sponsorship.correspondent_id
        child = sponsorship.child_id
        text = self._get_text(sponsorship)

        header = (
            f"{sponsor.global_id} - {sponsor.preferred_name} - \n"
            f"{child.local_id} - {child.preferred_name}"
            f" - {'Female' if child.gender == 'F' else 'Male'}"
            f" - {str(child.age)}"
        )

        return (
            self.template_id.generate_pdf(
                sponsorship.display_name,
                (header, ""),  # Headers (front/back)
                {"Original": [text]},  # Text
                self.mapped("image_ids.datas"),  # Images
            ),
            text,
        )
