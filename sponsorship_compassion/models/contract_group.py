##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models

from .product_names import BIRTHDAY_GIFT, CHRISTMAS_GIFT


class ContractGroup(models.Model):
    _inherit = "recurring.contract.group"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    contains_sponsorship = fields.Boolean(
        string="Contains sponsorship",
        compute="_compute_contains_sponsorship",
        readonly=True,
        default=lambda s: s.env.context.get("default_type", None)
        and "S" in s.env.context.get("default_type", "O"),
    )

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################

    def _compute_contains_sponsorship(self):
        for group in self:
            group.contains_sponsorship = group.mapped("contract_ids").filtered(
                lambda s: s.type in ("S", "SC", "SWP")
                and s.state not in ("terminated", "cancelled")
            )

    def _generate_invoices(self, invoicer, contract_id=None):
        # Exclude gifts from regular generation
        super(
            ContractGroup, self.with_context(open_invoices_sponsorship_only=True)
        )._generate_invoices(invoicer, contract_id)
        # We don't generate gift if the contract isn't active
        contracts = self.mapped("contract_ids").filtered(lambda c: c.state == "active")
        contracts._generate_gifts(invoicer, BIRTHDAY_GIFT)
        contracts._generate_gifts(invoicer, CHRISTMAS_GIFT)
        return True

    def build_inv_line_data(
        self, invoicing_date=False, gift_wizard=False, contract_line=False
    ):
        # Push analytic account
        res = super().build_inv_line_data(invoicing_date, gift_wizard, contract_line)
        if gift_wizard:
            res[
                "analytic_account_id"
            ] = gift_wizard.contract_id.origin_id.analytic_id.id
        elif contract_line:
            res[
                "analytic_account_id"
            ] = contract_line.contract_id.origin_id.analytic_id.id
        return res

    def _get_partner_for_contract(self, contract):
        return (
            super(ContractGroup, self)._get_partner_for_contract(contract)
            if not contract.send_gifts_to
            else contract[contract.send_gifts_to]
        )
