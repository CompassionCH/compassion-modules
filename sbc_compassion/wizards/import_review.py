##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, api, fields, _
from odoo.exceptions import UserError


class ImportReview(models.TransientModel):
    """
    Browse through the import lines and allow the user to review and correct
    the results easily.
    """

    _name = "import.letters.review"
    _description = "Review imported letters"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    progress = fields.Float(compute="_compute_current_line", store=True)
    current_line_index = fields.Integer(default=0)
    count = fields.Integer(compute="_compute_current_line", store=True)
    nb_lines = fields.Integer(compute="_compute_current_line", store=True)
    current_line_id = fields.Many2one(
        "import.letter.line",
        "Letter",
        compute="_compute_current_line",
        store=True,
        readonly=True,
    )
    postpone_import_id = fields.Many2one("import.letters.history", readonly=False)

    # Import line related fields
    state = fields.Selection(related="current_line_id.status", readonly=True)
    letter_image = fields.Binary(related="current_line_id.letter_image_preview")
    letter_file = fields.Binary(related="current_line_id.letter_image")
    fname = fields.Char(related="current_line_id.file_name")
    partner_id = fields.Many2one(related="current_line_id.partner_id", readonly=False)
    sponsorship_id = fields.Many2one(
        "recurring.contract", "Sponsorship", readonly=False
    )
    child_id = fields.Many2one(related="current_line_id.child_id", readonly=False)
    template_id = fields.Many2one(related="current_line_id.template_id", readonly=False)
    language_id = fields.Many2one(
        related="current_line_id.letter_language_id",
        order="translatable desc, id asc",
        readonly=False,
    )
    is_encourager = fields.Boolean(related="current_line_id.is_encourager")
    mandatory_review = fields.Boolean(related="current_line_id.mandatory_review")
    physical_attachments = fields.Selection(
        related="current_line_id.physical_attachments"
    )
    attachments_description = fields.Char(
        related="current_line_id.attachments_description"
    )
    edit = fields.Boolean("Edit mode")

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.multi
    @api.depends("current_line_index")
    def _compute_current_line(self):
        line_ids = self.env.context.get("line_ids")
        if line_ids:
            for review in self:
                review.current_line_id = line_ids[review.current_line_index]
                review.nb_lines = len(line_ids)
                review.count = review.current_line_index + 1
                review.progress = (float(review.count) / review.nb_lines) * 100

    @api.onchange("sponsorship_id")
    def _get_partner_child(self):
        for wizard in self:
            child = wizard.sponsorship_id.child_id
            if child:
                wizard.child_id = child

    @api.onchange("partner_id")
    def _get_default_sponsorship(self):
        self.ensure_one()
        if self.partner_id:
            sponsorships = self.env["recurring.contract"].search(
                [("correspondent_id", "=", self.partner_id.id)]
            )
            if len(sponsorships) == 1:
                self.sponsorship_id = sponsorships

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def next(self):
        """ Load the next import line in the view. """
        self.ensure_one()
        if self.current_line_id.status not in ("ok", "no_template"):
            raise UserError(_("Please review this import before going to the next."))
        self.write(
            {
                "current_line_index": self.current_line_index + 1,
                "sponsorship_id": False,
            }
        )
        self.current_line_id.reviewed = True

    @api.multi
    def finish(self):
        """ Return to import view. """
        self.ensure_one()
        import_history = self.current_line_id.import_id
        import_history.import_line_ids._compute_check_status()
        return {
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form,tree",
            "res_model": import_history._name,
            "res_id": import_history.id,
            "context": self.env.context,
            "target": "current",
        }

    @api.multi
    def postpone(self):
        """ Move the line in another import. """
        self.ensure_one()
        postpone_import = self.postpone_import_id
        current_import = self.current_line_id.import_id
        if not postpone_import:
            import_vals = current_import.get_correspondence_metadata()
            import_vals["import_completed"] = True
            postpone_import = self.env["import.letters.history"].create(import_vals)
            self.postpone_import_id = postpone_import
        self.current_line_id.import_id = postpone_import
        self.current_line_index += 1
