# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import logging
from openerp.osv import osv, fields

class account_analytic_invoice_line(osv.osv):
    _name = "account.analytic.invoice.line"
    _inherit = "account.analytic.invoice.line"

    _columns = {
        'analytics_id' : fields.many2one('account.analytic.plan.instance', 'Analytic Distribution', required=True),
    }
    
class account_analytic_account(osv.osv):
    _name = "account.analytic.account"
    _inherit = "account.analytic.account"
    
    def _prepare_invoice(self, cr, uid, contract, context=None):
        context = context or {}

        inv_obj = self.pool.get('account.invoice')
        journal_obj = self.pool.get('account.journal')
        fpos_obj = self.pool.get('account.fiscal.position')
        lang_obj = self.pool.get('res.lang')

        if not contract.partner_id:
            raise osv.except_osv(_('No Customer Defined!'),_("You must first select a Customer for Contract %s!") % contract.name )

        fpos = contract.partner_id.property_account_position or False
        journal_ids = journal_obj.search(cr, uid, [('type', '=','sale'),('company_id', '=', contract.company_id.id or False)], limit=1)
        if not journal_ids:
            raise osv.except_osv(_('Error!'),
            _('Please define a sale journal for the company "%s".') % (contract.company_id.name or '', ))

        partner_payment_term = contract.partner_id.property_payment_term and contract.partner_id.property_payment_term.id or False


        inv_data = {
           'reference': contract.code or False,
           'account_id': contract.partner_id.property_account_receivable.id,
           'type': 'out_invoice',
           'partner_id': contract.partner_id.id,
           'currency_id': contract.partner_id.property_product_pricelist.currency_id.id or False,
           'journal_id': len(journal_ids) and journal_ids[0] or False,
           'date_invoice': contract.recurring_next_date,
           'origin': contract.name,
           'fiscal_position': fpos and fpos.id,
           'payment_term': partner_payment_term,
           'company_id': contract.company_id.id or False,
        }
        invoice_id = inv_obj.create(cr, uid, inv_data, context=context)

        for line in contract.recurring_invoice_line_ids:

            res = line.product_id
            account_id = res.property_account_income.id
            if not account_id:
                account_id = res.categ_id.property_account_income_categ.id
            account_id = fpos_obj.map_account(cr, uid, fpos, account_id)

            taxes = res.taxes_id or False
            tax_id = fpos_obj.map_tax(cr, uid, fpos, taxes)

            if 'old_date' in context:
                lang_ids = lang_obj.search(cr, uid, [('code', '=', contract.partner_id.lang)], context=context)
                format = lang_obj.browse(cr, uid, lang_ids, context=context)[0].date_format
                line.name = line.name.replace('#START#', context['old_date'].strftime(format))
                line.name = line.name.replace('#END#', context['next_date'].strftime(format))

            invoice_line_vals = {
                'name': line.name,
                'account_id': account_id,
                'analytics_id': line.analytics_id.id,
                'price_unit': line.price_unit or 0.0,
                'quantity': line.quantity,
                'uos_id': line.uom_id.id or False,
                'product_id': line.product_id.id or False,
                'invoice_id' : invoice_id,
                'invoice_line_tax_id': [(6, 0, tax_id)],
            }
            self.pool.get('account.invoice.line').create(cr, uid, invoice_line_vals, context=context)

        inv_obj.button_compute(cr, uid, [invoice_id], context=context)
        inv_obj.action_date_assign(cr, uid, [invoice_id])
        inv_obj.action_move_create(cr, uid, [invoice_id], context=context)
        inv_obj.action_number(cr, uid, [invoice_id], context=context)
        inv_obj.invoice_validate(cr, uid, [invoice_id], context=context)
        return invoice_id