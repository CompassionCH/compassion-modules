# Copyright (C) 2018 Compassion CH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime

from odoo import models, fields, api


class BalanceEvolutionReport(models.TransientModel):
    _name = "balance.evolution.graph"

    day = fields.Date()
    employee_id = fields.Many2one("hr.employee", "Employee", readonly=False)
    balance = fields.Float()

    @api.model
    def populate_graph(self, employee_id):
        """
        Creates the rows for the balance graph of given employee
        :param employee_id: the employee
        :return: True
        """
        employee = self.env["hr.employee"].search([("id", "=", employee_id)])
        last_history_entry = self.env["hr.employee.period"].search(
            [
                ("employee_id", "=", employee.id),
                ("end_date", "<=", datetime.date.today()),
            ],
            order="end_date desc",
            limit=1,
        )

        end_date = datetime.date.today()

        if last_history_entry:
            # One day after last period
            end_date = last_history_entry.end_date
            start_date = end_date + datetime.timedelta(days=1)
            balance = last_history_entry.balance
        else:
            config = self.env["res.config.settings"].create({})
            config.set_beginning_date()
            start_date = config.get_beginning_date_for_balance_computation()
            balance = employee.initial_balance

        days, extra_hours_sum, _ = employee.complete_balance_computation(
            start_date=start_date, end_date=end_date, existing_balance=balance
        )

        # delete previous graph for this employee to avoid miscalculation
        # for graph display
        self.env["balance.evolution.graph"].search(
            [("employee_id", "=", employee_id)]
        ).unlink()

        for i, day in enumerate(days):
            self.create(
                {"employee_id": employee_id, "day": day, "balance": extra_hours_sum[i]}
            )
        return True
