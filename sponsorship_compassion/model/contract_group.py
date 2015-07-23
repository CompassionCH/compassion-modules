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

from openerp.osv import orm, fields
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools.translate import _

from datetime import datetime

from .product import GIFT_NAMES, SPONSORSHIP_CATEGORY

import logging
logger = logging.getLogger(__name__)


class contract_group(orm.Model):
    _inherit = 'recurring.contract.group'

    def _contains_sponsorship(
            self, cr, uid, ids, field_name, args, context=None):
        res = dict()
        for group in self.browse(cr, uid, ids, context):
            if group.contract_ids:
                for contract in group.contract_ids:
                    if 'S' in contract.type:
                        res[group.id] = True
                        break
                else:
                    res[group.id] = False
            else:
                res[group.id] = True
        return res

    _columns = {
        'contains_sponsorship': fields.function(
            _contains_sponsorship, string=_('Contains sponsorship'),
            type='boolean', readonly=True)
    }

    _defaults = {
        'contains_sponsorship': lambda self, cr, uid, context: 'S' in
        context.get('default_type', 'O')
    }

    def generate_invoices(self, cr, uid, ids, invoicer_id=None, context=None):
        """ Add birthday gifts generation. """
        invoicer_id = self._generate_birthday_gifts(cr, uid, ids, invoicer_id,
                                                    context)
        invoicer_id = super(contract_group, self).generate_invoices(
            cr, uid, ids, invoicer_id, context)
        return invoicer_id

    def _generate_birthday_gifts(self, cr, uid, ids, invoicer_id=None,
                                 context=None):
        """ Creates the annual birthday gift for sponsorships that
        have set the option for automatic birthday gift creation. """
        logger.info("Automatic Birthday Gift Generation Started.")
        if context is None:
            context = dict()
        ctx = context.copy()
        ctx['lang'] = 'en_US'
        if invoicer_id is None:
            invoicer_id = self.pool.get('recurring.invoicer').create(
                cr, uid, {'source': self._name}, ctx)
        ctx['recurring_invoicer_id'] = invoicer_id

        # Search active Sponsorships with automatic birthday gift
        gen_states = self._get_gen_states()
        contract_search = [('birthday_invoice', '>', 0.0),
                           ('state', 'in', gen_states)]
        if ids:
            contract_search.append(('group_id', 'in', ids))
        contract_obj = self.pool.get('recurring.contract')
        contract_ids = contract_obj.search(cr, uid, contract_search,
                                           context=ctx)

        # Exclude sponsorship if a gift is already open
        invl_obj = self.pool.get('account.invoice.line')
        product_id = self.pool.get('product.product').search(
            cr, uid, [('name', '=', GIFT_NAMES[0])], context=ctx)[0]
        for con_id in list(contract_ids):
            invl_ids = invl_obj.search(cr, uid, [
                ('state', '=', 'open'),
                ('contract_id', '=', con_id),
                ('product_id', '=', product_id)], context=ctx)
            if invl_ids:
                contract_ids.remove(con_id)

        if contract_ids:
            total = str(len(contract_ids))
            count = 1
            logger.info("Found {0} Birthday Gifts to generate.".format(total))
            gift_wizard_obj = self.pool.get('generate.gift.wizard')
            gift_wizard_id = gift_wizard_obj.create(cr, uid, {
                'description': _('Automatic birthday gift'),
                'invoice_date': datetime.today().strftime(DF),
                'product_id': product_id,
                'amount': 0.0}, ctx)

            # Generate invoices
            for contract in contract_obj.browse(cr, uid, contract_ids,
                                                ctx):
                logger.info("Birthday Gift Generation: {0}/{1} ".format(
                    str(count), total))
                gift_wizard_obj.write(cr, uid, gift_wizard_id, {
                    'amount': contract.birthday_invoice}, ctx)
                ctx['active_ids'] = [contract.id]
                gift_wizard_obj.generate_invoice(cr, uid, [gift_wizard_id],
                                                 ctx)
                count += 1

            gift_wizard_obj.unlink(cr, uid, gift_wizard_id, ctx)

        logger.info("Automatic Birthday Gift Generation Finished !!")
        return invoicer_id

    def _setup_inv_line_data(self, cr, uid, contract_line, invoice_id,
                             context=None):
        """ Contract gifts relate their invoice lines to sponsorship,
            Correspondence sponsorships don't create invoice lines.
        """
        invl_data = False
        contract = contract_line.contract_id
        if contract.type != 'SC':
            invl_data = super(contract_group, self)._setup_inv_line_data(
                cr, uid, contract_line, invoice_id, context)
            # If project is suspended, either skip invoice or replace product
            if contract.type == 'S' and not \
                    contract.child_id.project_id.disburse_funds:
                config_obj = self.pool.get('ir.config_parameter')
                suspend_config_id = config_obj.search(cr, uid, [(
                    'key', '=', 'sponsorship_compassion.suspend_product_id')],
                    context=context)
                if not suspend_config_id:
                    return False
                current_product = self.pool.get('product.product').browse(
                    cr, uid, invl_data['product_id'], {'lang': 'en_US'})
                if current_product.categ_name == SPONSORSHIP_CATEGORY:
                    product_id = int(config_obj.browse(
                        cr, uid, suspend_config_id[0], context).value)
                    invl_data.update(self.pool.get(
                        'recurring.contract').get_suspend_invl_data(
                        cr, uid, product_id, context))

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

        return invl_data
