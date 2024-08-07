##############################################################################
#
#    Copyright (C) 2016-2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Pierrick Muller <pmuller@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64

from odoo import fields, models


class PrintChildPicture(models.TransientModel):
    """
    Wizard for selecting the way to print the child picture.
    """

    _name = "print.childpicture"
    _description = "Select the print method (pdf)"

    state = fields.Selection([("new", "new"), ("pdf", "pdf")], default="new")
    pdf = fields.Boolean("Pdf")
    pdf_name = fields.Char(default="childpicture.pdf")
    pdf_download = fields.Binary(readonly=True)

    def _get_children_datas(self):
        children = (
            self.env["compassion.child"]
            .browse(self.env.context.get("active_ids"))
            .with_context(async_mode=False)
        )
        for child in children:
            child.get_infos()
        return children

    def get_report(self):
        """
        Print selected child dossier
        :return: Generated report
        """
        children = self._get_children_datas()

        data = {
            "is_pdf": self.pdf,
            "type": "partner_communication_compassion.child_picture",
        }
        report_name = "child_compassion.report_child_picture"
        report_ref = self.env.ref(report_name)
        if self.pdf:
            name = children.local_id if len(children) == 1 else "childpicture"
            self.pdf_name = f"{name}_{data['type'].split('_')[-1]}.pdf"
            pdf_data = report_ref.with_context(
                must_skip_send_to_printer=True
            )._render_qweb_pdf(children.ids, data=data)
            self.pdf_download = base64.encodebytes(pdf_data[0])
            self.state = "pdf"
            return {
                "name": "Download report",
                "type": "ir.actions.act_window",
                "res_model": self._name,
                "res_id": self.id,
                "view_mode": "form",
                "target": "new",
                "context": self.env.context,
            }
        return report_ref.report_action(children.ids, data=data, config=False)
