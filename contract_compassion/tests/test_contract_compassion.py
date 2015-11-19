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


from test_base_module import test_base_module
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp import fields
import logging
logger = logging.getLogger(__name__)


class test_contract_compassion(test_base_module):
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
        category = self.env['res.partner.category'].create({
            'name': 'sponsor'})
        self.partners.write({'category_id': [(4, category.id)]})

    def test_contract_compassion_first_scenario(self):
        """
            In this test we are testing states changement of a contract and if
            the old invoice are well cancelled when we pay one invoice.
        """
        contract_group = self._create_group(
            'do_nothing', self.partners.ids[0], 5,
            self.payment_term_id,
            other_vals={'recurring_value': 1, 'recurring_unit': 'month'})
        contract = self._create_contract(
            datetime.today().strftime(DF), contract_group,
            datetime.today().strftime(DF),
            other_vals={'channel': 'phone', 'type': 'O'})
        self._create_contract_line(
            contract.id, '40.0', other_vals={'quantity': '2'})
        self.assertEqual(contract.state, 'draft')

        # Switching to "waiting for payment" state
        contract.signal_workflow('contract_validated')
        self.assertEqual(contract.state, 'waiting')

        invoices = contract.button_generate_invoices().invoice_ids
        nb_invoices = len(invoices)
        self.assertEqual(nb_invoices, 6)
        self.assertEqual(invoices[3].state, 'open')

        # Payment of the third invoice so the
        # contract will be on the active state and the 2 first invoices should
        # be cancelled.
        self._pay_invoice(invoices[3])
        self.assertEqual(invoices[3].state, 'paid')
        self.assertEqual(invoices[0].state, 'cancel')
        self.assertEqual(invoices[1].state, 'cancel')
        self.assertEqual(invoices[2].state, 'cancel')
        self.assertEqual(invoices[4].state, 'open')
        self.assertEqual(invoices[5].state, 'open')
        self.assertEqual(contract.state, 'active')
        contract.signal_workflow('contract_terminated')
        self.assertEqual(contract.state, 'terminated')

    def test_contract_compassion_second_scenario(self):
        """
            Testing if invoices are well cancelled when we cancel the related
            contract.
        """
        contract_group = self._create_group(
            'do_nothing', self.partners.ids[1], 1,
            self.payment_term_id,
            other_vals={'recurring_value': 1, 'recurring_unit': 'month'})
        contract = self._create_contract(
            datetime.today().strftime(DF), contract_group,
            datetime.today().strftime(DF),
            other_vals={'channel': 'postal', 'type': 'O'})
        self._create_contract_line(
            contract.id, '200.0', other_vals={'quantity': '3'})
        # Switch to "waiting for payment" state
        contract.signal_workflow('contract_validated')
        invoices = contract.button_generate_invoices().invoice_ids
        self.assertEqual(invoices[0].state, 'open')
        self.assertEqual(invoices[1].state, 'open')
        self.assertEqual(len(invoices), 2)

        # Cancelling of the contract
        date_finish = fields.Datetime.now()
        contract.signal_workflow('contract_terminated')
        # Check a job for cleaning invoices has been created
        self.assertTrue(self.env['queue.job'].search([
            ('name', '=', 'Job for cleaning invoices of contracts.'),
            ('date_created', '>=', date_finish)]))
        # Force cleaning invoices immediatley
        contract._clean_invoices()
        self.assertEqual(contract.state, 'cancelled')
        self.assertEqual(invoices[0].state, 'cancel')
        self.assertEqual(invoices[1].state, 'cancel')

    def test_reset_open_invoices(self):
        """
            Testing of the method that update invoices when the contract
            is updated.
            THe invoice paid should not be updated, whereas the other one
            should be updated.
        """
        contract_group = self._create_group(
            'do_nothing', self.partners.ids[0], 1,
            self.payment_term_id,
            other_vals={'recurring_value': 1, 'recurring_unit': 'month'})
        contract_group2 = self._create_group(
            'do_nothing', self.partners.ids[1], 2,
            self.payment_term_id,
            other_vals={'recurring_value': 1, 'recurring_unit': 'month'})
        contract = self._create_contract(
            datetime.today().strftime(DF), contract_group,
            datetime.today().strftime(DF),
            other_vals={'channel': 'postal', 'type': 'O'})
        contract_line = self._create_contract_line(
            contract.id, '60.0', other_vals={'quantity': '2'})
        contract.signal_workflow('contract_validated')
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

    def test_contract_compassion_third_scenario(self):
        """
            Test the changement of a partner in a payment option and after that
            changement test if the BVR reference is set.
            Test the changement of the payment term and set it to the BVR one
            and check if the payment option of the contract has the good
            payment term.
            Test the changement of a payment option for a contract.
        """
        contract_group = self._create_group(
            'do_nothing', self.partners.ids[0], 1,
            self.payment_term_id,
            other_vals={'recurring_value': 1, 'recurring_unit': 'month'})
        contract_group2 = self._create_group(
            'do_nothing', self.partners.ids[1], 1,
            self.payment_term_id,
            other_vals={'recurring_value': 1, 'recurring_unit': 'month'})
        contract = self._create_contract(
            datetime.today().strftime(DF), contract_group,
            datetime.today().strftime(DF),
            other_vals={'channel': 'postal', 'type': 'O'})
        contract_group.write({'partner_id': self.partners.ids[1]})
        contract_group.on_change_partner_id()
        self.assertTrue(contract_group.bvr_reference)
        payment_termbvr_id = self.env['account.payment.term'].search(
            [('name', '=', 'BVR')])[0].id
        contract_group2.write({'payment_term_id': payment_termbvr_id})
        contract_group2.on_change_payment_term()
        self.assertTrue(contract_group2.bvr_reference)
        contract.signal_workflow('contract_validated')
        contract.write({'group_id': contract_group2.id})
        contract.on_change_group_id()
        self.assertEqual(
            contract.group_id.payment_term_id.id, payment_termbvr_id)
