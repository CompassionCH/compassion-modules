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
        cls.env.ref(
            "l10n_generic_coa.configurable_chart_template"
        ).try_loading_for_current_company()
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
            {"min_donation_amount": 50.0, "send_mode": "auto_digital_only", }
        )

    def test_success_stories_set(self):
        """ Pay some invoices and test the success stories are
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
        invoice.action_invoice_open()
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
