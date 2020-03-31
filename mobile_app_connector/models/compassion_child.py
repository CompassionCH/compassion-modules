##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import datetime
import logging

from odoo import models, api

logger = logging.getLogger(__name__)


class CompassionChild(models.Model):
    """ A sponsored child """

    _name = "compassion.child"
    _inherit = ["compassion.child", "compassion.mapped.model"]

    def get_app_json_no_wrap(self):
        """
        Called by HUB when data is needed for a tiles letters
        :return: dictionary with JSON data of the child
        """
        if not self:
            return {}
        if len(self) == 1:
            data = self.data_to_json("mobile_app_child")
        else:
            data = []
            for child in self:
                data.append(child.data_to_json("mobile_app_child"))
        return data

    @api.multi
    def get_app_json(self, multi=False, wrapper=False):
        """
        Called by HUB when data is needed for a tile
        :param multi: used to change the wrapper if needed
        :param wrapper: optional custom wrapper key for the dict
        :return: dictionary with JSON data of the children
        """
        children_pictures = self.sudo().mapped("pictures_ids")
        project = self.sudo().mapped("project_id")

        if not wrapper:
            wrapper = "Children" if multi else "Child"
        if not self:
            return {wrapper: []}

        if len(self) == 1 and not multi:
            data = self.data_to_json("mobile_app_child")
        else:
            data = []
            for child in self:
                data.append(child.data_to_json("mobile_app_child"))
        return {
            wrapper: data,
            "Images": children_pictures.filtered("image_url").get_app_json(multi=True),
            "Location": project.get_location_json(multi=False),
            "Time": {
                "ChildTime": project.get_time()[0],
                "ChildTimezone": project[0].timezone,
            },
            "OrderDate": max(self.mapped("sponsorship_ids.create_date")),
            "Weather": project[0].get_weather_json(multi=False),
        }

    @api.model
    def mobile_sponsor_children(self, **other_params):
        """
        Mobile app method:
        Returns the sponsored child list for a given sponsor.
        :param userid: the ref of the sponsor
        :param other_params: all request parameters
        :return: JSON list of sponsor children data
        """
        result = []
        partner_ref = self._get_required_param("userid", other_params)

        sponsor = self.env["res.partner"].search(
            [
                # TODO change filter, we can directly search for connected user
                ("ref", "=", partner_ref),
            ],
            limit=1,
        )
        children = self.search([("partner_id", "=", sponsor.id)])

        for child in children:
            result.append(child.data_to_json("mobile_app_child"))
        return result

    @api.model
    def mobile_get_child_bio(self, **other_params):
        """
        Mobile app method:
        Returns child bio of a given child
        :param other_params: child's global id
        :return: JSON list of child bio information
        """
        child = self.env["compassion.child"].search(
            [("global_id", "=", str(other_params["globalId"]))]
        )

        household = child.household_id

        guardians = household.member_ids.filtered(
            lambda x: x["is_caregiver"]
        ).translate("role")

        hobbies = child.translate("hobby_ids.value")

        family_members = household.member_ids.filtered(
            lambda x: "Beneficiary" not in x.role and (
                not x.child_id or x.child_id.id != child.id)).mapped(
            lambda x: x.name.replace(
                child.lastname, "").strip().split(
                " ")[0] + ", " + x.translate("role"))

        if isinstance(hobbies, str):
            hobbies = [hobbies]

        if isinstance(guardians, str):
            guardians = [guardians]

        at = self.env["ir.advanced.translation"].sudo()
        child_bio = {
            "educationLevel": self._lower(child.translate("education_level")),
            "academicPerformance": self._lower(child.translate("academic_performance")),
            "maleGuardianJob": at.get(household.translate("male_guardian_job")),
            "femaleGuardianJob": at.get(
                household.translate("female_guardian_job"), female=True
            ),
            "maleGuardianJobType": household.translate("male_guardian_job_type"),
            "femaleGuardianJobType": household.translate("female_guardian_job_type"),
            "hobbies": hobbies,
            "guardians": guardians,
            "familyMembers": family_members,
            "notEnrolledReason": self._lower((child.not_enrolled_reason or "")),
        }

        result = {"ChildBioServiceResult": child_bio}
        return result

    def _lower(self, value):
        # Lowercase except for German that has Capital letters for words.
        return value.lower() if self.env.lang != "de_DE" else value

    def _get_required_param(self, key, params):
        if key not in params:
            raise ValueError("Required parameter {}".format(key))
        return params[key]

    @api.multi
    def data_to_json(self, mapping_name=None):
        res = super().data_to_json(mapping_name)
        if not res:
            res = {}
        if "FullBodyImageURL" in res.keys():
            image_url = self.env["child.pictures.download.wizard"].get_picture_url(
                res["FullBodyImageURL"], "headshot", 300, 300
            )
            res["ImageUrl"] = image_url
            res["ImageURL"] = image_url
        for key, value in list(res.copy().items()):
            if key == "BirthDate":
                if value:
                    res[key] = datetime.datetime.strptime(value, "%Y-%m-%d").strftime(
                        "%d/%m/%Y %H:%M:%S"
                    )
            if key == "SupporterGroupId":
                if value:
                    res[key] = int(value)
            if key == "Gender":
                res[key] = "Female" if value == "F" else "Male"
            if not value:
                res[key] = None
        return res
