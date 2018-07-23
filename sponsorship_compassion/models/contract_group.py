# -*- coding: utf-8 -*-
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
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.addons.queue_job.job import job, related_action
from .product import GIFT_NAMES

logger = logging.getLogger(__name__)


class ContractGroup(models.Model):
    _inherit = 'recurring.contract.group'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    contains_sponsorship = fields.Boolean(
        string='Contains sponsorship', compute='_compute_contains_sponsorship',
        readonly=True, default=lambda self: 'S' in self.env.context.get(
            'default_type', 'O'))

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################

    @api.multi
    def _compute_contains_sponsorship(self):
        for group in self:
            types = group.mapped('contract_ids.type')
            group.contains_sponsorship = 'S' in types or 'SC' in types

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    @job(default_channel='root.recurring_invoicer')
    @related_action(action='related_action_invoicer')
    @api.multi
    def _generate_invoices(self, invoicer=None):
        """ Add birthday gifts generation. """
        invoicer = self._generate_birthday_gifts(invoicer)
        invoicer = super(ContractGroup, self)._generate_invoices(invoicer)
        return invoicer

    @api.multi
    def _generate_birthday_gifts(self, invoicer=None):
        """ Creates the annual birthday gift for sponsorships that
        have set the option for automatic birthday gift creation. """
        logger.info("Automatic Birthday Gift Generation Started.")

        if invoicer is None:
            invoicer = self.env['recurring.invoicer'].with_context(
                lang='en_US').create({'source': self._name})

        # Search active Sponsorships with automatic birthday gift
        gen_states = self._get_gen_states()
        contract_search = [('birthday_invoice', '>', 0.0),
                           ('state', 'in', gen_states)]
        if self.ids:
            contract_search.append(('group_id', 'in', self.ids))
        contract_obj = self.env['recurring.contract']
        contracts = contract_obj.search(contract_search)

        # Exclude sponsorship if a gift is already open
        invl_obj = self.env['account.invoice.line']
        product_id = self.env['product.product'].with_context(
            lang='en_US').search(
            [('name', '=', GIFT_NAMES[0])])[0].id

        for contract in contracts:
            invl_ids = invl_obj.search([
                ('state', '=', 'open'),
                ('contract_id', '=', contract.id),
                ('product_id', '=', product_id)])
            if contract.project_id.hold_gifts or invl_ids:
                contracts -= contract

        if contracts:
            total = str(len(contracts))
            count = 1
            logger.info("Found {0} Birthday Gifts to generate.".format(total))

            gift_wizard = self.env['generate.gift.wizard'].with_context(
                recurring_invoicer_id=invoicer.id).create({
                    'description': 'Automatic birthday gift',
                    'origin': 'Automatic birthday gift',
                    'invoice_date': datetime.today().strftime(DF),
                    'product_id': product_id,
                    'amount': 0.0})

            # Generate invoices
            for contract in contracts:
                logger.info("Birthday Gift Generation: {0}/{1} ".format(
                    str(count), total))
                try:
                    self._generate_birthday_gift(gift_wizard, contract)
                except:
                    logger.error("Gift generation failed")
                finally:
                    count += 1

            gift_wizard.unlink()

        logger.info("Automatic Birthday Gift Generation Finished !!")
        return invoicer

    def _generate_birthday_gift(self, gift_wizard, contract):
        gift_wizard.write({
            'amount': contract.birthday_invoice})
        gift_wizard.with_context(
            active_ids=contract.id).generate_invoice()
