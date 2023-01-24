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


""" This class is useful to lauch the parent tests again on the invoices"""
class BaseContractCompassionTest(TestRecurringContract):
    pass