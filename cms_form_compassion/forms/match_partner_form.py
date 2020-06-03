##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import re

from odoo import models, fields, _


class PartnerMatchform(models.AbstractModel):
    """A form that can create partner given data.
       It will put the found partner in field partner_id that must
       be present on the related model.
    """

    _name = "cms.form.match.partner"
    _description = "Form with partner matching"

    _inherit = ["cms.form", "res.partner.match"]

    partner_id = fields.Many2one("res.partner", readonly=False)
    partner_title = fields.Many2one(
        "res.partner.title", "Title", required=True, readonly=False
    )
    partner_firstname = fields.Char("First Name", required=True)
    partner_lastname = fields.Char("Last Name", required=True)
    partner_email = fields.Char("Email", required=True)
    partner_phone = fields.Char("Phone", required=True)
    partner_street = fields.Char("Street", required=True)
    partner_zip = fields.Char("Zip", required=True)
    partner_city = fields.Char("City", required=True)
    partner_country_id = fields.Many2one(
        "res.country", "Country", required=True, readonly=False
    )
    partner_state_id = fields.Many2one("res.country.state", "State", readonly=False)
    partner_lang = fields.Selection(
        lambda self: self.env["res.lang"].sudo().get_installed(),
        "Language"
    )
    partner_birthdate = fields.Date("Birthdate")

    #######################################################################
    #            Inject default values in form from main object           #
    #######################################################################
    def _form_load_partner_id(self, fname, field, value, **req_values):
        return value or req_values.get(fname, self.main_object.partner_id.id)

    def _form_load_partner_firstname(self, fname, field, value, **req_values):
        return value or self._load_partner_field(fname, **req_values)

    def _form_load_partner_lastname(self, fname, field, value, **req_values):
        return value or self._load_partner_field(fname, **req_values)

    def _form_load_partner_title(self, fname, field, value, **req_values):
        read_val = value or self._load_partner_field(fname, **req_values)
        if isinstance(read_val, models.Model):
            read_val = read_val.id
        return read_val

    def _form_load_partner_email(self, fname, field, value, **req_values):
        return value or self._load_partner_field(fname, **req_values)

    def _form_load_partner_phone(self, fname, field, value, **req_values):
        return value or self._load_partner_field(fname, **req_values)

    def _form_load_partner_street(self, fname, field, value, **req_values):
        return value or self._load_partner_field(fname, **req_values)

    def _form_load_partner_zip(self, fname, field, value, **req_values):
        return value or self._load_partner_field(fname, **req_values)

    def _form_load_partner_city(self, fname, field, value, **req_values):
        return value or self._load_partner_field(fname, **req_values)

    def _form_load_partner_country_id(self, fname, field, value, **req_values):
        read_val = value or self._load_partner_field(fname, **req_values)
        if isinstance(read_val, models.Model):
            read_val = read_val.id
        return read_val or self.env.ref("base.ch").id

    def _form_load_partner_lang(self, fname, field, value, **req_values):
        return value or self._load_partner_field(fname, **req_values)

    def _form_load_partner_birthdate(self, fname, field, value, **req_values):
        return value or self._load_partner_field(fname, **req_values)

    def _load_partner_field(self, fname, **req_values):
        """ For inherited forms, we try to load partner fields in
        partner_id field that may exist in main_object of form. """
        partner = self.main_object.partner_id or self.env["res.partner"]
        pf_name = fname.split("partner_")[1]
        return req_values.get(fname, getattr(partner.sudo(), pf_name, ""))

    #######################################################################
    #                         Field validation                            #
    #######################################################################
    def _form_validate_partner_phone(self, value, **req_values):
        if value and not re.match(r"^[+\d][\d\s]{7,}$", value, re.UNICODE):
            return "phone", _("Please enter a valid phone number")
        # No error
        return 0, 0

    def _form_validate_partner_email(self, value, **req_values):
        if value and not re.match(r"[^@]+@[^@]+\.[^@]+", value):
            return "email", _("Verify your e-mail address")
        # No error
        return 0, 0

    def _form_validate_partner_lastname(self, value, **req_values):
        return self._form_validate_alpha_field("last_name", value)

    def _form_validate_partner_firstname(self, value, **req_values):
        return self._form_validate_alpha_field("first_name", value)

    def _form_validate_partner_city(self, value, **req_values):
        return self._form_validate_alpha_field("city", value)

    def _form_validate_partner_street(self, value, **req_values):
        return self._form_validate_alpha_field("street", value)

    def _form_validate_alpha_field(self, field, value):
        if value and not re.match(r"^[\w\s'-/]+$", value, re.UNICODE):
            return field, _("Please avoid any special characters")
        # No error
        return 0, 0

    #######################################################################
    #                     FORM SUBMISSION METHODS                         #
    #######################################################################
    def form_before_create_or_update(self, values, extra_values):
        """
        Find and returns a matching partner, or create one.
        """
        super().form_before_create_or_update(values, extra_values)

        source_vals = self._get_partner_vals(values, extra_values)

        partner_id = values.get("partner_id")
        if partner_id:
            source_vals["partner_id"] = partner_id

        options = {
            "skip_update": extra_values.get("skip_update"),
            "skip_create": extra_values.get("skip_create"),
        }

        # Try to find a res.city.zip location for given data
        res_city_zip_obj = self.env["res.city.zip"]
        partner_location = res_city_zip_obj.search([
            ("name", '=', extra_values.get("partner_zip", None)),
            ("city_id.name", '=ilike', extra_values.get("partner_city"))
        ], limit=1)
        if not partner_location:
            partner_location = res_city_zip_obj.search([
                ("name", '=', extra_values.get('partner_zip', None))
            ])
        if len(partner_location) == 1:
            source_vals.update({
                "zip_id": partner_location.id,
                "city": partner_location.city_id.name,
                "city_id": partner_location.city_id.id,
                "state_id": partner_location.city_id.state_id.id,
            })

        self.partner_id = self.match_partner_to_infos(source_vals, options)
        values["partner_id"] = self.partner_id.id

    #######################################################################
    #                         PRIVATE METHODS                             #
    #######################################################################
    def _get_partner_vals(self, values, extra_values):
        all_values = values.copy()
        all_values.update(extra_values)
        prefix = "partner_"
        vals = {
            key.replace(prefix, ""): val
            for key, val in all_values.items()
            if key.startswith(prefix) and val
        }
        # Make active any partner that is matched
        vals["active"] = True
        return vals
