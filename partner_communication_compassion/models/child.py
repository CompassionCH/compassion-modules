##############################################################################
#
#    Copyright (C) 2016-2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from odoo import api, models, fields, _

from functools import reduce
from babel.dates import format_date

_logger = logging.getLogger(__name__)

# Ratio of white frame around the child picture
FRAME_RATIO = 0.08


def major_revision(child, revised_values):
    """Finds the correct communication to send."""
    if len(revised_values) == 1:
        communication_type = child.env["partner.communication.config"].search(
            [
                ("name", "ilike", revised_values.name),
                ("name", "like", "Major Revision"),
            ]
        )
    else:
        communication_type = child.env.ref(
            "partner_communication_compassion.major_revision_multiple"
        )
    if communication_type.active:
        child.env["partner.communication.job"].create(
            {
                "config_id": communication_type.id,
                "partner_id": child.sponsor_id.id,
                "object_ids": child.id,
                "user_id": communication_type.user_id.id,
            }
        )


class CompassionChild(models.Model):
    """Add fields for retrieving values for communications.
    Send a communication when a major revision is received.
    """

    _inherit = "compassion.child"

    old_values = fields.Char(compute="_compute_revised_values")
    old_firstname = fields.Char(compute="_compute_revised_values")
    current_values = fields.Char(compute="_compute_revised_values")
    completion_month = fields.Char(compute="_compute_completion_month")

    def _compute_revised_values(self):
        for child in self:
            child.old_values = child.revised_value_ids.get_list("old_value")
            child.current_values = child.revised_value_ids.get_field_value()
            child.old_firstname = (
                child.revised_value_ids.filtered(
                    lambda c: c.name == "First Name"
                ).old_value
                or child.firstname
            )

    def _major_revision(self, vals):
        """Private method when a major revision is received for a child.
        Send a communication to the sponsor.
        """
        super()._major_revision(vals)
        if self.revised_value_ids and self.sponsor_id:
            major_revision(self, self.revised_value_ids)

    def _compute_completion_month(self):
        """Completion month in full text."""
        for child in self:
            lang = child.sponsor_id.lang or self.env.lang or "en_US"
            completion = child.completion_date
            if completion:
                child.completion_month = format_date(completion, "MMMM", locale=lang)
            else:
                child.completion_month = False

    def new_photo(self):
        """
        Upon reception of a new child picture :
        - Mark sponsorships for pictures order if delivery is physical
        - Prepare communication for sponsor
        """
        super().new_photo()
        communication_config = self.env.ref("partner_communication_compassion.biennial")
        if not communication_config.active:
            return True
        job_obj = self.env["partner.communication.job"]
        for child in self.filtered(
            lambda r: r.sponsor_id
            and r.pictures_ids
            and r.sponsorship_ids[0].state == "active"
        ):
            sponsor = child.sponsor_id
            delivery = sponsor.photo_delivery_preference
            if "physical" in delivery or delivery == "both":
                # Mark sponsorship for order the picture
                child.sponsorship_ids[0].order_photo = True

            job_obj.create(
                {
                    "config_id": communication_config.id,
                    "partner_id": child.sponsor_id.id,
                    "object_ids": child.id,
                    "user_id": communication_config.user_id.id,
                }
            )
        return True

    def get_child_preposition_country(
        self,
        preposition_field="in_preposition",
        with_child_name=True,
        child_limit=float("inf"),
        country_limit=float("inf"),
        child_substitution="",
        country_substitution="",
        repeat_preposition=False,
    ):
        """
        Returns a string with children names and associated countries with the correct preposition
        :param preposition_field: name of the preposition field to use ('in_preposition', 'from_preposition')
        :param with_child_name: include or not the name of the children in the string
        :param child_limit: max number of children names to display in string
        :param country_limit: max number of country names to display in string
        :param child_substitution: alternative string to display if there are more than child_limit children
        :param country_substitution: alternative string to display if there are more than country_limit countries
        :param repeat_preposition: set to true if you want to repeat each time the country preposition
        :return: a nice string to use in communications (ex: "John and Jack in Ghana and July in Ecuador")
        """
        res_list = []
        if len(self.mapped("field_office_id")) > country_limit:
            return country_substitution
        res = ""
        if len(self) > child_limit:
            res = child_substitution + " "
        if (with_child_name and not res) or repeat_preposition:
            for country in self.mapped("field_office_id.country_id"):
                children = self.filtered(
                    lambda c: c.field_office_id.country_id == country
                )
                res_list.append(
                    (
                        children.get_list("preferred_name", translate=False) + " "
                        if not res
                        else ""
                    )
                    + getattr(country, preposition_field)
                    + country.name
                )
        else:
            for prep in list(
                set(self.mapped("field_office_id.country_id." + preposition_field))
            ):
                children = self.filtered(
                    lambda c: getattr(c.field_office_id.country_id, preposition_field)
                    == prep
                )
                countries = list(
                    set(children.mapped("field_office_id.country_id.name"))
                )
                if len(countries) > 1:
                    res_list.append(
                        prep
                        + ", ".join(countries[:-1])
                        + " "
                        + _("and")
                        + " "
                        + countries[-1]
                    )
                else:
                    res_list.append(prep + " " + countries[0])

        if len(res_list) > 1:
            res += ", ".join(res_list[:-1]) + " " + _("and") + " " + res_list[-1]
        else:
            res += res_list[0]
        return res


class Household(models.Model):
    """Send Communication when Household Major Revision is received."""

    _inherit = "compassion.household"

    def process_commkit(self, commkit_data):
        ids = super().process_commkit(commkit_data)
        households = self.browse(ids)
        for household in households:
            if household.revised_value_ids:
                for child in household.child_ids.filtered("sponsor_id"):
                    major_revision(child, self.revised_value_ids)
        return ids


class ChildNotes(models.Model):
    _inherit = "compassion.child.note"

    @api.model
    def create(self, vals):
        """Inform sponsor when receiving new Notes."""
        note = super().create(vals)
        child = note.child_id
        if child.sponsor_id:
            communication_config = self.env.ref(
                "partner_communication_compassion.child_notes"
            )
            if communication_config.active:
                self.env["partner.communication.job"].create(
                    {
                        "config_id": communication_config.id,
                        "partner_id": child.sponsor_id.id,
                        "object_ids": child.id,
                        "user_id": communication_config.user_id.id,
                    }
                )
        return note
