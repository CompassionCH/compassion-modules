##############################################################################
#
#    Copyright (C) 2014-2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester, Kevin Cristi, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging
import re
from datetime import datetime, timedelta

import requests

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError

from odoo.addons.message_center_compassion.tools.onramp_connector import OnrampConnector

logger = logging.getLogger(__name__)

try:
    from pytz import timezone
    from timezonefinder import TimezoneFinder
except (OSError, ImportError):
    logger.warning("Please install timezonefinder and pytz")


class CompassionProject(models.Model):
    """A compassion project"""

    _name = "compassion.project"
    _rec_name = "fcp_id"
    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
        "translatable.model",
        "compassion.mapped.model",
    ]
    _description = "Frontline Church Partner"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    # General Information
    #####################
    fcp_id = fields.Char(required=True)
    name = fields.Char(readonly=True)
    child_center_original_name = fields.Char(readonly=True)
    local_church_name = fields.Char(readonly=True)
    local_church_original_name = fields.Char(readonly=True)
    website = fields.Char(readonly=True)
    social_media_site = fields.Char(readonly=True)
    involvement_ids = fields.Many2many(
        "fcp.involvement", string="Involvement", readonly=True
    )
    available_for_visits = fields.Boolean(readonly=True)
    nb_csp_kids = fields.Integer("CSP kids count", readonly=True)
    nb_cdsp_kids = fields.Integer("CDSP kids count", readonly=True)
    last_update_date = fields.Date("Last update", readonly=True)
    interested_partner_ids = fields.Many2many(
        "compassion.global.partner",
        string="GP interested with a church engagement",
        readonly=True,
    )

    _sql_constraints = [
        ("fcp_id_uniq", "unique(fcp_id)", "The FCP Id must be unique."),
    ]

    # Location information
    ######################
    country_id = fields.Many2one("res.country", "Country", readonly=True)
    street = fields.Char(readonly=True)
    city = fields.Char(readonly=True)
    state_province = fields.Char(readonly=True)
    zip_code = fields.Char(readonly=True)
    gps_latitude = fields.Float(readonly=True)
    gps_longitude = fields.Float(readonly=True)
    timezone = fields.Char(readonly=True, compute="_compute_timezone", store=True)
    cluster = fields.Char(readonly=True)
    territory = fields.Char(readonly=True)
    field_office_id = fields.Many2one(
        "compassion.field.office",
        "National Office",
        compute="_compute_field_office",
        store=True,
        readonly=False,
    )

    # Church information
    ####################
    church_foundation_date = fields.Date(readonly=True)
    church_denomination = fields.Char(readonly=True)
    international_affiliation = fields.Char(readonly=True)
    ministry_ids = fields.Many2many(
        "fcp.church.ministry", string="Church ministries", readonly=True
    )
    preferred_lang_id = fields.Many2one(
        "res.lang.compassion", "Church preferred language", readonly=True
    )
    number_church_members = fields.Integer(readonly=True)
    weekly_child_attendance = fields.Integer(readonly=True)
    implemented_program_ids = fields.Many2many(
        "fcp.program",
        "fcp_implemented_programs",
        "fcp_id",
        "program_id",
        string="Programs implemented",
        readonly=True,
    )
    interested_program_ids = fields.Many2many(
        "fcp.program",
        "fcp_interested_programs",
        "fcp_id",
        "program_id",
        string="Programs of interest",
        readonly=True,
    )

    # Church infrastructure information
    ###################################
    church_building_size = fields.Float(help="Unit is square meters", readonly=True)
    church_ownership = fields.Selection(
        [
            ("Rented", "Rented"),
            ("Owned", "Owned"),
        ],
        readonly=True,
    )
    facility_ids = fields.Many2many(
        "fcp.church.facility", string="Church facilities", readonly=True
    )
    nb_staff_computers = fields.Char(size=2, readonly=True)
    nb_child_computers = fields.Char(size=2, readonly=True)
    nb_classrooms = fields.Char(size=2, readonly=True)
    nb_latrines = fields.Char(size=2, readonly=True)
    church_internet_access = fields.Char(readonly=True)
    mobile_device_ids = fields.Many2many(
        "fcp.mobile.device", string="Mobile devices", readonly=True
    )
    utility_ids = fields.Many2many(
        "fcp.church.utility", string="Church utilities", readonly=True
    )
    electrical_power = fields.Selection(
        [
            ("Not Available", "Not Available"),
            ("Available Sometimes", "Available Sometimes"),
            ("Available Most Of The Time", "Available Most of the Time"),
        ],
        readonly=True,
    )

    # FCP Activities
    ################
    spiritual_activity_babies_ids = fields.Many2many(
        "fcp.spiritual.activity",
        "fcp_spiritual_baby_act",
        string="Spiritual activities (0-5)",
        readonly=True,
    )
    spiritual_activity_kids_ids = fields.Many2many(
        "fcp.spiritual.activity",
        "fcp_spiritual_kid_act",
        string="Spiritual activities (6-11)",
        readonly=True,
    )
    spiritual_activity_ados_ids = fields.Many2many(
        "fcp.spiritual.activity",
        "fcp_spiritual_ado_act",
        string="Spiritual activities (12+)",
        readonly=True,
    )
    cognitive_activity_babies_ids = fields.Many2many(
        "fcp.cognitive.activity",
        "fcp_cognitive_baby_act",
        string="Cognitive activities (0-5)",
        readonly=True,
    )
    cognitive_activity_kids_ids = fields.Many2many(
        "fcp.cognitive.activity",
        "fcp_cognitive_kid_act",
        string="Cognitive activities (6-11)",
        readonly=True,
    )
    cognitive_activity_ados_ids = fields.Many2many(
        "fcp.cognitive.activity",
        "fcp_cognitive_ado_act",
        string="Cognitive activities (12+)",
        readonly=True,
    )
    physical_activity_babies_ids = fields.Many2many(
        "fcp.physical.activity",
        "fcp_physical_baby_act",
        string="Physical activities (0-5)",
        readonly=True,
    )
    physical_activity_kids_ids = fields.Many2many(
        "fcp.physical.activity",
        "fcp_physical_kid_act",
        string="Physical activities (6-11)",
        readonly=True,
    )
    physical_activity_ados_ids = fields.Many2many(
        "fcp.physical.activity",
        "fcp_physical_ado_act",
        string="Physical activities (12+)",
        readonly=True,
    )
    socio_activity_babies_ids = fields.Many2many(
        "fcp.sociological.activity",
        "fcp_socio_baby_act",
        string="Sociological activities (0-5)",
        readonly=True,
    )
    socio_activity_kids_ids = fields.Many2many(
        "fcp.sociological.activity",
        "fcp_socio_kid_act",
        string="Sociological activities (6-11)",
        readonly=True,
    )
    socio_activity_ados_ids = fields.Many2many(
        "fcp.sociological.activity",
        "fcp_socio_ado_act",
        string="Sociological activities (12+)",
        readonly=True,
    )
    reservation_id = fields.Many2one(
        "compassion.reservation",
        string="Project Reservation",
        readonly=True,
        ondelete="cascade",
    )
    activities_for_parents = fields.Char(readonly=True)

    # Community information
    #######################
    community_name = fields.Char(readonly=True)
    community_population = fields.Integer(readonly=True)
    primary_ethnic_group_name = fields.Char(readonly=True)
    primary_language_id = fields.Many2one(
        "res.lang.compassion", "Primary language", readonly=True
    )
    primary_adults_occupation_ids = fields.Many2many(
        "fcp.community.occupation", string="Primary adults occupation", readonly=True
    )
    local_currency = fields.Many2one(
        "res.currency", related="country_id.currency_id", readonly=False
    )
    monthly_income = fields.Float(
        help="Average family income in local currency", readonly=True
    )
    usd = fields.Many2one("res.currency", compute="_compute_usd", readonly=False)
    chf_income = fields.Float(compute="_compute_chf_income")
    unemployment_rate = fields.Float(readonly=True)
    annual_primary_school_cost = fields.Float(readonly=True, help="In local currency")
    annual_secondary_school_cost = fields.Float(readonly=True, help="In local currency")
    school_cost_paid_ids = fields.Many2many(
        "fcp.school.cost", string="School costs paid by FCP", readonly=True
    )
    school_year_begins = fields.Selection("_get_months", readonly=True)
    closest_city = fields.Char(readonly=True)
    closest_airport_distance = fields.Float(
        help="Distance in kilometers", readonly=True
    )
    time_to_airport = fields.Float(help="Time in minutes", readonly=True)
    transport_mode_to_airport = fields.Char(readonly=True)
    time_to_medical_facility = fields.Char(readonly=True)
    community_locale = fields.Char(readonly=True)
    community_climate = fields.Char(readonly=True)
    community_terrain = fields.Char(readonly=True, translate=True)
    typical_roof_material = fields.Selection("_get_materials", readonly=True)
    typical_floor_material = fields.Selection("_get_materials", readonly=True)
    typical_wall_material = fields.Selection("_get_materials", readonly=True)
    average_coolest_temperature = fields.Char(readonly=True)
    coolest_month = fields.Selection("_get_months", readonly=True)
    average_warmest_temperature = fields.Char(readonly=True)
    warmest_month = fields.Selection("_get_months", readonly=True)
    rainy_month_ids = fields.Many2many(
        "connect.month", string="Rainy months", readonly=True
    )
    planting_month_ids = fields.Many2many(
        "connect.month",
        relation="compassion_project_planting_months",
        string="Planting months",
        readonly=True,
    )
    harvest_month_ids = fields.Many2many(
        "connect.month",
        relation="compassion_project_harvest_months",
        string="Harvest months",
        readonly=True,
    )
    hunger_month_ids = fields.Many2many(
        "connect.month",
        relation="compassion_project_hunger_months",
        string="Hunger months",
        readonly=True,
    )
    cultural_rituals = fields.Text(readonly=True)
    economic_needs = fields.Text(readonly=True)
    health_needs = fields.Text(readonly=True)
    education_needs = fields.Text(readonly=True)
    social_needs = fields.Text(readonly=True)
    spiritual_needs = fields.Text(readonly=True)
    primary_diet_ids = fields.Many2many(
        "fcp.diet", string="Primary diet", readonly=True
    )
    fcp_disaster_impact_ids = fields.One2many(
        "fcp.disaster.impact",
        "project_id",
        "FCP Disaster Impacts",
        readonly=False,
    )
    current_weather = fields.Selection(
        [
            ("Clear", "Clear"),
            ("Clouds", "Clouds"),
            ("Rain", "Rain"),
            ("Storm", "Storm"),
            ("Mist", "Mist"),
            ("Thunderstorm", "Thunderstorm"),
            ("Haze", "Haze"),
            ("Drizzle", "Drizzle"),
            ("Snow", "Snow"),
            ("Smoke", "Smoke"),
            ("Dust", "Dust"),
            ("Fog", "Fog"),
            ("Sand", "Sand"),
            ("Ash", "Ash"),
            ("Squall", "Squall"),
            ("Tornado", "Tornado"),
        ]
    )
    current_temperature = fields.Float()
    last_weather_refresh_date = fields.Datetime()

    # Partnership
    #############
    partnership_start_date = fields.Date(readonly=True)
    program_start_date = fields.Date(readonly=True)
    program_end_date = fields.Date(readonly=True)

    # Program Settings
    ##################
    first_scheduled_letter = fields.Selection("_get_months", readonly=True)
    second_scheduled_letter = fields.Selection("_get_months", readonly=True)

    # Project state
    ###############
    lifecycle_ids = fields.One2many(
        "compassion.project.ile", "project_id", "Lifecycle events", readonly=True
    )
    covid_status_ids = fields.One2many(
        "compassion.project.covid_update",
        "fcp_id",
        "FCP Re-opening Status",
        readonly=True,
    )

    suspension = fields.Selection(
        [("suspended", "Suspended"), ("fund-suspended", "Suspended & fund retained")],
        "Suspension",
        compute="_compute_suspension_state",
        store=True,
        tracking=True,
    )
    status = fields.Selection(
        [
            ("A", _("Active")),
            ("P", _("Phase-out")),
            ("T", _("Terminated")),
            ("S", _("Suspended")),
        ],
        tracking=True,
        default="A",
        readonly=True,
    )
    last_reviewed_date = fields.Date(
        "Last reviewed date",
        tracking=True,
        readonly=True,
    )
    status_comment = fields.Text(related="lifecycle_ids.details", store=True)
    hold_cdsp_funds = fields.Boolean(related="lifecycle_ids.hold_cdsp_funds")
    hold_csp_funds = fields.Boolean(related="lifecycle_ids.hold_csp_funds")
    hold_gifts = fields.Boolean(related="lifecycle_ids.hold_gifts")
    hold_s2b_letters = fields.Boolean(related="lifecycle_ids.hold_s2b_letters")
    hold_b2s_letters = fields.Boolean(related="lifecycle_ids.hold_b2s_letters")

    # Project Descriptions
    ######################
    description_en = fields.Html("English description", readonly=True)
    description_left = fields.Html(compute="_compute_description")
    description_right = fields.Html(compute="_compute_description")

    re_opening_status = fields.Char(
        compute="_compute_re_opening_state",
        store=True,
        tracking=True,
    )

    @property
    def translated_fields(self):
        return [
            "involvement_ids.value",
            "ministry_ids.value",
            "implemented_program_ids.value",
            "interested_program_ids.value",
            "facility_ids.value",
            "mobile_device_ids.value",
            "utility_ids.value",
            "spiritual_activity_babies_ids.value",
            "spiritual_activity_kids_ids.value",
            "spiritual_activity_ados_ids.value",
            "cognitive_activity_babies_ids.value",
            "cognitive_activity_kids_ids.value",
            "cognitive_activity_ados_ids.value",
            "physical_activity_babies_ids.value",
            "physical_activity_kids_ids.value",
            "physical_activity_ados_ids.value",
            "socio_activity_babies_ids.value",
            "socio_activity_kids_ids.value",
            "socio_activity_ados_ids.value",
            "primary_adults_occupation_ids.value",
            "school_cost_paid_ids.value",
            "rainy_month_ids.name",
            "planting_month_ids.name",
            "harvest_month_ids.name",
            "hunger_month_ids.name",
            "primary_diet_ids.value",
            "preferred_lang_id.name",
            "primary_language_id.name",
            "church_ownership",
            "electrical_power",
            "school_year_begins",
            "typical_roof_material",
            "typical_floor_material",
            "typical_wall_material",
            "coolest_month",
            "warmest_month",
            "current_weather",
            "first_scheduled_letter",
            "second_scheduled_letter",
            "community_terrain",
        ]

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    def _compute_description(self):
        lang_map = self.env["compassion.project.description"]._supported_languages()

        for project in self:
            lang = self.env.lang or "en_US"
            description = getattr(project, lang_map.get(lang), "")
            project.description_right = description
            project.description_left = False

    @api.depends("fcp_id")
    def _compute_field_office(self):
        fo_obj = self.env["compassion.field.office"]
        for project in self.filtered("fcp_id"):
            fo = fo_obj.search([("field_office_id", "=", project.fcp_id[:2])])
            project.field_office_id = fo.id

    @api.model
    def _get_months(self):
        return self.env["connect.month"].get_months_selection()

    @api.depends("lifecycle_ids")
    def _compute_suspension_state(self):
        for project in self.filtered("lifecycle_ids"):
            most_recent_date = max(project.lifecycle_ids.mapped('date'))
            most_recent_lifecycles = project.lifecycle_ids.filtered(lambda r: r.date == most_recent_date)

            # Check if there is a lifecyle with type 'Reactivation' in the most recent date
            reactivation_lifecycle = next(
                (lifecycle for lifecycle in most_recent_lifecycles if lifecycle.type == 'Reactivation'), None)

            # If it exists, lifecycle with type 'Reactivation' is determinant
            if reactivation_lifecycle is None:
                determinant_lifecycle = most_recent_lifecycles[-1]
            else:
                determinant_lifecycle = reactivation_lifecycle
                project.suspension = False

            if determinant_lifecycle.type == "Suspension":
                project.suspension = (
                    "fund-suspended" if determinant_lifecycle.hold_cdsp_funds else "suspended"
                )
            elif determinant_lifecycle.type == "Reactivation":
                project.suspension = False

    @api.depends("covid_status_ids")
    def _compute_re_opening_state(self):
        for project in self.filtered("covid_status_ids"):
            project.re_opening_status = project.covid_status_ids[0].re_opening_status

    @api.model
    def _get_materials(self):
        return [
            ("Bamboo", "Bamboo"),
            ("Brick/Block/Cement", "Brick, block and cement"),
            ("Cardboard", "Cardboard"),
            ("Cement", "Cement"),
            ("Cloth/Carpet", "Cloth and carpet"),
            ("Dirt", "Dirt"),
            ("Leaves/Grass/Thatch", "Leaves, grass and thatch"),
            ("Leaves/Grass", "Leaves and grass"),
            ("Mud/Earth/Clay/Adobe", "Mud, earth, clay and adobe"),
            ("Plastic Sheets", "Plastic sheets"),
            ("Tile", "Tile"),
            ("Tin/Corrugated Iron", "Tin"),
            ("Wood", "Wood"),
            ("Tin", "Tin"),
            ("Plastic", "Plastic"),
        ]

    @api.depends("gps_longitude", "gps_latitude")
    def _compute_timezone(self):
        tf = TimezoneFinder()
        for project in self:
            if not project.gps_latitude or not project.gps_longitude:
                project.timezone = ""
            project.timezone = tf.timezone_at(
                lng=project.gps_longitude, lat=project.gps_latitude
            )

    def _compute_usd(self):
        usd = self.env.ref("base.USD")
        for project in self:
            project.usd = usd

    def _compute_chf_income(self):
        for project in self.filtered("country_id"):
            income = project.monthly_income / project.country_id.currency_id.rate
            if int(income) < 10:
                income = project.monthly_income / project.usd.rate
            project.chf_income = income

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals_list):
        """Avoid creating an already existing FCP."""
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        result = self
        for vals in vals_list:
            fcp_id = vals.get("fcp_id")
            project = self.search([("fcp_id", "=", fcp_id)])
            if not project:
                project = super().create(vals)
            result += project
        result.with_context(async_mode=True).update_informations()
        return result

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def suspend_funds(self):
        """Hook to perform some action when project is suspended.
        By default: log a message.
        """
        for project in self:
            project.message_post(
                body=_("The project was suspended."),
                subject=_("Project Suspended"),
                subtype_xmlid="mail.mt_comment",
            )
        return True

    def get_time(self):
        """
        Compute the current time in the project location
        :return: String in format
        """
        fmt = "%d/%m/%Y %H:%M:%S"
        return self.mapped(
            lambda x: timezone(x.timezone).localize(datetime.now()).strftime(fmt)
        )

    @api.model
    def set_missing_field_offices(self):
        self.search([("field_office_id", "=", False)])._compute_field_office()
        return True

    def update_weather(self):
        """
        Update the weather infos of the centers if it was not accessed in the
        last hour.
        :return:
        """
        for project in self:
            if not project.last_weather_refresh_date or (
                datetime.now() - project.last_weather_refresh_date > timedelta(hours=1)
            ):
                json = requests.get(
                    "https://api.openweathermap.org/data/2.5/weather"
                    + "?lat="
                    + str(project.gps_latitude)
                    + "&lon="
                    + str(project.gps_longitude)
                    + "&appid="
                    + tools.config.get("openweathermap_api_key")
                ).json()
                if json["cod"] != 200:
                    logging.error("Could not retrieve weather info.")
                    continue
                project.current_weather = json["weather"][0]["main"]
                project.current_temperature = json["main"]["temp"]
                project.last_weather_refresh_date = fields.Datetime.now()

    def get_activities(self, field, max_int=float("inf")):
        all_activities = (
            self.mapped(field + "_babies_ids")
            + self.mapped(field + "_kids_ids")
            + self.mapped(field + "_ados_ids")
        ).sorted()
        return all_activities[:max_int].mapped("value")

    def details_answer(self, vals):
        """Called when receiving the answer of GetDetails message."""
        self.ensure_one()
        vals["last_update_date"] = fields.Date.today()
        self.write(vals)
        self.env["compassion.project.description"].create({"project_id": self.id})
        return True

    @api.model
    def new_kit(self, commkit_data):
        """New project kit is received."""
        projects = self
        for project_data in commkit_data.get("ICPResponseList", [commkit_data]):
            fcp_id = project_data.get("ICP_ID")
            project = self.search([("fcp_id", "=", fcp_id)])
            vals = self.json_to_data(project_data)
            if project:
                projects += project
                project.write(vals)
            else:
                projects += self.create(vals)
        return projects.ids

    def json_to_data(self, json, mapping_name=None):
        odoo_data = super().json_to_data(json, mapping_name)
        status = odoo_data.get("status")
        if status:
            status_mapping = {
                "Active": "A",
                "Phase Out": "P",
                "Suspended": "S",
                "Transitioned": "T",
            }
            odoo_data["status"] = status_mapping[status]

        for key, val in odoo_data.items():
            if isinstance(val, str) and val.lower() in (
                "null",
                "false",
                "none",
                "other",
                "unknown",
            ):
                odoo_data[key] = False

        monthly_income = odoo_data.get("monthly_income")
        if monthly_income:
            monthly_income = monthly_income.replace(",", "")
            # Replace all but last dot
            monthly_income = re.sub(r"\.(?=[^.]*\.)", "", monthly_income)
            # Replace any alpha character
            monthly_income = re.sub(r"[a-zA-Z$ ]", "", monthly_income)
            try:
                float(monthly_income)
                odoo_data["monthly_income"] = monthly_income
            except ValueError:
                # Weird value received, we prefer to ignore it.
                del odoo_data["monthly_income"]
        return odoo_data

    def fetch_translations(self):
        """
        Contact GMC service in all installed languages in order to fetch all terms
        used in child description.
        """
        self._fetch_translations(self.env.ref("child_compassion.icp_details"))
        return self.edit_translations()

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    def update_informations(self):
        """Get the most recent informations for selected projects and update
        them accordingly."""
        message_obj = self.env["gmc.message"]
        action_id = self.env.ref("child_compassion.icp_details").id
        for project in self:
            message_vals = {
                "action_id": action_id,
                "object_id": project.id,
            }
            message = message_obj.create(message_vals)
            if "failure" in message.state and not self.env.context.get("async_mode"):
                raise UserError(message.failure_reason)

        return True

    def get_all_projects(self):
        message_obj = self.env["gmc.message"]
        action_id = self.env.ref("child_compassion.icp_search_request").id
        message = message_obj.create(
            {
                "action_id": action_id,
            }
        )
        if "failure" in message.state:
            raise UserError(message.failure_reason)

        return True

    def get_lifecycle_event(self):
        onramp = OnrampConnector(self.env)
        endpoint = "churchpartners/{}/kits/icplifecycleeventkit"
        lifecylcle_ids = list()
        for project in self:
            result = onramp.send_message(endpoint.format(project.fcp_id), "GET")
            if "ICPLifecycleEventList" in result.get("content", {}):
                lifecylcle_ids.extend(
                    self.env["compassion.project.ile"].process_commkit(
                        result["content"]
                    )
                )
        return lifecylcle_ids

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def reactivate_project(self):
        """To perform some actions when project is reactivated"""
        for project in self:
            project.message_post(
                body=_("The project is reactivated."),
                subject=_("Project Reactivation"),
                subtype_xmlid="mail.mt_comment",
            )
        return True

    def hold_gifts_action(self):
        pass

    def hold_letters_action(self):
        pass

    def reactivate_gifts(self):
        pass

    def reactivate_letters(self):
        pass
