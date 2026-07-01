##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, fields, models


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
    @api.depends("contract_ids", "contract_ids.type", "contract_ids.state")
    def _compute_contains_sponsorship(self):
        for group in self:
            group.contains_sponsorship = group.mapped("contract_ids").filtered(
                lambda s: s.type in ("S", "SC", "SWP")
                and s.state not in ("terminated", "cancelled")
            )

    def _generate_invoices(self):
        # Exclude gifts from regular generation
        super(
            ContractGroup, self.with_context(open_invoices_sponsorship_only=True)
        )._generate_invoices()
        contracts = self.active_contract_ids
        if contracts:
            contracts._generate_gifts(
                self.env.ref("sponsorship_compassion.gift_type_birthday")
            )
            contracts._generate_gifts(
                self.env.ref("sponsorship_compassion.gift_type_christmas")
            )
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

    def _should_skip_invoice_generation(
        self, invoicing_date, contracts, skip_suspended=True
    ):
        self.ensure_one()
        # T2325 For gift contracts,
        # we should check that all originating sponsorships were invoiced
        has_all_gifts = True
        gift_contracts = contracts.filtered(lambda c: c.type == "G")
        if gift_contracts:
            sponsorships = gift_contracts.mapped("contract_line_ids.sponsorship_id")
            already_invoiced = (
                self.env["account.move.line"]
                .search(
                    [
                        ("move_id.invoice_date", "=", invoicing_date),
                        ("contract_id", "in", sponsorships.ids),
                        ("product_id", "in", gift_contracts.mapped("product_ids").ids),
                    ]
                )
                .mapped("contract_id")
            )
            has_all_gifts = len(sponsorships) == len(already_invoiced)

        # If invoices come from sub proposal, ignore group suspension
        # to also generate already paid invoices
        is_sub_proposal = contracts.mapped(
            "parent_id.child_id"
        ) and not contracts.mapped("invoice_line_ids")
        if is_sub_proposal:
            skip_suspended = False
        has_all_other_invoices = super()._should_skip_invoice_generation(
            invoicing_date, contracts - gift_contracts, skip_suspended
        )
        return has_all_gifts and has_all_other_invoices
