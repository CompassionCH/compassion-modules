##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, fields, models


class CommunicationConfig(models.Model):
    _inherit = "partner.communication.config"

    revision_number = fields.Float(default=1.0, readonly=True)
    revision_date = fields.Date(default=fields.Date.today(), readonly=True)
    revision_ids = fields.One2many(
        "partner.communication.revision", "config_id", "Revisions", readonly=False
    )
    state = fields.Selection(
        [("active", "Active"), ("pending", "In Revision")],
        compute="_compute_state",
        store=True,
    )

    @api.depends("revision_ids", "revision_ids.state")
    def _compute_state(self):
        for config in self:
            rev_states = list(set(config.revision_ids.mapped("state")))
            if len(rev_states) == 1 and rev_states[0] == "active":
                config.state = "active"
            else:
                config.state = "pending"

    def new_proposition(self):
        """
        Called for creating a new revision text
        :return: view action for editing proposition text
        """
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_id": self.id,
            "res_model": self._name,
            "target": "current",
            "context": self.env.context,
        }

    def open_translation_view(self):
        for revision in self.mapped("revision_ids"):
            revision.edit_revision()
        return self.env["ir.translation"].translate_fields(
            "mail.template", self.email_template_id.id, "body_html"
        )
