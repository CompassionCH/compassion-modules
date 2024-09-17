from odoo import fields, models


class CommunicationSnippet(models.Model):
    _name = "communication.snippet"
    _description = "Communication Snippet"

    name = fields.Char(required=True, index=True)
    snippet_text = fields.Html(required=True, translate=True)

    def action_edit_snippet(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
        }
