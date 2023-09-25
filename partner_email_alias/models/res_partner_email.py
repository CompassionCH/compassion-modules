from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import email_normalize


class PartnerEmail(models.Model):
    _name = "res.partner.email"
    _description = "Contact e-mail alias"

    partner_id = fields.Many2one(
        "res.partner", required=True, index=True, ondelete="cascade"
    )
    email = fields.Char(required=True, index=True)

    _sql_constraints = [
        (
            "unique_email",
            "unique(email)",
            "This e-mail alias is already registered for a partner.",
        )
    ]

    @api.constrains("email")
    def _unique_email(self):
        for alias in self:
            if self.env["res.partner"].search_count(
                [("email_normalized", "=", alias.email)]
            ):
                raise ValidationError(
                    "This email address is already set in one partner"
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["email"] = email_normalize(vals.get("email"))
        return super().create(vals_list)

    def write(self, vals):
        if "email" in vals:
            vals["email"] = email_normalize(vals["email"])
