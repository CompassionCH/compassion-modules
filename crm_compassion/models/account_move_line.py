##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields


class AccountInvoiceLine(models.Model):
    """Add salespersons to invoice_lines."""

    _inherit = "account.move.line"

    user_id = fields.Many2one("res.partner", "Ambassador", readonly=False)
    event_id = fields.Many2one(
        "crm.event.compassion",
        "Event",
        related="analytic_account_id.event_id",
        store=True,
        readonly=True,
    )

    @api.onchange("contract_id")
    def on_change_contract_id(self):
        """Push Ambassador to invoice line."""
        if self.contract_id.ambassador_id:
            self.user_id = self.contract_id.ambassador_id
