##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Sebastien Toth <popod@me.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import tools
from odoo import models, fields, api


class SponsorshipsEvolutionMonthsReport(models.Model):
    _name = "sponsorships.evolution_months.report"
    _table = "sponsorships_evolution_months_report"
    _description = "Sponsorships Evolution By Months"
    _auto = False
    _rec_name = "study_date"

    study_date = fields.Char(readonly=True)
    sponsored = fields.Integer(readonly=True)
    sponsorships = fields.Integer(readonly=True)
    acquisition = fields.Integer(readonly=True)
    cancellation = fields.Integer(readonly=True)

    def _date_format(self):
        """
         Used to aggregate data in various formats (in subclasses) "
        :return: (date_trunc value, date format)
        """ ""
        return "month", "YYYY.MM"

    def init(self):
        """
        This SQL view is returning useful statistics about sponsorships.
        The outer query is using window functions to compute cumulative numbers
        Each inner query is computing sum of numbers grouped by _date_format
        :return: None
        """
        tools.drop_view_if_exists(self.env.cr, self._table)
        date_format = self._date_format()
        # We disable the check for SQL injection. The only risk of sql
        # injection is from 'self._table' which is not controlled by an
        # external source.
        # pylint:disable=E8103
        self.env.cr.execute(
            (
                """
                CREATE OR REPLACE VIEW %s AS
                """
                % self._table
                + """
            -- Super query making windows over monthly data, for cumulative
            -- numbers
            -- http://www.postgresqltutorial.com/postgresql-window-function/
            SELECT
              ROW_NUMBER() OVER () AS id,
              study_date AS raw_date,
              to_char(study_date, %s) AS study_date,

              coalesce(total_sponsored, 0) AS new_sponsored,
              coalesce(total_ended, 0) AS sponsored_terminated,
              sum(coalesce(total_sponsored, 0)) OVER (ORDER BY study_date) -
              sum(coalesce(total_ended, 0)) OVER (ORDER BY study_date)
                AS sponsored,

              sum(coalesce(acquisition, 0)) OVER (ORDER BY study_date) -
              sum(coalesce(cancellation, 0)) OVER (
                ORDER BY study_date) AS sponsorships,

              coalesce(acquisition, 0) AS acquisition,
              coalesce(cancellation, 0) AS cancellation

            FROM (
              -- Query returning the total activation by month
              SELECT
                date_trunc(%s, rc.activation_date) AS study_date,
                count(rc.activation_date) AS total_sponsored
              FROM recurring_contract AS rc
              WHERE rc.activation_date IS NOT NULL AND rc.child_id IS NOT NULL
              GROUP BY study_date
            ) AS activation
            -- Query returning the total ended by month
            FULL OUTER JOIN (
              SELECT
                date_trunc(%s, rc.end_date) AS study_date,
                count(rc.end_date) AS total_ended
              FROM recurring_contract AS rc
              WHERE rc.activation_date IS NOT NULL AND rc.end_date IS NOT NULL
                AND rc.child_id IS NOT NULL
              GROUP BY study_date
            ) AS ended USING (study_date)
            -- Query returning the acquisition (excluding subs) by month
            FULL OUTER JOIN (  SELECT
                date_trunc(%s, rc.activation_date) AS study_date,
                count(rc.activation_date) AS acquisition
              FROM recurring_contract AS rc
              WHERE rc.activation_date IS NOT NULL AND rc.child_id IS NOT NULL
              AND NOT EXISTS (
                SELECT id FROM recurring_contract parent
                WHERE id=rc.parent_id AND sponsorship_line_id IS NOT NULL
              )
              GROUP BY study_date
            ) AS acquisition USING (study_date)
            -- Query returning the cancellation by month
            FULL OUTER JOIN (  SELECT
                date_trunc(%s, rc.end_date) AS study_date,
                count(rc.end_date) AS cancellation
              FROM recurring_contract AS rc
              WHERE rc.child_id IS NOT NULL AND rc.end_date IS NOT NULL
              AND rc.sub_sponsorship_id IS NULL AND
              (rc.activation_date IS NOT NULL OR rc.parent_id IS NOT NULL)
              GROUP BY study_date
            ) AS cancellation USING (study_date)
        """
            ),
            [date_format[1]] + [date_format[0]] * 4,
        )
