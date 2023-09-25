##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
import time

from odoo.tests import SavepointCase

logger = logging.getLogger(__name__)


class TestThankYouLetters(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create accounting needed data
        cls.account_model = cls.env["account.account"]
        cls.eur_currency = cls.env.ref("base.EUR")
        try:
            cls.env.ref(
                "l10n_generic_coa.configurable_chart_template"
            ).try_loading_for_current_company()
        except ValueError:
            logger.error("Could not load configurable chart template properly")
        cls.account_revenue = cls.account_model.search(
            [
                (
                    "user_type_id",
                    "=",
                    cls.env.ref("account.data_account_type_revenue").id,
                ),
            ],
            limit=1,
        )
        cls.account_receivable = cls.account_model.search(
            [
                (
                    "user_type_id",
                    "=",
                    cls.env.ref("account.data_account_type_receivable").id,
                ),
            ],
            limit=1,
        )

        # Use products
        cls.product_membership = cls.env.ref("product.product_delivery_01")
        cls.product_ipod = cls.env.ref("product.product_product_11")
        cls.product_mouse = cls.env.ref("product.product_product_10")

        cls.env["thankyou.config"].create(
            {
                "min_donation_amount": 50.0,
                "send_mode": "auto_digital_only",
            }
        )

        cls.env["thankyou.config"].create(
            {
                "min_donation_amount": 1000.0,
                "need_call": "after_sending",
                "send_mode": "auto_digital_only",
            }
        )

    def test_success_stories_set(self):
        """Pay some invoices and test the success stories are
        correctly set according to the product settings.
        """
        asus = self.env.ref("base.res_partner_1")
        agrolait = self.env.ref("base.res_partner_2")
        china = self.env.ref("base.res_partner_3")
        invoice_ipod = self.create_invoice(asus.id, self.product_ipod.id, 35)
        invoice_mouse = self.create_invoice(agrolait.id, self.product_mouse.id, 35)
        invoice_membership = self.create_invoice(
            china.id, self.product_membership.id, 35
        )
        invoices = invoice_ipod + invoice_mouse + invoice_membership
        # No thank you letter before we register payment
        self.assertFalse(invoices.mapped("communication_id"))
        self.pay_invoice(invoices)

        # iPod should have a thank you with success story 2
        self.assertTrue(invoice_ipod.communication_id)
        self.assertEqual(
            invoice_ipod.communication_id.success_story_id,
            self.env.ref("thankyou_letters.success_story_2"),
        )
        # Test that the story stays when the text is refreshed
        invoice_ipod.communication_id.refresh_text()
        self.assertEqual(
            invoice_ipod.communication_id.success_story_id,
            self.env.ref("thankyou_letters.success_story_2"),
        )

        self.assertTrue(invoice_membership.communication_id)
        # TODO: question for Ema, where should the sponsorship be linked?
        # self.assertEqual(
        #     invoice_membership.communication_id.success_story_id,
        #     self.env.ref('thankyou_letters.success_story_2')
        # )

        # Mouse should not be thanked
        self.assertFalse(invoice_mouse.communication_id)

    def test_multiple_donation_thankyou(self):
        """send multiple donation of different config and expect communication
        To be adapt to big donors as total pending donation goes over 1000CHF"""

        # use the first thanks comm to avoid other issue (missing user_id reference in test db)
        thanks_partner_comm1 = self.env["partner.communication.config"].search(
            [("send_mode_pref_field", "like", "thankyou_preference")], limit=1
        )

        thanks_partner_comm2 = thanks_partner_comm1.copy()

        self.assertIsNot(thanks_partner_comm1, False)
        self.assertIsNot(thanks_partner_comm2, False)

        # create 2 products with identical communication and a 3rd one with
        product1 = self.env["product.product"].create(
            {
                "name": "product1",
                "partner_communication_config": thanks_partner_comm1.id,
                "requires_thankyou": True,
            }
        )

        product2 = self.env["product.product"].create(
            {
                "name": "product2",
                "partner_communication_config": thanks_partner_comm1.id,
                "requires_thankyou": True,
            }
        )

        product3 = self.env["product.product"].create(
            {
                "name": "product3",
                "partner_communication_config": thanks_partner_comm2.id,
                "requires_thankyou": True,
            }
        )

        self.assertIsNot(product1, False)
        self.assertIsNot(product2, False)

        partner = self.env["res.partner"].create({"name": "test partner"})

        invoice1 = self.create_invoice(partner.id, product1.id, 300)
        self.pay_invoice(invoice1)

        all_existing_comm = self.env["partner.communication.job"].search(
            [
                ("partner_id", "=", partner.id),
                ("state", "in", ("call", "pending")),
                ("config_id", "in", (thanks_partner_comm1 + thanks_partner_comm2).ids),
            ]
        )

        self.assertEqual(len(all_existing_comm), 1)
        self.assertEqual(
            thanks_partner_comm1.id, product1.partner_communication_config.id
        )

        invoice2 = self.create_invoice(partner.id, product2.id, 400)
        self.pay_invoice(invoice2)

        all_existing_comm = self.env["partner.communication.job"].search(
            [
                ("partner_id", "=", partner.id),
                ("state", "in", ("call", "pending")),
                ("config_id", "in", (thanks_partner_comm1 + thanks_partner_comm2).ids),
            ]
        )

        self.assertEqual(len(all_existing_comm), 1)

        comm_to_watch = all_existing_comm[0]
        prev_need_call = comm_to_watch.need_call

        invoice3 = self.create_invoice(partner.id, product3.id, 400)
        self.pay_invoice(invoice3)

        all_existing_comm = self.env["partner.communication.job"].search(
            [
                ("partner_id", "=", partner.id),
                ("state", "in", ("call", "pending")),
                ("config_id", "in", (thanks_partner_comm1 + thanks_partner_comm2).ids),
            ]
        )

        self.assertEqual(len(all_existing_comm), 2)
        self.assertNotEqual(prev_need_call, comm_to_watch.need_call)

    def create_invoice(self, partner_id, product_id, amount):
        invoice = self.env["account.invoice"].create(
            {
                "partner_id": partner_id,
                "currency_id": self.eur_currency.id,
                "name": "test",
                "account_id": self.account_receivable.id,
                "type": "out_invoice",
                "date_invoice": time.strftime("%Y-%m-%d"),
            }
        )
        self.env["account.invoice.line"].create(
            {
                "invoice_id": invoice.id,
                "product_id": product_id,
                "price_unit": amount,
                "quantity": 1,
                "name": "Great service",
                "account_id": self.account_revenue.id,
            }
        )
        invoice.action_post()
        return invoice

    def pay_invoice(self, invoices):
        bank_journal = self.env["account.journal"].search(
            [("code", "=", "BNK1")], limit=1
        )
        for invoice in invoices:
            payment = self.env["account.payment"].create(
                {
                    "journal_id": bank_journal.id,
                    "amount": invoice.amount_total,
                    "payment_date": invoice.date_due,
                    "payment_type": "inbound",
                    "payment_method_id": bank_journal.inbound_payment_method_ids[0].id,
                    "partner_type": "customer",
                    "partner_id": invoice.partner_id.id,
                    "currency_id": invoice.currency_id.id,
                    "invoice_ids": [(6, 0, invoice.ids)],
                }
            )
            payment.post()
