##############################################################################
#
#    Copyright (C) 2016-2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models


class ReportChildpackFull(models.AbstractModel):
    """
    Rendering context of the childpack reports.

    The print wizard passes its options (lang, type, print_qr, ...) through the
    ``data`` dictionary. When that dictionary is set, the web client builds the
    report URL without the record ids (see ``getReportUrl`` in web), so the
    report is rendered with no ``docids`` at all and would print a blank page.
    We therefore fall back on the ids the wizard stored in ``data['doc_ids']``.
    """

    _name = "report.child_compassion.childpack_full"
    _description = "Childpack report rendering context"

    @api.model
    def _get_report_values(self, docids, data=None):
        data = dict(data or {})
        docids = docids or data.get("doc_ids") or self.env.context.get("active_ids", [])
        lang = data.get("lang")
        docs = self.env["compassion.child"].browse(docids)
        if lang:
            docs = docs.with_context(lang=lang)
        data.update(
            {
                "doc_ids": docs.ids,
                "doc_model": "compassion.child",
                "docs": docs,
            }
        )
        return data


# pylint: disable=R7980
class ReportChildpackSmall(models.AbstractModel):
    _inherit = "report.child_compassion.childpack_full"
    _name = "report.child_compassion.childpack_small"
    _description = "Small childpack report rendering context"
