##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emmanuel Mathier, Loic Hausammann <loic_hausammann@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
"""
This module reads a zip file containing scans of mail and finds the relation
between the database and the mail.
"""
import base64
import logging
import io
import traceback

import fitz
from PIL import Image

from odoo.addons.queue_job.job import job, related_action

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from ..tools import read_barcode

logger = logging.getLogger(__name__)


class ImportLettersHistory(models.Model):
    _name = "import.letters.history"
    _inherit = ["import.letter.config", "mail.thread"]
    _order = "create_date desc"
    _rec_name = "create_date"

    state = fields.Selection(
        [
            ("draft", _("Draft")),
            ("pending", _("Analyzing")),
            ("open", _("Open")),
            ("ready", _("Ready")),
            ("done", _("Done")),
        ],
        compute="_compute_state",
        store=True,
        track_visibility="onchange",
    )
    import_completed = fields.Boolean()
    nber_letters = fields.Integer(
        "Number of files", readonly=True, compute="_compute_nber_letters"
    )
    data = fields.Many2many("ir.attachment", string="Add a file", readonly=False)
    import_line_ids = fields.One2many(
        "import.letter.line",
        "import_id",
        "Files to process",
        ondelete="cascade",
        readonly=False,
    )
    letters_ids = fields.One2many(
        "correspondence", "import_id", "Imported letters", readonly=True
    )
    config_id = fields.Many2one(
        "import.letter.config", "Import settings", readonly=False
    )

    @api.multi
    @api.depends(
        "import_line_ids",
        "import_line_ids.status",
        "letters_ids",
        "data",
        "import_completed",
    )
    def _compute_state(self):
        """ Check in which state self is by counting the number of elements in
        each Many2many
        """
        for import_letters in self:
            if import_letters.letters_ids:
                import_letters.state = "done"
            elif import_letters.import_completed:
                check = True
                for i in import_letters.import_line_ids:
                    if i.status != "ok":
                        check = False
                if check:
                    import_letters.state = "ready"
                else:
                    import_letters.state = "open"
            elif import_letters.import_line_ids:
                import_letters.state = "pending"
            else:
                import_letters.state = "draft"

    @api.onchange("data")
    def _compute_nber_letters(self):
        for letter in self:
            if letter.state in ("open", "pending", "ready"):
                letter.nber_letters = len(letter.import_line_ids)
            elif letter.state == "done":
                letter.nber_letters = len(letter.letters_ids)
            elif letter.state is False or letter.state == "draft":
                letter.nber_letters = len(letter.data)

    @api.model
    def create(self, vals):
        if vals.get("config_id"):
            other_import = self.search_count(
                [("config_id", "=", vals["config_id"]), ("state", "!=", "done")]
            )
            if other_import:
                raise UserError(
                    _("Another import with the same configuration is "
                      "already open. Please finish it before creating a new "
                      "one.")
                )
        return super().create(vals)

    @api.multi
    def button_import(self):
        for letters_import in self:
            letters_import.with_delay().run_analyze()
        return True

    @api.multi
    def button_save(self):
        # check if all the imports are OK
        for letters_h in self:
            if letters_h.state != "ready":
                raise UserError(_("Some letters are not ready"))
        # save the imports
        for letters in self:
            correspondence_vals = letters.import_line_ids.get_letter_data()
            # letters_ids should be empty before this line
            for vals in correspondence_vals:
                letters.letters_ids.create(vals)
            letters.import_line_ids.unlink()
        return True

    @api.multi
    def button_review(self):
        """ Returns a form view for import lines in order to browse them """
        self.ensure_one()
        return {
            "name": _("Review Imports"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "import.letters.review",
            "context": self.with_context(line_ids=self.import_line_ids.ids).env.context,
            "target": "current",
        }

    @api.onchange("config_id")
    def onchange_config(self):
        config = self.config_id
        if config:
            for field, val in list(config.get_correspondence_metadata().items()):
                setattr(self, field, val)

    def manual_imports_generator(self):
        """
        Generator function for the manual imports
        Decode the attachments from base64 to a PDF binary and then pass it to analysis

        yield:
            int: the current step in the analysis
            int: the current last step for the analysis
            str: the name of the file analysed
        """
        unique_files = set(self.data)
        unique_files_length = len(unique_files)
        for i, attachment in enumerate(unique_files):
            yield i + 1, unique_files_length, attachment.name
            pdf_data = base64.b64decode(attachment.with_context(bin_size=False).datas)
            self._analyze_pdf(pdf_data, attachment.name)

    @job(default_channel="root.sbc_compassion")
    @related_action(action="related_action_s2b_imports")
    def run_analyze(self, generator=None):
        """
        The analysis require a generator function that yield the names (for the logs)
        and call the _analyze_pdf function on the pdf file to analyse

        Using generators allows us to be more flexible
        on what we analyse without code duplication.
        Additionally, since it uses generators, it does flood the memory with all the documents
        before the analysis
        (With generators don't need to read all the documents before sending them to analysis)

        The generator must yield the following values:
            int: the current step in the analysis
            int: the current last step for the analysis (may or may
            str: the name of the file analysed
        """
        if generator is None:
            generator = self.manual_imports_generator

        self.ensure_one()
        self.state = "pending"
        logger.info("Letters import started...")

        for current_file, nb_files_to_import, filename in generator():
            logger.info(f"{current_file}/{nb_files_to_import} : {filename}")

        logger.info(f"Letters import completed !")
        # remove all the files (now they are inside import_line_ids)
        self.data.unlink()
        self.import_completed = True

    def pdf_to_image(self, pdf_data):
        pdf = fitz.Document("pdf", pdf_data)
        page0 = next(pdf.pages())
        image = self.convert_pdf_page_to_image(page0)
        return image

    @staticmethod
    def convert_pdf_page_to_image(page):
        mat = fitz.Matrix(4.5, 4.5)
        pix = page.get_pixmap(matrix=mat, alpha=0)
        mode = "RGBA" if pix.alpha else "RGB"
        size = [pix.width, pix.height]
        image = Image.frombytes(mode, size, pix.samples)
        return image

    @staticmethod
    def create_preview(image):
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        preview_b64 = base64.b64encode(buffer.getvalue())
        return preview_b64

    @staticmethod
    def crop_letter_text(img):
        """Crop image to obtain text area for standard templates
        """
        box = [
            0.03 * img.width,
            0.15 * img.height,
            (1 - 0.03) * img.width,
            0.5 * img.height
        ]
        box = tuple([int(i) for i in box])
        img = img.crop(box)
        return img

    def _analyze_pdf(self, pdf_data, file_name):
        try:
            data = {
                "import_id": self.id,
                "file_name": file_name,
                "letter_image": base64.b64encode(pdf_data),
                "template_id": self.template_id.id,
            }

            image = self.pdf_to_image(pdf_data)
            partner_code, child_code = read_barcode.letter_barcode_detection(image)
            letter_text_image = self.crop_letter_text(image)
            letter_text_str = self.env["ocr"].image_to_string(letter_text_image)
            data["letter_language_id"] = self.env["langdetect"].detect_language(letter_text_str).id
            data["letter_image_preview"] = self.create_preview(image)

            partner = self.env["res.partner"].search([
                ("ref", "=", partner_code), ("has_sponsorships", "=", True)])

            # since the child code and local_id accept NULL
            # this ensure that even if the child_code is None we don't retrieve
            # one for those
            child = self.env["compassion.child"]
            if child_code:
                child = child.search([("local_id", "=", child_code)], limit=1)

            data["partner_id"] = partner.id
            data["child_id"] = child.id

            self.env["import.letter.line"].create(data)
            # this commit is really important
            # it avoid having to keep the "data"s in memory until the whole process is finished
            # each time a letter is scanned, it is also inserted in the DB
            self._cr.commit()
        except Exception as e:
            logger.error(f"Couldn't import file {file_name} : \n{traceback.format_exc()}")
            return
