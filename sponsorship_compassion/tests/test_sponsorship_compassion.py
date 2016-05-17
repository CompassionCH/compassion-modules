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
from openerp import fields
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

    def test_sponsorship_compassion_first_scenario(self):
        """
            This first scenario consists in creating a sponsorship contract
            (type 'S') and associate a child to the sponsor.
            Check the different states of the contract and check if there are
            no mistakes.
        """
        # Create a child and get the project associated
        child = self.env['compassion.child'].create({'local_id': 'PE03760140'})
        child.get_infos()
        # Creation of the sponsorship contract
        sp_group = self._create_group(
            'do_nothing', self.partners.ids[0], 1, self.payment_term_id)
        self._create_group(
            'do_nothing', self.partners.ids[1], 1, self.payment_term_id)
        sponsorship = self._create_contract(
            datetime.today().strftime(DF), sp_group,
            datetime.today().strftime(DF),
            other_vals={
                'origin_id': self.origin_id,
                'channel': 'postal',
                'type': 'S',
                'child_id': child.id,
                'correspondant_id': sp_group.partner_id.id
            })
        # Check if ref and language speaking of partner are set automatically
        partner_obj = self.env['res.partner']
        self.assertTrue(partner_obj.browse(self.partners.ids[0]).ref)
        self.assertTrue(partner_obj.browse(self.partners.ids[0]).lang)
        sponsorship.write({'partner_id': self.partners[1].id})
        sponsorship.on_change_partner_id()
        self.assertEqual(sponsorship.correspondant_id, sponsorship.partner_id)
        self.assertTrue(sponsorship.contract_line_ids)
        self.assertEqual(len(sponsorship.contract_line_ids), 2)
        self.assertEqual(sponsorship.state, 'draft')
        sponsorship.signal_workflow('contract_validated')
        self.assertEqual(sponsorship.state, 'waiting')
        invoices = sponsorship.button_generate_invoices().invoice_ids
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
        gift_inv = self.env['account.invoice'].browse(gift_inv_ids)
        gift_inv[0].signal_workflow('invoice_open')
        self._pay_invoice(gift_inv[0])
        self.assertEqual(gift_inv[0].state, 'paid')

        # Suspend of the sponsorship contract
        child.project_id.with_context(
            async_mode=False).write({'disburse_funds': False})
        invoice1 = self.env['account.invoice'].browse(invoices[1].id)
        self.assertEqual(invoice.state, 'cancel')
        self.assertEqual(invoice1.state, 'cancel')

        # Reactivation of the sponsorship contract
        child.project_id.write({'disburse_funds': True})
        self.assertEqual(invoice.state, 'open')
        self.assertEqual(invoice1.state, 'open')
        date_finish = fields.Datetime.now()
        sponsorship.signal_workflow('contract_terminated')
        # Check a job for cleaning invoices has been created
        self.assertTrue(self.env['queue.job'].search([
            ('name', '=', 'Job for cleaning invoices of contracts.'),
            ('date_created', '>=', date_finish)]))
        # Force cleaning invoices immediatley
        sponsorship._clean_invoices()
        self.assertTrue(sponsorship.state, 'terminated')
        self.assertEqual(invoice.state, 'cancel')
        self.assertEqual(invoice1.state, 'cancel')

    def test_sponsorship_compassion_second_scenario(self):
        """
            We are testing in this scenario the other type of sponsorship
            contract (type 'SC'). Check if we pass from "draft" state to
            "active" state directly by the validation button. Check if there
            are no invoice lines too. Test if a contract is
            cancelled well if we don't generate invoices.
        """
        child = self.env['compassion.child'].create({'local_id': 'IO06790211'})
        child.project_id.write({'disburse_funds': True})
        sp_group = self._create_group(
            'do_nothing', self.partners.ids[0], 1, self.payment_term_id)
        sponsorship = self._create_contract(
            datetime.today().strftime(DF), sp_group,
            datetime.today().strftime(DF),
            other_vals={
                'origin_id': self.origin_id,
                'channel': 'postal',
                'type': 'SC',
                'child_id': child.id,
                'correspondant_id': sp_group.partner_id.id
            })
        sponsorship.signal_workflow('contract_validated')
        self.assertEqual(sponsorship.state, 'active')
        self.assertEqual(len(sponsorship.invoice_line_ids), 0)
        sponsorship.signal_workflow('contract_terminated')
        self.assertTrue(sponsorship.state, 'terminated')
        sponsorship2 = self._create_contract(
            datetime.today().strftime(DF), sp_group,
            datetime.today().strftime(DF),
            other_vals={
                'origin_id': self.origin_id,
                'channel': 'postal',
                'type': 'S',
                'child_id': child.id,
                'correspondant_id': sp_group.partner_id.id
            })
        sponsorship2.signal_workflow('contract_validated')
        sponsorship2.signal_workflow('contract_terminated')
        self.assertEqual(sponsorship2.state, 'cancelled')

    def test_sponsorship_compassion_third_scenario(self):
        """
            Test of the general contract (type 'O'). It's approximately the
            same test than the contract_compassion's one.
        """
        contract_group = self._create_group(
            'do_nothing', self.partners.ids[0], 1, self.payment_term_id)
        contract = self._create_contract(
            datetime.today().strftime(DF), contract_group,
            datetime.today().strftime(DF),
            other_vals={
                'type': 'O',
                'correspondant_id': contract_group.partner_id.id
            })
        contract2 = self._create_contract(
            datetime.today().strftime(DF), contract_group,
            datetime.today().strftime(DF),
            other_vals={
                'type': 'O',
                'correspondant_id': contract_group.partner_id.id
            })
        self._create_contract_line(
            contract.id, '40.0', other_vals={'quantity': '2'})
        contract_line = self._create_contract_line(
            contract2.id, '137', other_vals={'quantity': '4'})
        self.assertEqual(contract.state, 'draft')
        contract.contract_line_ids += contract_line
        self.assertEqual(
            contract.total_amount,
            contract_line.subtotal + contract.contract_line_ids[0].subtotal)
        # Switching to "waiting for payment" state
        contract.signal_workflow('contract_validated')
        self.assertEqual(contract.state, 'waiting')
        invoices = contract.button_generate_invoices().invoice_ids
        nb_invoices = len(invoices)
        self.assertEqual(nb_invoices, 2)
        self.assertEqual(invoices[0].state, 'open')
        self.assertEqual(invoices[1].state, 'open')
        self._pay_invoice(invoices[0])
        self._pay_invoice(invoices[1])
        self.assertEqual(contract.state, 'active')
        contract.signal_workflow('contract_terminated')
        self.assertEqual(contract.state, 'terminated')
        is_unlinked = contract2.unlink()
        self.assertTrue(is_unlinked)

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
        child1 = self.env['compassion.child'].create({'local_id':
                                                      'UG08320010'})
        child2 = self.env['compassion.child'].create({'local_id':
                                                      'UG08320011'})
        child3 = self.env['compassion.child'].create({'local_id':
                                                      'UG08320013'})
        sp_group = self._create_group(
            'do_nothing', self.partners.ids[0], 1, self.payment_term_id)
        sponsorship1 = self._create_contract(
            datetime.today().strftime(DF), sp_group,
            datetime.today().strftime(DF),
            other_vals={
                'origin_id': self.origin_id,
                'channel': 'postal',
                'type': 'S',
                'child_id': child1.id,
                'correspondant_id': sp_group.partner_id.id
            })
        sponsorship2 = self._create_contract(
            datetime.today().strftime(DF), sp_group,
            datetime.today().strftime(DF),
            other_vals={
                'origin_id': self.origin_id,
                'channel': 'postal',
                'type': 'S',
                'child_id': child1.id,
                'correspondant_id': sp_group.partner_id.id
            })
        sponsorship2.write({'child_id': child2.id})
        sponsorship3 = self._create_contract(
            datetime.today().strftime(DF), sp_group,
            datetime.today().strftime(DF),
            other_vals={
                'origin_id': self.origin_id,
                'channel': 'postal',
                'type': 'S',
                'child_id': child3.id,
                'correspondant_id': sp_group.partner_id.id
            })
        sponsorship1.signal_workflow('contract_validated')
        sponsorship2.signal_workflow('contract_validated')
        sponsorship3.signal_workflow('contract_validated')
        original_price1 = sponsorship1.total_amount
        original_price2 = sponsorship2.total_amount
        original_price3 = sponsorship3.total_amount
        self.assertEqual(sponsorship1.state, 'waiting')
        self.assertEqual(sponsorship2.state, 'waiting')
        self.assertEqual(sponsorship3.state, 'waiting')
        invoices = sponsorship1.button_generate_invoices().invoice_ids
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
        action_move = self.partners[0].unreconciled_transaction_items()
        self.assertTrue(action_move)
        action = self.partners[0].show_lines()
        self.assertTrue(action)
