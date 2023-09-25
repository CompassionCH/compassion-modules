##############################################################################
#
#    Copyright (C) 2023 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models


class ContractGroup(models.Model):
    """Adds the Salesperson to the generated invoices."""

    _inherit = "recurring.contract.group"

    def build_inv_line_data(
        self, invoicing_date=False, gift_wizard=False, contract_line=False
    ):
        res = super().build_inv_line_data(invoicing_date, gift_wizard, contract_line)
        if gift_wizard:
            res["user_id"] = gift_wizard.contract_id.ambassador_id.id
        elif contract_line:
            res["user_id"] = contract_line.contract_id.ambassador_id.id
        return res
