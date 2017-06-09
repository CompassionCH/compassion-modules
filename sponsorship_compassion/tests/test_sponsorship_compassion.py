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

import logging
import mock

from datetime import date

from openerp import fields
from openerp.addons.contract_compassion.tests.test_contract_compassion \
    import BaseContractCompassionTest


mock_update_hold = ('openerp.addons.child_compassion.models.compassion_hold'
                    '.CompassionHold.update_hold')
mock_release_hold = ('openerp.addons.child_compassion.models.compassion_hold'
                     '.CompassionHold.release_hold')
logger = logging.getLogger(__name__)


class BaseSponsorshipTest(BaseContractCompassionTest):
    def setUp(self):
        super(BaseSponsorshipTest, self).setUp()
        # Creation of an origin
        self.origin_id = self.env['recurring.contract.origin'].create(
            {'type': 'event'}).id
        self.product = self.env['product.product'].search([
            ('name', '=', 'Sponsorship')
        ], limit=1)

    def create_child(self, local_id):
        return self.env['compassion.child'].create({
            'local_id': local_id,
            'global_id': self.ref(9),
            'type': 'CDSP',
            'state': 'N',
            'birthdate': '2010-01-01',
            'project_id': self.env['compassion.project'].create({
                'icp_id': local_id[:5]
            }).id,
            'hold_id': self.env['compassion.hold'].create({
                'hold_id': self.ref(9),
                'type': 'Consignment Hold',
                'expiration_date': fields.Datetime.now(),
                'primary_owner': 1,
            }).id
        })

    def create_contract(self, vals, line_vals):
        # Add default values
        default_values = {
            'type': 'S',
            'correspondant_id': vals['partner_id'],
            'origin_id': self.origin_id,
        }
        default_values.update(vals)
        return super(BaseSponsorshipTest,
                     self).create_contract(default_values, line_vals)

    @mock.patch(mock_update_hold)
    def validate_sponsorship(self, contract, update_hold):
        """
        Validates a sponsorship without updating hold with Connect
        :param contract: recurring.contract object
        :return: mock object on update hold method
        """
        update_hold.return_value = True
        contract.signal_workflow('contract_validated')
        return update_hold


