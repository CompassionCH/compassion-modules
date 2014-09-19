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

import time
from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp import netsvc


class reconcile_fund_wizard(orm.TransientModel):
    _name = 'reconcile.fund.wizard'

    _columns = {
        'fund_id': fields.many2one('product.product', 'Fund', required=True),
    }

    def reconcile_with_fund(self, cr, uid, ids, context=None):
        ''' Generate an invoice corresponding to the selected fund
            and reconcile it with selected move lines
        '''
        if isinstance(ids, list):
            ids = ids[0]

        wizard = self.browse(cr, uid, ids, context)
        res = {}
        invoice_obj = self.pool.get('account.invoice')
        move_line_obj = self.pool.get('account.move.line')
        journal_obj = self.pool.get('account.journal')

        journal_ids = journal_obj.search(
            cr, uid, [('type', '=', 'sale'), ('company_id', '=', 1 or False)],
            limit=1)

        date_invoice = None
        residual = 0.0
        for line in move_line_obj.browse(cr, uid, context.get('active_ids'),
                                         context):
            residual += line.credit - line.debit
            if line.credit > 0:
                date_invoice = line.date

        if residual < 0:
            raise orm.except_orm(
                'ResidualError',
                _('This can only be done if credits > debits'))

        move_line = move_line_obj.browse(
            cr, uid, context.get('active_id'), context)
        partner = move_line.partner_id
        inv_data = {
            'account_id': partner.property_account_receivable.id,
            'type': 'out_invoice',
            'partner_id': partner.id,
            'journal_id': len(journal_ids) and journal_ids[0] or False,
            'date_invoice': date_invoice,
            'payment_term': 1,  # Immediate payment
            'bvr_reference': '',
        }

        active_ids = context.get('active_ids')
        invoice_id = invoice_obj.create(cr, uid, inv_data, context=context)
        if invoice_id:
            res.update(self._generate_invoice_line(
                cr, uid, invoice_id, wizard.fund_id,
                residual, partner.id, context=context))

            # Validate the invoice
            wf_service = netsvc.LocalService('workflow')
            wf_service.trg_validate(
                uid, 'account.invoice', invoice_id, 'invoice_open', cr)
            invoice = invoice_obj.browse(cr, uid, invoice_id, context)
            move_line_ids = move_line_obj.search(
                cr, uid, [('move_id', '=', invoice.move_id.id),
                          ('account_id', '=', inv_data['account_id'])],
                context=context)
            active_ids.extend(move_line_ids)
        move_line_obj.reconcile(cr, uid, active_ids)

        return res

    def _generate_invoice_line(self, cr, uid, invoice_id, product, price,
                               partner_id, context=None):

        inv_line_data = {
            'name': product.name,
            'account_id': product.property_account_income.id,
            'price_unit': price,
            'quantity': 1,
            'uos_id': False,
            'product_id': product.id or False,
            'invoice_id': invoice_id,
        }

        res = {}

        # Define analytic journal
        analytic = self.pool.get('account.analytic.default').account_get(
            cr, uid, product.id, partner_id, uid, time.strftime('%Y-%m-%d'),
            context=context)
        if analytic and analytic.analytics_id:
            inv_line_data['analytics_id'] = analytic.analytics_id.id

        res['name'] = product.name

        self.pool.get('account.invoice.line').create(
            cr, uid, inv_line_data, context=context)
        return res
