##############################################################################
#
#    Copyright (C) 2014-2023 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import _, api, fields, models


class Contracts(models.Model):
    """Adds the Salesperson to the contract."""

    _inherit = "recurring.contract"

    ambassador_id = fields.Many2one("res.partner", "Ambassador", readonly=False)

    @api.onchange("origin_id")
    def on_change_origin(self):
        origin = self.origin_id
        if origin:
            ambassador = origin.get_ambassador()
            if ambassador:
                self.ambassador_id = ambassador

    @api.onchange("child_id")
    def onchange_child_id(self):
        hold = self.hold_id
        if hold:
            origin = hold.get_origin()
            if origin:
                self.origin_id = origin
            if hold.channel and hold.channel == "web":
                self.medium_id = self.env.ref("utm.utm_medium_website")
            if hold.ambassador:
                self.ambassador_id = hold.ambassador
            self.campaign_id = hold.campaign_id
            if hold.comments:
                return {
                    "warning": {
                        "title": _("The child has some comments"),
                        "message": hold.comments,
                    }
                }

    def contract_waiting(self):
        super().contract_waiting()
        for contract in self:
            notif_template = (
                contract.origin_id.event_id.ambassador_sponsorship_config_id
            )
            if notif_template and contract.ambassador_id:
                self.env["partner.communication.job"].create(
                    {
                        "config_id": notif_template.id,
                        "partner_id": contract.ambassador_id.id,
                        "object_ids": contract.id,
                    }
                )
