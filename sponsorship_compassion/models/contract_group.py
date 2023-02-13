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
from odoo.addons.recurring_contract.models.product_names import CHRISTMAS_GIFT, BIRTHDAY_GIFT


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
                lambda s: s.type in ("S", "SC", "SWP") and s.state not in (
                    "terminated", "cancelled")
            )

    def _generate_invoices(self):
        invoicer = super()._generate_invoices()
        # We don't generate gift if the contract isn't active
        contracts = self.contract_ids.filtered(lambda c: c.state == 'active')
        contracts._generate_gifts(invoicer, BIRTHDAY_GIFT)
        contracts._generate_gifts(invoicer, CHRISTMAS_GIFT)
        return invoicer