from odoo import models


class AccountInvoiceReport(models.Model):
    _inherit = ["account.invoice.report", "fiscal.year.report"]
    _name = "account.invoice.report"

    def _select(self):
        """
        Add fiscal month in VIEW columns
        July is the first month and June is the twelve month
        """
        select_str = super()._select()
        select_str += ", " + self._select_fiscal_year("sub.date")
        return select_str
