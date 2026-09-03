##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _render_qweb_html(self, report_ref, docids, data=None):
        # QWeb overwrites the ``lang`` rendering value with the language of the
        # rendering environment (``ir.qweb._prepare_environment``), so a language
        # requested through ``data["lang"]`` is lost whenever the report is
        # rendered from an environment in another language — typically
        # base_report_to_printer's ``print_document``, which renders with the
        # user's own language when the report is sent to the printer. Align the
        # environment language with the requested one.
        lang = data and data.get("lang") or self.env.lang
        return super(IrActionsReport, self.with_context(lang=lang))._render_qweb_html(
            report_ref, docids, data=data
        )
