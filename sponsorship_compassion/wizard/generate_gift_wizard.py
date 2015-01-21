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

from openerp.osv import orm, fields
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools import mod10r
from openerp.tools.translate import _

from ..model.product import GIFT_TYPES
from datetime import datetime
import time


class generate_gift_wizard(orm.TransientModel):
    """ This wizard generates a Gift Invoice for a given contract. """
    _name = 'generate.gift.wizard'

    _columns = {
        'amount': fields.float(_("Gift Amount"), required=True),
        'product_id': fields.many2one(
            'product.product', _("Gift Type"), required=True),
        'invoice_date': fields.date(_("Invoice date")),
        'description': fields.char(_("Additional comments"), size=200),
    }

    _defaults = {
        'invoice_date': datetime.today().strftime(DF),
    }

    def generate_invoice(self, cr, uid, ids, context=None):
        # Read data in english
        if context is None:
            context = {}
        ctx = context.copy()
        ctx['lang'] = 'en_US'
        # Ids of contracts are stored in context
        wizard = self.browse(cr, uid, ids[0], ctx)
        invoice_ids = list()
        for contract in self.pool.get('recurring.contract').browse(
                cr, uid, context.get('active_ids', list()), ctx):
            partner = contract.partner_id

            if contract.child_id and contract.state == 'active':
                invoice_obj = self.pool.get('account.invoice')
                journal_ids = self.pool.get('account.journal').search(
                    cr, uid,
                    [('type', '=', 'sale'), ('company_id', '=', 1 or False)],
                    limit=1)

                if wizard.product_id.name == GIFT_TYPES[0]:   # Birthday Gift
                    invoice_date = self.compute_date_birthday_invoice(
                        contract.child_id.birthdate, wizard.invoice_date)
                else:
                    invoice_date = wizard.invoice_date

                inv_data = {
                    'account_id': partner.property_account_receivable.id,
                    'type': 'out_invoice',
                    'partner_id': partner.id,
                    'journal_id': len(journal_ids) and journal_ids[0] or False,
                    'date_invoice': wizard.invoice_date,
                    'payment_term': 1,  # Immediate payment
                    'bvr_reference': self._generate_bvr_reference(
                        contract, wizard.product_id),
                }

                invoice_id = invoice_obj.create(cr, uid, inv_data,
                                                context=context)
                if invoice_id:
                    self._generate_invoice_line(
                        cr, uid, invoice_id, wizard, contract, context=ctx)
                    invoice_ids.append(invoice_id)
            else:
                raise orm.except_orm(
                    _("Generation Error"),
                    _("You can only generate gifts for active child "
                      "sponsorships"))
        return {
            'name': _('Generated Invoices'),
            'view_mode': 'tree,form',
            'view_type': 'form',
            'res_model': 'account.invoice',
            'domain': [('id', 'in', invoice_ids)],
            'context': {'form_view_ref': 'account.invoice_form'},
            'type': 'ir.actions.act_window',
        }

    def _generate_invoice_line(self, cr, uid, invoice_id, wizard,
                               contract, context=None):
        product = wizard.product_id

        inv_line_data = {
            'name': wizard.description,
            'account_id': product.property_account_income.id,
            'price_unit': wizard.amount,
            'quantity': 1,
            'uos_id': False,
            'product_id': product.id or False,
            'invoice_id': invoice_id,
            'contract_id': contract.id,
        }

        # Define analytic journal
        analytic = self.pool.get('account.analytic.default').account_get(
            cr, uid, product.id, contract.partner_id.id, uid,
            time.strftime(DF), context=context)
        if analytic and analytic.analytics_id:
            inv_line_data['analytics_id'] = analytic.analytics_id.id

        # Give a better name to invoice_line
        if not wizard.description:
            inv_line_data['name'] = contract.child_id.code
            inv_line_data['name'] += " - " + contract.child_id.birthdate \
                if product.name == 'Birthday Gift' else ""

        self.pool.get('account.invoice.line').create(
            cr, uid, inv_line_data, context=context)

        return True

    def _generate_bvr_reference(self, contract, product):
        ref = contract.partner_id.ref
        bvr_reference = '0' * (9 + (7 - len(ref))) + ref
        num_pol_ga = str(contract.num_pol_ga)
        bvr_reference += '0' * (5 - len(num_pol_ga)) + num_pol_ga
        # Type of gift
        bvr_reference += str(GIFT_TYPES.index(product.name)+1)
        bvr_reference += '0' * 4

        if len(bvr_reference) == 26:
            return mod10r(bvr_reference)

    def fields_view_get(self, cr, user, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        """ Dynamically compute the domain of field product_id to return
        only Gifts products.
        """
        res = super(generate_gift_wizard, self).fields_view_get(
            cr, user, view_id, view_type, context, toolbar, submenu)
        if view_type == 'form':
            gifts_ids = self.pool.get('product.product').search(
                cr, user, [('name', 'in', GIFT_TYPES)],
                context={'lang': 'en_US'})
            res['fields']['product_id']['domain'] = [('id', 'in', gifts_ids)]

        return res

    def compute_date_birthday_invoice(self, child_birthdate, payment_date):
        """Set date of invoice two months before child's birthdate"""
        inv_date = datetime.strptime(payment_date, DF)
        birthdate = datetime.strptime(child_birthdate, DF)
        new_date = inv_date
        if birthdate.month >= inv_date.month + 2:
            new_date = inv_date.replace(day=28, month=birthdate.month-2)
        elif birthdate.month + 3 < inv_date.month:
            new_date = birthdate.replace(
                day=28, year=inv_date.year+1) + relativedelta(months=-2)
            new_date = max(new_date, inv_date)
        return new_date.strftime(DF)
