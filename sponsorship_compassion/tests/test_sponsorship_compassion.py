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


from datetime import datetime
from openerp import netsvc
from openerp.addons.contract_compassion.tests.test_base_module\
    import test_base_module
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
import logging
logger = logging.getLogger(__name__)


class test_sponsorship_compassion(test_base_module):

    def setUp(self):
        super(test_sponsorship_compassion, self).setUp()
        # Creation of an origin
        self.origin_id = self.env['recurring.contract.origin'].create(
            {'type': 'event'}).id
        # Retrieve of income account
        account_obj = self.env['account.account']
        property_account_income = account_obj.search([
            ('type', '=', 'other'),
            ('name', '=', 'Property Account Income Test')]).ids[0]
        property_account_expense = self.env['account.account'].search([
            ('type', '=', 'other'),
            ('name', '=', 'Property Account Expense Test')
        ]).ids[0]
        # Retrieve and modification of products
        product_obj = self.env['product.product']
        self.product_sp = product_obj.search(
            [('name', '=', 'Sponsorship')])[0]
        self.product_gf = product_obj.search(
            [('name', '=', 'General Fund')])[0]
        self.product_bf = product_obj.search(
            [('name', '=', 'Birthday Gift')])[0]
        self.product_fg = product_obj.search(
            [('name', '=', 'Family Gift')])[0]
        self.product_sp.write({
            'property_account_income': property_account_income,
            'property_account_expense': property_account_expense,
            })
        self.product_gf.write({
            'property_account_income': property_account_income,
            'property_account_expense': property_account_expense,
        })
        self.product_bf.write({
            'property_account_income': property_account_income,
            'property_account_expense': property_account_expense,
        })
        self.product_fg.write({
            'property_account_income': property_account_income,
            'property_account_expense': property_account_expense,
        })
        # Add of account for id's 1 product
        product = self.env['product.product'].browse(1)
        product.property_account_income = property_account_income

    def test_sponsorship_compassion_first_scenario(self):
        """
            This first scenario consists in creating a sponsorship contract
            (type 'S') and associate a child to the sponsor.
            Check the different states of the contract and check if there are
            no mistakes.
        """
        # Create a child and get the project associated
        child = self._create_child('PE3760140')
        child.get_infos()
        # Creation of the sponsorship contract
        sp_group = self._create_group(
            'do_nothing', self.partners.ids[0], 1, self.payment_term_id)
        sponsorship_id = self._create_contract(
            datetime.today().strftime(DF), sp_group,
            datetime.today().strftime(DF),
            other_vals={
                'origin_id': self.origin_id,
                'channel': 'postal',
                'type': 'S',
                'child_id': child.id
            }, bool=True)
        self.assertTrue(sponsorship_id)

        # Check if ref and language speaking of partner are set automatically
        partner_obj = self.env['res.partner']
        self.assertTrue(partner_obj.browse(self.partners.ids[0]).ref)
        self.assertTrue(partner_obj.browse(self.partners.ids[0]).lang)

        contract_obj = self.env['recurring.contract']
        sponsorship = contract_obj.browse(sponsorship_id)

        self.assertTrue(sponsorship.contract_line_ids)
        self.assertEqual(len(sponsorship.contract_line_ids), 2)
        self.assertEqual(sponsorship.state, 'draft')
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(
            self.uid, 'recurring.contract',
            sponsorship_id, 'contract_validated', self.cr)
        self.assertEqual(sponsorship.state, 'waiting')
        invoicer_id = sponsorship.button_generate_invoices()
        invoices = invoicer_id.invoice_ids
        self.assertEqual(len(invoices), 2)
        self.assertEqual(invoices[0].state, 'open')
        self._pay_invoice(invoices[0])
        invoice = self.env['account.invoice'].browse(invoices[0].id)
        self.assertEqual(invoice.state, 'paid')
        self.assertEqual(sponsorship.state, 'active')

        # Generate gifts for the child
        gift_wiz_obj = self.env['generate.gift.wizard']
        gift_wiz = gift_wiz_obj.create(
            {
                'product_id': self.product_bf.id,
                'amount': 200.0,
                'invoice_date': datetime.today().strftime(DF),
            })
        gift_inv_ids = gift_wiz.with_context(
            active_ids=[sponsorship.id]).generate_invoice()['domain'][0][2]
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(
            self.uid, 'account.invoice',
            gift_inv_ids[0], 'invoice_open', self.cr)
        gift_inv = self.env['account.invoice'].browse(gift_inv_ids)
        self._pay_invoice(gift_inv[0])
        self.assertEqual(gift_inv[0].state, 'paid')

        # Suspend of the sponsorship contract
        child.project_id.write({'disburse_funds': False})
        invoice1 = self.env['account.invoice'].browse(invoices[1].id)
        self.assertEqual(invoice.state, 'cancel')
        self.assertEqual(invoice1.state, 'cancel')

        # Reactivation of the sponsorship contract
        child.project_id.write({'disburse_funds': True})
        self.assertEqual(invoice.state, 'open')
        self.assertEqual(invoice1.state, 'open')
        wf_service.trg_validate(
            self.uid, 'recurring.contract',
            sponsorship_id, 'contract_terminated', self.cr)
        self.assertTrue(sponsorship.state, 'terminated')
        self.assertEqual(invoice.state, 'cancel')
        self.assertEqual(invoice1.state, 'cancel')

    def test_sponsorship_compassion_second_scenario(self):
        """
            We are testing in this scenario the other type of sponsorship
            contract (type 'SC'). Check if we pass from "draft" state to
            "active" state directly by the validation button. Check if there
            are no invoice lines too.
        """
        child = self._create_child('IO6790211')
        # child.get_infos()
        child.project_id.write({'disburse_funds': True})
        sp_group = self._create_group(
            'do_nothing', self.partners.ids[0], 1, self.payment_term_id)
        sponsorship_id = self._create_contract(
            datetime.today().strftime(DF), sp_group,
            datetime.today().strftime(DF),
            other_vals={
                'origin_id': self.origin_id,
                'channel': 'postal',
                'type': 'SC',
                'child_id': child.id
            }, bool=True)
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(
            self.uid, 'recurring.contract',
            sponsorship_id, 'contract_validated', self.cr)
        contract_obj = self.env['recurring.contract']
        sponsorship = contract_obj.browse(sponsorship_id)
        self.assertEqual(sponsorship.state, 'active')
        self.assertEqual(len(sponsorship.invoice_line_ids), 0)
        wf_service.trg_validate(
            self.uid, 'recurring.contract',
            sponsorship_id, 'contract_terminated', self.cr)
        self.assertTrue(sponsorship.state, 'terminated')

    def test_sponsorship_compassion_third_scenario(self):
        """
            Test of the general contract (type 'O'). It's approximately the
            same test than the contract_compassion's one.
        """
        contract_group = self._create_group(
            'do_nothing', self.partners.ids[0], 1, self.payment_term_id)
        contract_id = self._create_contract(
            datetime.today().strftime(DF), contract_group,
            datetime.today().strftime(DF), other_vals={'type': 'O'}, bool=True)
        self._create_contract_line(
            contract_id, '40.0', other_vals={'quantity': '2'})
        contract_obj = self.env['recurring.contract']
        contract = contract_obj.browse(contract_id)
        self.assertEqual(contract.state, 'draft')

        # Switching to "waiting for payment" state
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(
            self.uid, 'recurring.contract',
            contract_id, 'contract_validated', self.cr)
        self.assertEqual(contract.state, 'waiting')
        invoicer_id = contract.button_generate_invoices()
        invoices = invoicer_id.invoice_ids
        nb_invoices = len(invoices)
        self.assertEqual(nb_invoices, 2)
        self.assertEqual(invoices[0].state, 'open')
        self.assertEqual(invoices[1].state, 'open')
        self._pay_invoice(invoices[0])
        self._pay_invoice(invoices[1])
        self.assertEqual(contract.state, 'active')
        wf_service.trg_validate(
            self.uid, 'recurring.contract',
            contract_id, 'contract_terminated', self.cr)
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
        child1 = self._create_child('UG8320010')
        child2 = self._create_child('UG8320011')
        child3 = self._create_child('UG8320013')
        sp_group = self._create_group(
            'do_nothing', self.partners.ids[0], 1, self.payment_term_id)
        sponsorship_id1 = self._create_contract(
            datetime.today().strftime(DF), sp_group,
            datetime.today().strftime(DF),
            other_vals={
                'origin_id': self.origin_id,
                'channel': 'postal',
                'type': 'S',
                'child_id': child1.id
            }, bool=True)
        sponsorship_id2 = self._create_contract(
            datetime.today().strftime(DF), sp_group,
            datetime.today().strftime(DF),
            other_vals={
                'origin_id': self.origin_id,
                'channel': 'postal',
                'type': 'S',
                'child_id': child2.id
            }, bool=True)
        sponsorship_id3 = self._create_contract(
            datetime.today().strftime(DF), sp_group,
            datetime.today().strftime(DF),
            other_vals={
                'origin_id': self.origin_id,
                'channel': 'postal',
                'type': 'S',
                'child_id': child3.id
            }, bool=True)
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
        contract_obj = self.env['recurring.contract']
        sponsorship1 = contract_obj.browse(sponsorship_id1)
        sponsorship2 = contract_obj.browse(sponsorship_id2)
        sponsorship3 = contract_obj.browse(sponsorship_id3)
        original_price1 = sponsorship1.total_amount
        original_price2 = sponsorship2.total_amount
        original_price3 = sponsorship3.total_amount
        self.assertEqual(sponsorship1.state, 'waiting')
        self.assertEqual(sponsorship2.state, 'waiting')
        self.assertEqual(sponsorship3.state, 'waiting')
        invoicer_id1 = sponsorship1.button_generate_invoices()
        invoices = invoicer_id1.invoice_ids
        self._pay_invoice(invoices[0])
        self._pay_invoice(invoices[1])
        invoice1 = self.env['account.invoice'].browse(invoices[1].id)
        invoice2 = self.env['account.invoice'].browse(invoices[0].id)
        self.assertEqual(
            invoice1.amount_total,
            original_price1 + original_price2 + original_price3)
        self.assertEqual(
            invoice2.amount_total,
            original_price1 + original_price2 + original_price3)
        self.assertEqual(invoice1.state, 'paid')
        self.assertEqual(invoice2.state, 'paid')
        child3.write({'state': 'F'})
        self.assertEqual(child3.state, 'F')
        self.assertEqual(child3.sponsor_id.id, False)
