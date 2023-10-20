##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


from odoo import api, models, fields


class FieldOffice(models.Model):
    _name = "compassion.field.office"
    _inherit = "compassion.mapped.model"
    _description = "National Office"
    _order = "country_name,field_office_id"

    name = fields.Char("Name")
    field_office_id = fields.Char(required=True)
    project_ids = fields.One2many(
        "compassion.project", "field_office_id", "Compassion projects", readonly=False
    )
    region = fields.Char()
    country_director = fields.Char()
    date_start = fields.Date("National office start")
    issue_email = fields.Char()
    phone_number = fields.Char()
    website = fields.Char()
    social_media_site = fields.Char()
    country = fields.Char(string="country")
    country_id = fields.Many2one("res.country", "Country", readonly=False)
    country_code = fields.Char(related="country_id.code")
    country_name = fields.Char(related="country_id.name", store=True, readonly=True)
    street = fields.Char()
    city = fields.Char()
    province = fields.Char()
    zip_code = fields.Char()
    currency = fields.Char()
    learning_image_url = fields.Char()
    learning_summary = fields.Text(translate=True)
    learning_ids = fields.One2many(
        "field.office.learning",
        "field_office_id",
        string="What I learn",
        readonly=False,
    )
    available_on_childpool = fields.Boolean(
        default=True, help="Uncheck to restrict child selection from this field office."
    )

    primary_language_id = fields.Many2one(
        "res.lang.compassion", "Primary " "language", readonly=False
    )
    spoken_language_ids = fields.Many2many(
        "res.lang.compassion",
        "field_office_spoken_langs",
        string="Spoken languages",
        readonly=False,
    )
    translated_language_ids = fields.Many2many(
        "res.lang.compassion",
        "field_office_translated_langs",
        string="Translated languages",
        readonly=False,
    )

    staff_number = fields.Integer()
    country_information = fields.Char()
    high_risk_ids = fields.Many2many(
        "fo.high.risk", string="Participant high risks", readonly=False
    )

    disaster_alert_ids = fields.Many2many(
        "fo.disaster.alert", string="Disaster alerts", readonly=False
    )
    fcp_hours_week = fields.Integer("Hours/week", default=8)
    fcp_meal_week = fields.Integer("Meals/week", default=1)
    fcp_medical_check = fields.Integer(
        "Medical check/year", default=1
    )
    fcp_ids = fields.One2many(
        "compassion.project",
        "field_office_id",
        "FCP",

        readonly=False,
    )

    _sql_constraints = [
        (
            "field_office_id",
            "unique(field_office_id)",
            "The field already exists in database.",
        ),
    ]

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    def update_informations(self):
        """ Get the most recent informations for selected field offices and
        update them accordingly. """
        message_obj = self.env["gmc.message"]
        action_id = self.env.ref("child_compassion.field_office_details").id

        message_vals = {
            "action_id": action_id,
            "object_id": self.id,
        }
        message_obj.with_context(async_mode=False).create(message_vals)
        return True


class FieldOfficeHighRisks(models.Model):
    _name = "fo.high.risk"
    _inherit = "connect.multipicklist"
    _description = "FO high risk"
    res_model = "compassion.field.office"
    res_field = "high_risk_ids"

    value = fields.Char(translate=True)
