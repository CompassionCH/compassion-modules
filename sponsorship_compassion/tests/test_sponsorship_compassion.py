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
from unittest import mock

from dateutil.relativedelta import relativedelta
from dateutil.utils import today

from odoo import fields

from odoo.addons.sponsorship_compassion.models.product_names import (
    GIFT_PRODUCTS_REF,
    PRODUCT_GIFT_CHRISTMAS,
)

from .test_contract_compassion import BaseContractCompassionTest

mock_update_hold = (
    "odoo.addons.child_compassion.models.compassion_hold" ".CompassionHold.update_hold"
)
mock_release_hold = (
    "odoo.addons.child_compassion.models.compassion_hold" ".CompassionHold.release_hold"
)
mock_get_infos = (
    "odoo.addons.child_compassion.models.child_compassion" ".CompassionChild.get_infos"
)
mock_get_lifecycle = (
    "odoo.addons.child_compassion.models.child_compassion"
    ".CompassionChild.get_lifecycle_event"
)
mock_project_infos = (
    "odoo.addons.child_compassion.models.project_compassion"
    ".CompassionProject.update_informations"
)

logger = logging.getLogger(__name__)


class BaseSponsorshipTest(BaseContractCompassionTest):
    def setUp(self):
        super().setUp()
        # Create the GIFT products for the gifts tests
        product_vals = {
            "name": "gifts test",
            "type": "service",
            "categ_id": self.env.ref("sponsorship_compassion.product_category_gift").id,
            "sale_ok": True,
        }
        for gift in [GIFT_PRODUCTS_REF[0], PRODUCT_GIFT_CHRISTMAS]:
            product_vals.update({"default_code": gift})
            self.env["product.product"].create(product_vals)
        # Creation of an origin
        self.origin_id = (
            self.env["recurring.contract.origin"].create({"type": "event"}).id
        )
        self.product = self.env["product.product"].create(
            {
                "name": "Sponsorship test",
                "type": "service",
                "categ_id": self.env.ref(
                    "sponsorship_compassion.product_category_sponsorship",
                    self.env["product.category"],
                ).id,
                "sale_ok": True,
            }
        )
        # Direct debit payment method
        dd_pay_method = self.env["account.payment.method"].create(
            {
                "name": "DD_Gifts",
                "code": "gift_direct_debit",
                "payment_type": "inbound",
                "bank_account_required": False,
            }
        )
        dd_pay_mode = self.env["account.payment.mode"].create(
            {
                "name": "Test Direct Debit of customers",
                "bank_account_link": "variable",
                "payment_method_id": dd_pay_method.id,
            }
        )
        # Create a child and get the project associated
        self.child = self.create_child("PE012304567")
        # Creation of the sponsorship contract
        sp_group = self.create_group(
            {"partner_id": self.partner_1.id, "payment_mode_id": dd_pay_mode.id}
        )
        self.sponsorship = self.create_contract(
            {
                "partner_id": self.partner_1.id,
                "group_id": sp_group.id,
                "child_id": self.child.id,
                "type": "S",
            },
            [{"amount": 50.0, "product_id": self.product.id}],
        )

    @mock.patch(mock_update_hold)
    @mock.patch(mock_get_infos)
    @mock.patch(mock_project_infos)
    def create_child(self, local_id, project_infos, get_infos, update_hold):
        project_infos.return_value = True
        get_infos.return_value = True
        update_hold.return_value = True
        return self.env["compassion.child"].create(
            {
                "local_id": local_id,
                "global_id": self.ref(9),
                "firstname": "Test",
                "preferred_name": "Test",
                "lastname": "Last",
                "type": "CDSP",
                "state": "N",
                "birthdate": today() + relativedelta(years=-3, months=3),
                "project_id": self.env["compassion.project"]
                .create({"fcp_id": local_id[:5]})
                .id,
                "hold_id": self.env["compassion.hold"]
                .create(
                    {
                        "hold_id": self.ref(9),
                        "type": "Consignment Hold",
                        "expiration_date": fields.Datetime.now()
                        + relativedelta(weeks=2),
                        "primary_owner": 1,
                    }
                )
                .id,
            }
        )

    @mock.patch(mock_update_hold)
    def create_contract(self, vals, line_vals, update_hold):
        update_hold.return_value = True
        # Add default values
        default_values = {
            "type": "S",
            "correspondent_id": vals["partner_id"],
            "origin_id": self.env["recurring.contract.origin"]
            .create({"type": "event"})
            .id,
        }
        default_values.update(vals)
        return super().create_contract(default_values, line_vals)

    def create_contract_line(self, vals):
        default_values = {
            "contract_id": 0,
            "amount": 5,
            "product_id": self.product.id,
            "quantity": 1,
        }
        default_values.update(vals)
        return self.env["recurring.contract.line"].create(default_values)

    @mock.patch(mock_update_hold)
    @mock.patch(mock_project_infos)
    @mock.patch(mock_get_infos)
    def change_child(self, sponsorship, child, update_hold, project_info, get_info):
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
        return sponsorship.write({"child_id": child.id})

    @mock.patch(mock_update_hold)
    def waiting_sponsorship(self, contract, update_hold):
        """
        Validates a sponsorship without updating hold with Connect
        :param contract: recurring.contract object
        :return: mock object on update hold method
        """
        update_hold.return_value = True
        contract.contract_waiting()
        return update_hold

    def pay_sponsorship(self, sponsorship):
        invoices = sponsorship.invoice_line_ids.mapped("move_id")
        if not invoices:
            sponsorship.button_generate_invoices()
            invoices = sponsorship.invoice_line_ids.mapped("move_id")
        self.assertEqual(len(invoices), 1)
        for invoice in reversed(invoices):
            self.assertEqual(invoices[0].state, "posted")
            self._pay_invoice(invoice)


