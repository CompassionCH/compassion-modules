##############################################################################
#
#    Copyright (C) 2016-2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64

from odoo import api, fields, models


class PrintChildpack(models.TransientModel):
    """
    Wizard for selecting a the child dossier type and language.
    """

    _name = "print.childpack"
    _description = "Select the child dossier type and language"

    type = fields.Selection(
        [
            ("child_compassion.childpack_full", "Full Childpack"),
            ("child_compassion.childpack_small", "Small Childpack"),
        ],
        default=lambda s: s._default_type(),
    )
    lang = fields.Selection("_lang_selection", default=lambda s: s._default_lang())
    state = fields.Selection([("new", "new"), ("pdf", "pdf")], default="new")
    pdf = fields.Boolean("Print background")
    pdf_name = fields.Char(default="childpack.pdf")
    pdf_download = fields.Binary(readonly=True)
    module_name = fields.Char(compute="_compute_module_name")

    @api.model
    def _lang_selection(self):
        languages = self.env["res.lang"].search([])
        return [(language.code, language.name) for language in languages]

    @api.model
    def _default_type(self):
        child = self.env["compassion.child"].browse(self.env.context.get("active_id"))
        if child.sponsor_id:
            return "child_compassion.childpack_small"
        return "child_compassion.childpack_full"

    @api.model
    def _default_lang(self):
        child = self.env["compassion.child"].browse(self.env.context.get("active_id"))
        if child.sponsor_id:
            return child.sponsor_id.lang
        return self.env.lang

    def _compute_module_name(self):
        self.module_name = __name__.split(".")[2]

    def _get_children_datas(self):
        children = (
            self.env["compassion.child"]
            .browse(self.env.context.get("active_ids"))
            .with_context(lang=self.lang, async_mode=False)
        )
        lang = self.lang
        project_lang_map = self.env["compassion.project.description"]._supported_languages()
        child_lang_map = self.env["compassion.child.description"]._supported_languages()

        for child in children:
            if not getattr(child.project_id, project_lang_map.get(lang)):
                child.project_id.update_informations()
            if not getattr(child, child_lang_map.get(lang)):
                child.get_infos()
        return children

    def get_report(self):
        """
        Print selected child dossier
        :return: Generated report
        """
        children = self._get_children_datas()

        data = {
            "lang": self.lang,
            "doc_ids": children.ids,
            "is_pdf": self.pdf,
            "type": self.type,
        }
        report_name = self.module_name + ".report_" + self.type.split(".")[1]
        report_ref = self.env.ref(report_name).with_context(lang=self.lang)
        if self.pdf:
            name = children.local_id if len(children) == 1 else "childpacks"
            self.pdf_name = (
                f"{name}_{self.type.split('_')[-1]}_{self.lang.split('_')[0]}.pdf"
            )
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
