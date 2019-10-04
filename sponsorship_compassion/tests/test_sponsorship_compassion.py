# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Albert SHENOUDA <albert.shenouda@efrei.net>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging
import mock

from datetime import date

from odoo import fields
from odoo.addons.contract_compassion.tests.test_contract_compassion \
    import BaseContractCompassionTest


mock_update_hold = ('odoo.addons.child_compassion.models.compassion_hold'
                    '.CompassionHold.update_hold')
mock_release_hold = ('odoo.addons.child_compassion.models.compassion_hold'
                     '.CompassionHold.release_hold')
mock_get_infos = ('odoo.addons.child_compassion.models.child_compassion'
                  '.CompassionChild.get_infos')
mock_project_infos = ('odoo.addons.child_compassion.models.project_compassion'
                      '.CompassionProject.update_informations')

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
        self.env['thankyou.config'].create({
            'min_donation_amount': 50.0,
            'send_mode': 'auto_digital_only',
        })

    @mock.patch(mock_update_hold)
    @mock.patch(mock_get_infos)
    @mock.patch(mock_project_infos)
    def create_child(self, local_id, project_infos, get_infos, update_hold):
        project_infos.return_value = True
        get_infos.return_value = True
        update_hold.return_value = True
        return self.env['compassion.child'].create({
            'local_id': local_id,
            'global_id': self.ref(9),
            'firstname': 'Test',
            'preferred_name': 'Test',
            'lastname': 'Last',
            'type': 'CDSP',
            'state': 'N',
            'birthdate': '2010-01-01',
            'project_id': self.env['compassion.project'].create({
                'fcp_id': local_id[:5]
            }).id,
            'hold_id': self.env['compassion.hold'].create({
                'hold_id': self.ref(9),
                'type': 'Consignment Hold',
                'expiration_date': fields.Datetime.now(),
                'primary_owner': 1,
            }).id
        })

    @mock.patch(mock_update_hold)
    def create_contract(self, vals, line_vals, update_hold):
        update_hold.return_value = True
        # Add default values
        default_values = {
            'type': 'S',
            'correspondent_id': vals['partner_id'],
            'origin_id': self.origin_id,
        }
        default_values.update(vals)
        return super(BaseSponsorshipTest,
                     self).create_contract(default_values, line_vals)

    def create_contract_line(self, vals):
        default_values = {
            'contract_id': 0,
            'amount': 5,
            'product_id': 1,
            'quantity': 1,
        }
        default_values.update(vals)
        return self.env['recurring.contract.line'].create(default_values)

    @mock.patch(mock_update_hold)
    @mock.patch(mock_project_infos)
    @mock.patch(mock_get_infos)
    def change_child(self, sponsorship, child, update_hold, project_info,
                     get_info):
        """
        Change the child of a sponsorship
        :param sponsorship: the sponsorship in which we should change the child
        :param child: the child to add to the sponsorship
        :param update_hold: mock
        :param project_info: mock
        :param get_info: mock
        :return: the result of the write operation
        """
        # The following lines ensure that the test is run in local without
        # making requests to GMC.
        update_hold.return_value = True
        project_info.return_value = True
        get_info.return_value = True
        return sponsorship.write({'child_id': child.id})

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

    def pay_sponsorship(self, sponsorship):
        invoices = sponsorship.button_generate_invoices().invoice_ids
        self.assertEqual(len(invoices), 2)
        for invoice in reversed(invoices):
            self.assertEqual(invoices[0].state, 'open')
            self._pay_invoice(invoice)


