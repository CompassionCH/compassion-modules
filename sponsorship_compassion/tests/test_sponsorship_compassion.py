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
logger = logging.getLogger(__name__)


class test_sponsorship_compassion(common.TransactionCase):

    def setUp(self):
        super(test_sponsorship_compassion, self).setUp()
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
        property_account_expense = self.registry('account.account').search(
            self.cr, self.uid, [
                ('type', '=', 'other'),
                ('name', '=', 'Property Account Expense Test')
            ])[0]
        # Creation of partners
        partner_obj = self.registry('res.partner')
        self.partner_id = partner_obj.create(self.cr, self.uid, {
            'name': 'Monsieur Pumba',
            'property_account_receivable': property_account_receivable,
            'property_account_payable': property_account_payable,
            'notification_email_send': 'comment',
        })
        # Retrieve a payment term
        payment_term_obj = self.registry('account.payment.term')
        self.payment_term_id = payment_term_obj.search(self.cr, self.uid, [
            ('name', '=', '15 Days')
        ])[0]
        # Retrieve and modification of products
        product_obj = self.registry('product.product')
        self.product_sp_id = product_obj.search(
            self.cr, self.uid, [('name', '=', 'Sponsorship')])[0]
        self.product_gf_id = product_obj.search(
            self.cr, self.uid, [('name', '=', 'General Fund')])[0]
        self.product_bf_id = product_obj.search(
            self.cr, self.uid, [('name', '=', 'Birthday Gift')])[0]
        self.product_fg_id = product_obj.search(
            self.cr, self.uid, [('name', '=', 'Family Gift')])[0]
        product_obj.write(self.cr, self.uid, self.product_sp_id, {
            'property_account_income': property_account_income,
            'property_account_expense': property_account_expense,
            })
        product_obj.write(self.cr, self.uid, self.product_gf_id, {
            'property_account_income': property_account_income,
            'property_account_expense': property_account_expense,
        })
        product_obj.write(self.cr, self.uid, self.product_bf_id, {
            'property_account_income': property_account_income,
            'property_account_expense': property_account_expense,
        })
        product_obj.write(self.cr, self.uid, self.product_fg_id, {
            'property_account_income': property_account_income,
            'property_account_expense': property_account_expense,
        })
        # Creation of an origin
        self.origin_id = self.registry('recurring.contract.origin').create(
            self.cr, self.uid, {'type': 'event'})

    def test_sponsorship_compassion_first_scenario(self):
        """
            This first scenario consists in creating a sponsorship contract
            (type 'S') and associate a child to the sponsor.
            Check the different states of the contract and check if there are
            no mistakes.
        """
        # Create a child and get the project associated
        child_id = self._create_child('PE3760140')
        child = self.registry('compassion.child').browse(
            self.cr, self.uid, child_id)
        child.get_infos()
        child.project_id.write({'disburse_funds': True})

        # Creation of the sponsorship contract
        sp_group = self._create_group(
            'do_nothing', self.partner_id, 1, self.payment_term_id)
        sponsorship_id = self._create_sponsorship(
            datetime.today().strftime(DF), sp_group,
            datetime.today().strftime(DF), self.origin_id, 'postal', 'S',
            child_id)
        self.assertTrue(sponsorship_id)

        # Check if ref and language speaking of partner are set automatically
        partner_obj = self.registry('res.partner')
        self.assertTrue(partner_obj.browse(
            self.cr, self.uid, self.partner_id).ref)
        self.assertTrue(partner_obj.browse(
            self.cr, self.uid, self.partner_id).lang)

        contract_obj = self.registry('recurring.contract')
        sponsorship = contract_obj.browse(
            self.cr, self.uid, sponsorship_id)
        self.assertTrue(sponsorship.contract_line_ids)
        self.assertEqual(len(sponsorship.contract_line_ids), 2)
        self.assertEqual(sponsorship.state, 'draft')
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(
            self.uid, 'recurring.contract',
            sponsorship_id, 'contract_validated', self.cr)
        sponsorship = contract_obj.browse(
            self.cr, self.uid, sponsorship_id)
        self.assertEqual(sponsorship.state, 'waiting')
        invoicer_obj = self.registry('recurring.invoicer')
        invoicer_id = sponsorship.button_generate_invoices()
        invoices = invoicer_obj.browse(
            self.cr, self.uid, invoicer_id).invoice_ids
        self.assertEqual(len(invoices), 2)
        self.assertEqual(invoices[0].state, 'open')
        self._pay_invoice(invoices[1].id)
        invoice = self.registry('account.invoice').browse(
            self.cr, self.uid, invoices[1].id)
        self.assertEqual(invoice.state, 'paid')
        sponsorship = contract_obj.browse(self.cr, self.uid, sponsorship_id)
        self.assertEqual(sponsorship.state, 'active')

        # Generate gifts for the child
        gift_wiz_obj = self.registry('generate.gift.wizard')
        gift_wiz_id = gift_wiz_obj.create(
            self.cr, self.uid, {
                'product_id': self.product_bf_id,
                'amount': 200.0,
                'invoice_date': datetime.today().strftime(DF),
            })
        gift_wiz = gift_wiz_obj.browse(self.cr, self.uid, gift_wiz_id)
        gift_inv_ids = gift_wiz.generate_invoice(
            {'active_ids': [sponsorship_id]})['domain'][0][2]
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(
            self.uid, 'account.invoice',
            gift_inv_ids[0], 'invoice_open', self.cr)
        gift_inv = self.registry('account.invoice').browse(
            self.cr, self.uid, gift_inv_ids)
        self._pay_invoice(gift_inv[0].id)
        self.assertEqual(gift_inv[0].state, 'paid')

        # Suspend of the sponsorship contract
        child.project_id.write({'disburse_funds': False})
        invoice = self.registry('account.invoice').browse(
            self.cr, self.uid, invoices[0].id)
        invoice1 = self.registry('account.invoice').browse(
            self.cr, self.uid, invoices[1].id)
        self.assertEqual(invoice.state, 'cancel')
        self.assertEqual(invoice1.state, 'cancel')

        # Reactivation of the sponsorship contract
        child.project_id.write({'disburse_funds': True})
        invoice = self.registry('account.invoice').browse(
            self.cr, self.uid, invoices[0].id)
        invoice1 = self.registry('account.invoice').browse(
            self.cr, self.uid, invoices[1].id)
        self.assertEqual(invoice.state, 'open')
        self.assertEqual(invoice1.state, 'open')
        wf_service.trg_validate(
            self.uid, 'recurring.contract',
            sponsorship_id, 'contract_terminated', self.cr)
        sponsorship = contract_obj.browse(self.cr, self.uid, sponsorship_id)
        self.assertTrue(sponsorship.state, 'terminated')
        invoice = self.registry('account.invoice').browse(
            self.cr, self.uid, invoices[0].id)
        invoice1 = self.registry('account.invoice').browse(
            self.cr, self.uid, invoices[1].id)
        self.assertEqual(invoice.state, 'cancel')
        self.assertEqual(invoice1.state, 'cancel')

    def test_sponsorship_compassion_second_scenario(self):
        """
            We are testing in this scenario the other type of sponsorship
            contract (type 'SC'). Check if we pass from "draft" state to
            "active" state directly by the validation button. Check if there
            are no invoice lines too.
        """
        child_id = self._create_child('IO6790211')
        child = self.registry('compassion.child').browse(
            self.cr, self.uid, child_id)
        child.get_infos()
        child.project_id.write({'disburse_funds': True})
        sp_group = self._create_group(
            'do_nothing', self.partner_id, 1, self.payment_term_id)
        sponsorship_id = self._create_sponsorship(
            datetime.today().strftime(DF), sp_group,
            datetime.today().strftime(DF), self.origin_id, 'postal', 'SC',
            child_id)
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(
            self.uid, 'recurring.contract',
            sponsorship_id, 'contract_validated', self.cr)
        contract_obj = self.registry('recurring.contract')
        sponsorship = contract_obj.browse(
            self.cr, self.uid, sponsorship_id)
        self.assertEqual(sponsorship.state, 'active')
        self.assertEqual(len(sponsorship.invoice_line_ids), 0)
        wf_service.trg_validate(
            self.uid, 'recurring.contract',
            sponsorship_id, 'contract_terminated', self.cr)
        sponsorship = contract_obj.browse(self.cr, self.uid, sponsorship_id)
        self.assertTrue(sponsorship.state, 'terminated')

    def test_sponsorship_compassion_third_scenario(self):
        """
            Test of the general contract (type 'O'). It's approximately the
            same test than the contract_compassion's one.
        """
        contract_group = self._create_group(
            'do_nothing', self.partner_id, 1, self.payment_term_id)
        contract_id = self._create_contract(
            datetime.today().strftime(DF), contract_group,
            datetime.today().strftime(DF), 'O')
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
        self.assertEqual(nb_invoices, 2)
        self.assertEqual(invoices[0].state, 'open')
        self.assertEqual(invoices[1].state, 'open')
        self._pay_invoice(invoices[1].id)
        self._pay_invoice(invoices[0].id)
        contract = contract_obj.browse(self.cr, self.uid, contract_id)
        self.assertEqual(contract.state, 'active')
        wf_service.trg_validate(
            self.uid, 'recurring.contract',
            contract_id, 'contract_terminated', self.cr)
        contract = contract_obj.browse(
            self.cr, self.uid, contract_id)
        self.assertEqual(contract.state, 'terminated')

    def test_sponsorship_compassion_fourth_scenario(self):
        """
            In this final scenario we are testing the creation of 3 sponsorship
            contracts for the same partner with for each contract one child to
            sponsor.
            We will make a child stop and leave the sponsorship program,
            check if that child have no more sponsor id.
            Check if the 3 contracts create one merged invoice for every month
            (2 months here) with the good values.
        """
        child_id1 = self._create_child('UG8320010')
        child_id2 = self._create_child('UG8320011')
        child_id3 = self._create_child('UG8320013')
        child_obj = self.registry('compassion.child')
        child1 = child_obj.browse(self.cr, self.uid, child_id1)
        child2 = child_obj.browse(self.cr, self.uid, child_id2)
        child3 = child_obj.browse(self.cr, self.uid, child_id3)
        child1.get_infos()
        child2.get_infos()
        child3.get_infos()
        sp_group = self._create_group(
            'do_nothing', self.partner_id, 1, self.payment_term_id)
        sponsorship_id1 = self._create_sponsorship(
            datetime.today().strftime(DF), sp_group,
            datetime.today().strftime(DF), self.origin_id, 'postal', 'S',
            child_id1)
        sponsorship_id2 = self._create_sponsorship(
            datetime.today().strftime(DF), sp_group,
            datetime.today().strftime(DF), self.origin_id, 'postal', 'S',
            child_id2)
        sponsorship_id3 = self._create_sponsorship(
            datetime.today().strftime(DF), sp_group,
            datetime.today().strftime(DF), self.origin_id,
            'postal', 'S', child_id3)
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(
            self.uid, 'recurring.contract',
            sponsorship_id1, 'contract_validated', self.cr)
        wf_service.trg_validate(
            self.uid, 'recurring.contract',
            sponsorship_id2, 'contract_validated', self.cr)
        wf_service.trg_validate(
            self.uid, 'recurring.contract',
            sponsorship_id3, 'contract_validated', self.cr)
        contract_obj = self.registry('recurring.contract')
        sponsorship1 = contract_obj.browse(self.cr, self.uid, sponsorship_id1)
        sponsorship2 = contract_obj.browse(self.cr, self.uid, sponsorship_id2)
        sponsorship3 = contract_obj.browse(self.cr, self.uid, sponsorship_id3)
        original_price1 = sponsorship1.total_amount
        original_price2 = sponsorship2.total_amount
        original_price3 = sponsorship3.total_amount
        self.assertEqual(sponsorship1.state, 'waiting')
        self.assertEqual(sponsorship2.state, 'waiting')
        self.assertEqual(sponsorship3.state, 'waiting')
        invoicer_obj = self.registry('recurring.invoicer')
        invoicer_id1 = sponsorship1.button_generate_invoices()
        invoices = invoicer_obj.browse(
            self.cr, self.uid, invoicer_id1).invoice_ids
        self._pay_invoice(invoices[1].id)
        self._pay_invoice(invoices[0].id)
        invoice1 = self.registry('account.invoice').browse(
            self.cr, self.uid, invoices[1].id)
        invoice2 = self.registry('account.invoice').browse(
            self.cr, self.uid, invoices[0].id)
        self.assertEqual(
            invoice1.amount_total,
            original_price1 + original_price2 + original_price3)
        self.assertEqual(
            invoice2.amount_total,
            original_price1 + original_price2 + original_price3)
        self.assertEqual(invoice1.state, 'paid')
        self.assertEqual(invoice2.state, 'paid')
        child3.write({'state': 'F'})
        child3 = child_obj.browse(self.cr, self.uid, child_id3)
        self.assertEqual(child3.state, 'F')
        self.assertEqual(child3.sponsor_id.id, False)

    def _create_sponsorship(self, start_date, group_id, next_invoice_date,
                            origin_id, channel, type, child_id):
        group = self.registry('recurring.contract.group').browse(
            self.cr, self.uid, group_id)
        partner_id = group.partner_id.id
        sponsorship_id = self.registry('recurring.contract').create(
            self.cr, self.uid, {
                'start_date': start_date,
                'partner_id': partner_id,
                'correspondant_id': partner_id,
                'group_id': group_id,
                'next_invoice_date': next_invoice_date,
                'origin_id': origin_id,
                'channel': channel,
                'type': type,
                'child_id': child_id,
            }, {'default_type': type})
        return sponsorship_id

    def _create_contract(self, start_date, group_id, next_invoice_date, type):
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
            'correspondant_id': partner_id,
            'group_id': group_id,
            'next_invoice_date': next_invoice_date,
            'type': type,
        }, {'default_type': type})
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

    def _create_group(self, change_method, partner_id, adv_biling_months,
                      payment_term_id):
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
            'partner_id': partner_id,
            'advance_billing_months': adv_biling_months,
            'payment_term_id': payment_term_id,
        }
        group.write(group_vals)
        return group_id

    def _create_child(self, code):
        child_id = self.registry('compassion.child').create(
            self.cr, self.uid, {
                'code': code,
            })
        return child_id

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
