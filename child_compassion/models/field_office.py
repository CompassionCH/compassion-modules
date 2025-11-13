##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

import requests
import wbgapi as wbg

from odoo import fields, models

_logger = logging.getLogger(__name__)


class FieldOffice(models.Model):
    _name = "compassion.field.office"
    _inherit = "compassion.mapped.model"
    _description = "National Office"
    _order = "country_name,field_office_id"

    name = fields.Char()
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
    country_name = fields.Char(related="country_id.name", readonly=True)
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
    fcp_medical_check = fields.Integer("Medical check/year", default=1)
    fcp_ids = fields.One2many(
        "compassion.project",
        "field_office_id",
        "FCP",
        readonly=False,
    )
    # World Bank data fields
    capital_city = fields.Char(translate=True)
    population = fields.Integer()
    male_life_expectancy = fields.Integer()
    female_life_expectancy = fields.Integer()
    urban_water_access = fields.Float()
    rural_water_access = fields.Float()
    adult_literacy_rate = fields.Float()
    infant_mortality_rate = fields.Float()
    under_five_mortality_rate = fields.Float()
    less_than_2_dollars_a_day = fields.Float()
    # Factbook information
    factbook_url = fields.Char(
        help="URL to the CIA World Factbook page for this country.",
    )
    religions = fields.Char(translate=True)

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
        """Get the most recent informations for selected field offices and
        update them accordingly."""
        message_obj = self.env["gmc.message"]
        action_id = self.env.ref("child_compassion.field_office_details").id

        message_vals = {
            "action_id": action_id,
            "object_id": self.id,
        }
        message_obj.with_context(queue_job__no_delay=True).create(message_vals)
        return True

    def refresh_worldbank_data(self):
        self.ensure_one()
        country_code = self.country_id.code_alpha3
        indicators = {
            "population": "SP.POP.TOTL",
            "male_life_expectancy": "SP.DYN.LE00.MA.IN",
            "female_life_expectancy": "SP.DYN.LE00.FE.IN",
            "urban_water_access": "SH.H2O.SMDW.UR.ZS",
            "rural_water_access": "SH.H2O.SMDW.RU.ZS",
            "adult_literacy_rate": "SE.ADT.LITR.ZS",
            "infant_mortality_rate": "SP.DYN.IMRT.IN",
            "under_five_mortality_rate": "SH.DYN.MORT",
            "less_than_2_dollars_a_day": "SI.POV.DDAY",
        }
        for field, indicator in indicators.items():
            try:
                data = list(wbg.data.fetch(indicator, country_code, mrnev=1))
            except wbg.APIResponseError:
                _logger.error(
                    "Failed to fetch data for %s with indicator %s and country code %s",
                    field,
                    indicator,
                    country_code,
                )
                data = []
            if data:
                value = data[0]["value"]
                if field in (
                    "urban_water_access",
                    "rural_water_access",
                    "adult_literacy_rate",
                    "less_than_2_dollars_a_day",
                ):
                    value /= 100
                elif field in (
                    "infant_mortality_rate",
                    "under_five_mortality_rate",
                ):
                    value /= 1000
                setattr(self, field, value)

    def refresh_capital_city(self):
        self.ensure_one()
        country_code = self.country_id.code
        if not country_code:
            return

        def fetch_capital(url):
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                data = response.json()
                if len(data) > 1 and data[1] and isinstance(data[1][0], dict):
                    return data[1][0].get("capitalCity")
            _logger.error("Failed to fetch capital city with URL %s", url)
            return None

        # Fetch default (English) capital city
        url = f"https://api.worldbank.org/v2/country/{country_code}?format=json"
        capital = fetch_capital(url)
        if capital:
            self.capital_city = capital

        # Fetch capital city for other languages
        for lang in self.env["res.lang"].search([("code", "!=", "en_US")]):
            url = f"https://api.worldbank.org/v2/{lang.code[:2]}/country/{country_code}?format=json"
            capital = fetch_capital(url)
            if capital:
                self.with_context(lang=lang.code).capital_city = capital

    def refresh_factbook_data(self):
        self.ensure_one()
        if not self.factbook_url:
            return
        response = requests.get(self.factbook_url, timeout=3)
        if response.status_code == 200:
            country_data = response.json()
            religion_data = country_data.get("People and Society", {}).get(
                "Religions", {}
            )
            if religion_data:
                self.religions = religion_data.get("text")


class FieldOfficeHighRisks(models.Model):
    _name = "fo.high.risk"
    _inherit = "connect.multipicklist"
    _description = "FO high risk"
    res_model = "compassion.field.office"
    res_field = "high_risk_ids"

    value = fields.Char(translate=True)
