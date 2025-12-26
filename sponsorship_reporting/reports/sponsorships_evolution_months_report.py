##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Sebastien Toth <popod@me.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models, tools


class SponsorshipsEvolutionMonthsReport(models.Model):
    _name = "sponsorships.evolution_months.report"
    _description = "Sponsorships Evolution By Months"
    _table = "sponsorships_evolution_months_report"
    _auto = False
    _rec_name = "study_date"

    study_date = fields.Char(readonly=True)
    sponsored = fields.Integer(string="Total Sponsored", readonly=True)
    sponsorships = fields.Integer(string="Net Sponsorships", readonly=True)
    acquisition = fields.Integer(string="Acquisitions", readonly=True)
    cancellation = fields.Integer(string="Cancellations", readonly=True)

    def _date_format(self):
        """
        Used to aggregate data in various formats (in subclasses).
        Returns:
            tuple: (Postgres date_trunc interval, Postgres to_char format)
        """
        return "month", "YYYY.MM"

    def init(self):
        """
        Create the SQL view.
        The outer query uses window functions to compute cumulative numbers.
        Each inner query computes sums grouped by the _date_format.
        """
        tools.drop_view_if_exists(self.env.cr, self._table)

        # Get the interval (e.g., 'month') and format (e.g., 'YYYY.MM')
        trunc_interval, char_format = self._date_format()

        # pylint:disable=E8103
        self.env.cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                -- Super query making windows over data for cumulative numbers
                SELECT
                    ROW_NUMBER() OVER () AS id,
                    study_date AS raw_date,
                    to_char(study_date, %s) AS study_date,

                    COALESCE(total_sponsored, 0) AS new_sponsored,
                    COALESCE(total_ended, 0) AS sponsored_terminated,

                    -- Cumulative Sponsored Calculation
                    SUM(COALESCE(total_sponsored, 0)) OVER (ORDER BY study_date) -
                    SUM(COALESCE(total_ended, 0)) OVER (ORDER BY study_date)
                        AS sponsored,

                    -- Cumulative Sponsorships Calculation
                    SUM(COALESCE(acquisition, 0)) OVER (ORDER BY study_date) -
                    SUM(COALESCE(cancellation, 0)) OVER (ORDER BY study_date)
                        AS sponsorships,

                    COALESCE(acquisition, 0) AS acquisition,
                    COALESCE(cancellation, 0) AS cancellation

                FROM (
                    -- 1. Activations
                    SELECT
                        date_trunc(%s, rc.activation_date) AS study_date,
                        count(rc.activation_date) AS total_sponsored
                    FROM recurring_contract AS rc
                    WHERE rc.activation_date IS NOT NULL
                      AND rc.child_id IS NOT NULL
                    GROUP BY date_trunc(%s, rc.activation_date)
                ) AS activation

                -- 2. Ends (Full Outer Join)
                FULL OUTER JOIN (
                    SELECT
                        date_trunc(%s, rc.end_date) AS study_date,
                        count(rc.end_date) AS total_ended
                    FROM recurring_contract AS rc
                    WHERE rc.activation_date IS NOT NULL
                      AND rc.end_date IS NOT NULL
                      AND rc.child_id IS NOT NULL
                    GROUP BY date_trunc(%s, rc.end_date)
                ) AS ended USING (study_date)

                -- 3. Acquisitions (Excluding subs)
                FULL OUTER JOIN (
                    SELECT
                        date_trunc(%s, rc.activation_date) AS study_date,
                        count(rc.activation_date) AS acquisition
                    FROM recurring_contract AS rc
                    WHERE rc.activation_date IS NOT NULL
                      AND rc.child_id IS NOT NULL
                      AND NOT EXISTS (
                        SELECT id FROM recurring_contract parent
                        WHERE id = rc.parent_id AND sponsorship_line_id IS NOT NULL
                      )
                    GROUP BY date_trunc(%s, rc.activation_date)
                ) AS acquisition USING (study_date)

                -- 4. Cancellations
                FULL OUTER JOIN (
                    SELECT
                        date_trunc(%s, rc.end_date) AS study_date,
                        count(rc.end_date) AS cancellation
                    FROM recurring_contract AS rc
                    WHERE rc.child_id IS NOT NULL
                      AND rc.end_date IS NOT NULL
                      AND rc.sub_sponsorship_id IS NULL
                      AND (rc.activation_date IS NOT NULL OR rc.parent_id IS NOT NULL)
                    GROUP BY date_trunc(%s, rc.end_date)
                ) AS cancellation USING (study_date)
            )
            """,
            (
                char_format,  # For to_char
                trunc_interval,  # For activation group
                trunc_interval,  # ...repeat for group by
                trunc_interval,  # For ended group
                trunc_interval,
                trunc_interval,  # For acquisition group
                trunc_interval,
                trunc_interval,  # For cancellation group
                trunc_interval,
            ),
        )
