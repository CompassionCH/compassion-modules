##############################################################################
#
#    Copyright (C) 2023 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Simon Gonzalez <sgonzalez@ikmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from dateutil.relativedelta import relativedelta

from odoo import fields, models


class RecurringContract(models.Model):
    _inherit = ["recurring.contract"]

    type = fields.Selection(
        selection_add=[("CSP", "Survival Sponsorship")], ondelete={"CSP": "set default"}
    )

    def invoice_paid(self, invoice):
        super().invoice_paid(invoice)
        self.filtered(lambda c: c.type == "CSP").contract_active()

    def limited_time(self):
        for contract in self:
            contract.end_date = fields.datetime.now() + relativedelta(months=18)
