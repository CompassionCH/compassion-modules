from odoo import models
from odoo.tools import SQL


class AccountInvoiceReport(models.Model):
    _inherit = ["account.invoice.report", "fiscal.year.report"]
    _name = "account.invoice.report"

    def _select(self):
        """
        Add fiscal month in VIEW columns.
        In Odoo 18, the alias for the move table is usually 'move'.
        """
        select_sql = super()._select()
        fiscal_fields_str = self._select_fiscal_year("move.invoice_date")

        return SQL("%s, %s", select_sql, SQL(fiscal_fields_str))
