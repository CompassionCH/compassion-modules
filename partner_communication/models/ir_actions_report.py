##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, fields, models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    print_delay = fields.Integer(
        "Print delay (ms)",
        default=-1,
        help="Time that wkhtmltopdf waits for the javascript of the page before "
        "printing it. Reports without javascript (all our communications) have "
        "nothing to wait for and are generated about 2 seconds faster with 0. "
        "-1 uses the system parameter report.print_delay (1 second by default).",
    )

    @api.model
    def _run_wkhtmltopdf(self, bodies, report_ref=False, *args, **kwargs):
        report = self._get_report(report_ref) if report_ref else None
        if report and report.print_delay >= 0:
            # The delay is read when the arguments of wkhtmltopdf are built
            report_model = self.with_context(report_print_delay=report.print_delay)
            return super(IrActionsReport, report_model)._run_wkhtmltopdf(
                bodies, report_ref, *args, **kwargs
            )
        return super()._run_wkhtmltopdf(bodies, report_ref, *args, **kwargs)

    @api.model
    def _build_wkhtmltopdf_args(self, *args, **kwargs):
        command_args = super()._build_wkhtmltopdf_args(*args, **kwargs)
        delay = self.env.context.get("report_print_delay")
        if delay is not None and "--javascript-delay" in command_args:
            command_args[command_args.index("--javascript-delay") + 1] = str(delay)
        return command_args
