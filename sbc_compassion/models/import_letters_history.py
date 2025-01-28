##############################################################################
#
#    Copyright (C) 2014-2024 Compassion CH (http://www.compassion.ch)
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
import io
import logging

from PyPDF2 import PdfFileReader
from pdf2image import convert_from_bytes

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..tools import read_barcode

logger = logging.getLogger(__name__)


class ImportLettersHistory(models.Model):
    _name = "import.letters.history"
    _inherit = ["import.letter.config", "mail.thread"]
    _order = "create_date desc"
    _rec_name = "create_date"
    _description = "S2B Letter Import"

    state = fields.Selection(
        [
            ("draft", _("Draft")),
            ("pending", _("Analyzing Files")),
            ("open", _("In Review")),
            ("ready", _("Ready to import")),
            ("done", _("Done")),
        ],
        tracking=True,
        default="draft",
        copy=False,
        required=True,
    )
    nber_letters = fields.Integer(
        "Number of files", readonly=True, compute="_compute_nber_letters"
    )
    data = fields.Many2many("ir.attachment", string="Add a file", readonly=False)
    import_line_ids = fields.One2many(
        "import.letter.line",
        "import_id",
        "Files to process",
        readonly=False,
    )
    letters_ids = fields.One2many(
        "correspondence", "import_id", "Imported letters", readonly=True
    )
    config_id = fields.Many2one(
        "import.letter.config", "Import settings", readonly=False
    )

    failed_file_name = fields.Text(
        string="Files with errors",
        help="Displays the name of the files that failed the PDF analysis.",
        readonly=True,
        default="",
    )

    @api.onchange("data")
    def _compute_nber_letters(self):
        for letter in self:
            if letter.state in ("open", "pending", "ready"):
                letter.nber_letters = len(letter.import_line_ids)
            elif letter.state == "done":
                letter.nber_letters = len(letter.letters_ids)
            elif letter.state is False or letter.state == "draft":
                letter.nber_letters = len(letter.data)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("config_id"):
                other_import = self.search_count(
                    [("config_id", "=", vals["config_id"]), ("state", "!=", "done")]
                )
                if other_import:
                    raise UserError(
                        _(
                            "Another import with the same configuration is "
                            "already open. Please finish it before creating a new "
                            "one."
                        )
                    )
        return super().create(vals_list)

    def button_import(self):
        self.ensure_one()
        self.state = "pending"
        job = self.delayable().run_analyze()
        after_job = self.delayable().write({"state": "open"})
        job.on_done(after_job).delay()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Success"),
                "message": _("Letters are being imported in background."),
                "type": "success",
            },
        }

    def button_save(self):
        # check if all the imports are OK
        self.ensure_one()
        if self.state != "ready":
            raise UserError(_("Some letters are not ready"))
        self.failed_file_name = False
        # save the imports
        failed_names = []
        correspondence_vals = self.import_line_ids.get_letter_data()
        # letters_ids should be empty before this line
        for import_line, vals in zip(self.import_line_ids, correspondence_vals):
            try:
                with self.env.cr.savepoint():
                    pdf_data = base64.b64decode(vals.get("pdf_data"))
                    pdf_buffer = io.BytesIO(pdf_data)
                    pdf_document = PdfFileReader(pdf_buffer)
                    if pdf_document.getNumPages() == 0:
                        raise ValueError("page count is 0")
                    self.letters_ids.create(vals)
                    import_line.unlink()
            except Exception:
                logger.error("Error while saving import", exc_info=True)
                failed_names.append(vals.get("file_name"))

        if failed_names:
            self.write(
                {
                    "failed_file_name": "\n".join(failed_names),
                }
            )
            return False
        else:
            self.write(
                {
                    "state": "done",
                }
            )
            return True

    def button_review(self):
        """Returns a form view for import lines in order to browse them"""
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

    def run_analyze(self, generator=None):
        """
        The analysis require a generator function that yield the names (for the logs)
        and call the _analyze_pdf function on the pdf file to analyse

        Using generators allows us to be more flexible
        on what we analyse without code duplication.
        Additionally, since it uses generators, it does flood
        the memory with all the documents
        before the analysis
        (With generators don't need to read all the documents before sending
        them to analysis)

        The generator must yield the following values:
            int: the current step in the analysis
            int: the current last step for the analysis (may or may
            str: the name of the file analysed
        """
        if generator is None:
            generator = self.manual_imports_generator

        self.ensure_one()
        self.state = "pending"

        for current_file, nb_files_to_import, filename in generator():
            logger.info(f"{current_file}/{nb_files_to_import} : {filename}")

        # remove all the files (now they are inside import_line_ids)
        self.data.unlink()

    @staticmethod
    def create_preview(image):
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        preview_b64 = base64.b64encode(buffer.getvalue())
        return preview_b64

    @staticmethod
    def crop(image):
        # ignore top and bottom part cause they usually contain non interesting text
        return image.crop((0, image.height * 0.15, image.width, image.height * 0.85))

    def _analyze_pdf(self, pdf_data, file_name):
        try:
            letter_image = base64.b64encode(pdf_data)
            data = {
                "import_id": self.id,
                "file_name": file_name,
                "letter_image": letter_image,
                "template_id": self.template_id.id,
            }

            image = convert_from_bytes(pdf_data, 100, last_page=1)[0]
            partner_code, child_code = read_barcode.letter_barcode_detection(image)
            letter_str, _ = self.env["ocr"].image_to_string(self.crop(image))
            if letter_str:
                data["letter_language_id"] = (
                    self.env["langdetect"].detect_language(letter_str).id
                )
            data["letter_image_preview"] = self.create_preview(image)

            partner_obj = self.env["res.partner"]
            partner = partner_obj.search(
                [("ref", "=", partner_code), ("has_sponsorships", "=", True)], limit=2
            )
            if len(partner) == 2:
                partner = partner_obj

            child = self.env["compassion.child"]
            if child_code:
                child = child.search([("local_id", "=", child_code)], limit=1)

            data["partner_id"] = partner.id
            data["child_id"] = child.id

            self.env["import.letter.line"].create(data)
            # this commit is really important
            # it avoids having to keep the "data"s in memory until the whole process is
            # finished each time a letter is scanned, it is also inserted in the DB
            # pylint: disable=invalid-commit
            self._cr.commit()
        except Exception:
            failed_files = self.failed_file_name or ""
            if failed_files:
                failed_files += "\n"
            failed_files += file_name
            self.write(
                {
                    "failed_file_name": failed_files,
                }
            )
            logger.error("Import file %s failed", file_name, exc_info=True)

    def open_letters(self):
        return {
            "type": "ir.actions.act_window",
            "name": _("Imported letters"),
            "res_model": "correspondence",
            "view_mode": "tree,form",
            "domain": [("import_id", "=", self.id)],
        }
