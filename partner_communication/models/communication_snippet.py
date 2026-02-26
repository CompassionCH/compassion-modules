from odoo import fields, models


class CommunicationSnippetCategory(models.Model):
    _name = "communication.snippet.category"
    _description = "Communication Snippet Category"

    name = fields.Char(string="Category Name", required=True)

    _sql_constraints = [
        (
            "name_unique",
            "unique(name)",
            "The name of the category must be unique.",
        )
    ]


class CommunicationSnippet(models.Model):
    _name = "communication.snippet"
    _description = "Communication Snippet"

    name = fields.Char(required=True, index=True)
    snippet_text = fields.Html(required=True, translate=True, sanitize=False)
    description = fields.Text(string="Description")

    category_id = fields.Many2one(
        "communication.snippet.category",
        string="Category",
        help="Category of the communication snippet",
    )

    def action_edit_snippet(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
        }
