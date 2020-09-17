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
import zipfile
from io import BytesIO

from odoo.addons.queue_job.job import job, related_action

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from ..tools import import_letter_functions as func

logger = logging.getLogger(__name__)


class ImportLettersHistory(models.Model):
    """
    Keep history of imported letters.
    This class allows the user to import some letters (individually or in a
    zip file) in the database by doing an automatic analysis.
    The code is reading QR codes in order to detect child and partner codes
    for every letter, using the zxing library for code detection.
    """

    _name = "import.letters.history"
    _inherit = ["import.letter.config", "mail.thread"]
    _description = _(
        """History of the letters imported from a zip
    or a PDF/TIFF"""
    )
    _order = "create_date desc"
    _rec_name = "create_date"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

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

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
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
        """
        Counts the number of scans. If a zip file is given, the number of
        scans inside is counted.
        """
        for letter in self:
            if letter.state in ("open", "pending", "ready"):
                letter.nber_letters = len(letter.import_line_ids)
            elif letter.state == "done":
                letter.nber_letters = len(letter.letters_ids)
            elif letter.state is False or letter.state == "draft":
                # counter
                tmp = 0
                # loop over all the attachments
                for attachment in letter.data:
                    # pdf or tiff case
                    if func.check_file(attachment.name) == 1:
                        tmp += 1
                    # zip case
                    elif func.is_zip(attachment.name):
                        # create a tempfile and read it
                        zip_file = BytesIO(
                            base64.b64decode(
                                attachment.with_context(bin_size=False).datas
                            )
                        )
                        # catch ALL the exceptions that can be raised
                        # by class zipfile
                        try:
                            zip_ = zipfile.ZipFile(zip_file, "r")
                            list_file = zip_.namelist()
                            # loop over all files in zip
                            for tmp_file in list_file:
                                tmp += func.check_file(tmp_file) == 1
                        except zipfile.BadZipfile:
                            raise UserError(
                                _("Zip file corrupted (" + attachment.name + ")")
                            )
                        except zipfile.LargeZipFile:
                            raise UserError(
                                _("Zip64 is not supported(" + attachment.name + ")")
                            )

                letter.nber_letters = tmp
            else:
                raise UserError(_("State: '%s' not implemented") % letter.state)

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
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
        return super().create(vals)

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def button_import(self):
        """
        Analyze the attachment in order to create the letter's lines
        """
        for letters_import in self:
            if letters_import.data:
                letters_import.state = "pending"
                if self.env.context.get("async_mode", True):
                    letters_import.with_delay()._run_analyze()
                else:
                    letters_import._run_analyze()
        return True

    @api.multi
    def button_save(self):
        """
        save the import_line as a correspondence
        """
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

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    @job(default_channel="root.sbc_compassion")
    @related_action(action="related_action_s2b_imports")
    def _run_analyze(self):
        """
        Analyze each attachment:
        - check for duplicate file names and skip them
        - decompress zip file if necessary
        - call _analyze_attachment for every resulting file
        """
        self.ensure_one()
        # keep track of file names to detect duplicates
        file_name_history = []
        logger.info("Imported files analysis started...")
        progress = 1

        for attachment in self.data:
            if attachment.name not in file_name_history:
                file_name_history.append(attachment.name)
                file_data = base64.b64decode(
                    attachment.with_context(bin_size=False).datas
                )
                # check for zip
                if func.check_file(attachment.name) == 2:
                    zip_file = BytesIO(file_data)
                    zip_ = zipfile.ZipFile(zip_file, "r")
                    for f in zip_.namelist():
                        logger.debug(f"Analyzing file {progress}/{self.nber_letters}")
                        self._analyze_attachment(zip_.read(f), f)
                        progress += 1
                # case with normal format (PDF,TIFF)
                elif func.check_file(attachment.name) == 1:
                    logger.debug(f"Analyzing file {progress}/{self.nber_letters}")
                    self._analyze_attachment(file_data, attachment.name)
                    progress += 1
                else:
                    raise UserError(_("Only zip/pdf files are supported."))
            else:
                raise UserError(_("Two files are the same"))

        # remove all the files (now they are inside import_line_ids)
        self.data.unlink()
        self.import_completed = True
        logger.info("Imported files analysis completed.")

    def _analyze_attachment(self, file_data, file_name):
        line_vals = func.analyze_attachment(
            self.env, file_data, file_name, self.template_id
        )
        for i in range(0, len(line_vals)):
            line_vals[i]["import_id"] = self.id
            self.env["import.letter.line"].create(line_vals[i])
