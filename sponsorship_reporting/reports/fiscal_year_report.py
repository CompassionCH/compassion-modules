from odoo import fields, models


class AccountInvoiceReport(models.AbstractModel):
    """
    Abstract class used in reports to add fiscal year analysis on a date field
    """

    _name = "fiscal.year.report"
    _description = "Fiscal Year Report"

    fiscal_month_number = fields.Integer(readonly=True)
    valid_month = fields.Boolean(
        help="Is the fiscal month already passed in current fiscal year?", readonly=True
    )
    fiscal_year = fields.Char(readonly=True)

    def _select_fiscal_year(self, date_field):
        """
        Add fields selection for fiscal year analysis
        :param: date_field: the date column that will be analyzed
        :return: SELECT SQL query that can be used in a SQL view for
                 constructing the fiscal year fields.
        """
        return f"""
            CASE WHEN EXTRACT(month FROM {date_field}) > 6
            THEN EXTRACT(month FROM {date_field}) - 6
            ELSE EXTRACT(month FROM {date_field}) + 6
            END
            AS fiscal_month_number,

            CASE WHEN EXTRACT(month FROM now()) > 6
            THEN
                CASE WHEN EXTRACT(month FROM {date_field}) > 6
                THEN EXTRACT(month FROM {date_field}) - 6 < EXTRACT(
                    month FROM now()) - 6
                ELSE EXTRACT(month FROM {date_field}) + 6 < EXTRACT(
                    month FROM now()) - 6
                END
            ELSE
                CASE WHEN EXTRACT(month FROM {date_field}) > 6
                THEN EXTRACT(month FROM {date_field}) - 6 < EXTRACT(
                    month FROM now()) + 6
                ELSE EXTRACT(month FROM {date_field}) + 6 < EXTRACT(
                    month FROM now()) + 6
                END
            END
            AS valid_month,

            'FY ' ||
            CASE WHEN EXTRACT(month FROM {date_field}) > 6
            THEN EXTRACT(year FROM {date_field})::varchar || '-' ||
                 (EXTRACT(year FROM {date_field})::int + 1)::varchar
            ELSE (EXTRACT(year FROM {date_field})::int - 1)::varchar || '-' ||
                 EXTRACT(year FROM {date_field})::varchar
            END
            AS fiscal_year
        """
