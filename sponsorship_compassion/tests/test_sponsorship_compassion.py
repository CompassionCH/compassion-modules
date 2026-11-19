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

from dateutil.relativedelta import relativedelta
from dateutil.utils import today

from odoo import fields

from .test_contract_compassion import BaseContractCompassionTest

logger = logging.getLogger(__name__)

GIFT_TYPE_CODES = ["gift_birthday", "gift_christmas"]


class BaseSponsorshipTest(BaseContractCompassionTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, no_upsert=True))

    def setUp(self):
        super().setUp()
        # Attach a product to the gift types used by the gifts tests
        gift_types = self.env["sponsorship.gift.type"].search(
            [("code", "in", GIFT_TYPE_CODES)]
        )
        gift_category = self.env.ref("sponsorship_compassion.product_category_gift")
        for gift_type in gift_types.filtered(lambda t: not t.product_id):
            gift_type.product_id = self.env["product.product"].create(
                {
                    "name": f"{gift_type.name} test",
                    "type": "service",
                    "categ_id": gift_category.id,
                    "sale_ok": True,
                    "default_code": gift_type.code,
                }
            )
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
                "default_code": "sponsorship",
            }
        )
        self.donation = self.env["product.product"].create(
            {"name": "Donation test", "default_code": "fund_gen"}
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

        # Create account used in unreconciled_transaction_items
        account = self.env["account.account"]
        if account.search_count([("code", "=", "1050")]) == 0:
            account.create(
                {
                    "name": "Some test account",
                    "account_type": "asset_current",
                    "reconcile": True,
                    "code": "1050",
                }
            )

        # Create a child and get the project associated
        self.child = self.create_child("PE012304567")
        # Creation of the sponsorship contract
        self.sp_group = self.create_group(
            {"partner_id": self.partner_1.id, "payment_mode_id": dd_pay_mode.id}
        )
        self.sponsorship = self.create_contract(
            {
                "partner_id": self.partner_1.id,
                "group_id": self.sp_group.id,
                "child_id": self.child.id,
                "type": "S",
            },
            [{"amount": 50.0, "product_id": self.product.id}],
        )

    def create_child(self, local_id):
        return self.env["compassion.child"].create(
            {
                "local_id": local_id,
                "global_id": self.ref(9),
                "firstname": "Test",
                "preferred_name": "Test",
                "lastname": "Last",
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
                        "primary_owner": self.env.user.id,
                    }
                )
                .id,
            }
        )

    def create_contract(self, vals, line_vals):
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

    def change_child(self, sponsorship, child):
        """
        Change the child of a sponsorship
        :param sponsorship: the sponsorship in which we should change the child
        :param child: the child to add to the sponsorship
        :return: the result of the write operation
        """
        return sponsorship.write({"child_id": child.id})

    def waiting_sponsorship(self, contract):
        """
        Validates a sponsorship
        :param contract: recurring.contract object
        :return: the result of contract_waiting
        """
        return contract.contract_waiting()

    def pay_sponsorship(self, sponsorship):
        invoices = sponsorship.invoice_line_ids.mapped("move_id")
        if not invoices:
            sponsorship.button_generate_invoices()
            invoices = sponsorship.invoice_line_ids.mapped("move_id")
        self.assertEqual(len(invoices), 1)
        for invoice in reversed(invoices):
            self.assertEqual(invoices[0].state, "posted")
            self._pay_invoice(invoice)
