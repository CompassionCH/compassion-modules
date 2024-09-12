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

from odoo.addons.recurring_contract.tests.test_recurring_contract import (
    BaseContractTest,
)

logger = logging.getLogger(__name__)


class BaseContractCompassionTest(BaseContractTest):
    def create_contract(self, vals, line_vals):
        # Add default values
        default_values = {"type": "O"}
        default_values.update(vals)
        return super().create_contract(default_values, line_vals)