class TestSponsorship(BaseSponsorshipTest):

    def test_sponsorship_compassion_first_scenario(self):
        """
            This first scenario consists in creating a sponsorship contract
            (type 'S') and associate a child to the sponsor.
            Check the different states of the contract and check if there are
            no mistakes.
        """
        # Create a child and get the project associated

        # Creation of the sponsorship contract
        child = self.create_child('PE012304567')
        sp_group = self.create_group({'partner_id': self.michel.id})
        sponsorship = self.create_contract(
            {
                'partner_id': self.michel.id,
                'group_id': sp_group.id,
                'child_id': child.id,
            },
            [{'amount': 50.0}]
        )
        # Check that the child is sponsored
        self.assertEqual(child.state, 'P')
        self.assertEqual(sponsorship.state, 'draft')

        # Check correspondent is updated when partner is changed
        group = self.env['recurring.contract.group'].search([
            ('partner_id', '=', self.thomas.id)
        ])
        if not group:
            self.create_group({'partner_id': self.thomas.id})
        sponsorship.write({'partner_id': self.thomas.id})
        sponsorship.on_change_partner_id()
        self.assertEqual(sponsorship.correspondant_id, sponsorship.partner_id)
        self.assertEqual(child.sponsor_id, self.thomas)

        # Test validation of contract
        update_hold = self.validate_sponsorship(sponsorship)
        self.assertEqual(sponsorship.state, 'waiting')
        self.assertTrue(update_hold.called)
        hold = child.hold_id
        self.assertEqual(hold.type, 'No Money Hold')

        invoices = sponsorship.button_generate_invoices().invoice_ids
        self.assertEqual(len(invoices), 2)
        invoice = self.env['account.invoice'].browse(invoices[1].id)
        self.assertEqual(invoice.state, 'open')
        self._pay_invoice(invoice)
        self.assertEqual(invoice.state, 'paid')
        self.assertEqual(sponsorship.state, 'active')

        # Generate gifts for the child
        gift_wiz_obj = self.env['generate.gift.wizard']
        gift_wiz = gift_wiz_obj.create(
            {
                'product_id': self.product.search([
                    ('name', '=', 'Birthday Gift')
                ]).id,
                'amount': 200.0,
                'invoice_date': fields.Date.today(),
            })
        gift_inv_ids = gift_wiz.with_context(
            active_ids=[sponsorship.id]).generate_invoice()['domain'][0][2]
        gift_inv = self.env['account.invoice'].browse(gift_inv_ids)
        gift_inv[0].signal_workflow('invoice_open')
        self._pay_invoice(gift_inv[0])
        self.assertEqual(gift_inv[0].state, 'paid')

        # Suspend of the sponsorship contract
        self.env['compassion.project.ile'].create({
            'project_id': child.project_id.id,
            'type': 'Suspension',
            'hold_cdsp_funds': True,
        })
        invoice1 = self.env['account.invoice'].browse(invoices[0].id)
        today = date.today()
        invoice_date = fields.Date.from_string(invoice.date_invoice)
        if invoice_date < today:
            self.assertEqual(invoice.state, 'paid')
        else:
            self.assertEqual(invoice.state, 'cancel')

        self.assertEqual(invoice1.state, 'cancel')

        # Reactivation of the sponsorship contract
        self.env['compassion.project.ile'].create({
            'project_id': child.project_id.id,
            'type': 'Reactivation',
            'hold_cdsp_funds': False,
        })
        if invoice_date < today:
            self.assertEqual(invoice.state, 'paid')
        else:
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
        if invoice_date < today:
            self.assertEqual(invoice.state, 'paid')
        else:
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
        child = self.create_child('IO06790211')
        sp_group = self.create_group({'partner_id': self.david.id})
        sponsorship = self.create_contract(
            {
                'type': 'SC',
                'child_id': child.id,
                'group_id': sp_group.id,
                'partner_id': self.david.id,
            },
            [{'amount': 50.0}]
        )
        # Activate correspondence sponsorship
        update_hold = self.validate_sponsorship(sponsorship)
        self.assertEqual(sponsorship.state, 'active')
        self.assertFalse(update_hold.called)

        # Termination of correspondence
        sponsorship.signal_workflow('contract_terminated')
        self.assertTrue(sponsorship.state, 'terminated')

        # Create regular sponsorship
        child = self.create_child('IO06890212')
        sponsorship2 = self.create_contract(
            {
                'child_id': child.id,
                'partner_id': self.david.id,
                'group_id': sp_group.id
            },
            [{'amount': 50.0}]
        )
        update_hold = self.validate_sponsorship(sponsorship2)
        self.assertEqual(sponsorship2.state, 'waiting')
        self.assertTrue(update_hold.called)
        hold = child.hold_id
        self.assertEqual(hold.type, 'No Money Hold')

        sponsorship2.signal_workflow('contract_terminated')
        self.assertEqual(sponsorship2.state, 'cancelled')

    def _test_sponsorship_compassion_third_scenario(self):
        """
            Test of the general contract (type 'O'). It's approximately the
            same test than the contract_compassion's one.
        """
        # TODO Migrate this test
        contract_group = self._create_group(
            'do_nothing', self.partners.ids[0], 1, self.payment_mode_id)
        contract = self._create_contract(
            other_vals={
                'type': 'O',
                'correspondant_id': contract_group.partner_id.id
            })
        contract2 = self._create_contract(
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

    def _test_sponsorship_compassion_fourth_scenario(self):
        """
            In this final scenario we are testing the creation of 3 sponsorship
            contracts for the same partner with for each contract one child to
            sponsor.
            We will make a child stop and leave the sponsorship program,
            check if that child have no more sponsor id.
            Check if the 3 contracts create one merged invoice for every month
            (2 months here) with the good values.
        """
        # TODO Migrate this test
        child1 = self.env['compassion.child'].create({'local_id':
                                                      'UG08320010'})
        child2 = self.env['compassion.child'].create({'local_id':
                                                      'UG08320011'})
        child3 = self.env['compassion.child'].create({'local_id':
                                                      'UG08320013'})
        sp_group = self._create_group(
            'do_nothing', self.partners.ids[0], 1, self.payment_mode_id)
        sponsorship1 = self._create_contract(
            other_vals={
                'origin_id': self.origin_id,
                'channel': 'postal',
                'type': 'S',
                'child_id': child1.id,
                'correspondant_id': sp_group.partner_id.id
            })
        sponsorship2 = self._create_contract(
            other_vals={
                'origin_id': self.origin_id,
                'channel': 'postal',
                'type': 'S',
                'child_id': child1.id,
                'correspondant_id': sp_group.partner_id.id
            })
        sponsorship2.write({'child_id': child2.id})
        sponsorship3 = self._create_contract(
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
