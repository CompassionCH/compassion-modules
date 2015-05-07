# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import netsvc
from openerp.osv import orm, fields
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools import mod10r
from openerp.tools.translate import _

from datetime import datetime
from dateutil.relativedelta import relativedelta
import time

import logging

logger = logging.getLogger(__name__)


class generate_gift_wizard(orm.TransientModel):
    """ This wizard generates a Gift Invoice for a given contract. """
    _name = 'generate.gift.wizard'

    _columns = {
        'amount': fields.float(_("Gift Amount"), required=True),
        'product_id': fields.many2one(
            'product.product', _("Gift Type"), required=True),
        'invoice_date': fields.date(_("Invoice date")),
        'description': fields.char(_("Additional comments"), size=200),
    }

    _defaults = {
        'invoice_date': datetime.today().strftime(DF),
    }

    def generate_from_cron(self, cr, uid, context=None):
        """ Creates the annual birthday gift for LSV/DD contracts that
        have set the option for automatic withdrawal. """
        logger.info("Automatic Birthday Gift Withdrawal CRON Started.")
        if context is None:
            context = dict()

        contract_obj = self.pool.get('recurring.contract')
        invl_obj = self.pool.get('account.invoice.line')
        gen_states = self.pool.get(
            'recurring.contract.group')._get_gen_states()
        product_id = self.pool.get('product.product').search(
            cr, uid, [('name', '=', 'Birthday Gift')],
            context={'lang': 'en_US'})[0]

        # Search active LSV/DD Sponsorships with birthday withdrawal
        contract_ids = contract_obj.search(cr, uid, [
            ('birthday_withdrawal', '>', 0.0),
            ('state', 'in', gen_states),
            '|', ('payment_term_id.name', 'ilike', 'LSV'),
            ('payment_term_id.name', 'ilike', 'Postfinance')],
            context=context)
        # Exclude sponsorship if a gift is already open
        for con_id in list(contract_ids):
            invl_ids = invl_obj.search(cr, uid, [
                ('state', '=', 'open'),
                ('contract_id', '=', con_id),
                ('product_id', '=', product_id)], context=context)
            if invl_ids:
                contract_ids.remove(con_id)

        if contract_ids:
            total = str(len(contract_ids))
            count = 1
            logger.info("Found {0} Birthday Gifts to generate.".format(total))
            wf_service = netsvc.LocalService('workflow')
            wizard_id = self.create(cr, uid, {
                'description': _('Automatic withdrawal for birthday gift'),
                'invoice_date': datetime.today().strftime(DF),
                'product_id': product_id}, context)

            # Generate and validate invoices
            for contract in contract_obj.browse(cr, uid, contract_ids,
                                                context):
                logger.info("Invoice Generation: {0}/{1} ".format(
                    str(count), total))
                self.write(cr, uid, wizard_id, {
                    'amount': contract.birthday_withdrawal}, context)
                context['active_ids'] = [contract.id]
                invoice_id = self.generate_invoice(
                    cr, uid, [wizard_id], context)['domain'][0][2][0]
                wf_service.trg_validate(
                    uid, 'account.invoice', invoice_id, 'invoice_open', cr)
                count += 1

            self.unlink(cr, uid, wizard_id, context)

        logger.info("Automatic Birthday Gift Withdrawal CRON Finished !!")
        return True

    def generate_invoice(self, cr, uid, ids, context=None):
        # Read data in english
        if context is None:
            context = {}
        ctx = context.copy()
        ctx['lang'] = 'en_US'
        # Ids of contracts are stored in context
        wizard = self.browse(cr, uid, ids[0], ctx)
        invoice_ids = list()
        for contract in self.pool.get('recurring.contract').browse(
                cr, uid, context.get('active_ids', list()), ctx):
            partner = contract.partner_id

            if contract.type == 'S' and contract.state == 'active':
                invoice_obj = self.pool.get('account.invoice')
                journal_ids = self.pool.get('account.journal').search(
                    cr, uid,
                    [('type', '=', 'sale'), ('company_id', '=', 1 or False)],
                    limit=1)

                if wizard.product_id.name == 'Birthday Gift':
                    invoice_date = self.compute_date_birthday_invoice(
                        contract.child_id.birthdate, wizard.invoice_date)
                else:
                    invoice_date = wizard.invoice_date

                inv_data = {
                    'account_id': partner.property_account_receivable.id,
                    'type': 'out_invoice',
                    'partner_id': partner.id,
                    'journal_id': len(journal_ids) and journal_ids[0] or False,
                    'date_invoice': invoice_date,
                    'payment_term': 1,  # Immediate payment
                    'bvr_reference': self._generate_bvr_reference(
                        contract, wizard.product_id),
                }

                invoice_id = invoice_obj.create(cr, uid, inv_data,
                                                context=context)
                if invoice_id:
                    self._generate_invoice_line(
                        cr, uid, invoice_id, wizard, contract, context=ctx)
                    invoice_ids.append(invoice_id)
            else:
                raise orm.except_orm(
                    _("Generation Error"),
                    _("You can only generate gifts for active child "
                      "sponsorships"))
        return {
            'name': _('Generated Invoices'),
            'view_mode': 'tree,form',
            'view_type': 'form',
            'res_model': 'account.invoice',
            'domain': [('id', 'in', invoice_ids)],
            'context': {'form_view_ref': 'account.invoice_form'},
            'type': 'ir.actions.act_window',
        }

    def _generate_invoice_line(self, cr, uid, invoice_id, wizard,
                               contract, context=None):
        product = wizard.product_id

        inv_line_data = {
            'name': wizard.description,
            'account_id': product.property_account_income.id,
            'price_unit': wizard.amount,
            'quantity': 1,
            'uos_id': False,
            'product_id': product.id or False,
            'invoice_id': invoice_id,
            'contract_id': contract.id,
        }

        # Define analytic journal
        analytic = self.pool.get('account.analytic.default').account_get(
            cr, uid, product.id, contract.partner_id.id, uid,
            time.strftime(DF), context=context)
        if analytic and analytic.analytics_id:
            inv_line_data['analytics_id'] = analytic.analytics_id.id

        # Give a better name to invoice_line
        if not wizard.description:
            inv_line_data['name'] = contract.child_id.code
            inv_line_data['name'] += " - " + contract.child_id.birthdate \
                if product.name == 'Birthday Gift' else ""

        self.pool.get('account.invoice.line').create(
            cr, uid, inv_line_data, context=context)

        return True

    def _generate_bvr_reference(self, contract, product):
        gift_bvr_ref = {
            'Birthday Gift': 1,
            'General Gift': 2,
            'Family Gift': 3,
            'Project Gift': 4,
            'Graduation Gift': 5
        }
        ref = contract.partner_id.ref
        bvr_reference = '0' * (9 + (7 - len(ref))) + ref
        num_pol_ga = str(contract.num_pol_ga)
        bvr_reference += '0' * (5 - len(num_pol_ga)) + num_pol_ga
        # Type of gift
        bvr_reference += str(gift_bvr_ref[product.name])
        bvr_reference += '0' * 4

        if contract.group_id.payment_term_id and \
                'LSV' in contract.group_id.payment_term_id.name:
            bvr_reference = '004874969' + bvr_reference[9:]
        if len(bvr_reference) == 26:
            return mod10r(bvr_reference)

    def fields_view_get(self, cr, user, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        """ Dynamically compute the domain of field product_id to return
        only Gifts products.
        """
        res = super(generate_gift_wizard, self).fields_view_get(
            cr, user, view_id, view_type, context, toolbar, submenu)
        if view_type == 'form':
            gifts_ids = self.pool.get('product.product').search(
                cr, user, [('type', '=', 'G')],
                context={'lang': 'en_US'})
            res['fields']['product_id']['domain'] = [('id', 'in', gifts_ids)]

        return res

    def compute_date_birthday_invoice(self, child_birthdate, payment_date):
        """Set date of invoice two months before child's birthdate"""
        inv_date = datetime.strptime(payment_date, DF)
        birthdate = datetime.strptime(child_birthdate, DF)
        new_date = inv_date
        if birthdate.month >= inv_date.month + 2:
            new_date = inv_date.replace(day=28, month=birthdate.month-2)
        elif birthdate.month + 3 < inv_date.month:
            new_date = birthdate.replace(
                day=28, year=inv_date.year+1) + relativedelta(months=-2)
            new_date = max(new_date, inv_date)
        return new_date.strftime(DF)
