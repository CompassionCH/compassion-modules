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
from dateutil.relativedelta import relativedelta
import logging
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
        account_obj = self.env['account.account']
        account_type_obj = self.env['account.account.type']
        account_type = account_type_obj.search([
            ('code', '=', 'receivable')]).ids[0]
        property_account_receivable = account_obj.search([
            ('type', '=', 'receivable'),
            ('user_type', '=', account_type)]).ids[0]
        account_type = account_type_obj.search([
            ('code', '=', 'payable')]).ids[0]
        property_account_payable = account_obj.search([
            ('type', '=', 'payable'),
            ('user_type', '=', account_type)]).ids[0]
        property_account_income = account_obj.search([
            ('type', '=', 'other'),
            ('name', '=', 'Property Account Income Test')]).ids[0]
        # Creation of partners
        partner_obj = self.env['res.partner']
        self.partners = partner_obj.create({
            'name': 'Monsieur Client 197',
            'property_account_receivable': property_account_receivable,
            'property_account_payable': property_account_payable,
            'notification_email_send': 'none',
            'ref': '00001111',
        })
        self.partners += partner_obj.create({
            'name': 'Client 197',
            'property_account_receivable': property_account_receivable,
            'property_account_payable': property_account_payable,
            'notification_email_send': 'none',
            'ref': '00002222',
        })
        # Retrieve a payement term
        payment_term_obj = self.env['account.payment.term']
        self.payment_term_id = payment_term_obj.search([
            ('name', '=', '15 Days')])[0].id
        product = self.env['product.product'].browse(1)
        product.property_account_income = property_account_income

    def test_contract_compassion_first_scenario(self):
        """
            In this test we are testing states changement of a contract and if
            the old invoice are well cancelled when we pay one invoice.
        """
        # Creation of a the next fiscal year
        next_year = (datetime.strptime(
            (datetime.today().strftime(DF)), DF)
            + relativedelta(years=+1)).year
        fiscal_year = self.env['account.fiscalyear'].create({
            'name': next_year,
            'code': next_year,
            'date_start': datetime.strptime((datetime(
                next_year, 1, 1)).strftime(DF), DF),
            'date_stop': datetime.strptime((datetime(
                next_year, 12, 31)).strftime(DF), DF),
            })
        fiscal_year.create_period()
        contract_group = self._create_group(
            'do_nothing', 1, 'month', self.partners.ids[0], 5,
            self.payment_term_id)
        contract = self._create_contract(
            datetime.today().strftime(DF), contract_group,
            'phone', datetime.today().strftime(DF))
        contract_id = contract.id
        self._create_contract_line(
            contract_id, '2', '40.0')

        self.assertEqual(contract.state, 'draft')

        # Switching to "waiting for payment" state
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(
            self.uid, 'recurring.contract',
            contract_id, 'contract_validated', self.cr)
        self.assertEqual(contract.state, 'waiting')

        invoices = contract.button_generate_invoices().invoice_ids
        nb_invoices = len(invoices)
        self.assertEqual(nb_invoices, 6)
        self.assertEqual(invoices[3].state, 'open')

        # Payment of the third invoice so the
        # contract will be on the active state and the 2 first invoices should
        # be canceled.
        self._pay_invoice(invoices[3])
        self.assertEqual(invoices[3].state, 'paid')
        self.assertEqual(invoices[0].state, 'cancel')
        self.assertEqual(invoices[1].state, 'cancel')
        self.assertEqual(invoices[2].state, 'cancel')
        self.assertEqual(invoices[4].state, 'open')
        self.assertEqual(invoices[5].state, 'open')
        self.assertEqual(contract.state, 'active')
        wf_service.trg_validate(
            self.uid, 'recurring.contract',
            contract_id, 'contract_terminated', self.cr)
        self.assertEqual(contract.state, 'terminated')

    def test_contract_compassion_second_scenario(self):
        """
            Testing if invoices are well cancelled when we cancel the related
            contract.
        """
        contract_group = self._create_group(
            'do_nothing', 1, 'month', self.partners.ids[1], 1,
            self.payment_term_id)
        contract = self._create_contract(
            datetime.today().strftime(DF), contract_group, 'postal',
            datetime.today().strftime(DF))
        contract_id = contract.id
        self._create_contract_line(contract_id, '3', '200.0')

        # Switch to "waiting for payment" state
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(
            self.uid, 'recurring.contract',
            contract_id, 'contract_validated', self.cr)
        invoices = contract.button_generate_invoices().invoice_ids
        self.assertEqual(invoices[0].state, 'open')
        self.assertEqual(invoices[1].state, 'open')
        self.assertEqual(len(invoices), 2)

        # Cancelling of the contract
        wf_service.trg_validate(
            self.uid, 'recurring.contract',
            contract_id, 'contract_terminated', self.cr)
        self.assertEqual(contract.state, 'cancelled')
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
            'do_nothing', 1, 'month', self.partners.ids[0], 1,
            self.payment_term_id)
        contract_group2 = self._create_group(
            'do_nothing', 1, 'month', self.partners.ids[1], 2,
            self.payment_term_id)
        contract = self._create_contract(
            datetime.today().strftime(DF), contract_group,
            'postal', datetime.today().strftime(DF))
        contract_id = contract.id
        contract_line = self._create_contract_line(contract_id, '2', '60.0')

        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(
            self.uid, 'recurring.contract',
            contract_id, 'contract_validated', self.cr)
        invoices = contract.button_generate_invoices().invoice_ids
        self._pay_invoice(invoices[0])
        self.assertEqual(len(invoices), 2)

        # Updating of the contract
        contract_line.write({
            'quantity': '3',
            'amount': '100.0',
        })
        contract.write({
            'group_id': contract_group2.id})

        # Check if the invoice unpaid is well updated
        invoice_upd = invoices[1]
        invoice_line_up = invoice_upd.invoice_line[0]
        self.assertEqual(invoice_line_up.price_unit, contract_line.amount)
        self.assertEqual(
            invoice_line_up.price_subtotal, contract_line.subtotal)

    def _create_contract(self, start_date, group, channel,
                         next_invoice_date):
        """
            Create a contract. For that purpose we have created a partner
            to get his id.
        """
        # Creation of a contract
        contract_obj = self.env['recurring.contract']
        partner_id = group.partner_id.id
        return contract_obj.create({
            'start_date': start_date,
            'partner_id': partner_id,
            'group_id': group.id,
            'channel': channel,
            'next_invoice_date': next_invoice_date,
            'type': 'O',
        })

    def _create_contract_line(self, contract_id, quantity, price):
        """ Create contract's lines """
        return self.env['recurring.contract.line'].create({
            'product_id': 1,
            'amount': price,
            'quantity': quantity,
            'contract_id': contract_id,
        })

    def _create_group(self, change_method, rec_value, rec_unit, partner_id,
                      adv_biling_months, payment_term_id, ref=None):
        """
            Create a group with 2 possibilities :
                - ref is not given so it takes "/" default values
                - ref is given
        """
        group_obj = self.env['recurring.contract.group']
        group_vals = {
            'partner_id': partner_id,
            'change_method': change_method,
            'recurring_value': rec_value,
            'recurring_unit': rec_unit,
            'partner_id': partner_id,
            'advance_billing_months': adv_biling_months,
            'payment_term_id': payment_term_id,
        }
        if ref:
            group_vals['ref'] = ref
        return group_obj.create(group_vals)

    def _pay_invoice(self, invoice):
        bank_journal = self.env['account.journal'].search(
            [('code', '=', 'TBNK')])[0]
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        account_id = invoice.partner_id.property_account_receivable.id
        move = move_obj.create({
            'journal_id': bank_journal.id
        })
        move_line_obj.create({
            'name': 'BNK-' + invoice.number,
            'move_id': move.id,
            'partner_id': invoice.partner_id.id,
            'account_id': bank_journal.default_debit_account_id.id,
            'debit': invoice.amount_total,
            'journal_id': bank_journal.id,
            'period_id': invoice.period_id.id,
            'date': invoice.date_due
        })
        mv_line = move_line_obj.create({
            'name': 'PAY-' + invoice.number,
            'move_id': move.id,
            'partner_id': invoice.partner_id.id,
            'account_id': account_id,
            'credit': invoice.amount_total,
            'journal_id': invoice.journal_id.id,
            'period_id': invoice.period_id.id,
            'date': invoice.date_due
        })
        move.button_validate()
        to_reconcile = move_line_obj.search([
            ('move_id', '=', invoice.move_id.id),
            ('account_id', '=', account_id)]) + mv_line
        to_reconcile.reconcile()
