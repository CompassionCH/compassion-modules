##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class HoldWizard(models.TransientModel):
    """
    Class used for searching interventions in the Mi3 Portal.
    """

    _inherit = "compassion.mapped.model"
    _name = "compassion.intervention.hold.wizard"
    _description = "Intervention Hold Wizard"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    intervention_id = fields.Many2one(
        "compassion.global.intervention", "Intervention", readonly=False
    )
    created_intervention_id = fields.Many2one("compassion.intervention", readonly=False)
    hold_amount = fields.Float(required=True)
    hold_id = fields.Char()
    usd = fields.Many2one(related="intervention_id.currency_usd", readonly=False)
    expiration_date = fields.Date(required=True)
    next_year_opt_in = fields.Boolean()
    user_id = fields.Many2one(
        "res.users",
        "Primary owner",
        default=lambda s: s.env.user,
        domain=[("share", "=", False)],
        required=True,
        readonly=False,
    )
    secondary_owner = fields.Char()
    service_level = fields.Selection(
        [
            ("Level 1", _("Level 1")),
            ("Level 2", _("Level 2")),
            ("Level 3", _("Level 3")),
        ],
        required=True,
        default="Level 2",
    )

    def hold_sent(self, hold_vals):
        """Called when hold is created"""
        del hold_vals["intervention_id"]
        intervention_vals = self.intervention_id.get_vals()
        intervention_vals.update(hold_vals)
        intervention_vals.update(
            {
                "expiration_date": self.expiration_date,
                "next_year_opt_in": self.next_year_opt_in,
                "user_id": self.user_id.id,
                "secondary_owner": self.secondary_owner,
                "service_level": self.service_level,
                "state": "on_hold",
            }
        )
        intervention = self.env["compassion.intervention"].search(
            [("intervention_id", "=", self.intervention_id.intervention_id)]
        )
        if intervention:
            intervention.with_context(hold_update=False).write(intervention_vals)
        else:
            # Grant create access rights to create intervention
            intervention = (
                self.env["compassion.intervention"]
                .with_context(async_mode=True)
                .sudo()
                .create(intervention_vals)
            )
            # Replace author of record to avoid having admin
            intervention.message_ids.sudo().write(
                {"author_id": self.env.user.partner_id.id}
            )
        self.created_intervention_id = intervention

    def make_hold(self):
        self.ensure_one()
        create_hold = self.env.ref(
            "intervention_compassion.intervention_create_hold_action"
        )
        message = (
            self.env["gmc.message"]
            .with_context(async_mode=False)
            .create(
                {
                    "action_id": create_hold.id,
                    "object_id": self.id,
                }
            )
        )
        if "failure" in message.state:
            raise UserError(message.failure_reason)

        return {
            "name": _("Intervention"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "compassion.intervention",
            "context": self.env.context,
            "res_id": self.created_intervention_id.id,
            "target": "current",
        }

    @api.onchange("intervention_id")
    def onchange_intervention(self):
        for wizard in self.filtered("intervention_id.type"):
            if "Ongoing" in wizard.intervention_id.type:
                wizard.service_level = "Level 1"
