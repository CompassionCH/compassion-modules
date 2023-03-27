##############################################################################
#
#    Copyright (C) 2015-2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Albert SHENOUDA <albert.shenouda@efrei.net>, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from datetime import date

from odoo.addons.recurring_contract.tests.test_recurring_contract import TestRecurringContract

from odoo.exceptions import UserError

""" This class is useful to lauch the parent tests again on the invoices"""
class BaseContractCompassionTest(TestRecurringContract):
    def test_create_contract_with_invoice_but_wrong_pay_mode(self):
        with self.assertRaises(UserError):
            self.contract_obj.create({
                'reference': "TEST False contract",
                'partner_id': self.partner.id,
                'group_id': self.group.id,
                'pricelist_id': self.env.ref('product.list0').id,
                'contract_line_ids': [
                    (0, 0, {'product_id': self.product.id, 'amount': 250, 'quantity': 800})],
                "birthday_invoice": 90000
            })
        with self.assertRaises(UserError):
            self.contract_obj.create({
                'reference': "TEST False contract 1",
                'partner_id': self.partner.id,
                'group_id': self.group.id,
                'pricelist_id': self.env.ref('product.list0').id,
                'contract_line_ids': [
                    (0, 0, {'product_id': self.product.id, 'amount': 250, 'quantity': 800})],
                "christmas_invoice": 90000
            })