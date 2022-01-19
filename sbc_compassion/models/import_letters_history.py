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
import traceback

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

    def local_generator(self):
        d = set(self.data)
        n = len(d)
        for i, attachment in enumerate(d):
            yield i + 1, n, attachment.name
            pdf_data = base64.b64decode(attachment.with_context(bin_size=False).datas)
            self._analyze_pdf(pdf_data, attachment.name)

    @job(default_channel="root.sbc_compassion")
    @related_action(action="related_action_s2b_imports")
    def run_analyze(self, generator=None):
        if generator is None:
            generator = self.local_generator

        self.ensure_one()
        self.state = "pending"
        logger.info("Letters import started...")

        for i, n, file in generator():
            logger.info(f"{i}/{n} : {file}")

        logger.info(f"Letters import completed !")
        # remove all the files (now they are inside import_line_ids)
        self.data.unlink()
        self.import_completed = True

    def _analyze_pdf(self, pdf_data, file_name):
        try:
            partner_code, child_code, preview = read_barcode.letter_barcode_detection_pipeline(pdf_data)
        except Exception as e:
            logger.error(f"Couldn't import file {file_name} : \n{traceback.format_exc()}")
            return

        partner = self.env["res.partner"].search([("ref", "=", partner_code)], limit=1)
        if partner:
            partner_id = partner.id
        else:
            partner_id = None

        child = self.env["compassion.child"].search(["|", ("code", "=", child_code), ("local_id", "=", child_code)], limit=1)
        if child:
            child_id = child.id
        else:
            child_id = None

        data = {
            "import_id": self.id,
            "partner_id": partner_id,
            "child_id": child_id,
            "letter_image_preview": preview,
            "letter_image": pdf_data,
            "file_name": file_name,
            "template_id": self.template_id.id,
        }
        self.env["import.letter.line"].create(data)
        # this commit is really important
        # it avoid having to keep the "data"s in memory until the whole process is finished
        # each time a letter is scanned, it is also inserted in the DB
        self._cr.commit()
