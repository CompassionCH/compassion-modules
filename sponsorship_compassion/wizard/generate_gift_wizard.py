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
            'product.product', _("Gift Type"), required=True,
            domain=[('name', 'in', GIFT_TYPES)]),
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
        # Id of contract is stored in context
        contract = self.pool.get('recurring.contract').browse(
            cr, uid, context.get('active_id'), ctx)
        wizard = self.browse(cr, uid, ids[0], ctx)
        partner = contract.partner_id

        if contract.child_id and contract.state == 'active':
            invoice_obj = self.pool.get('account.invoice')
            journal_ids = self.pool.get('account.journal').search(
                cr, uid,
                [('type', '=', 'sale'), ('company_id', '=', 1 or False)],
                limit=1)

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
        else:
            raise orm.except_orm(
                _("Generation Error"),
                _("You can only generate gifts for active child "
                  "sponsorships"),
            )

        ir_model_data = self.pool.get('ir.model.data')
        invoice_view_id = ir_model_data.get_object_reference(
            cr, uid, 'account',
            'invoice_form')[1]
        return {
            'name': 'Generated Invoice',
            'view_mode': 'form',
            'view_type': 'form,tree',
            'view_id': invoice_view_id,
            'res_id': invoice_id,  # id of the object to which to redirect
            'res_model': 'account.invoice',  # object name
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
