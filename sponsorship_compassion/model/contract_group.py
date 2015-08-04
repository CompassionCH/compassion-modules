# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester, Emanuel Cino
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import api, fields, models
from openerp.osv import orm
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools.translate import _

from datetime import datetime

from .product import GIFT_NAMES, SPONSORSHIP_CATEGORY

import logging
import time

logger = logging.getLogger(__name__)


class contract_group(models.Model):
    _inherit = 'recurring.contract.group'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    contains_sponsorship = fields.Boolean(
        string='Contains sponsorship', compute='_contains_sponsorship',
        readonly=True, default=lambda self: 'S' in self.env.context.get(
            'default_type', 'O'))

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################

    @api.one
    def _contains_sponsorship(self):
        types = self.mapped('contract_ids.type')
        self.contains_sponsorship = 'S' in types or 'SC' in types

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################

    def generate_invoices(self, invoicer=None):
        """ Add birthday gifts generation. """
        invoicer = self._generate_birthday_gifts(invoicer)
        invoicer = super(contract_group, self).generate_invoices(invoicer)
        return invoicer

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################

    @api.multi
    def _generate_birthday_gifts(self, invoicer=None):
        """ Creates the annual birthday gift for sponsorships that
        have set the option for automatic birthday gift creation. """
        logger.info("Automatic Birthday Gift Generation Started.")

        if invoicer is None:
            invoicer = self.env['recurring.invoicer'].with_context(
                lang='en_US').create({'source': self._name})

        self.env.context = self.with_context(
            {'lang': 'en_US',
             'recurring_invoicer_id': invoicer.id}).env.context

        # Search active Sponsorships with automatic birthday gift
        gen_states = self._get_gen_states()
        contract_search = [('birthday_invoice', '>', 0.0),
                           ('state', 'in', gen_states)]
        if self.ids:
            contract_search.append(('group_id', 'in', self.ids))
        contract_obj = self.env['recurring.contract']
        contract_ids = contract_obj.search(contract_search).ids

        # Exclude sponsorship if a gift is already open
        invl_obj = self.env['account.invoice.line']
        product_id = self.env['product.product'].search(
            [('name', '=', GIFT_NAMES[0])])[0].id

        for con_id in contract_ids:
            invl_ids = invl_obj.search([
                ('state', '=', 'open'),
                ('contract_id', '=', con_id),
                ('product_id', '=', product_id)])
            if invl_ids:
                contract_ids.remove(con_id)

        if contract_ids:
            total = str(len(contract_ids))
            count = 1
            logger.info("Found {0} Birthday Gifts to generate.".format(total))

            gift_wizard = self.env['generate.gift.wizard'].create({
                'description': _('Automatic birthday gift'),
                'invoice_date': datetime.today().strftime(DF),
                'product_id': product_id,
                'amount': 0.0})

            # Generate invoices
            for contract in contract_obj.browse(contract_ids):
                logger.info("Birthday Gift Generation: {0}/{1} ".format(
                    str(count), total))
                gift_wizard.write({
                    'amount': contract.birthday_invoice})
                gift_wizard.with_context(
                    active_ids=contract.id).generate_invoice()
                count += 1

            gift_wizard.unlink()

        logger.info("Automatic Birthday Gift Generation Finished !!")
        return invoicer

    @api.multi
    def _setup_inv_line_data(self, contract_line, invoice):
        """ Contract gifts relate their invoice lines to sponsorship,
            Correspondence sponsorships don't create invoice lines.
            Add analytic account to invoice_lines.
        """
        invl_data = False
        contract = contract_line.contract_id
        if contract.type != 'SC':
            invl_data = super(contract_group, self)._setup_inv_line_data(
                contract_line, invoice)

            # If project is suspended, either skip invoice or replace product
            if contract.type == 'S' and not \
                    contract.child_id.project_id.disburse_funds:
                config_obj = self.env['ir.config_parameter']
                suspend_config_id = config_obj.search([(
                    'key', '=',
                    'sponsorship_compassion.suspend_product_id')])
                if not suspend_config_id:
                    return False
                current_product = self.env['product.product'].with_context(
                    lang='en_US').browse(invl_data['product_id'])
                if current_product.categ_name == SPONSORSHIP_CATEGORY:
                    invl_data.update(self.env[
                        'recurring.contract'].get_suspend_invl_data(
                            suspend_config_id.id))

            if contract.type == 'G':
                sponsorship = contract_line.sponsorship_id
                if sponsorship.state in self._get_gen_states():
                    invl_data['contract_id'] = sponsorship.id
                else:
                    raise orm.except_orm(
                        _('Invoice generation error'),
                        _('No active sponsorship found for child {0}. '
                          'The gift contract with id {1} is not valid.')
                        .format(sponsorship.child_code, str(contract.id)))

            product_id = contract_line.product_id.id
            partner_id = contract_line.contract_id.partner_id.id
            analytic = self.env['account.analytic.default'].account_get(
                product_id, partner_id, time.strftime('%Y-%m-%d'))
            if analytic and analytic.analytic_id:
                invl_data.update({
                    'account_analytic_id': analytic.analytic_id.id})

        return invl_data
