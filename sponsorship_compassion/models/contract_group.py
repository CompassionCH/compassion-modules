##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging
from datetime import datetime

from odoo import api, fields, models
from .product_names import GIFT_REF

logger = logging.getLogger(__name__)


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
    change_method = fields.Selection(default="clean_invoices")

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################

    def _compute_contains_sponsorship(self):
        for group in self:
            group.contains_sponsorship = group.mapped("contract_ids").filtered(
                lambda s: s.type in ("S", "SC", "SWP") and s.state not in (
                    "terminated", "cancelled")
            )

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _generate_invoices(self, invoicer=None, **kwargs):
        """ Add birthday gifts generation. """
        invoicer = self._generate_birthday_gifts(invoicer)
        invoicer = super()._generate_invoices(invoicer, **kwargs)
        return invoicer

    def _generate_birthday_gifts(self, invoicer=None):
        """ Creates the annual birthday gift for sponsorships that
        have set the option for automatic birthday gift creation. """
        logger.debug("Automatic Birthday Gift Generation Started.")

        if invoicer is None:
            invoicer = (
                self.env["recurring.invoicer"].with_context(lang="en_US").create({})
            )

        # Search active Sponsorships with automatic birthday gift
        gen_states = self._get_gen_states()
        contract_search = [("birthday_invoice", ">", 0.0), ("state", "in", gen_states)]
        if self.ids:
            contract_search.append(("group_id", "in", self.ids))
        contract_obj = self.env["recurring.contract"]
        contracts = contract_obj.search(contract_search)

        # Exclude sponsorship if a gift is already open
        invl_obj = self.env["account.move.line"]
        product_id = (
            self.env["product.product"]
                .search([("default_code", "=", GIFT_REF[0])], limit=1)
                .id
        )

        for contract in contracts:
            invl_ids = invl_obj.search(
                [
                    ("state", "=", "posted"),
                    ("contract_id", "=", contract.id),
                    ("product_id", "=", product_id),
                ]
            )
            if contract.project_id.hold_gifts or invl_ids:
                contracts -= contract

        if contracts:
            total = str(len(contracts))
            count = 1
            logger.debug(f"Found {total} Birthday Gifts to generate.")

            gift_wizard = (
                self.env["generate.gift.wizard"]
                    .with_context(recurring_invoicer_id=invoicer.id)
                    .create(
                    {
                        "description": "Automatic birthday gift",
                        "invoice_date": datetime.today().date(),
                        "product_id": product_id,
                        "amount": 0.0,
                    }
                )
            )

            # Generate invoices
            for contract in contracts:
                logger.debug(f"Birthday Gift Generation: {count}/{total} ")
                try:
                    self._generate_birthday_gift(gift_wizard, contract)
                except:
                    logger.error("Gift generation failed")
                finally:
                    count += 1

        logger.debug("Automatic Birthday Gift Generation Finished !!")
        return invoicer

    def _generate_birthday_gift(self, gift_wizard, contract):
        gift_wizard.write({"amount": contract.birthday_invoice})
        gift_wizard.with_context(active_ids=contract.id).generate_invoice()
