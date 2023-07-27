##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import tools
from odoo import models, fields, api


class SponsorshipsEvolutionMonthsReport(models.Model):
    _name = "sponsorship.line.report"
    _table = "sponsorship_line_report"
    _description = "Sponsorship Line"
    _auto = False

    name = fields.Char(compute="_compute_name")
    partner_id = fields.Many2one("res.partner", "Partner", readonly=True)
    sponsor_line = fields.Integer("Sponsor line number")
    acquisition_id = fields.Many2one("recurring.contract", "Acquisition", readonly=True)
    cancellation_id = fields.Many2one(
        "recurring.contract", "Cancellation", readonly=True
    )
    is_active = fields.Boolean(readonly=True)

    @api.multi
    def _compute_name(self):
        for line in self:
            line.name = f"{line.partner_id.name} / Line #{line.sponsor_line}"

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        # We disable the check for SQL injection. The only risk of sql
        # injection is from 'self._table' which is not controlled by an
        # external source.
        # pylint:disable=E8103
        self.env.cr.execute(
            """
            CREATE OR REPLACE VIEW %s AS
            """
            % self._table
            + """
            -- http://www.postgresqltutorial.com/postgresql-window-function/
            select *,
            case
                when cancellation_id IS NULL THEN true
                ELSE false
            end AS is_active
            from (
                select min(c.id) as acquisition_id,
                max(c.id) as last_sponsorship_id,
                sponsorship_line_id as id,
                max(p.id) as partner_id,
                row_number() over (partition by max(p.id)
                                   order by sponsorship_line_id)
                    as sponsor_line
                from recurring_contract c JOIN res_partner p
                    ON c.correspondent_id = p.id
                where sponsorship_line_id is not null
                group by sponsorship_line_id
            ) AS acquisition
            FULL OUTER JOIN (
                select id as cancellation_id, sponsorship_line_id as id
                from recurring_contract
                WHERE child_id IS NOT NULL AND end_date IS NOT NULL
                  AND sub_sponsorship_id IS NULL AND
                  (activation_date IS NOT NULL OR parent_id IS NOT NULL)
            ) AS cancellation USING(id)
            where id is not null
            order by id
        """
        )
