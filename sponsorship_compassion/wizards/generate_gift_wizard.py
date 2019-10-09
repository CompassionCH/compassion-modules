##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, fields, models, _
from odoo.tools import config

from dateutil.relativedelta import relativedelta

from ..models.product_names import GIFT_NAMES
import logging

logger = logging.getLogger(__name__)
test_mode = config.get('test_enable')


class GenerateGiftWizard(models.TransientModel):
    """ This wizard generates a Gift Invoice for a given contract. """
    _name = 'generate.gift.wizard'

    amount = fields.Float("Gift Amount", required=True)
    product_id = fields.Many2one(
        'product.product', "Gift Type", required=True)
    invoice_date = fields.Date(default=fields.Date.today())
    description = fields.Char("Additional comments", size=200)
    force = fields.Boolean(
        'Force creation', help="Creates the gift even if one was already "
        "made the same year.")

    @api.multi
    def generate_invoice(self):
        # Read data in english
        self.ensure_one()
        self = self.with_context(lang='en_US')
        if not self.description:
            self.description = self.product_id.display_name
        invoice_ids = list()
        gen_states = self.env['recurring.contract.group']._get_gen_states()

        # Ids of contracts are stored in context
        for contract in self.env['recurring.contract'].browse(
                self.env.context.get('active_ids', list())).filtered(
            lambda c: 'S' in c.type and c.state in gen_states
        ):
                    if self.product_id.name == GIFT_NAMES[0]:
                        # Birthday Gift
                        if not contract.child_id.birthdate:
                            logger.error(
                                'The birthdate of the child is missing!')
                            continue
                        # This is set in the view in order to let the user
                        # choose the invoice date. Otherwise (called from code)
                        # the invoice date will be computed based on the
                        # birthday of the child.
                        if self.env.context.get('force_date'):
                            invoice_date = self.invoice_date
                        else:
                            invoice_date = self.compute_date_birthday_invoice(
                                contract.child_id.birthdate,
                                self.invoice_date)
                        begin_year = fields.Date.from_string(
                            self.invoice_date).replace(month=1, day=1)
                        end_year = begin_year.replace(month=12, day=31)
                        # If a gift was already made for the year, abort
                        invoice_line_ids = self.env[
                            'account.invoice.line'].search([
                                ('product_id', '=', self.product_id.id),
                                ('due_date', '>=', fields.Date.to_string(
                                    begin_year)),
                                ('due_date', '<=', fields.Date.to_string(
                                    end_year)),
                                ('contract_id', '=', contract.id),
                                ('state', '!=', 'cancel')])
                        if invoice_line_ids and not self.force:
                            continue
                    else:
                        invoice_date = self.invoice_date
                    inv_data = self._setup_invoice(contract, invoice_date)
                    invoice = self.env['account.invoice'].create(inv_data)
                    invoice.action_invoice_open()
                    # Commit at each invoice creation. This does not break
                    # the state
                    if not test_mode:
                        self.env.cr.commit()   # pylint: disable=invalid-commit
                    invoice_ids.append(invoice.id)

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
    def _setup_invoice(self, contract, invoice_date):
        journal_id = self.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', 1)], limit=1).id
        return {
            'type': 'out_invoice',
            'partner_id': contract.gift_partner_id.id,
            'journal_id': journal_id,
            'date_invoice': invoice_date,
            'payment_mode_id': contract.payment_mode_id.id,
            'recurring_invoicer_id': self.env.context.get(
                'recurring_invoicer_id', False),
            'invoice_line_ids': [(0, 0, self.with_context(
                journal_id=journal_id)._setup_invoice_line(contract))]
        }

    @api.multi
    def _setup_invoice_line(self, contract):
        self.ensure_one()
        product = self.product_id
        account = product.property_account_income_id.id or self.env[
            'account.invoice.line']._default_account()

        inv_line_data = {
            'name': self.description,
            'account_id': account,
            'price_unit': self.amount,
            'quantity': 1,
            'product_id': product.id,
            'contract_id': contract.id,
        }

        # Define analytic journal
        analytic = self.env['account.analytic.default'].account_get(
            product.id, contract.partner_id.id, date=fields.Date.today())
        if analytic and analytic.analytic_id:
            inv_line_data['account_analytic_id'] = analytic.analytic_id.id

        return inv_line_data

    @api.model
    def compute_date_birthday_invoice(self, child_birthdate, payment_date):
        """Set date of invoice two months before child's birthdate"""
        inv_date = fields.Date.from_string(payment_date)
        birthdate = fields.Date.from_string(child_birthdate)
        new_date = inv_date
        if birthdate.month >= inv_date.month + 2:
            new_date = inv_date.replace(day=28, month=birthdate.month - 2)
        elif birthdate.month + 3 < inv_date.month:
            new_date = birthdate.replace(
                day=28, year=inv_date.year + 1) + relativedelta(months=-2)
            new_date = max(new_date, inv_date)
        return fields.Date.to_string(new_date)
