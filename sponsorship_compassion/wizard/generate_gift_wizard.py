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

from openerp import api, exceptions, fields, models, _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools import mod10r

from datetime import datetime
from dateutil.relativedelta import relativedelta

from ..model.product import GIFT_NAMES
import time


class generate_gift_wizard(models.TransientModel):
    """ This wizard generates a Gift Invoice for a given contract. """
    _name = 'generate.gift.wizard'

    amount = fields.Float("Gift Amount", required=True)
    product_id = fields.Many2one(
        'product.product', "Gift Type", required=True)
    invoice_date = fields.Date(default=datetime.today().strftime(DF))
    description = fields.Char("Additional comments", size=200)

    @api.multi
    def generate_invoice(self):
        # Read data in english
        self.ensure_one()
        self = self.with_context(lang='en_US')
        invoice_ids = list()
        gen_states = self.env['recurring.contract.group']._get_gen_states()
        # Ids of contracts are stored in context
        for contract in self.env['recurring.contract'].browse(
                self.env.context.get('active_ids', list())):
            partner = contract.partner_id

            if 'S' in contract.type and contract.state in gen_states:
                journal_id = self.env['account.journal'].search(
                    [('type', '=', 'sale'), ('company_id', '=', 1 or False)],
                    limit=1).id

                # Birthday Gift
                if not contract.child_id.birthdate:
                        raise exceptions.Warning(
                            'BirthdayError',
                            _('The birthdate of the child is missing !'))
                if self.product_id.name == GIFT_NAMES[0]:
                    invoice_date = self.compute_date_birthday_invoice(
                        contract.child_id.birthdate, self.invoice_date)
                    # If a gift was already made for that date, create one
                    # for next year.
                    invoice_line_ids = self.env[
                        'account.invoice.line'].search([
                            ('product_id', '=', self.product_id.id),
                            ('due_date', '=', invoice_date),
                            ('contract_id', '=', contract.id)])
                    if invoice_line_ids:
                        invoice_date = (datetime.strptime(invoice_date, DF) +
                                        relativedelta(months=12)).strftime(DF)
                else:
                    invoice_date = self.invoice_date
                inv_data = {
                    'account_id': partner.property_account_receivable.id,
                    'type': 'out_invoice',
                    'partner_id': partner.id,
                    'journal_id': journal_id,
                    'date_invoice': invoice_date,
                    'payment_term': 1,  # Immediate payment
                    'bvr_reference': self._generate_bvr_reference(
                        contract, self.product_id),
                    'recurring_invoicer_id': self.env.context.get(
                        'recurring_invoicer_id', False)
                }

                invoice = self.env['account.invoice'].create(inv_data)
                if invoice:
                    inv_line_data = self._setup_invoice_line(
                        invoice, contract)
                    self.env['account.invoice.line'].create(inv_line_data)
                    invoice_ids.append(invoice.id)
            else:
                raise exceptions.Warning(
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

    @api.multi
    def _setup_invoice_line(self, invoice, contract):
        self.ensure_one()
        product = self.product_id

        inv_line_data = {
            'name': self.description,
            'account_id': product.property_account_income.id,
            'price_unit': self.amount,
            'quantity': 1,
            'uos_id': False,
            'product_id': product.id or False,
            'invoice_id': invoice.id,
            'contract_id': contract.id,
        }

        # Define analytic journal
        analytic = self.env['account.analytic.default'].account_get(
            product.id, contract.partner_id.id, time.strftime(DF))
        if analytic and analytic.analytic_id:
            inv_line_data['account_analytic_id'] = analytic.analytic_id.id

        # Give a better name to invoice_line
        if not self.description:
            inv_line_data['name'] = contract.child_id.code
            inv_line_data['name'] += " - " + contract.child_id.birthdate \
                if product.name == GIFT_NAMES[0] else ""

        return inv_line_data

    @api.multi
    def _generate_bvr_reference(self, contract, product):
        self.ensure_one()
        ref = contract.partner_id.ref
        bvr_reference = '0' * (9 + (7 - len(ref))) + ref
        num_pol_ga = str(contract.num_pol_ga)
        bvr_reference += '0' * (5 - len(num_pol_ga)) + num_pol_ga
        # Type of gift
        bvr_reference += str(GIFT_NAMES.index(product.name) + 1)
        bvr_reference += '0' * 4

        if contract.group_id.payment_term_id and \
                'LSV' in contract.group_id.payment_term_id.name:
            # Get company BVR adherent number
            user = self.env.user
            bank_obj = self.env['res.partner.bank']
            company_bank = bank_obj.search([
                ('partner_id', '=', user.company_id.partner_id.id),
                ('bvr_adherent_num', '!=', False)])
            if company_bank:
                bvr_reference = company_bank.bvr_adherent_num +\
                    bvr_reference[9:]
        if len(bvr_reference) == 26:
            return mod10r(bvr_reference)

    @api.model
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
