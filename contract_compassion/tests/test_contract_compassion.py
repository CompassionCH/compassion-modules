# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Albert SHENOUDA <albert.shenouda@efrei.net>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.tests import common
from datetime import datetime
from openerp import netsvc
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
import logging
import pdb
logger = logging.getLogger(__name__)


class test_contract_compassion(common.TransactionCase):
    """
        Test Project contract compassion.
        We are testing 3 scenarios :
         - in the first, we are testing the changement of state of a contract
         and we are testing what is happening when we pay an invoice.
         - in the second one, we are testing what is happening when we cancel
         a contract.
         - in the last one, we are testing the _reset_open_invoices method.
    """

    def setUp(self):
        super(test_contract_compassion, self).setUp()
        # Retrieve receivable and payable accounts
        account_type = self.registry('account.account.type').search(
            self.cr, self.uid, [
                ('code', '=', 'receivable'),
            ])[0]
        property_account_receivable = self.registry('account.account').search(
            self.cr, self.uid, [
                ('type', '=', 'receivable'),
                ('user_type', '=', account_type)
            ])[0]
        account_type = self.registry('account.account.type').search(
            self.cr, self.uid, [
                ('code', '=', 'payable'),
            ])[0]
        property_account_payable = self.registry('account.account').search(
            self.cr, self.uid, [
                ('type', '=', 'payable'),
                ('user_type', '=', account_type)])[0]
        property_account_income = self.registry('account.account').search(
            self.cr, self.uid, [
                ('type', '=', 'other'),
                ('name', '=', 'Property Account Income Test')
            ])[0]
        # Creation of partners
        partner_obj = self.registry('res.partner')
        self.partner_id = partner_obj.create(self.cr, self.uid, {
            'name': 'Monsieur Client 197',
            'property_account_receivable': property_account_receivable,
            'property_account_payable': property_account_payable,
            'notification_email_send': 'none',
            'ref': '00001111',
        })
        self.partner_id1 = partner_obj.create(self.cr, self.uid, {
            'name': 'Client 197',
            'property_account_receivable': property_account_receivable,
            'property_account_payable': property_account_payable,
            'notification_email_send': 'none',
            'ref': '00002222',
        })
        # Retrieve a payement term
        payment_term_obj = self.registry('account.payment.term')
        self.payment_term_id = payment_term_obj.search(self.cr, self.uid, [
            ('name', '=', '15 Days')
        ])[0]
        product_obj = self.registry('product.product')
        product_obj.write(self.cr, self.uid, 1, {
            'property_account_income': property_account_income,
            })

    def test_contract_compassion_first_scenario(self):
        """
            In this test we are testing states changement of a contract and if
            the old invoice are well cancelled when we pay one invoice.
        """
        current_year = str(int(datetime.today().strftime(DF)[:4]) + 1)        
        fiscal_year_id = self.registry('account.fiscalyear').create(
            self.cr, self.uid, {
                'name': current_year,
                'code': current_year,
                'date_start': str(datetime(
                    int(datetime.today().strftime(DF)[:4]) + 1, 1, 1)),
                'date_stop': str(datetime(
                    int(datetime.today().strftime(DF)[:4]) + 1, 12, 31)),
            })
        fiscal_year = self.registry('account.fiscalyear').browse(
            self.cr, self.uid, [fiscal_year_id])    
        fiscal_year[0].create_period()
        contract_group = self._create_group(
            'do_nothing', 1, 'month', self.partner_id, 5, self.payment_term_id)
        contract_id = self._create_contract(
            datetime.today().strftime(DF), contract_group,
            'phone', datetime.today().strftime(DF))
        self._create_contract_line(
            contract_id, '2', '40.0')
    
        contract_obj = self.registry('recurring.contract')
        contract = contract_obj.browse(self.cr, self.uid, contract_id)
        self.assertEqual(contract.state, 'draft')

        # Switching to "waiting for payment" state
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(
            self.uid, 'recurring.contract',
            contract_id, 'contract_validated', self.cr)
        contract = contract_obj.browse(
            self.cr, self.uid, contract_id)
        self.assertEqual(contract.state, 'waiting')
        invoicer_obj = self.registry('recurring.invoicer')
        invoicer_id = contract.button_generate_invoices()
        invoices = invoicer_obj.browse(
            self.cr, self.uid, invoicer_id).invoice_ids
        nb_invoices = len(invoices)
        self.assertEqual(nb_invoices, 6)
        self.assertEqual(invoices[3].state, 'open')
        # Payment of the third invoice so the
        # contract will be on the active state and the 2 first invoices should
        # be canceled.
        self._pay_invoice(invoices[3].id)
        invoices = invoicer_obj.browse(
            self.cr, self.uid, invoicer_id).invoice_ids
        contract = contract_obj.browse(self.cr, self.uid, contract_id)
        self.assertEqual(invoices[3].state, 'paid')
        self.assertEqual(invoices[0].state, 'open')
        self.assertEqual(invoices[1].state, 'open')
        self.assertEqual(invoices[2].state, 'open')
        self.assertEqual(invoices[4].state, 'cancel')
        self.assertEqual(invoices[5].state, 'cancel')
        self.assertEqual(contract.state, 'active')
        wf_service.trg_validate(
            self.uid, 'recurring.contract',
            contract_id, 'contract_terminated', self.cr)
        contract = contract_obj.browse(
            self.cr, self.uid, contract_id)
        self.assertEqual(contract.state, 'terminated')

    def test_contract_compassion_second_scenario(self):
        """
            Testing if invoices are well cancelled when we cancel the related
            contract.
        """
        contract_group = self._create_group(
            'do_nothing', 1, 'month', self.partner_id1, 1,
            self.payment_term_id)
        contract_id = self._create_contract(
            datetime.today().strftime(DF), contract_group, 'postal',
            datetime.today().strftime(DF))
        self._create_contract_line(
            contract_id, '3', '200.0')

        # Switch to "waiting for payment" state
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(
            self.uid, 'recurring.contract',
            contract_id, 'contract_validated', self.cr)
        contract_obj = self.registry('recurring.contract')
        contract = contract_obj.browse(
            self.cr, self.uid, contract_id)
        invoicer_obj = self.registry('recurring.invoicer')
        invoicer_id = contract.button_generate_invoices()
        invoices = invoicer_obj.browse(
            self.cr, self.uid, invoicer_id).invoice_ids
        self.assertEqual(invoices[0].state, 'open')
        self.assertEqual(invoices[1].state, 'open')
        self.assertEqual(len(invoices), 2)

        # Cancelling of the contract
        wf_service.trg_validate(
            self.uid, 'recurring.contract',
            contract_id, 'contract_terminated', self.cr)
        contract = contract_obj.browse(
            self.cr, self.uid, contract_id)
        self.assertEqual(contract.state, 'cancelled')
        invoices = invoicer_obj.browse(
            self.cr, self.uid, invoicer_id).invoice_ids
        self.assertEqual(invoices[0].state, 'cancel')
        self.assertEqual(invoices[1].state, 'cancel')

    def test_reset_open_invoices(self):
        """
            Testing of the method that update invoices when the contract
            is updated.
            THe invoice paid should not be updated, whereas the other one
            should be upadted.
        """
        contract_group = self._create_group(
            'do_nothing', 1, 'month', self.partner_id, 1,
            self.payment_term_id)
        contract_group2 = self._create_group(
            'do_nothing', 1, 'month', self.partner_id1, 2,
            self.payment_term_id)
        contract_id = self._create_contract(
            datetime.today().strftime(DF), contract_group,
            'postal', datetime.today().strftime(DF))
        contract_line_id = self._create_contract_line(
            contract_id, '2', '60.0')

        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(
            self.uid, 'recurring.contract',
            contract_id, 'contract_validated', self.cr)
        contract_obj = self.registry('recurring.contract')
        contract = contract_obj.browse(
            self.cr, self.uid, contract_id)
        invoicer_obj = self.registry('recurring.invoicer')
        invoicer_id = contract.button_generate_invoices()
        invoices = invoicer_obj.browse(
            self.cr, self.uid, invoicer_id).invoice_ids
        self._pay_invoice(invoices[1].id)
        self.assertEqual(len(invoices), 2)

        # Updating of the contract
        contract_line_obj = self.registry('recurring.contract.line')
        contract_line_obj.write(
            self.cr, self.uid, contract_line_id, {
                'quantity': '3',
                'amount': '100.0',
            })
        contract_obj.write(
            self.cr, self.uid, contract_id, {
                'group_id': contract_group2,
            })
        ctr_line_id = contract_line_obj.browse(
            self.cr, self.uid, contract_line_id)

        # Check if the invoice unpaid is well updated
        invoice_obj = self.registry('account.invoice')
        invoice_upd = invoice_obj.browse(self.cr, self.uid, invoices[0].id)
        invoice_line_up = self.registry('account.invoice.line').browse(
            self.cr, self.uid, invoice_upd.invoice_line[0].id)
        self.assertEqual(invoice_line_up.price_unit, ctr_line_id.amount)
        self.assertEqual(invoice_line_up.price_subtotal, ctr_line_id.subtotal)

    def _create_contract(self, start_date, group_id, channel,
                         next_invoice_date):
        """
            Create a contract. For that purpose we have created a partner
            to get his id.
        """
        # Creation of a contract
        contract_obj = self.registry('recurring.contract')
        group_obj = self.registry('recurring.contract.group')
        group = group_obj.browse(self.cr, self.uid, group_id)
        partner_id = group.partner_id.id
        contract_id = contract_obj.create(self.cr, self.uid, {
            'start_date': start_date,
            'partner_id': partner_id,
            'group_id': group_id,
            'channel': channel,
            'next_invoice_date': next_invoice_date,
            'type': 'O',
        })
        return contract_id

    def _create_contract_line(self, contract_id, quantity, price):
        """ Create contract's lines """
        contract_line_obj = self.registry('recurring.contract.line')
        contract_line_id = contract_line_obj.create(self.cr, self.uid, {
            'product_id': 1,
            'amount': price,
            'quantity': quantity,
            'contract_id': contract_id,
        })
        return contract_line_id

    def _create_group(self, change_method, rec_value, rec_unit, partner_id,
                      adv_biling_months, payment_term_id, ref=None):
        """
            Create a group with 2 possibilities :
                - ref is not given so it takes "/" default values
                - ref is given
        """
        group_obj = self.registry('recurring.contract.group')
        group_id = group_obj.create(self.cr, self.uid, {
            'partner_id': partner_id,
        })
        group = group_obj.browse(self.cr, self.uid, group_id)
        group_vals = {
            'change_method': change_method,
            'recurring_value': rec_value,
            'recurring_unit': rec_unit,
            'partner_id': partner_id,
            'advance_billing_months': adv_biling_months,
            'payment_term_id': payment_term_id,
        }
        if ref:
            group_vals['ref'] = ref
        group.write(group_vals)
        return group_id

    def _pay_invoice(self, invoice_id):
        journal_obj = self.registry('account.journal')
        bank_journal_id = self.registry('account.journal').search(
            self.cr, self.uid, [('code', '=', 'TBNK')])[0]
        bank_journal = journal_obj.browse(self.cr, self.uid, bank_journal_id)
        move_obj = self.registry('account.move')
        move_line_obj = self.registry('account.move.line')
        invoice = self.registry('account.invoice').browse(
            self.cr, self.uid, invoice_id)
        account_id = invoice.partner_id.property_account_receivable.id
        move_id = move_obj.create(self.cr, self.uid, {
            'journal_id': bank_journal_id
        })
        move_line_obj.create(self.cr, self.uid, {
            'name': 'BNK-' + invoice.number,
            'move_id': move_id,
            'partner_id': invoice.partner_id.id,
            'account_id': bank_journal.default_debit_account_id.id,
            'debit': invoice.amount_total,
            'journal_id': bank_journal_id,
            'period_id': invoice.period_id.id,
            'date': invoice.date_due
        })
        mv_line_id = move_line_obj.create(self.cr, self.uid, {
            'name': 'PAY-' + invoice.number,
            'move_id': move_id,
            'partner_id': invoice.partner_id.id,
            'account_id': account_id,
            'credit': invoice.amount_total,
            'journal_id': invoice.journal_id.id,
            'period_id': invoice.period_id.id,
            'date': invoice.date_due
        })
        move_obj.button_validate(self.cr, self.uid, [move_id])
        to_reconcile = move_line_obj.search(self.cr, self.uid, [
            ('move_id', '=', invoice.move_id.id),
            ('account_id', '=', account_id)]) + [mv_line_id]
        move_line_obj.reconcile(self.cr, self.uid, to_reconcile)
