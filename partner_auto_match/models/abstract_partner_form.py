##############################################################################
#
#    Copyright (C) 2023 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PartnerForm(models.AbstractModel):
    _name = "cms.form.partner"
    _description = "Object for partner fields in forms"

    partner_title = fields.Many2one("res.partner.title", "Title")
    partner_lastname = fields.Char("Lastname")
    partner_firstname = fields.Char("Firstname")
    partner_street = fields.Char("Street")
    partner_zip = fields.Char("Zip")
    partner_city = fields.Char("City")
    partner_email = fields.Char("Email")
    partner_birthdate_date = fields.Date("Birthdate")
    partner_phone = fields.Char("Phone")
    partner_mobile = fields.Char("Mobile")
    partner_function = fields.Char("Job")
    partner_lang = fields.Many2one("res.lang", "Main language")
    partner_spoken_lang_ids = fields.Many2many(
        "res.lang.compassion",
        string="Languages I can read",
        domain=[("translatable", "=", True)],
    )
    partner_id = fields.Many2one(
        "res.partner", "Partner", default=lambda s: s.env.user.partner_id
    )
    match_update = fields.Boolean(default=False)
    match_create = fields.Boolean(default=True)

    @api.model
    def _convert_vals_for_res_partner(self, vals):
        """
        Gets the vals dict for this object and maps it to res.partner fields.
        @param vals: dict of cms.form.partner fields
        @return: dict of res.partner fields
        """
        res = {
            key.replace("partner_", ""): value
            for key, value in vals.items()
            if key.startswith("partner_")
        }
        # Convert language record_id into its code (as stored in partner)
        lang = res.get("lang")
        if lang and isinstance(lang, int):
            res["lang"] = self.env["res.lang"].browse(lang).code
        return res

    @api.model_create_multi
    def create(self, vals_list):
        """
        Automatically fill the partner_id relation at creation, based on
        the entered form values (using res.partner.match)
        The values of the form can contain special data for changing
        the behaviour:
            - match_update: whether it should update the partner with the data
            - match_create: whether it should create a partner (if none found)
        """
        for vals in vals_list:
            match_update = vals.get("match_update", False)
            match_create = vals.get("match_create", True)
            if vals.get("partner_id") and match_update:
                partner_vals = self._convert_vals_for_res_partner(vals)
                partner = self.env["res.partner"].browse(partner_vals["id"])
                self.env["res.partner.match"].update_partner(partner, partner_vals)
            if not vals.get("partner_id") and (match_update or match_create):
                partner_vals = self._convert_vals_for_res_partner(vals)
                vals["partner_id"] = (
                    self.env["res.partner.match"]
                    .match_values_to_partner(partner_vals, match_update, match_create)
                    .id
                )
        return super().create(vals_list)
