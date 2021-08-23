# Copyright (C) 2021 Compassion CH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AssignRequestWizard(models.TransientModel):
    _name = "holiday.closure.template.preview"
    _description = "Holiday Closure Template Preview"

    preview_text = fields.Html(default=lambda s: s.get_default(), readonly=True)

    @api.model
    def get_default(self):
        template = self.env.ref("crm_request.business_closed_email_template")
        fake_claim = self.env["crm.claim"].create({
            "partner_id": self.env.user.partner_id.id,
            "name": "Holiday preview",
            "holiday_closure_id": self.env.context.get("active_id")
        })
        res = ""
        for lang in self.env["res.lang"].search([]):
            res += f"<h2>{lang.name}:</h2>"
            fake_claim.language = lang.code
            res += template.with_context(lang=lang.code)._render_template(
                template.body_html, template.model, fake_claim.id)
            res += "<br/><br/>"
        fake_claim.unlink()
        return res
