from odoo import api, models

# Careful: This limit should be set the same as in account_move_reconciliation.js:31
MAX_LINES_FOR_RECONCILE_WIDGET = 10


class AccountReconciliationWidget(models.AbstractModel):
    _inherit = "account.reconciliation.widget"

    @api.model
    def get_bank_statement_line_data(self, st_line_ids, excluded_ids=None):
        """
        Limit the number of visible lines for performance reason.
        """
        results = super().get_bank_statement_line_data(st_line_ids, excluded_ids)
        lines = results["lines"]
        for i in range(min(MAX_LINES_FOR_RECONCILE_WIDGET, len(lines)), len(lines)):
            lines[i]["visible"] = False
        return results

    @api.model
    def get_move_lines_for_bank_statement_line(
        self,
        st_line_id,
        partner_id=None,
        excluded_ids=None,
        search_str=False,
        offset=0,
        limit=None,
        mode=None,
    ):
        """
        Propose up to 12 move lines for a complete year, and avoid too much propositions
        """
        if limit is not None and limit < 12:
            limit = 12
        if limit is None:
            limit = 40
        return super().get_move_lines_for_bank_statement_line(
            st_line_id, partner_id, excluded_ids, search_str, offset, limit, mode
        )

    def _prepare_move_lines(
        self, move_lines, target_currency=False, target_date=False, recs_count=0
    ):
        """
        Sort move lines according to Compassion criterias :
        Move line for current month at first,
        Then other move_lines, from the oldest to the newest.
        :param move_lines:
        :param target_currency:
        :param target_date:
        :return:
        """

        def _sort_move_line(move_line):
            date = target_date or move_line.date
            limit_year = date.year - 5
            index = limit_year
            mv_date = move_line.date_maturity or move_line.date
            if mv_date.month == date.month and mv_date.year == date.year:
                index += 1
            else:
                index += mv_date.month + (mv_date.year - limit_year) * 12
            return index

        move_lines = move_lines.sorted(_sort_move_line)
        return super()._prepare_move_lines(
            move_lines, target_currency, target_date, recs_count
        )

    @api.model
    def process_bank_statement_line(self, st_line_ids, data):
        # Execute a job to speedup the interface. The returned data is not used anyway.
        super().with_delay().process_bank_statement_line(st_line_ids, data)
        return {}
