# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Albert SHENOUDA <albert.shenouda@efrei.net>
#
#    The licence is in the file __openerp__.py
#
##############################################################################


from openerp.addons.recurring_contract.tests.test_base_contract \
    import test_base_contract
import logging
logger = logging.getLogger(__name__)


class test_base_module(test_base_contract):

    def setUp(self):
        # Retrieve of income account
        super(test_base_module, self).setUp()
        property_account_income = self.env['account.account'].search([
            ('type', '=', 'other'),
            ('name', '=', 'Property Account Income Test')]).ids[0]
        property_account_expense = self.env['account.account'].search([
            ('type', '=', 'other'),
            ('name', '=', 'Property Account Expense Test')
        ]).ids[0]
        # Retrieve and modification of products
        product_obj = self.env['product.product']
        self.product_sp = product_obj.search(
            [('name', '=', 'Sponsorship')])
        self.product_gf = product_obj.search(
            [('name', '=', 'General Fund')])
        self.product_bf = product_obj.search(
            [('name', '=', 'Birthday Gift')])
        self.product_fg = product_obj.search(
            [('name', '=', 'Family Gift')])
        if self.product_sp:
            self.product_sp[0].write({
                'property_account_income': property_account_income,
                'property_account_expense': property_account_expense,
                })
        if self.product_gf:
            self.product_gf[0].write({
                'property_account_income': property_account_income,
                'property_account_expense': property_account_expense,
            })
        if self.product_bf:
            self.product_bf[0].write({
                'property_account_income': property_account_income,
                'property_account_expense': property_account_expense,
            })
        if self.product_fg:
            self.product_fg[0].write({
                'property_account_income': property_account_income,
                'property_account_expense': property_account_expense,
            })
        # Add of account for id's 1 product
        product = self.env['product.product'].browse(1)
        product.property_account_income = property_account_income

    def _pay_invoice(self, invoice):
        bank_journal = self.env['account.journal'].search(
            [('code', '=', 'TBNK')])[0]
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        account_id = invoice.partner_id.property_account_receivable.id
        move = move_obj.create({
            'journal_id': bank_journal.id
        })
        move_line_obj.create({
            'name': 'BNK-' + invoice.number,
            'move_id': move.id,
            'partner_id': invoice.partner_id.id,
            'account_id': bank_journal.default_debit_account_id.id,
            'debit': invoice.amount_total,
            'journal_id': bank_journal.id,
            'period_id': invoice.period_id.id,
            'date': invoice.date_due
        })
        mv_line = move_line_obj.create({
            'name': 'PAY-' + invoice.number,
            'move_id': move.id,
            'partner_id': invoice.partner_id.id,
            'account_id': account_id,
            'credit': invoice.amount_total,
            'journal_id': invoice.journal_id.id,
            'period_id': invoice.period_id.id,
            'date': invoice.date_due
        })
        move.button_validate()
        to_reconcile = move_line_obj.search([
            ('move_id', '=', invoice.move_id.id),
            ('account_id', '=', account_id)]) + mv_line
        to_reconcile.reconcile()
