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
    csp_country = fields.Char(
        "CSP Country", compute="_compute_csp_country",
        readonly=True, store=True
    )

    def invoice_paid(self, invoice):
        super().invoice_paid(invoice)
        self.filtered(lambda c: c.type == "CSP").contract_active()

    def limited_time(self):
        for contract in self:
            contract.end_date = fields.datetime.now() + relativedelta(months=18)

    def _compute_csp_country(self):
        for contract in self:
            if contract.type == 'CSP':
                product = contract.contract_line_ids.product_id
                csp_product = product.survival_sponsorship_field_office_id
                if csp_product:
                    contract.csp_country = csp_product.country_name
