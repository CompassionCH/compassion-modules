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
from .product_names import GIFT_PRODUCTS_REF, CHRISTMAS_GIFT, BIRTHDAY_GIFT, PRODUCT_GIFT_CHRISTMAS

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
        """ Generates gifts invoices """
        invoicer = self._generate_gifts(invoicer, CHRISTMAS_GIFT)
        invoicer = self._generate_gifts(invoicer, BIRTHDAY_GIFT)
        invoicer = super()._generate_invoices(invoicer, **kwargs)
        return invoicer

    def _generate_gifts(self, invoicer=None, gift_type=None):
        """ Creates the annual gifts for sponsorships that
        have set the option for automatic birthday or christmas gifts creation. """
        if not gift_type:
            raise Exception(f"Can't be called with an invalid gift type {gift_type}. The value should either be {CHRISTMAS_GIFT} or {BIRTHDAY_GIFT}")
        logger.debug(f"Automatic {gift_type} Gift Generation Started.")

        if invoicer is None:
            invoicer = (
                self.env["recurring.invoicer"].with_context(lang="en_US").create({})
            )

        # Search active Sponsorships with automatic birthday gift
        gen_states = self._get_gen_states()
        contract_search = [(f"{gift_type}_invoice", ">", 0.0), ("state", "in", gen_states)]
        if self.ids:
             contract_search.append(("group_id", "in", self.ids))
        contract_obj = self.env["recurring.contract"]
        contracts = contract_obj.search(contract_search)

        # Exclude sponsorship if a gift is already open
        invl_obj = self.env["account.move.line"]
        product_id = (
            self.env["product.product"]
                .with_company(contracts.company_id.id)
                .search([("default_code", "=", GIFT_PRODUCTS_REF[0] if gift_type == BIRTHDAY_GIFT else PRODUCT_GIFT_CHRISTMAS)], limit=1)
                .id
        )

        for contract in contracts:
            if contract.project_id.hold_gifts:
                contracts -= contract

        if contracts:
            total = str(len(contracts))
            count = 1
            logger.debug(f"Found {total} {gift_type} Gifts to generate.")

            gift_wizard = (
                self.env["generate.gift.wizard"]
                    .with_context(recurring_invoicer_id=invoicer.id)
                    .create(
                    {
                        "description": f"Automatic {gift_type} gift",
                        "invoice_date": datetime.today().date(),
                        "product_id": product_id,
                        "amount": 0.0,
                    }
                )
            )

            # Generate invoices
            for contract in contracts:
                logger.debug(f"{gift_type} Gift Generation: {count}/{total} ")
                try:
                    self._generate_gift(gift_wizard, contract, gift_type)
                except Exception as e:
                    logger.error(f"Gift generation failed. {e}")
                finally:
                    count += 1

        logger.debug(f"Automatic {gift_type} Gift Generation Finished !!")
        return invoicer

    def _generate_gift(self, gift_wizard, contract, gift_type):
        gift_wizard.write({"amount": contract.christmas_invoice if gift_type == CHRISTMAS_GIFT else contract.birthday_invoice})
        gift_wizard.with_context(active_ids=contract.id).generate_invoice()
