##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields


class ContractOrigin(models.Model):
    """ Add event to origin of a contract """

    _inherit = "recurring.contract.origin"

    event_id = fields.Many2one(
        "crm.event.compassion", "Event", readonly=False, ondelete="cascade")

    @api.depends("type")
    def _compute_name(self):
        for origin in self:
            if origin.type == "event":
                origin.name = origin.event_id.full_name
            else:
                super(ContractOrigin, origin)._compute_name()

    @api.multi
    def write(self, vals):
        """ Propagate ambassador into contracts and invoice lines. """
        if "partner_id" in vals:
            for origin in self:
                old_ambassador_id = origin.partner_id.id
                sponsorships = self.env["recurring.contract"].search(
                    [("origin_id", "=", origin.id), ("user_id", "=", old_ambassador_id)]
                )
                sponsorships.write({"user_id": vals["partner_id"]})
                invoice_lines = self.env["account.invoice.line"].search(
                    [("contract_id", "in", sponsorships.ids)]
                )
                invoice_lines.write({"user_id": vals["partner_id"]})
        return super().write(vals)

    def _find_same_origin(self, vals):
        return self.search(
            [
                ("type", "=", vals.get("type")),
                ("partner_id", "=", vals.get("partner_id")),
                "|",
                ("analytic_id", "=", vals.get("analytic_id")),
                ("event_id", "=", vals.get("event_id")),
                ("country_id", "=", vals.get("country_id")),
                ("other_name", "=", vals.get("other_name")),
            ],
            limit=1,
        )
