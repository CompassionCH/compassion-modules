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

from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp.osv import orm, fields
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools.translate import _

import logging
logger = logging.getLogger(__name__)

class contract_group(orm.Model):
    _name = 'simple.recurring.contract.group'
    _desc = 'A group of contracts'

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        res = [(gr.id, gr.payment_term_id.name) for gr in self.browse(
               cr, uid, ids, context)]
        return res

    def _get_next_invoice_date(self, cr, uid, ids, name, args, context=None):
        res = {}
        for group in self.browse(cr, uid, ids, context):
            res[group.id] = min(
                [c.next_invoice_date for c in group.contract_ids])

        return res

    def _get_groups_from_contract(self, cr, uid, ids, context=None):
        group_ids = set()
        contract_obj = self.pool.get('simple.recurring.contract')
        for contract in contract_obj.browse(cr, uid, ids, context):
            group_ids.add(contract.group_id.id)
        return list(group_ids)

    _columns = {
        # TODO sequence for name/ref ?
        'recurring_unit': fields.selection([
            ('day', _('Day(s)')),
            ('week', _('Week(s)')),
            ('month', _('Month(s)')),
            ('year', _('Year(s)'))], _('Reccurency'), required=True),
        'recurring_value': fields.integer(
            _('Generate every'), required=True),
        'partner_id': fields.many2one(
            'res.partner', _('Partner'), required=True,
            ondelete='cascade'),
        'contract_ids': fields.one2many(
            'simple.recurring.contract', 'group_id', _('Contracts'),
            readonly=True),
        'advance_billing': fields.selection([
            ('bimonthly', _('Bimonthly')),
            ('quarterly', _('Quarterly')),
            ('fourmonthly', _('Four-monthly')),
            ('biannual', _('Bi-annual')),
            ('annual', _('Annual'))], _('Advance billing'),
            help = _('Advance billing allows you to generate invoices in '
                     'advance. For example, you can generate the invoices '
                     'for each month of the year and send them to the '
                     'customer in january.')),
        'payment_term_id': fields.many2one('account.payment.term',
                                           _('Payment Term')),
        'next_invoice_date': fields.function(
            _get_next_invoice_date, type='date',
            string=_('Smallest invoice date for related contracts'),
            store={
                'simple.recurring.contract': (
                    _get_groups_from_contract, ['next_invoice_date'], 20),
                }),
    }

    _defaults = {
        'recurring_unit': 'month',
        'recurring_value': 1,
    }

    def generate_invoices(self, cr, uid, ids, invoicer_id=None,
                          is_group=False, context=None):
        ''' Checks all contracts and generate invoices if needed.
        Create an invoice per contract group per date.
        '''
        inv_obj = self.pool.get('account.invoice')
        journal_obj = self.pool.get('account.journal')
        contract_obj = self.pool.get('simple.recurring.contract')

        if not ids:
            ids = self.search(cr, uid, [], context=context)
        
        journal_ids = journal_obj.search(
            cr, uid, [('type', '=','sale'),('company_id', '=', 1 or False)],
            limit=1)
        delay_dict = {'annual': 12, 'biannual': 6, 'fourmonthly': 4,
                      'quarterly': 3, 'bimonthly' : 2}
        # Invoice lines are generated for an active contract
        # If group.next_inv_date <= today
        #   and contr.next_inv_date <= group.next_inv_date
        #   or (group.next_inv_date > today
        #      and contr.next_inv_date <= group.next_inv_date + adv_billing
        #      and contract had an invoice generated in the process)
        #
        # The last condition ensures that we won't start to do advance billing
        # for contract who had initial next_invoice_date > today.
        for group_id in ids:
            adv_bill_candidate = set()
            contract_group = self.browse(cr, uid, group_id, context)
            month_delta = contract_group.advance_billing and \
                            delay_dict[contract_group.advance_billing] or 0
            limit_date = datetime.today() + relativedelta(months=+month_delta)
            while True: # Emulate a do-while loop
                # contract_group update 'cause next_inv_date has been modified
                contract_group = self.browse(cr, uid, group_id, context)
                group_inv_date = contract_group.next_invoice_date
                if datetime.strptime(group_inv_date, DF) <= datetime.today():
                    contr_ids = [c.id
                                 for c in contract_group.contract_ids
                                 if c.next_invoice_date <= group_inv_date
                                 and c.state in self._get_gen_states()]
                    adv_bill_candidate.update(contr_ids)
                else:
                    contr_ids = [c.id
                                 for c in contract_group.contract_ids
                                 if datetime.strptime(c.next_invoice_date, DF)\
                                    <= limit_date
                                 and c.id in adv_bill_candidate
                                 and c.state in self._get_gen_states()]

                if not contr_ids:
                    break

                inv_data = self._setup_inv_data(cr, uid, contract_group,
                                                journal_ids, invoicer_id,
                                                context=context)
                invoice_id = inv_obj.create(cr, uid, inv_data, context=context)

                for contract in contract_obj.browse(cr, uid, contr_ids, context):
                    self._generate_invoice_lines(cr, uid, contract, invoice_id,
                                                 context)
                inv_obj.button_compute(cr, uid, [invoice_id], context=context)

    def _setup_inv_data(self, cr, uid, con_gr, journal_ids,
                        invoicer_id, context=None):
        ''' Setup a dict with data passed to invoice.create.
            If any custom data is wanted in invoice from contract group, just
            inherit this method.
        '''
        today = datetime.today().strftime(DF)
        partner = con_gr.partner_id

        inv_data = {
            'account_id': partner.property_account_receivable.id,
            'type': 'out_invoice',
            'partner_id': partner.id,
            'journal_id': len(journal_ids) and journal_ids[0] or False,
            'currency_id': partner.property_product_pricelist.currency_id.id \
                            or False,
            'date_invoice': con_gr.next_invoice_date,
            'recurring_invoicer_id': invoicer_id,
            'payment_term': con_gr.payment_term_id \
                                and con_gr.payment_term_id.id or False,
            }

        return inv_data

    def _setup_inv_line_data(self, cr, uid, contract_line, invoice_id,
                             context=None):
        ''' Setup a dict with data passed to invoice_line.create.
        If any custom data is wanted in invoice line from contract,
        just inherit this method.
        '''
        product = contract_line.product_id

        inv_line_data = {
            'name': product.name,
            'account_id': product.property_account_income.id,
            'price_unit': contract_line.amount or 0.0,
            'quantity': contract_line.quantity,
            'uos_id': False,
            'product_id': product.id or False,
            'invoice_id' : invoice_id,
            'contract_id': contract_line.contract_id.id,
        }

        return inv_line_data

    def _generate_invoice_lines(self, cr, uid, contract, invoice_id,
                               context=None):
        inv_line_obj = self.pool.get('account.invoice.line')
        for contract_line in contract.contract_line_ids:
            inv_line_data = self._setup_inv_line_data(cr, uid, contract_line,
                                                      invoice_id, context)
            inv_line_obj.create(cr, uid, inv_line_data, context=context)

        vals = {}

        contract_obj = self.pool.get('simple.recurring.contract')
        next_date = contract_obj._compute_next_invoice_date(contract)
        vals['next_invoice_date'] = next_date.strftime(DF)

        contract_obj.write(cr, uid, [contract.id], vals)

    def _get_gen_states(self):
        return ['active']