class TestSponsorship(BaseSponsorshipTest):
    def test_sponsorship_compassion_multiple_contract(self):
        """
        We are testing the generation of invoices on multiple contract on
        the same payment option
        """
        sponsorship = self.sponsorship
        # Check that the child is sponsored
        # Test validation of contract
        self.waiting_sponsorship(sponsorship)
        self.assertEqual(sponsorship.state, "waiting")
        # Invoices should be generated when the contract goes from draft to waiting
        invoices = sponsorship.invoice_line_ids.mapped("move_id")
        self._pay_invoice(invoices[0])
        self.assertEqual(sponsorship.state, "active")

        # Generate gifts for the child
        sponsorship.write({"birthday_invoice": 100})
        sponsorship.button_generate_invoices()
        gift_invoice = sponsorship.invoice_line_ids.mapped("move_id").filtered(
            lambda m: m.invoice_category == "gift"
        )
        self._pay_invoice(gift_invoice[0])
        self.assertEqual(gift_invoice[0].payment_state, "paid")
        self.assertEqual(
            gift_invoice[0].invoice_date.month,
            (sponsorship.child_id.birthdate - relativedelta(months=2)).month,
        )
        child = self.create_child("S008320011")
        sponsorship2 = self.create_contract(
            {
                "child_id": child.id,
                "group_id": sponsorship.group_id.id,
                "partner_id": sponsorship.partner_id.id,
            },
            [{"amount": 50.0, "product_id": self.product.id}],
        )
        self.waiting_sponsorship(sponsorship2)
        self.assertEqual(
            sponsorship.group_id.active_contract_ids.mapped(
                "invoice_line_ids.move_id.invoice_line_ids.contract_id"
            ),
            sponsorship + sponsorship2,
        )

    def test_sponsorship_compassion_first_scenario(self):
        """
        This first scenario consists in creating a sponsorship contract
        (type 'S') and associate a child to the sponsor.
        Check the different states of the contract and check if there are
        no mistakes.
        """
        child = self.child
        sponsorship = self.sponsorship
        # Check that the child is sponsored
        self.assertEqual(child.state, "P")
        self.assertEqual(sponsorship.state, "draft")

        # Test validation of contract
        update_hold = self.waiting_sponsorship(sponsorship)
        self.assertEqual(sponsorship.state, "waiting")
        self.assertTrue(update_hold.called)
        hold = child.hold_id
        self.assertEqual(hold.type, "No Money Hold")
        # Invoices should be generated when the contract goes from draft to waiting
        invoices = sponsorship.invoice_line_ids.mapped("move_id")
        self.assertEqual(len(invoices), 1)
        invoice = invoices[0]
        self.assertEqual(invoice.payment_state, "not_paid")
        self._pay_invoice(invoice)
        self.assertEqual(invoice.payment_state, "paid")
        self.assertEqual(sponsorship.state, "active")

        # Generate gifts for the child
        sponsorship.write({"birthday_invoice": 100})
        sponsorship.button_generate_invoices()
        gift_invoice = sponsorship.invoice_line_ids.mapped("move_id").filtered(
            lambda m: m.invoice_category == "gift"
        )
        self._pay_invoice(gift_invoice[0])
        self.assertEqual(gift_invoice[0].payment_state, "paid")
        self.assertEqual(
            gift_invoice[0].invoice_date.month,
            (sponsorship.child_id.birthdate - relativedelta(months=2)).month,
        )

    @mock.patch(mock_get_lifecycle)
    def test_sponsorship_compassion_fourth_scenario(self, lifecycle_mock):
        """
        In this final scenario we are testing the creation of 3 sponsorship
        contracts for the same partner with for each contract one child to
        sponsor.
        We will make a child stop and leave the sponsorship program,
        check if that child have no more sponsor id.
        Check if the 3 contracts create one merged invoice for every month
        (2 months here) with the good values.
        """
        lifecycle_mock.return_value = True
        child1 = self.create_child("UG72320010")
        child2 = self.create_child("S008320011")
        child3 = self.create_child("SA12311013")
        sp_group = self.create_group(
            {
                "partner_id": self.partner_1.id,
                "advance_billing_months": 1,
                "payment_mode_id": self.payment_mode.id,
            }
        )
        sponsorship1 = self.create_contract(
            {
                "child_id": child1.id,
                "group_id": sp_group.id,
                "partner_id": sp_group.partner_id.id,
            },
            [{"amount": 50.0, "product_id": self.product.id}],
        )
        sponsorship2 = self.create_contract(
            {
                "child_id": child1.id,
                "group_id": sp_group.id,
                "partner_id": sp_group.partner_id.id,
            },
            [{"amount": 50.0, "product_id": self.product.id}],
        )
        sponsorship3 = self.create_contract(
            {
                "child_id": child3.id,
                "group_id": sp_group.id,
                "partner_id": sp_group.partner_id.id,
            },
            [{"amount": 50.0}],
        )
        res = self.change_child(sponsorship2, child2)
        self.assertTrue(res)
        self.assertEqual(sponsorship1.child_id, child1)
        self.assertEqual(sponsorship2.child_id, child2)
        total_price = 0
        sponsorships = sponsorship3 + sponsorship2 + sponsorship1
        for sponsorship in sponsorships.filtered(
            lambda s: s.state in ["waiting", "active"]
        ):
            self.waiting_sponsorship(sponsorship)
            total_price += sponsorship.total_amount
            self.assertEqual(sponsorship.state, "waiting")
        invoices = sponsorship1.invoice_line_ids.mapped("move_id")
        for invoice in reversed(invoices):
            self._pay_invoice(invoice)
            invoiced = self.env["account.move"].browse(invoice.id)
            self.assertEqual(invoiced.amount_total, total_price)
            self.assertEqual(invoiced.payment_state, "paid")
        child3.child_departed()
        self.assertEqual(child3.state, "F")
        self.assertEqual(child3.sponsor_id.id, False)
        action_move = self.partner_1.unreconciled_transaction_items()
        self.assertTrue(action_move)
        action = self.partner_1.show_lines()
        self.assertTrue(action)

    def test_change_partner(self):
        """Test changing partner of contract."""
        partner = self.partner_1
        child1 = self.create_child("UG18920017")
        sp_group = self.create_group(
            {
                "partner_id": partner.id,
                "payment_mode_id": self.payment_mode.id,
            }
        )
        sponsorship = self.create_contract(
            {
                "child_id": child1.id,
                "group_id": sp_group.id,
                "partner_id": sp_group.partner_id.id,
            },
            [{"amount": 50.0, "product_id": self.product.id}],
        )
        self.waiting_sponsorship(sponsorship)
        sponsorship.button_generate_invoices()
        invoices = sponsorship.mapped("invoice_line_ids.move_id")
        invoice_state = list(set(invoices.mapped("state")))
        partner_invoice = invoices.mapped("partner_id")
        self.assertEqual(len(invoice_state), 1)
        self.assertEqual(invoice_state[0], "posted")
        self.assertEqual(partner_invoice, partner)
        # Change partner
        sponsorship.write({"partner_id": self.partner_2})
        invoice_state = list(set(invoices.mapped("state")))
        self.assertEqual(invoice_state[0], "posted")
        partner_invoice = invoices.mapped("partner_id")
        self.assertEqual(partner_invoice, self.partner_2)

    def test_commitment_number_on_partner_change(self):
        """Test if commitment number is correctly updated"""
        partner = self.partner_1
        partner2 = self.partner_2

        child1 = self.create_child("UG18920019")
        child2 = self.create_child("UG18920011")

        sp_group1 = self.create_group(
            {
                "partner_id": partner.id,
                "payment_mode_id": self.payment_mode.id,
            }
        )

        sp_group2 = self.create_group(
            {
                "partner_id": partner2.id,
                "payment_mode_id": self.payment_mode.id,
            }
        )

        sponsorship1 = self.create_contract(
            {
                "child_id": child1.id,
                "group_id": sp_group1.id,
                "partner_id": sp_group1.partner_id.id,
            },
            [{"amount": 50.0, "product_id": self.product.id}],
        )

        sponsorship2 = self.create_contract(
            {
                "child_id": child2.id,
                "group_id": sp_group2.id,
                "partner_id": sp_group2.partner_id.id,
            },
            [{"amount": 50.0, "product_id": self.product.id}],
        )

        sponsorship2.partner_id = partner

        self.assertGreater(
            sponsorship2.commitment_number, sponsorship1.commitment_number
        )

    def test_correct_default_correspondent(self):
        partner = self.partner_1

        child1 = self.create_child("UG18920021")

        sp_group1 = self.create_group(
            {
                "partner_id": partner.id,
                "payment_mode_id": self.payment_mode.id,
            }
        )

        sponsorship1 = self.create_contract(
            {
                "child_id": child1.id,
                "group_id": sp_group1.id,
                "partner_id": sp_group1.partner_id.id,
            },
            [{"amount": 50.0, "product_id": self.product.id}],
        )

        self.assertEqual(sponsorship1.correspondent_id, partner)

    def test_partly_paid_sponsorship_activation(self):
        """
        Correspondence sponsorship with partial payment should not be automatically activated
        unlink SC sponsorship with total_amount of 0.
        """
        child = self.create_child("PE012304567")

        contract_group = self.create_group(
            {
                "partner_id": self.partner_1.id,
            }
        )
        contract = self.create_contract(
            {
                "type": "SC",
                "partner_id": self.partner_1.id,
                "group_id": contract_group.id,
                "child_id": child.id,
            },
            [{"amount": 50.0, "product_id": self.product.id}],
        )

        self.assertEqual(contract.state, "draft")
        self.waiting_sponsorship(contract)
        self.assertEqual(contract.state, "waiting")
