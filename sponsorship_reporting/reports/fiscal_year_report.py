##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models


class FiscalYearReport(models.AbstractModel):
    """
    Abstract class used in reports to add fiscal year analysis on a date field.
    Assumes a Fiscal Year running from July 1st to June 30th.
    """

    _name = "fiscal.year.report"
    _description = "Fiscal Year Report"

    fiscal_month_number = fields.Integer(string="Fiscal Month", readonly=True)
    valid_month = fields.Boolean(
        string="Is Past Month",
        help="Is the fiscal month already passed in current fiscal year?",
        readonly=True,
    )
    fiscal_year = fields.Char(readonly=True)

    def _select_fiscal_year(self, date_field):
        """
        Generates SQL selection fields for fiscal year analysis.

        :param date_field: The SQL column name (e.g., 'am.date') to analyze.
        :return: A string containing the SQL SELECT fragments.
        """
        # Logic: If Month > 6 (July-Dec), it is the start of the FY (Months 1-6).
        #        If Month <= 6 (Jan-June), it is the end of the FY (Months 7-12).
        return f"""
            CASE
                WHEN EXTRACT(month FROM {date_field}) > 6
                THEN EXTRACT(month FROM {date_field}) - 6
                ELSE EXTRACT(month FROM {date_field}) + 6
            END AS fiscal_month_number,

            -- Compare the fiscal month of the date_field vs the fiscal month of NOW()
            CASE
                -- Calculate Fiscal Month for NOW() and compare
                WHEN (
                    CASE
                        WHEN EXTRACT(month FROM now()) > 6
                        THEN EXTRACT(month FROM now()) - 6
                        ELSE EXTRACT(month FROM now()) + 6
                    END
                ) > (
                    CASE
                        WHEN EXTRACT(month FROM {date_field}) > 6
                        THEN EXTRACT(month FROM {date_field}) - 6
                        ELSE EXTRACT(month FROM {date_field}) + 6
                    END
                )
                THEN TRUE
                ELSE FALSE
            END AS valid_month,

            'FY ' ||
            CASE
                WHEN EXTRACT(month FROM {date_field}) > 6
                THEN EXTRACT(year FROM {date_field})::varchar || '-' ||
                     (EXTRACT(year FROM {date_field})::int + 1)::varchar
                ELSE (EXTRACT(year FROM {date_field})::int - 1)::varchar || '-' ||
                     EXTRACT(year FROM {date_field})::varchar
            END AS fiscal_year
        """
