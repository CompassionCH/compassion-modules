##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import calendar
import datetime

from odoo import _, fields, models

from odoo.addons.sponsorship_compassion.models.product_names import GIFT_CATEGORY


class SponsorshipContract(models.Model):
    _inherit = "recurring.contract"

    number_gifts = fields.Integer(compute="_compute_nb_gifts")

    def _compute_nb_gifts(self):
        gift_obj = self.env["sponsorship.gift"]
        for contract in self:
            sponsorship_ids = contract.ids
            if contract.type == "G":
                sponsorship_ids = contract.mapped("contract_line_ids.sponsorship_id.id")
            contract.number_gifts = gift_obj.search_count(
                [
                    ("sponsorship_id", "in", sponsorship_ids),
                ]
            )

    def invoice_paid(self, invoice):
        """Prevent to reconcile invoices for fund-suspended projects
        or sponsorships older than 3 months."""
        for invl in invoice.invoice_line_ids:
            existing_gift_for_invl = self.env["sponsorship.gift"].search(
                [("invoice_line_ids", "in", invl.id)]
            )
            if (
                invl.product_id.categ_name == GIFT_CATEGORY
                and invl.contract_id.child_id
                and not existing_gift_for_invl
            ):
                # Create the Sponsorship Gift
                gift = self.env["sponsorship.gift"].create_from_invoice_line(invl)

                if not invl.contract_id.is_active:
                    gift.message_post(body="Associated contract is not active")
                    gift.state = "verify"

        super().invoice_paid(invoice)

    def contract_active(self):
        res = super().contract_active()

        for contract in self:
            if contract.is_active:
                for invl in contract.invoice_line_ids.filtered("gift_id"):
                    gift = invl.gift_id
                    if gift.state == "verify":
                        gift.state = "draft"
                        if gift.message_id.state == "postponed":
                            gift.message_id.state = "new"

        return res

    def open_gifts(self):
        sponsorship_ids = self.ids
        if self.type == "G":
            sponsorship_ids = self.mapped("contract_line_ids.sponsorship_id.id")
        return {
            "name": _("Sponsorship gifts"),
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "res_model": "sponsorship.gift",
            "domain": [("sponsorship_id", "in", sponsorship_ids)],
            "context": self.env.context,
            "target": "current",
        }

    def hold_gifts(self):
        for contract in self:
            today = datetime.date.today()
            first_day = today.replace(day=1)
            last_day = today.replace(
                day=calendar.monthrange(today.year, today.month)[1]
            )
            suspended_gifts = self.env["sponsorship.gift"].search(
                [
                    ("child_id.project_id", "=", contract.project_id.id),
                    ("create_date", ">=", first_day),
                    ("create_date", "<=", last_day),
                    ("state", "=", "In Progress"),
                ]
            )
            suspended_gifts.action_suspended()

        # Postpone open gifts (not received by GMC).
        pending_gifts = self.env["sponsorship.gift"].search(
            [("sponsorship_id", "in", self.ids), ("gmc_gift_id", "=", False)]
        )
        pending_gifts.action_verify()

    def reactivate_gifts(self):
        for contract in self:
            suspended_gifts = self.env["sponsorship.gift"].search(
                [
                    ("child_id.project_id", "=", contract.project_id.id),
                    ("state", "=", "suspended"),
                ]
            )
            suspended_gifts.action_in_progress()

        # Put again gifts in OK state.
        pending_gifts = self.env["sponsorship.gift"].search(
            [("sponsorship_id", "in", self.ids), ("state", "=", "verify")]
        )
        pending_gifts = pending_gifts.filtered(lambda g: g.is_eligible()[0])
        pending_gifts.action_ok()
