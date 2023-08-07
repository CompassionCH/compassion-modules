from odoo import api, models, fields, tools, _


class EndSponsorshipsMonthReport(models.Model):
    _name = "end.sponsorships.month.report"
    _inherit = "fiscal.year.report"
    # _table = 'end_sponsorships_month_report'
    _description = "End of sponsorships monthly report"
    _auto = False
    _rec_name = "end_date"

    end_date = fields.Datetime(readonly=True)
    sub_sponsorship_id = fields.Many2one("recurring.contract", readonly=True)
    category = fields.Selection(
        [("child", "Child departure"), ("sponsor", "Sponsor end")], readonly=True
    )
    sub_category = fields.Selection(
        [("sub", "Sub"), ("no_sub", "No sub")], readonly=True
    )
    end_reason_id = fields.Selection(
        [
            ("2", _("Mistake from our staff")),
            ("3", _("Death of partner")),
            ("4", _("Moved to foreign country")),
            ("5", _("Not satisfied")),
            ("6", _("Doesn't pay")),
            ("8", _("Personal reasons")),
            ("9", _("Never paid")),
            ("12", _("Financial reasons")),
            ("25", _("Not given")),
        ],
        readonly=True,
    )
    partner_id = fields.Many2one("res.partner", "Partner", readonly=True)
    lang = fields.Selection("select_lang", readonly=True)
    sds_state = fields.Selection(
        [
            ("draft", _("Draft")),
            ("active", _("Active")),
            ("sub_waiting", _("Sub waiting")),
            ("sub", _("Sub")),
            ("sub_accept", _("Sub Accept")),
            ("sub_reject", _("Sub Reject")),
            ("no_sub", _("No sub")),
            ("cancelled", _("Cancelled")),
        ],
        readonly=True,
    )
    active_percentage = fields.Float(
        string="Percentage (/active)",
        help="Percentage on active sponsorships in that period",
        readonly=True,
    )
    total_percentage = fields.Float(
        string="Percentage (/terminated)",
        help="Percentage on total ended sponsorships in that period",
        readonly=True,
    )

    @api.model
    def select_lang(self):
        langs = self.env["res.lang"].search([])
        return [(lang.code, lang.name) for lang in langs]

    def _select_category(self):
        return """
            CASE c.end_reason_id
            WHEN '1' THEN 'child'
            ELSE 'sponsor'
            END
            AS category
        """

    def _select_sub_category(self):
        return """
            CASE c.sds_state
            WHEN 'sub' THEN 'sub'
            WHEN 'sub_accept' THEN 'sub'
            ELSE 'no_sub'
            END
            AS sub_category
        """

    def _join_stats(self):
        """Useful to compare against number active sponsorships in the
        period."""
        return """
            JOIN sponsorships_evolution_months_report s
            ON to_char(c.end_date, 'YYYY.MM') = s.study_date
        """

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        # We disable the check for SQL injection. The only risk of sql
        # injection is from 'self._table' which is not controlled by an
        # external source.
        # pylint:disable=E8103
        self.env.cr.execute(
            """
            CREATE OR REPLACE VIEW %s AS
            SELECT c.id, c.end_date, c.end_reason_id, c.sub_sponsorship_id,
                   c.sds_state, p.id as partner_id, %s, %s, %s,
                   p.lang, 100/s.sponsored as active_percentage,
                   100.0/s.sponsored_terminated as total_percentage,
                   s.sponsored_terminated,
                   s.study_date
            FROM recurring_contract c JOIN res_partner p
              ON c.correspondent_id = p.id
              %s
            WHERE c.state = 'terminated' AND c.child_id IS NOT NULL
            AND c.end_date IS NOT NULL
        """
            % (
                self._table,
                self._select_fiscal_year("c.end_date"),
                self._select_category(),
                self._select_sub_category(),
                self._join_stats(),
            )
        )
