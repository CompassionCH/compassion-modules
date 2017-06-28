# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from odoo import api, models, fields


class AccountInvoiceLine(models.Model):
    """ Add salespersons to invoice_lines. """
    _inherit = "account.invoice.line"

    user_id = fields.Many2one(
        'res.partner', 'Ambassador')
    currency_id = fields.Many2one(
        'res.currency', 'Currency', related='invoice_id.currency_id',
        store=True)

    @api.onchange('contract_id')
    def on_change_contract_id(self):
        """ Push Ambassador to invoice line. """
        contract = self.contract_id
        if contract and contract.user_id:
            self.user_id = contract.user_id.id


class GenerateGiftWizard(models.TransientModel):
    """ Push salespersons to generated invoices """
    _inherit = 'generate.gift.wizard'

    def _setup_invoice_line(self, contract):
        invl_data = super(GenerateGiftWizard, self)._setup_invoice_line(
            contract)
        if contract.user_id:
            invl_data['user_id'] = contract.user_id.id
        return invl_data
