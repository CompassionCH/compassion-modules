# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester <csester@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import api, models


class account_invoice(models.Model):
    _name = 'account.invoice'
    _inherit = 'account.invoice'

    @api.multi
    def confirm_paid(self):
        """ Call invoice_paid method on related contracts. """
        super(account_invoice, self).confirm_paid()
        for invoice in self:
            contracts = invoice.mapped('invoice_line.contract_id')
            contracts.invoice_paid(invoice)

    @api.multi
    def action_reopen(self):
        """ Call invoice_unpaid method on related contract. """
        self.write({'state': 'open'})
        for invoice in self:
            contracts = invoice.mapped('invoice_line.contract_id')
            contracts.invoice_unpaid(invoice)
