##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, fields, models, tools


class SponsorshipLineReport(models.Model):
    _name = "sponsorship.line.report"
    _description = "Sponsorship Line Report"
    _auto = False

    name = fields.Char(compute="_compute_name")
    partner_id = fields.Many2one("res.partner", string="Partner", readonly=True)
    sponsor_line = fields.Integer(string="Sponsor line number", readonly=True)
    acquisition_id = fields.Many2one(
        "recurring.contract", string="Acquisition", readonly=True
    )
    cancellation_id = fields.Many2one(
        "recurring.contract", string="Cancellation", readonly=True
    )
    is_active = fields.Boolean(readonly=True)

    @api.depends("partner_id", "sponsor_line")
    def _compute_name(self):
        for line in self:
            if line.partner_id:
                line.name = f"{line.partner_id.name} / Line #{line.sponsor_line}"
            else:
                line.name = f"Unknown Partner / Line #{line.sponsor_line}"

    def init(self):
        """Create the SQL view."""
        tools.drop_view_if_exists(self.env.cr, self._table)
        # We disable the check for SQL injection. The only risk of sql
        # injection is from 'self._table' which is not controlled by an
        # external source.
        # pylint:disable=E8103
        self.env.cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                -- http://www.postgresqltutorial.com/postgresql-window-function/
                SELECT
                    COALESCE(acquisition.id, cancellation.id) as id,
                    acquisition.acquisition_id,
                    acquisition.last_sponsorship_id,
                    acquisition.partner_id,
                    acquisition.sponsor_line,
                    cancellation.cancellation_id,
                    CASE
                        WHEN cancellation.cancellation_id IS NULL THEN true
                        ELSE false
                    END AS is_active
                FROM (
                    SELECT
                        min(c.id) as acquisition_id,
                        max(c.id) as last_sponsorship_id,
                        sponsorship_line_id as id,
                        max(p.id) as partner_id,
                        row_number() OVER (PARTITION BY max(p.id)
                                           ORDER BY sponsorship_line_id) as sponsor_line
                    FROM recurring_contract c
                    JOIN res_partner p ON c.correspondent_id = p.id
                    WHERE sponsorship_line_id IS NOT NULL
                    GROUP BY sponsorship_line_id
                ) AS acquisition
                FULL OUTER JOIN (
                    SELECT
                        id as cancellation_id,
                        sponsorship_line_id as id
                    FROM recurring_contract
                    WHERE child_id IS NOT NULL
                      AND end_date IS NOT NULL
                      AND sub_sponsorship_id IS NULL
                      AND (activation_date IS NOT NULL OR parent_id IS NOT NULL)
                ) AS cancellation USING(id)
                WHERE COALESCE(acquisition.id, cancellation.id) IS NOT NULL
            )
            """
        )
