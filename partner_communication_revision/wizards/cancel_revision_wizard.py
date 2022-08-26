##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, api, fields


class ValidateRevisionWizard(models.TransientModel):
    _name = "partner.communication.cancel.proposition"
    _description = "Cancel proposition wizard"

    revision_id = fields.Many2one(
        "partner.communication.revision",
        default=lambda s: s._default_revision(),
        required=True,
        readonly=False,
    )
    revision_mode = fields.Selection(
        [("proposition", "Reviser"), ("correction", "Corrector")],
        "Assign revision to",
        required=True,
        default="correction",
    )
    user_id = fields.Many2one(
        "res.users",
        "Set person in charge",
        domain=[("share", "=", False)],
        compute="_compute_user_id",
        inverse="_inverse_user_id",
        readonly=False,
    )
    comments = fields.Text()

    @api.model
    def _default_revision(self):
        return self.env["partner.communication.revision"].browse(
            self.env.context.get('active_id')
        )

    def _compute_user_id(self):
        for wizard in self:
            if wizard.revision_mode == "proposition":
                wizard.user_id = wizard.revision_id.user_id
            else:
                wizard.user_id = wizard.revision_id.correction_user_id

    def _inverse_user_id(self):
        for wizard in self:
            if wizard.revision_mode == "proposition":
                wizard.revision_id.user_id = wizard.user_id
            else:
                wizard.revision_id.correction_user_id = wizard.user_id

    @api.onchange("revision_id", "revision_mode")
    def onchange_revision_id(self):
        self._compute_user_id()

    def cancel_revision(self):
        self.ensure_one()
        revision_vals = {"state": "pending", "is_master_version": False}
        if self.revision_mode != "proposition":
            revision_vals.update(
                {
                    "state": "submit",
                    "proposition_correction": self.revision_id.proposition_text,
                    "subject_correction": self.revision_id.subject,
                }
            )
        self.revision_id.write(revision_vals)
        if self.user_id != self.env.user or self.comments:
            next_action_text = (
                f"<b>Next action for {self.user_id.firstname}: "
                "Make corrections and resubmit.</b><br/><br/>"
            )
            body = f"The text was set back in revision by {self.env.user.firstname}"
            if self.comments:
                body += f" with following comments:<br/><br/>{self.comments.strip()}"
            else:
                body += "."

            subject = (
                f"[{self.revision_id.display_name}] Approval cancelled: "
                "text needs corrections"
            )
            self.revision_id.notify_proposition(subject, next_action_text + body)

        return True
