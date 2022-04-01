##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from collections import defaultdict
from datetime import datetime, timedelta

from odoo import models, api, fields, _
from odoo.exceptions import UserError
from odoo.addons.queue_job.job import job

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.model
    def mobile_post_invoice(self, json_data, **parameters):
        """
            Mobile app method:
            POST a Donation for a children or a pool

            When the user is paying for sponsorship
                - Find the oldest open partner invoice (created monthly)
                - Check if the amount and number of sponsorships are matching
                - If found, it will reuse the invoice, otherwise it will warn staff.
            Notes:
            - The app sends a single product of 50.- for the sponsorships by wrongly
            merging the fund donation into the sponsorship product

            :param json_data:
            :param parameters:
            :return: sample response
        """
        wrapper = DonationDataWrapper(json_data, self.sudo().env)
        result = {
            "Gift": [],
            "Donation": [],
            # The typo is on purpose (UK did this)
            "SendAGiftPublishResult": "Donation data Recieved."
            if wrapper.gift_treated
            else "Cannot send the appeals/gifts",
        }
        if wrapper.gift_treated or not wrapper.partner_id:
            return result

        payments = (
            wrapper.child_gifts + wrapper.fund_donations
        )

        if 'android' in wrapper.source:
            utc_medium = self.env.ref("sms_sponsorship.utm_medium_android")
        else:
            utc_medium = self.env.ref("sms_sponsorship.utm_medium_ios")

        invoice_lines_values = []
        for payment in payments:
            l_vals = {
                "product_id": payment["product_id"].id,
                "account_id": payment["product_id"].property_account_income_id.id,
                "quantity": 1,
                "price_unit": payment["amount"],
                "name": payment["product_id"].name,
                "medium_id": utc_medium.id,
            }
            if "contract_id" in payment:
                l_vals["contract_id"] = payment["contract_id"].id

            invoice_lines_values.append(l_vals)

        # create invoice and merge lines
        lines_cmd = [(0, 0, v) for v in invoice_lines_values]
        invoice = self.sudo()
        delay = datetime.now() + timedelta(minutes=15)

        if wrapper.sponsorships_payments:
            # User is paying for sponsorship: only if everything match an open invoice,
            # we will use it.
            total_sponsorship = sum(map(
                lambda sp: float(sp.get("amount", 0)), wrapper.sponsorships_payments))
            sponsorships = self.env["recurring.contract"].sudo()
            for sp in wrapper.sponsorships_payments:
                sponsorships += sp.get("contract_id")
            # Generate invoices to increase chance for donation to match
            sponsorships.button_generate_invoices()
            sponsorship_invoice = invoice.search(
                [
                    ("partner_id", "=", wrapper.partner_id),
                    ("state", "=", "open"),
                    ("amount_total", "=", total_sponsorship),
                    ("invoice_category", "=", "sponsorship")
                ],
                order="date asc",
                limit=1,
            )
            sp_invoice_contracts = sponsorship_invoice.invoice_line_ids.mapped(
                "contract_id"
            )
            common_sponsorships = sp_invoice_contracts & sponsorships
            if common_sponsorships and len(common_sponsorships) == len(
                    sp_invoice_contracts
            ):
                invoice = sponsorship_invoice
                invoice.origin = wrapper.source + " sponsorship payment"
                if lines_cmd:
                    # Merge other donations into the sponsorship invoice
                    if wrapper.child_gifts:
                        # We don't allow merging child gifts and sponsorship
                        raise UserError(_(
                            "You cannot pay your sponsorship with gifts at the "
                            "same time. Please make two separate donations."))
                    invoice.action_invoice_cancel()
                    invoice.action_invoice_draft()
                    invoice.write({"invoice_line_ids": lines_cmd})
                    for line in invoice.invoice_line_ids:
                        bckp_price = line.price_unit
                        line._onchange_product_id()
                        line.price_unit = bckp_price
                    invoice.action_invoice_open()
                    invoice.message_post(
                        body="Sponsorship invoice used for mobile app donation.")
                    invoice.with_delay(eta=delay).remove_mobile_donation_if_not_paid()
            else:
                # No matching sponsorship payment, we don't accept the payment
                raise UserError(_(
                    "Your sponsorship payment doesn't match any expected payment. "
                    "Please reach to our team to check what is due."))

        if not invoice:
            invoice = self.sudo().create(
                {
                    "partner_id": wrapper.partner_id,
                    "invoice_line_ids": lines_cmd,
                    "origin": wrapper.source,
                    "type": "out_invoice",
                    "date_invoice": fields.Date.today(),
                    "auto_cancel_date": delay,
                    "payment_mode_id": False  # We don't know yet how it will be paid
                }
            )
            for line in invoice.invoice_line_ids:
                bckp_price = line.price_unit
                line._onchange_product_id()
                line.price_unit = bckp_price
            invoice.action_invoice_open()

        result["Donation"].append(invoice.id)
        return result

    def action_invoice_paid(self):
        """
        Notify the sponsor that we received the donation.
        :return:
        """
        res = super(AccountInvoice, self).action_invoice_paid()
        for invoice in self:
            partner = invoice.partner_id
            has_app = self.env['firebase.registration'].search_count([
                ('partner_id', '=', partner.id)
            ])
            if invoice.invoice_category in ('gift', 'fund') and has_app \
                    and not invoice.avoid_thankyou_letter:
                invoice.send_mobile_notification()
        return res

    def send_mobile_notification(self):
        self.ensure_one()
        payment_moves = self.mapped("payment_move_line_ids.move_id")
        if payment_moves.mapped("mobile_notification_id"):
            # Avoid sending duplicate notifications
            return True

        partner = self.partner_id
        # This ensures the translation func is done in the right language _()
        context = {"lang": partner.lang}
        lines = self.mapped("invoice_line_ids").with_context(context)
        children = lines.mapped("contract_id.child_id")
        amount, for_text = lines.get_donations()
        for_text = for_text or _("one of our fund")
        if children:
            if len(children) > 1:
                for_text = children.get_number()
            else:
                for_text = children.preferred_name

        notification = self.env["firebase.notification"].create(
            {
                "topic": "spam",  # to ensure he will receive the notification
                "destination": "Donation",  # to put the gift icon
                "product_template_id": lines.mapped(
                    "product_id.product_tmpl_id")[:1].id,
                "partner_ids": [(6, 0, partner.ids)],
                "title": _("You gave CHF %s.- for %s") % (amount, for_text),
                "body": _("Thank you for your generosity!"),
                "res_model": self._name,
                "res_id": self.id
            }
        )
        notification.send()
        payment_moves.write({"mobile_notification_id": notification.id})
        return True

    @job(default_channel="root.mobile_app_connector")
    def remove_mobile_donation_if_not_paid(self):
        """ Job utility to remove donation from sponsorship invoice in case the
        transaction was aborted. """
        self.ensure_one()
        sponsorship_category = self.env.ref(
            "sponsorship_compassion.product_category_sponsorship")
        if self.state == "open":
            self.action_invoice_cancel()
            self.action_invoice_draft()
            self.env.clear()
            self.mapped("invoice_line_ids").filtered(
                lambda l: l.product_id.categ_id != sponsorship_category).unlink()
            self.origin = False
            self.action_invoice_open()
            self.message_post(
                body="Removed mobile donation as no payment was received")
        return True


