# -*- coding: utf-8 -*-
##############################################################################
#
#    Authors: Emanuel Cino
#    Copyright (c) 2014 Compassion Suisse (http://www.compassion.ch)
#    All Rights Reserved
#
#    WARNING: This program as such is intended to be used by professional
#    programmers who take the whole responsibility of assessing all potential
#    consequences resulting from its eventual inadequacies and bugs.
#    End users who are looking for a ready-to-use solution with commercial
#    guarantees and support are strongly advised to contact a Free Software
#    Service Company.
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


from openerp.osv.orm import Model
from openerp.osv import fields
from openerp.addons.account_statement_base_completion.statement import ErrorTooManyPartner
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp import netsvc
import datetime
import time

GIFT_TYPES = ['Birthday Gift', 'General Gift',
              'Family Gift', 'Project Gift', 'Graduation Gift']


class AccountStatementCompletionRule(Model):

    """Add rules to complete account based on the BVR reference of the invoice and the reference of the partner."""

    _inherit = "account.statement.completion.rule"

    def _get_functions(self, cr, uid, context=None):
        res = super(AccountStatementCompletionRule, self)._get_functions(
            cr, uid, context=context)
        res.extend([
            ('get_from_partner_ref',
             'Compassion: From line reference (based on the partner reference)'),
            ('get_from_bvr_ref',
             'Compassion: From line reference (based on the BVR reference of the sponsor)'),
            ('get_from_amount',
             'Compassion: From line amount (based on the amount of the supplier invoice)'),
            ('get_from_lsv_dd', 'Compassion: Put LSV DD Credits in 1098'),
        ])
        return res

    _columns = {
        'function_to_call': fields.selection(_get_functions, 'Method')
    }

    def get_from_partner_ref(self, cr, uid, id, st_line, context=None):
        """
        If line ref match a partner reference, update partner and account
        Then, call the generic st_line method to complete other values.
        :param dict st_line: read of the concerned account.bank.statement.line
        :return:
            A dict of value that can be passed directly to the write method of
            the statement line or {}
           {'partner_id': value,
            'account_id' : value,
            ...}
        """
        ref = st_line['ref'].strip()
        res = {}
        partner_obj = self.pool.get('res.partner')
        partner_ids = partner_obj.search(cr, uid, [(
            'ref', '=', str(int(ref[9:16]))), ('is_company', '=', False)], context=context)

        # Test that only one partner matches.
        partner = None
        if partner_ids:
            if len(partner_ids) == 1:
                partner = partner_obj.browse(
                    cr, uid, partner_ids[0], context=context)
                res['partner_id'] = partner.id
                res['account_id'] = partner.property_account_receivable.id
                # If we fall under this rule of completion, it means there is
                # no open invoice corresponding to the payment. We may need to
                # generate one depending on the payment type.
                res.update(
                    self._generate_invoice(cr, uid, st_line, partner, context=context))
            else:
                raise ErrorTooManyPartner(('Line named "%s" (Ref:%s) was matched by more '
                                           'than one partner while looking on partners') %
                                          (st_line['name'], st_line['ref']))
        return res

    def get_from_bvr_ref(self, cr, uid, id, st_line, context=None):
        """
        If line ref match an invoice BVR Reference, update partner and account
        Then, call the generic st_line method to complete other values.
        :param dict st_line: read of the concerned account.bank.statement.line
        :return:
            A dict of value that can be passed directly to the write method of
            the statement line or {}
           {'partner_id': value,
            'account_id' : value,
            ...}
        """
        ref = st_line['ref'].strip()
        res = {}
        partner = None

        # Search Contract
        contract_obj = self.pool.get('simple.recurring.contract')
        contract_ids = contract_obj.search(
            cr, uid, [('bvr_reference', '=', ref)], context=context)
        if contract_ids:
            partner = contract_obj.browse(
                cr, uid, contract_ids, context=context)[0].partner_id
        else:
            # Search open Customer Invoices (with field 'bvr_reference' set)
            invoice_obj = self.pool.get('account.invoice')
            invoice_ids = invoice_obj.search(
                cr, uid, [('bvr_reference', '=', ref), ('state', '=', 'open')], context=context)
            if not invoice_ids:
                # Search open Supplier Invoices (with field 'reference_type'
                # set to BVR)
                invoice_ids = invoice_obj.search(cr, uid, [(
                    'reference_type', '=', 'bvr'), ('reference', '=', ref), ('state', '=', 'open')], context=context)
            if invoice_ids:
                partner = invoice_obj.browse(
                    cr, uid, invoice_ids, context=context)[0].partner_id

        if partner:
            res['partner_id'] = partner.id
            res['account_id'] = partner.property_account_receivable.id

        return res

    def get_from_amount(self, cr, uid, id, st_line, context=None):
        """ If line amount match an open supplier invoice, update partner and account. """
        amount = float(st_line['amount'])
        res = {}
        # We check only for debit entries
        if amount < 0:
            invoice_obj = self.pool.get('account.invoice')
            invoice_ids = invoice_obj.search(cr, uid, [('type', '=', 'in_invoice'), (
                'state', '=', 'open'), ('amount_total', '=', abs(amount))], context=context)
            res = {}
            if invoice_ids:
                if len(invoice_ids) == 1:
                    invoice = invoice_obj.browse(
                        cr, uid, invoice_ids[0], context=context)
                    res['partner_id'] = invoice.partner_id.id
                    res['account_id'] = invoice.account_id.id
                else:
                    invoices = invoice_obj.browse(
                        cr, uid, invoice_ids, context=context)
                    partner_id = invoices[0].partner_id.id
                    for invoice in invoices:
                        if invoice.partner_id.id != partner_id:
                            raise ErrorTooManyPartner(('Line named "%s" (Ref:%s) was matched by more '
                                                       'than one invoice while looking on open supplier invoices') %
                                                      (st_line['name'], st_line['ref']))
                    res['partner_id'] = partner_id
                    res['account_id'] = invoices[0].account_id.id

        return res

    def get_from_lsv_dd(self, cr, uid, id, st_line, context=None):
        """ If line is a LSV or DD credit, change the account to 1098. """
        label = st_line.get('name', '')
        lsv_dd_strings = [u'BULLETIN DE VERSEMENT',
                          u'ORDRE DEBIT DIRECT',
                          u'Crèdit LSV']
        is_lsv_dd = False
        res = {}
        for credit_string in lsv_dd_strings:
            is_lsv_dd = is_lsv_dd or credit_string in label
        if is_lsv_dd:
            account_id = self.pool.get('account.account').search(
                cr, uid, [('code', '=', '1098')], context=context)
            if account_id:
                res['account_id'] = account_id[0]

        return res

    def _generate_invoice(self, cr, uid, st_line, partner, context=None):
        """ Genereates an invoice corresponding to the statement line read in order to reconcile the corresponding move lines. """
        product = self.pool.get('product.product').browse(cr, uid, self._find_product_id(
            cr, uid, st_line['ref'], context=context), context=context)
        res = {}

        if product.id:
            invoice_obj = self.pool.get('account.invoice')
            journal_ids = self.pool.get('account.journal').search(
                cr, uid, [('type', '=', 'sale'), ('company_id', '=', 1 or False)], limit=1)
            invoicer_id = self.pool.get('account.bank.statement').browse(
                cr, uid, st_line['statement_id'][0], context=context).recurring_invoicer_id.id

            today = datetime.date.today().strftime(DEFAULT_SERVER_DATE_FORMAT)
            pay_term_obj = self.pool.get('account.payment.term')

            inv_data = {
                'account_id': partner.property_account_receivable.id,
                'type': 'out_invoice',
                'partner_id': partner.id,
                'journal_id': len(journal_ids) and journal_ids[0] or False,
                #'currency_id': contract.partner_id.property_product_pricelist.currency_id.id or False,
                'date_invoice': today,
                'payment_term': 1,  # Immediate payment
                'bvr_reference': st_line['ref'],
                'recurring_invoicer_id': invoicer_id,
            }

            invoice_id = invoice_obj.create(cr, uid, inv_data, context=context)
            if invoice_id:
                res.update(self._generate_invoice_line(
                    cr, uid, invoice_id, product, st_line, partner.id, context=context))

                if product.name not in GIFT_TYPES:
                    # Validate the invoice
                    wf_service = netsvc.LocalService('workflow')
                    wf_service.trg_validate(
                        uid, 'account.invoice', invoice_id, 'invoice_open', cr)

        return res

    def _find_product_id(self, cr, uid, ref, context=None):
        """ Finds what kind of payment it is, based on the reference of the statement line. """
        product_obj = self.pool.get('product.product')
        payment_type = int(ref[21])
        product_id = 0
        if payment_type in range(1, 6):
            # Sponsor Gift
            product_ids = product_obj.search(
                cr, uid, [('name_template', '=', GIFT_TYPES[payment_type - 1])], context=context)
            product_id = product_ids[0] if product_ids else 0
        elif payment_type in range(6, 8):
            # Fund donation
            product_ids = product_obj.search(
                cr, uid, [('gp_fund_id', '=', int(ref[22:26]))], context=context)
            product_id = product_ids[0] if product_ids else 0

        return product_id

    def _generate_invoice_line(self, cr, uid, invoice_id, product, st_line, partner_id, context=None):
        inv_line_data = {
            'name': product.name,
            'account_id': product.property_account_income.id,
            'price_unit': st_line['amount'],
            'quantity': 1,
            'uos_id': False,
            'product_id': product.id or False,
            'invoice_id': invoice_id,
        }

        res = {}

        # Define analytic journal
        analytic = self.pool.get('account.analytic.default').account_get(
            cr, uid, product.id, partner_id, uid, time.strftime('%Y-%m-%d'), context=context)
        if analytic and analytic.analytics_id:
            inv_line_data['analytics_id'] = analytic.analytics_id.id

        res['name'] = product.name
        # Get the contract of the sponsor in the case of a gift
        if product.name in GIFT_TYPES:
            contract_obj = self.pool.get('simple.recurring.contract')
            contract_number = int(st_line['ref'][16:21])
            contract_ids = contract_obj.search(
                cr, uid, [('partner_id', '=', partner_id)], context=context)
            if contract_number < len(contract_ids):
                contract = contract_obj.browse(
                    cr, uid, contract_ids[contract_number], context=context)
                inv_line_data['contract_id'] = contract.id
                inv_line_data['name'] = contract.child_id.code
                inv_line_data[
                    'name'] += " - " + contract.child_id.birthdate if product.name == GIFT_TYPES[0] else ""
                res['name'] += " [" + inv_line_data['name'] + "]"
            else:
                res['name'] += " [Child not found] "

        self.pool.get('account.invoice.line').create(
            cr, uid, inv_line_data, context=context)
        return res


class AccountStatement(Model):

    """ Adds a relation to a recurring invoicer. """

    _inherit = 'account.bank.statement'

    _columns = {
        'recurring_invoicer_id': fields.many2one('recurring.invoicer', 'Invoicer'),
    }

    def button_auto_completion(self, cr, uid, ids, context=None):
        invoicer_obj = self.pool.get('recurring.invoicer')
        invoicer_id = invoicer_obj.create(cr, uid, {}, context=context)
        self.write(
            cr, uid, ids, {'recurring_invoicer_id': invoicer_id}, context=context)

        super(AccountStatement, self).button_auto_completion(
            cr, uid, ids, context=context)

        if not invoicer_obj.browse(cr, uid, invoicer_id, context=context).invoice_ids:
            invoicer_obj.unlink(cr, uid, invoicer_id, context=context)

    def button_invoices(self, cr, uid, ids, context=None):
        invoicer_id = self.browse(
            cr, uid, ids[0], context=context).recurring_invoicer_id.id

        return {
            'name': 'Generated Invoices',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'res_model': 'account.invoice',
            'domain': [('recurring_invoicer_id', '=', invoicer_id)],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {'form_view_ref': 'account.invoice_form'},
        }
