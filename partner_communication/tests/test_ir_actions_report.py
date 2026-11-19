from unittest.mock import patch

from odoo.tests import TransactionCase

from odoo.addons.base.models.ir_actions_report import IrActionsReport


class TestReportPrintDelay(TransactionCase):
    def setUp(self):
        super().setUp()
        self.report = self.env.ref("partner_communication.report_a4_communication")
        self.paperformat = self.report.get_paperformat()

    def _delay(self, args):
        return args[args.index("--javascript-delay") + 1]

    def test_communication_report_has_no_delay(self):
        self.assertEqual(self.report.print_delay, 0)

    def test_system_parameter_is_the_default(self):
        self.env["ir.config_parameter"].sudo().set_param("report.print_delay", "750")
        args = self.env["ir.actions.report"]._build_wkhtmltopdf_args(
            self.paperformat, False
        )
        self.assertEqual(self._delay(args), "750")

    def test_run_wkhtmltopdf_uses_the_delay_of_the_report(self):
        seen = {}

        def fake_run(self, bodies, report_ref=False, *args, **kwargs):
            seen["delay"] = self.env.context.get("report_print_delay")
            return b""

        with patch.object(IrActionsReport, "_run_wkhtmltopdf", fake_run):
            self.env["ir.actions.report"]._run_wkhtmltopdf([], self.report.id)
            self.assertEqual(seen["delay"], 0)
            # -1 leaves the system parameter in charge
            self.report.print_delay = -1
            self.env["ir.actions.report"]._run_wkhtmltopdf([], self.report.id)
            self.assertIsNone(seen["delay"])

    def test_delay_of_the_context_is_in_the_arguments(self):
        args = (
            self.env["ir.actions.report"]
            .with_context(report_print_delay=0)
            ._build_wkhtmltopdf_args(self.paperformat, False)
        )
        self.assertEqual(self._delay(args), "0")