class DonationDataWrapper:
    def __init__(self, json, env):
        self.partner_id = int(json.get("supporter", 0) or 0)
        self.gift_treated = json.get("LastInsertedDonationId") or json.get(
            "LastInsertedGiftId"
        )
        self.source = json.get("source", "iOS")

        self.fund_donations = []
        self.sponsorships_payments = []
        self.child_gifts = []

        fund_ids = json.get("appealtype", [])
        fund_amounts = json.get("appealamount", [])
        gift_products = json.get("gifttype", [])
        gift_amounts = json.get("giftamount", [])
        child_ids = json.get("need", [])

        # Map fund donations to products
        product_obj = env["product.product"].sudo()
        for i, product_id in enumerate(fund_ids):
            product = product_obj.search(
                [("product_tmpl_id", "=", product_id)], limit=1
            )
            if not product:
                raise ValueError(_("The product %s was not found") % product_id)
            self.fund_donations.append(
                {"product_id": product, "amount": fund_amounts[i], }
            )

        # Map gift_products (gifts and sponsorships payments)
        for i, product_id in enumerate(gift_products):
            product = product_obj.search(
                [("product_tmpl_id", "=", product_id)], limit=1
            )
            if not product:
                raise ValueError(_("The product %s was not found") % product_id)

            spn = (
                env["recurring.contract"]
                .search(
                    [
                        ("child_id", "=", child_ids[i]),
                        "|",
                        ("correspondent_id", "=", self.partner_id),
                        ("partner_id", "=", self.partner_id),
                        ("state", "not in", ["terminated", "cancelled"]),
                    ]
                )
                .ensure_one()
            )
            p = {
                "contract_id": spn,
                "child_id": child_ids[i],
                "product_id": product,
                "amount": gift_amounts[i],
            }
            if product.product_tmpl_id == env.ref(
                    "sponsorship_compassion.product_template_sponsorship"
            ):
                self.sponsorships_payments.append(p)
            else:
                self.child_gifts.append(p)

    def is_multiple_months_payment(self):
        # check whether the user is trying to pay multiple times for a single contract
        d = defaultdict(list)
        for spn in self.sponsorships_payments:
            d[spn["contract_id"].id].append(spn)
        return any(len(d[x]) > 1 for x in d)
