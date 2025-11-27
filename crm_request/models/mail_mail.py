from odoo import api, models


class MailMail(models.Model):
    _inherit = "mail.mail"

    """Provides a way to send e-mail to the alias address of a contact
    (should be set in the context where needed).
    """

    @api.model_create_multi
    def create(self, vals_list):
        email_alias = self.env.context.get("use_email_alias")
        if email_alias:
            if not isinstance(vals_list, list):
                vals_list = [vals_list]
            for vals in vals_list:
                del vals["recipient_ids"]
                vals["email_to"] = email_alias
        return super().create(vals_list)
