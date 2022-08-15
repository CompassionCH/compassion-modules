##############################################################################
#
#    Copyright (C) 2021 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = "account.move.line"

    last_payment = fields.Date(related="invoice_id.last_payment", store=True)

    def filter_for_contract_rewind(self, filter_state):
        """ Only use sponsorship invoices for sponsorships. """
        res = super().filter_for_contract_rewind(filter_state)
        contract = self.mapped("contract_id")
        if contract and "S" in contract.type:
            res = res.filtered(
                lambda l: l.product_id.categ_id == self.env.ref(
                    "sponsorship_compassion.product_category_sponsorship"))
        return res
