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

    def _generate_invoices(self, invoicer, contract_ids=None):
        # Exclude gifts from regular generation
        super(
            ContractGroup, self.with_context(open_invoices_sponsorship_only=True)
        )._generate_invoices(invoicer, contract_ids)
        if contract_ids:
            contracts = self.env["recurring.contract"].browse(contract_ids).exists()
        else:
            contracts = self.mapped("contract_ids")
        # We don't generate gift if the contract isn't active
        contracts = contracts.filtered(lambda c: c.state == "active")
        if contracts:
            contracts._generate_gifts(invoicer, BIRTHDAY_GIFT)
            contracts._generate_gifts(invoicer, CHRISTMAS_GIFT)
        return True

    def build_inv_line_data(
        self, invoicing_date=False, gift_wizard=False, contract_line=False
    ):
        # Push parent sponsorship for gift contracts
        res = super().build_inv_line_data(invoicing_date, gift_wizard, contract_line)
        if contract_line and contract_line.contract_id.type == "G":
            res["contract_id"] = contract_line.sponsorship_id
        return res

    def _get_partner_for_contract(self, contract, gift_wizard=False):
        if gift_wizard and contract.send_gifts_to:
            return contract[contract.send_gifts_to]
        return super()._get_partner_for_contract(contract, gift_wizard)

    def _get_open_invoices_filter(self, invoicing_date, contracts):
        if contracts is None:
            contracts = self.active_contract_ids
        # T2325 Include originating sponsorships for gift contracts
        # to avoid duplicate invoices
        contracts |= contracts.mapped("contract_line_ids.sponsorship_id")
        return super()._get_open_invoices_filter(invoicing_date, contracts)

    def _should_skip_invoice_generation(
        self, invoicing_date, contracts=None, skip_suspended=True
    ):
        # If invoices come from sub proposal, ignore group suspension
        # to also generate already paid invoices
        self.ensure_one()
        check_contracts = contracts or self.active_contract_ids
        is_sub_proposal = check_contracts.mapped(
            "parent_id.child_id"
        ) and not check_contracts.mapped("invoice_line_ids")
        skip_suspended = not is_sub_proposal
        return super()._should_skip_invoice_generation(
            invoicing_date, contracts, skip_suspended
        )
