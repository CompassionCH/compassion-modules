##############################################################################
#
#    Copyright (C) 2014-2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino, Cyril Sester
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging
from datetime import datetime, date

from dateutil.relativedelta import relativedelta

from odoo.addons.message_center_compassion.models.field_to_json import RelationNotFound
from odoo.addons.message_center_compassion.tools.onramp_connector import OnrampConnector
from odoo.addons.queue_job.job import job, related_action

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from .compassion_hold import HoldType

logger = logging.getLogger(__name__)


class CompassionChild(models.Model):
    """ A sponsored child """

    _name = "compassion.child"
    _rec_name = "local_id"
    _inherit = [
        "compassion.generic.child",
        "mail.thread",
        "mail.activity.mixin",
        "translatable.model",
    ]
    _description = "Sponsored Child"
    _order = "local_id asc,date desc"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    # General Information
    #####################
    local_id = fields.Char(track_visibility="onchange")
    code = fields.Char(help="Old child reference")
    compass_id = fields.Char("Compass ID", oldname="unique_id")
    estimated_birthdate = fields.Boolean(readonly=True)
    cognitive_age_group = fields.Char(readonly=True)
    cdsp_type = fields.Selection(
        [("Home Based", "Home based"), ("Center Based", "Center based")],
        track_visibility="onchange",
        readonly=True,
    )
    last_review_date = fields.Date(track_visibility="onchange", readonly=True)
    last_photo_date = fields.Date()
    type = fields.Selection(
        [("CDSP", "CDSP"), ("LDP", "LDP")], required=True, default="CDSP"
    )
    date = fields.Datetime("Allocation date")
    completion_date = fields.Date(readonly=True)
    completion_date_change_reason = fields.Char(readonly=True)
    state = fields.Selection(
        [
            ("W", "Waiting Hold"),
            ("N", "Consigned"),
            ("I", "On Internet"),
            ("P", "Sponsored"),
            ("F", "Departed"),
            ("R", "Released"),
            ("S", "For SMS"),
        ],
        readonly=True,
        required=True,
        track_visibility="onchange",
        default="W",
    )
    is_available = fields.Boolean(compute="_compute_available")
    sponsor_id = fields.Many2one(
        "res.partner", "Sponsor", track_visibility="onchange", readonly=True
    )
    partner_id = fields.Many2one("res.partner", related="sponsor_id", readonly=False)
    sponsor_ref = fields.Char("Sponsor reference", related="sponsor_id.ref")
    has_been_sponsored = fields.Boolean()
    exit_reason = fields.Char(compute="_compute_exit_reason")
    non_latin_name = fields.Char()
    birthday_dm = fields.Char("Birthday", compute="_compute_birthday_month", store=True)
    birthday_month = fields.Selection(
        compute="_compute_birthday_month", selection="_get_months", store=True
    )

    # Hold Information
    ##################
    hold_id = fields.Many2one("compassion.hold", "Hold", readonly=True)
    hold_type = fields.Selection(related="hold_id.type", store=True)
    hold_channel = fields.Selection(related="hold_id.channel", store=True)
    hold_owner = fields.Many2one(
        related="hold_id.primary_owner", store=True, readonly=False
    )
    hold_ambassador = fields.Many2one(
        related="hold_id.ambassador", store=True, readonly=False
    )
    hold_expiration = fields.Datetime(
        related="hold_id.expiration_date", string="Hold expiration", store=True
    )

    # Beneficiary Favorites
    #######################
    hobby_ids = fields.Many2many("child.hobby", string="Hobbies", readonly=True)
    duty_ids = fields.Many2many(
        "child.household.duty", string="Household duties", readonly=True
    )
    project_activity_ids = fields.Many2many(
        "child.project.activity",
        string="Project activities",
        readonly=True,
        oldname="activity_ids",
    )
    subject_ids = fields.Many2many(
        "child.school.subject", string="School subjects", readonly=True
    )

    # Education information
    #######################
    education_level = fields.Selection(
        [
            ("Not Enrolled", "Not Enrolled"),
            ("Preschool", "preschool"),
            ("Primary", "primary school"),
            ("Secondary", "secondary school"),
            ("Highschool", "high school"),
            ("University Graduate", "university"),
        ],
        readonly=True,
    )
    local_grade_level = fields.Char(readonly=True)
    us_grade_level = fields.Char(readonly=True)
    academic_performance = fields.Selection(
        [
            ("Above Average", "Above average"),
            ("Average", "Average"),
            ("Below Average", "Below average"),
            ("Not Available", ""),
        ],
        readonly=True,
    )
    vocational_training_type = fields.Selection(
        [
            ("Agriculture", "Agriculture"),
            ("Architecture / Drafting", "Architecture"),
            ("Art / Design", "Art / Design"),
            ("Automotive", "Automotive"),
            ("Automotive / Mechanics", "Automotive"),
            ("Business/Administrative", "Business administration"),
            ("Business / Administration", "Business administration"),
            ("Clothing Trades", "Clothing trades"),
            ("Computer Technology", "Computer technology"),
            ("Computer / Technology", "Computer technology"),
            ("Communication Studies", "Communication Studies"),
            ("Construction/ Tradesman", "Construction"),
            ("Construction / Tradesman", "Construction"),
            ("Cooking / Food Service", "Cooking and food service"),
            ("Cosmetology", "Cosmetology"),
            ("Electrical/ Electronics", "Electronics"),
            ("Electrical / Electronics", "Electronics"),
            ("Graphic Arts", "Graphic arts"),
            ("Hospitality / Hotel / Tourism", "Hospitality, hotel and tourism"),
            (
                "Income-Generating Program at Project",
                "Income-generating program at project",
            ),
            (
                "Industrial / Manufacturing / Fabrication",
                "Industrial / Manufacturing / Fabrication",
            ),
            ("Manufacturing/ Fabrication", "Manufacturing / Fabrication"),
            ("Manufacturing / Fabrication", "Manufacturing / Fabrication"),
            ("Medical/ Health Services", "Medical / Health services"),
            ("Medical / Health Services", "Medical / Health services"),
            ("Not Enrolled", "Not enrolled"),
            ("Not enrolled", "Not enrolled"),
            ("Other", "Other"),
            ("Para-Medical / Medical / Health Services", "Medical / Health services"),
            ("Telecommunication", "Telecommunication"),
            ("Transportation", "Transportation"),
            ("Transportation/ Driver", "Driver"),
            ("Transportation / Driver", "Driver"),
        ],
        readonly=True,
    )
    university_year = fields.Integer(readonly=True)
    major_course_study = fields.Selection(
        [
            ("Accounting", "Accounting"),
            ("Accounting / Finance", "Accounting"),
            ("Agriculture", "Agriculture"),
            ("Architecture", "Architecture"),
            ("Art / Design", "Art / Design"),
            ("Biology", "Biology"),
            ("Biology / Medicine", "Biology / Medicine"),
            ("Business", "Business"),
            ("Business / Management / Commerce", "Business management"),
            ("Commerce", "Commerce"),
            ("Communication Studies", "Communication Studies"),
            ("Community Development", "Community development"),
            ("Computer Science ", "Computer Science"),
            ("Computer Science / Information Technology", "Computer science"),
            ("Criminology", "Criminology"),
            ("Criminology / Law Enforcement", "Criminology"),
            ("Economics", "Economics"),
            ("Education", "Education"),
            ("Engineering", "Engineering"),
            ("English", "English"),
            ("Fine Arts", "Fine Arts"),
            ("Government / Political Science", "Government / Political Science"),
            ("Graphic Arts", "Graphic Arts"),
            ("Graphic Arts / Fine Arts", "Graphic arts"),
            ("History", "History"),
            ("Hospitality", "Hospitality"),
            ("Hospitality / Hotel Management", "Hotel management"),
            ("Hospitality / Hotel Management / Culinary Arts", "Hotel Management"),
            ("Hotel Management", "Hotel Management"),
            ("Information Technology", "Information Technology"),
            ("Information / Technology", "Information Technology"),
            ("Language", "Language"),
            ("Law", "Law"),
            ("Law Enforcement", "Law Enforcement"),
            ("Management", "Management"),
            ("Mathematics", "Mathematics"),
            ("Medical/ Health Services", "Medical / Health services"),
            ("Medical / Health Services", "Medical / Health services"),
            ("Medicine", "Medicine"),
            ("Nursing", "Nursing"),
            ("Psychology", "Psychology"),
            ("Sales and Marketing", "Sales and marketing"),
            ("Science", "Science"),
            ("Social Science", "Social Science"),
            ("Sociology", "Sociology"),
            ("Sociology / Social Science", "Sociology"),
            ("Theology", "Theology"),
            ("Theology / Christian Studies", "Theology"),
            ("Tourism", "Tourism"),
            ("Transportation", "Transportation"),
            ("Other", "Other"),
            ("Undecided", "Undecided"),
        ],
        readonly=True,
    )
    not_enrolled_reason = fields.Char(readonly=True)

    # Spiritual information
    #######################
    christian_activity_ids = fields.Many2many(
        "child.christian.activity", string="Christian activities", readonly=True
    )

    # Medical information
    #####################
    weight = fields.Char(readonly=True)
    height = fields.Char(readonly=True)
    physical_disability_ids = fields.Many2many(
        "child.physical.disability", string="Physical disabilities", readonly=True
    )
    chronic_illness_ids = fields.Many2many(
        "child.chronic.illness", string="Chronic illnesses", readonly=True
    )

    # Case Studies
    ##############
    lifecycle_ids = fields.One2many(
        "compassion.child.ble", "child_id", "Lifecycle events", readonly=True
    )
    assessment_ids = fields.One2many(
        "compassion.child.cdpr", "child_id", "Assessments", readonly=True
    )
    note_ids = fields.One2many(
        "compassion.child.note", "child_id", "Notes", readonly=True
    )
    revised_value_ids = fields.One2many(
        "compassion.major.revision", "child_id", "Major revisions", readonly=True
    )
    pictures_ids = fields.One2many(
        "compassion.child.pictures",
        "child_id",
        "Child pictures",
        track_visibility="onchange",
        readonly=False,
    )
    household_id = fields.Many2one("compassion.household", "Household", readonly=True)
    portrait = fields.Binary(related="pictures_ids.headshot")
    fullshot = fields.Binary(related="pictures_ids.fullshot")
    child_disaster_impact_ids = fields.One2many(
        "child.disaster.impact", "child_id", "Child Disaster Impact", readonly=True
    )
    is_special_needs = fields.Boolean()

    # Descriptions
    ##############
    desc_en = fields.Text("English description", readonly=True)

    # Just for migration
    delegated_comment = fields.Text()

    _sql_constraints = [
        ("compass_id", "unique(compass_id)", "The child already exists in database."),
        ("global_id", "unique(global_id)", "The child already exists in database."),
    ]

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################

    def _compute_available(self):
        for child in self:
            child.is_available = child.state in self._available_states()

    @api.model
    def _available_states(self):
        return ["N", "I"]

    def _compute_exit_reason(self):
        for child in self:
            exit_details = child.lifecycle_ids.with_context(lang="en_US").filtered(
                lambda l: l.type in ("Planned Exit", "Unplanned Exit")
            )
            if exit_details:
                child.exit_reason = exit_details[0].request_reason

    @api.model
    def _get_months(self):
        return self.env["connect.month"].get_months_selection()[12:]

    @api.depends("birthdate")
    def _compute_birthday_month(self):
        for child in self.filtered("birthdate"):
            child.birthday_month = child.with_context(lang="en_US").get_date(
                "birthdate", "MMMM"
            )
            child.birthday_dm = child.get_date("birthdate", "MM-dd")

    @api.constrains("state", "hold_type")
    def check_state(self):
        # child state vs hold type validity mapping
        consignment_holds = [
            HoldType.CONSIGNMENT_HOLD.value,
            HoldType.E_COMMERCE_HOLD.value,
        ]
        no_hold = [False]
        valid_states = {
            "W": no_hold,
            "N": consignment_holds
            + [
                HoldType.CHANGE_COMMITMENT_HOLD.value,
                HoldType.DELINQUENT_HOLD.value,
                HoldType.REINSTATEMENT_HOLD.value,
                HoldType.RESERVATION_HOLD.value,
                HoldType.SPONSOR_CANCEL_HOLD.value,
                HoldType.SUB_CHILD_HOLD.value,
                HoldType.NO_MONEY_HOLD.value,
            ],
            "I": consignment_holds,
            "P": no_hold
            + [HoldType.NO_MONEY_HOLD.value, HoldType.SUB_CHILD_HOLD.value],
            "F": no_hold,
            "R": no_hold,
            "S": consignment_holds,
        }
        for child in self:
            if child.hold_type not in valid_states[child.state]:
                raise ValidationError(
                    _("Child %s has invalid state %s for hold type %s")
                    % (child.local_id, child.state, child.hold_type)
                )

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """
        If child with global_id already exists, update it instead of creating
        a new one.
        """
        global_id = vals.get("global_id")
        child = self.search([("global_id", "=", global_id)])
        if child:
            child.write(vals)
        else:
            child = super().create(vals)
            # directly fetch picture to have it before get_infos
            child.with_delay().update_child_pictures()
        return child

    @api.multi
    def unlink(self):
        holds = self.mapped("hold_id").filtered(
            lambda h: h.state == "active" and h.type != HoldType.NO_MONEY_HOLD.value
        )
        res = super().unlink()
        holds.release_hold()
        return res

    @api.multi
    @job(default_channel="root.child_compassion")
    @related_action("related_action_child_compassion")
    def unlink_job(self):
        """ Small wrapper to unlink only released children. """
        return self.filtered(lambda c: c.state == "R").unlink()

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def details_answer(self, vals):
        """ Called when receiving the answer of GetDetails message. """
        self.ensure_one()
        self.write(vals)
        self.env["compassion.child.description"].create({"child_id": self.id})
        self.update_child_pictures()
        return True

    @api.model
    def major_revision(self, commkit_data):
        """ Called when a MajorRevision Kit is received. """
        child_ids = list()
        for child_data in commkit_data.get(
            "BeneficiaryMajorRevisionList", [commkit_data]
        ):
            global_id = child_data.get("Beneficiary_GlobalID")
            child = self.search([("global_id", "=", global_id)])
            if child:
                child_ids.append(child.id)
                child._major_revision(self.json_to_data(child_data))
        return child_ids

    @api.model
    def new_kit(self, commkit_data):
        """ New child kit is received. """
        children = self
        for child_data in commkit_data.get("BeneficiaryResponseList", [commkit_data]):
            global_id = child_data.get("Beneficiary_GlobalID")
            child = self.search([("global_id", "=", global_id)])
            if child:
                children += child
                child.write(self.json_to_data(child_data))
        children.update_child_pictures()
        return children.ids

    def convert_us_grade_to_education_level(self):
        """
        Takes the US Grade level field and converts to the education level
        which is used in child descriptions.
        :return: True
        """
        self.ensure_one()
        if self.us_grade_level and (
            not self.education_level or self.education_level == "Not Enrolled"
        ):
            grade_mapping = {
                "P": "Preschool",
                "K": "Preschool",
                "1": "Primary",
                "2": "Primary",
                "3": "Primary",
                "4": "Primary",
                "5": "Primary",
                "6": "Primary",
                "7": "Secondary",
                "8": "Secondary",
                "9": "Secondary",
                "10": "Highschool",
                "11": "Highschool",
                "12": "Highschool",
            }
            self.education_level = grade_mapping.get(self.us_grade_level)

    def get_number(self):
        """ Returns a string telling how many children are in the recordset.
        """
        number_dict = {
            1: _("one"),
            2: _("two"),
            3: _("three"),
            4: _("four"),
            5: _("five"),
            6: _("six"),
            7: _("seven"),
            8: _("eight"),
            9: _("nine"),
            10: _("ten"),
        }
        return number_dict.get(len(self), str(len(self))) + " " + self.get("child")

    @api.multi
    def json_to_data(self, json, mapping_name=None):
        while True:  # catch more than one relation not found
            try:
                data = super().json_to_data(json, mapping_name)
                break
            except RelationNotFound as e:
                self.fetch_missing_relational_records(
                    e.field_relation, e.value, e.json_name
                )

        # Update household
        household_data = data.pop("household_id", {})
        household_id = household_data.get("household_id")
        household = self.env["compassion.household"].search(
            [("household_id", "=", household_id)]
        )
        if household:
            household.write(household_data)
        elif household_data:
            data["household_id"] = household.create(household_data).id
        return data

    def fetch_missing_relational_records(self, field_relation, values, json_name):
        """ Fetch missing relational records in various languages.

        Method used to catch missing values for household duties, hobbies,
        and Christian activities of compassion.child and write them onto
        the database.

        :param field_relation: relation
        :param values: missing relational values
        :param json_name: key name in content
        :type field_relation: str
        :type values: str or list of str
        :type json_name: str

        TODO: check if value already exists in another form (spaces, with regex...)

        """
        onramp = OnrampConnector()
        endpoint = "beneficiaries/{0}/details?FinalLanguage={1}"
        languages_map = {
            "English": "en_US",
            "French": "fr_CH",
            "German": "de_DE",
            "Italian": "it_IT",
        }
        # transform values to list first
        if not isinstance(values, list):
            values = [values]
        # go over all missing values, keep count of index to know which translation
        # to take from onramp result
        for i, value in enumerate(values):
            # check if hobby/household duty, etc... exists in our database
            search_vals = [("name", "=", value)]
            relation_obj = self.env[field_relation]
            if hasattr(relation_obj, "value"):
                search_vals.insert(0, "|")
                search_vals.append(("value", "=", value))
            search_count = relation_obj.search_count(search_vals)
            # if not exist, then create it
            if not search_count:
                value_record = (
                    self.env[field_relation]
                    .sudo()
                    .create({"name": value, "value": value})
                )
                # fetch translation
                for lang_literal, lang_context in languages_map.items():
                    result = onramp.send_message(
                        endpoint.format(self[0].global_id, lang_literal), "GET"
                    )
                    if "BeneficiaryResponseList" in result.get("content", {}):
                        content = result["content"]["BeneficiaryResponseList"][0]
                        if json_name in content:
                            content_values = content[json_name]
                            if not isinstance(content_values, list):
                                content_values = [content_values]
                            translation = content_values[i]
                            value_record.with_context(
                                lang=lang_context
                            ).value = translation

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def get_infos(self):
        """Get the most recent case study, basic informations, updates
           portrait picture and creates the project if it doesn't exist.
        """
        message_obj = self.env["gmc.message"]
        action_id = self.env.ref("child_compassion.beneficiaries_details").id
        for child in self:
            message_vals = {
                "action_id": action_id,
                "object_id": child.id,
                "child_id": child.id,
            }
            message = message_obj.create(message_vals)
            if message.state == "failure" and not self.env.context.get("async_mode"):
                raise UserError(message.failure_reason)
        return True

    @api.multi
    @job
    @related_action("related_action_child_compassion")
    def update_child_pictures(self):
        """
        Check if there is a new picture if all conditions are satisfied:
        - At least two pictures
        - Difference between two last pictures is at least 6 months
        - Last picture is no older than 6 months
        :return: True
        """
        res = True
        # Update child's pictures
        for child in self:
            res = child._get_last_pictures() and res
            pictures = child.pictures_ids
            if res and len(pictures) > 1:
                today = date.today()
                last_photo = pictures[1].date
                new_photo = pictures[0].date
                diff_pic = relativedelta(new_photo, last_photo)
                diff_today = relativedelta(today, new_photo)
                if (diff_pic.months > 6 or diff_pic.years > 0) and (
                    diff_today.months <= 6 and diff_today.years == 0
                ):
                    child.new_photo()
        return res

    # Lifecycle methods
    ###################
    @api.multi
    def new_photo(self):
        """
        Hook for doing something when a new photo is attached to the child.
        """
        pass

    @api.multi
    def get_lifecycle_event(self):
        onramp = OnrampConnector()
        endpoint = "beneficiaries/{}/kits/beneficiarylifecycleeventkit"
        lifecylcle_ids = list()
        for child in self:
            result = onramp.send_message(endpoint.format(child.global_id), "GET")
            if "BeneficiaryLifecycleEventList" in result.get("content", {}):
                lifecylcle_ids.extend(
                    self.env["compassion.child.ble"].process_commkit(result["content"])
                )
        return lifecylcle_ids

    ##########################################################################
    #                            WORKFLOW METHODS                            #
    ##########################################################################
    @api.multi
    def child_waiting_hold(self):
        """ Called on child creation. """
        if self.mapped("hold_id"):
            local_ids = self.filtered("hold_id").mapped("local_id")
            raise UserError(
                _("Children %s have a hold that should not be removed.")
                % ",".join(local_ids)
            )
        self.write({"state": "W", "sponsor_id": False})
        return True

    @api.multi
    def child_consigned(self, hold_id):
        """Called on child allocation."""
        self.write({"state": "N", "hold_id": hold_id, "date": fields.Datetime.now()})
        # Cancel planned deletion
        jobs = (
            self.env["queue.job"]
            .sudo()
            .search(
                [
                    ("name", "=", "Job for deleting released children."),
                    ("func_string", "like", self.ids),
                    ("state", "=", "enqueued"),
                ]
            )
        )
        jobs.button_done()
        jobs.unlink()
        self.get_infos()
        return True

    @api.multi
    def child_sponsored(self, sponsor_id):
        self.ensure_one()
        if self.state in ("W", "F", "R"):
            raise UserError(
                _(
                    "[%s] This child has not a valid hold and cannot be sponsored."
                ) % self.local_id
            )
        hold = self.hold_id
        if hold.type != HoldType.SUB_CHILD_HOLD.value:
            hold.write(
                {
                    "type": HoldType.NO_MONEY_HOLD.value,
                    "expiration_date": hold.get_default_hold_expiration(
                        HoldType.NO_MONEY_HOLD
                    ),
                }
            )
        return self.write(
            {"state": "P", "has_been_sponsored": True, "sponsor_id": sponsor_id}
        )

    @api.multi
    def child_unsponsored(self):
        for child in self:
            values = {"sponsor_id": False}
            update_hold = False
            if child.sponsor_id:
                if child.hold_id.type == HoldType.NO_MONEY_HOLD.value:
                    update_hold = True
                    values["state"] = "N"
                else:
                    values["state"] = "N" if child.hold_id else "R"
            child.write(values)
            if update_hold:
                child.hold_id.write(
                    {
                        "type": HoldType.CONSIGNMENT_HOLD.value,
                        "expiration_date": child.hold_id.get_default_hold_expiration(
                            HoldType.CONSIGNMENT_HOLD
                        ),
                    }
                )

        # Retrieve livecycle events to have the info when setting up a new sponsorship
        self.get_lifecycle_event()

        return True

    @api.multi
    def child_released(self, state="R"):
        """ Is called when a child is released to the global childpool. """
        self.write({"sponsor_id": False, "state": state, "hold_id": False})
        # Check if it was a depart and retrieve lifecycle event
        self.get_lifecycle_event()

        # the children will be deleted when we reach their expiration date
        postpone = 60 * 60 * 24 * 7  # One week by default
        today = datetime.today()
        for child in self.filtered(lambda c: not c.has_been_sponsored):
            if child.hold_expiration:
                expire = child.hold_expiration
                postpone = (expire - today).total_seconds() + 60

            child.with_delay(eta=postpone).unlink_job()

        return True

    @api.multi
    def child_departed(self):
        """ Is called when a child is departed. """
        return self.child_released(state="F")

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################

    @api.multi
    def _get_last_pictures(self):
        self.ensure_one()

        pictures_obj = self.env["compassion.child.pictures"]
        pictures = pictures_obj.create(
            {"child_id": self.id, "image_url": self.image_url}
        )
        if pictures:
            # Add a note in child
            self.message_post(
                body=_("The picture has been updated."),
                subject=_("Picture update"),
                message_type="comment",
            )

        return pictures

    def _major_revision(self, vals):
        """ Private method when a major revision is received for a child.
            :param vals: Record values received from connect
        """
        self.ensure_one()
        # First write revised values, then everything else
        self.write({"revised_value_ids": vals.pop("revised_value_ids")})
        self.write(vals)
        self.get_infos()