class TestSponsorship(BaseSponsorshipTest):

    def test_sponsorship_compassion_first_scenario(self):
        """
            This first scenario consists in creating a sponsorship contract
            (type 'S') and associate a child to the sponsor.
            Check the different states of the contract and check if there are
            no mistakes.
        """
        # Create a child and get the project associated
        child = self.create_child('PE012304567')

        # Creation of the sponsorship contract
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
        gift_inv[0].action_invoice_open()
        self._pay_invoice(gift_inv[0])
        self.assertEqual(gift_inv[0].state, 'paid')

        # Suspend of the sponsorship contract
        contracts_in_invoices = invoices.mapped(
            'invoice_line_ids.contract_id')
        self.env['compassion.project.ile'].create({
            'project_id': child.project_id.id,
            'type': 'Suspension',
            'name': 'LE-15156-544',
            'hold_cdsp_funds': True,
        })
        logger.info(
            "Suspension done, this is the dates and states of invoices")
        logger.info(str(invoices.mapped('date_invoice')))
        logger.info(str(invoices.mapped('state')))
        invoice1 = invoices[0]
        today = date.today()
        invoice_date = fields.Date.from_string(invoice.date_invoice)
        if invoice_date < today:
            self.assertEqual(invoice.state, 'paid')
        else:
            if len(contracts_in_invoices) == 1:
                self.assertEqual(invoice.state, 'cancel')
            else:
                self.assertEqual(invoice.state, 'open')
                self.assertNotIn(sponsorship, invoice.mapped(
                    'invoice_line_ids.contract_id'))

        if len(contracts_in_invoices) == 1:
            self.assertEqual(invoice1.state, 'cancel')
        else:
            self.assertEqual(invoice.state, 'open')
            self.assertNotIn(sponsorship, invoice1.mapped(
                'invoice_line_ids.contract_id'))

        # Reactivation of the sponsorship contract
        self.env['compassion.project.ile'].create({
            'project_id': child.project_id.id,
            'name': 'LE-54654-545411',
            'type': 'Reactivation',
            'hold_cdsp_funds': False,
        })
        if invoice_date < today:
            self.assertEqual(invoice.state, 'paid')
        else:
            self.assertEqual(invoice.state, 'open')
        self.assertEqual(invoice1.state, 'open')
        sponsorship.signal_workflow('contract_terminated')
        # Force cleaning invoices immediatley
        sponsorship._clean_invoices()
        self.assertTrue(sponsorship.state, 'terminated')
        if invoice_date < today:
            self.assertEqual(invoice.state, 'paid')
        else:
            if len(contracts_in_invoices) == 1:
                self.assertEqual(invoice.state, 'cancel')
                self.assertEqual(invoice1.state, 'cancel')
            else:
                self.assertNotIn(sponsorship, invoice.mapped(
                    'invoice_line_ids.contract_id'))
                self.assertNotIn(sponsorship, invoice1.mapped(
                    'invoice_line_ids.contract_id'))

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

    def test_sponsorship_compassion_third_scenario(self):
        """
            Test of the general contract (type 'O'). It's approximately the
            same test than the contract_compassion's one.
        """
        contract_amount = [50, 75]
        amount = [17, 29]
        quantity = [1, 20]
        contract_group = self.create_group({
            'change_method': 'do_nothing',
            'partner_id': self.michel.id,
            'payment_mode_id': self.payment_mode.id
        })
        contract1 = self.create_contract({
            'type': 'O',
            'partner_id': contract_group.partner_id.id,
            'group_id': contract_group.id
        },
            [{'amount': contract_amount[0]}]
        )
        contract2 = self.create_contract({
            'type': 'O',
            'partner_id': contract_group.partner_id.id,
            'group_id': contract_group.id
        },
            [{'amount': contract_amount[1]}]
        )
        self.create_contract_line({
            'contract_id': contract1.id,
            'amount': amount[0],
            'quantity': quantity[0]
        })
        contract_line = self.create_contract_line({
            'contract_id': contract2.id,
            'amount': amount[1],
            'quantity': quantity[1]
        })
        self.assertEqual(contract1.state, 'draft')
        contract1.contract_line_ids += contract_line
        self.assertEqual(contract_line.contract_id, contract1)
        self.assertEqual(len(contract2.contract_line_ids), 1)
        self.assertEqual(contract1.total_amount, contract_amount[0] +
                         sum([amount[i] * q for i, q in enumerate(quantity)]))

        self.assertEqual(contract2.total_amount, contract_amount[1])

        # Switching to "waiting for payment" state
        self.validate_sponsorship(contract1)
        self.assertEqual(contract1.state, 'waiting')
        self.pay_sponsorship(contract1)
        self.assertEqual(contract1.state, 'active')
        contract1.signal_workflow('contract_terminated')
        self.assertEqual(contract1.state, 'cancelled')
        self.assertTrue(contract2.unlink())

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
        child1 = self.create_child('UG72320010')
        child2 = self.create_child('S008320011')
        child3 = self.create_child('SA12311013')
        sp_group = self.create_group({
            'change_method': 'do_nothing',
            'partner_id': self.michel.id,
            'advance_billing_months': 1,
            'payment_mode_id': self.payment_mode.id
        })
        sponsorship1 = self.create_contract({
            'child_id': child1.id,
            'group_id': sp_group.id,
            'partner_id': sp_group.partner_id.id
        },
            [{'amount': 50.0}]
        )
        sponsorship2 = self.create_contract({
            'child_id': child1.id,
            'group_id': sp_group.id,
            'partner_id': sp_group.partner_id.id
        },
            [{'amount': 50.0}]
        )
        sponsorship3 = self.create_contract({
            'child_id': child3.id,
            'group_id': sp_group.id,
            'partner_id': sp_group.partner_id.id
        },
            [{'amount': 50.0}]
        )
        res = self.change_child(sponsorship2, child2)
        self.assertTrue(res)
        self.assertEqual(sponsorship1.child_id, child1)
        self.assertEqual(sponsorship2.child_id, child2)
        total_price = 0
        for sponsorship in [sponsorship1, sponsorship2, sponsorship3]:
            self.validate_sponsorship(sponsorship)
            total_price += sponsorship.total_amount
            self.assertEqual(sponsorship.state, 'waiting')
        invoices = sponsorship1.button_generate_invoices().invoice_ids
        for invoice in reversed(invoices):
            self._pay_invoice(invoice)
            invoiced = self.env['account.invoice'].browse(invoice.id)
            self.assertEqual(invoiced.amount_total, total_price)
            self.assertEqual(invoiced.state, 'paid')
        child3.child_departed()
        self.assertEqual(child3.state, 'F')
        self.assertEqual(child3.sponsor_id.id, False)
        action_move = self.michel.unreconciled_transaction_items()
        self.assertTrue(action_move)
        action = self.michel.show_lines()
        self.assertTrue(action)

    def test_sponsorship_compassion_fifth_scenario(self):
        """
        Testing the workflow transitions. In particular the termination of
        the contract if they were sent to GMC or not (global_id set).
        """
        child1 = self.create_child('UG83320015')
        child2 = self.create_child('UG28320016')
        sp_group = self.create_group({
            'change_method': 'do_nothing',
            'partner_id': self.michel.id,
            'advance_billing_months': 1,
            'payment_mode_id': self.payment_mode.id
        })
        sponsorship1 = self.create_contract(
            {
                'child_id': child1.id,
                'group_id': sp_group.id,
                'partner_id': sp_group.partner_id.id
            },
            [{'amount': 50.0}]
        )
        sponsorship2 = self.create_contract(
            {
                'child_id': child2.id,
                'group_id': sp_group.id,
                'partner_id': sp_group.partner_id.id
            },
            [{'amount': 50.0}]
        )
        sponsorships = [sponsorship1, sponsorship2]
        for sponsorship in sponsorships:
            self.assertEqual(sponsorship.state, 'draft')
            self.validate_sponsorship(sponsorship)
            self.assertEqual(sponsorship.state, 'waiting')
            self.pay_sponsorship(sponsorship)
        sponsorship1.global_id = 12349123
        sponsorship1.signal_workflow('contract_terminated')
        self.assertEqual(sponsorship1.state, 'terminated')
        sponsorship2.signal_workflow('contract_terminated')
        self.assertEqual(sponsorship2.state, 'cancelled')

    def test_number_sponsorships(self):
        partner = self.michel

        def valid(number_sponsorships, has_sponsorships):
            self.assertEqual(partner.number_sponsorships, number_sponsorships)
            self.assertEqual(partner.has_sponsorships, has_sponsorships)
            self.assertEqual(partner.number_children, number_sponsorships)

        valid(0, False)
        child1 = self.create_child('UG18320017')
        child2 = self.create_child('UG08320018')
        sp_group = self.create_group({
            'change_method': 'do_nothing',
            'partner_id': partner.id,
            'payment_mode_id': self.payment_mode.id
        })
        sponsorship1 = self.create_contract(
            {
                'child_id': child1.id,
                'group_id': sp_group.id,
                'partner_id': sp_group.partner_id.id
            },
            [{'amount': 50.0}]
        )
        sponsorship2 = self.create_contract(
            {
                'child_id': child2.id,
                'group_id': sp_group.id,
                'partner_id': sp_group.partner_id.id
            },
            [{'amount': 50.0}]
        )
        valid(0, False)
        self.validate_sponsorship(sponsorship1)
        valid(0, False)
        self.pay_sponsorship(sponsorship1)
        valid(1, True)
        sponsorship1.update({'partner_id': self.thomas.id})
        valid(1, True)
        sponsorship1.update({'correspondent_id': self.thomas.id})
        valid(0, False)
        sponsorship1.update({'partner_id': partner.id})
        valid(1, True)
        self.validate_sponsorship(sponsorship2)
        self.pay_sponsorship(sponsorship2)
        valid(2, True)
        sponsorship2.signal_workflow('contract_terminated')
        valid(1, True)
        sponsorship1.signal_workflow('contract_terminated')
        valid(0, False)

    def test_change_partner(self):
        """ Test changing partner of contract."""
        partner = self.michel
        child1 = self.create_child('UG18920017')
        sp_group = self.create_group({
            'change_method': 'do_nothing',
            'partner_id': partner.id,
            'payment_mode_id': self.payment_mode.id
        })
        sponsorship = self.create_contract(
            {
                'child_id': child1.id,
                'group_id': sp_group.id,
                'partner_id': sp_group.partner_id.id
            },
            [{'amount': 50.0}]
        )
        self.validate_sponsorship(sponsorship)
        sponsorship.button_generate_invoices()
        invoices = sponsorship.mapped('invoice_line_ids.invoice_id')
        invoice_state = list(set(invoices.mapped('state')))
        partner_invoice = invoices.mapped('partner_id')
        self.assertEqual(len(invoice_state), 1)
        self.assertEqual(invoice_state[0], 'open')
        self.assertEqual(partner_invoice, partner)
        # Change partner
        sponsorship.partner_id = self.thomas
        invoice_state = list(set(invoices.mapped('state')))
        self.assertEqual(invoice_state[0], 'open')
        partner_invoice = invoices.mapped('partner_id')
        self.assertEqual(partner_invoice, self.thomas)
