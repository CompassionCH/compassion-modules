# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.osv import orm
from openerp.tools.translate import _

from . import gp_connector


class account_invoice(orm.Model):
    _inherit = 'account.invoice'

    def action_cancel(self, cr, uid, ids, context=None):
        """ If an invoice was cancelled, update the situation in GP. """
        for invoice in self.browse(cr, uid, ids, context):
            # Customer invoice going from 'open' to 'cancel' state
            if invoice.type == 'out_invoice' and invoice.state == 'open':
                contract_ids = set()
                gp_connect = gp_connector.GPConnect(cr, uid)
                for line in invoice.invoice_line:
                    contract = line.contract_id
                    if contract and contract.id not in contract_ids:
                        contract_ids.add(contract.id)
                        if not gp_connect.register_payment(contract.id):
                            raise orm.except_orm(
                                _("GP Sync Error"),
                                _("The cancellation could not be registered "
                                  "into GP. Please contact an IT person."))
        return super(account_invoice, self).action_cancel(cr, uid, ids,
                                                          context)

    def action_move_create(self, cr, uid, ids, context=None):
        """ If an invoice was cancelled,
            and validated again, update the situation in GP.
        """
        res = super(account_invoice, self).action_move_create(cr, uid, ids,
                                                              context)
        for invoice in self.browse(cr, uid, ids, context):
            if invoice.type == 'out_invoice' and invoice.internal_number:
                contract_ids = set()
                gp_connect = gp_connector.GPConnect(cr, uid)
                for line in invoice.invoice_line:
                    contract = line.contract_id
                    if contract and contract.id not in contract_ids:
                        contract_ids.add(contract.id)
                        if not gp_connect.undo_payment(contract.id):
                            raise orm.except_orm(
                                _("GP Sync Error"),
                                _("Please contact an IT person."))
        return res
