from odoo import api, models, fields, _
from odoo.tools import email_normalize


class ResPartner(models.Model):
    _inherit = "res.partner"

    email_alias_ids = fields.One2many("res.partner.email", "partner_id", "Email aliases")

    def get_alias(self, email):
        """
        Returns the res.partner.email record associated to the given email address.
        :return: <res.partner.email> record
        """
        self.ensure_one()
        return self.email_alias_ids.filtered(lambda a: a.email == email_normalize(email))

    @api.model
    def find_or_create(self, email, assert_valid_email=False):
        if not email:
            raise ValueError(_('An email is required for find_or_create to work'))
        # Include aliases in search
        parsed_name, parsed_email = self._parse_partner_name(email)
        if parsed_email:
            email_normalized = email_normalize(parsed_email)
            if email_normalized:
                partner = self.search([
                    "|", ("email_normalized", "=", email_normalized), ("email_alias_ids.email", "=", email_normalized)
                ], limit=1)
                if partner:
                    return partner
        return super().find_or_create(email, assert_valid_email=assert_valid_email)
