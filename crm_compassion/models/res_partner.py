##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import _, fields, models

from odoo.addons.partner_communication.models.communication_config import (
    CommunicationConfig,
)


class Partner(models.Model):
    _inherit = "res.partner"

    ambassador_receipt_send_mode = fields.Selection(
        CommunicationConfig.get_delivery_preferences,
        default="digital_only",
    )
    receive_ambassador_receipts = fields.Boolean(
        compute="_compute_receive_ambassador_receipts",
        inverse="_inverse_receive_ambassador_receipts",
    )

    def _compute_receive_ambassador_receipts(self):
        for partner in self:
            partner.receive_ambassador_receipts = (
                partner.ambassador_receipt_send_mode != "none"
            )

    def _inverse_receive_ambassador_receipts(self):
        # We expose only a simple setting and use digital_only send_mode
        for partner in self:
            partner.ambassador_receipt_send_mode = (
                "digital_only" if (partner.receive_ambassador_receipts) else "none"
            )

    def open_events(self):
        event_ids = (
            self.env["crm.event.compassion"]
            .search([("partner_id", "child_of", self.ids)])
            .ids
        )

        return {
            "name": _("Events"),
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "res_model": "crm.event.compassion",
            "target": "current",
            "domain": [("id", "in", event_ids)],
        }

    def create_odoo_user(self):
        portal = self.env["portal.wizard"].create({})
        users_portal = portal.mapped("user_ids")
        users_portal.write({"in_portal": True})
        res = portal.action_apply()
        return res

    def _compute_opportunity_count(self):
        super()._compute_opportunity_count()
        for partner in self:
            operator = "child_of" if partner.is_company else "="
            partner.opportunity_count += self.env["crm.lead"].search_count(
                [
                    ("partner_id", operator, partner.id),
                    ("type", "=", "opportunity"),
                    ("active", "=", False),
                ]
            )

    def log_call(self):
        """Prepare crm.phonecall creation."""
        self.ensure_one()
        action_ctx = self.env.context.copy()
        action_ctx.update(
            {
                "default_state": "done",
                "default_partner_id": self.id,
                "default_partner_mobile": self.mobile,
                "default_partner_phone": self.phone,
                "origin": "employee",
            }
        )
        domain = [("partner_id", "=", self.id)]

        return {
            "name": _("Log your call"),
            "domain": domain,
            "res_model": "crm.phonecall",
            "view_mode": "form,tree,calendar",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": action_ctx,
        }
