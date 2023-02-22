##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Coninckx <david@coninckx.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import sys
from datetime import datetime, timedelta, date
from math import ceil

from dateutil.relativedelta import relativedelta
from odoo.addons.message_center_compassion.tools.onramp_connector import OnrampConnector

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class GlobalChildSearch(models.TransientModel):
    """
    Class used for searching children in the global childpool.
    """

    _name = "compassion.childpool.search"
    _inherit = ["compassion.mapped.model"]

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    # Quick Search parameters
    gender = fields.Selection([("Male", "Male"), ("Female", "Female")])
    field_office_ids = fields.Many2many(
        "compassion.field.office",
        "childpool_field_office_search_rel",
        string="Field Offices",
        readonly=False,
    )
    min_age = fields.Integer(size=2)
    max_age = fields.Integer(size=2)
    birthday_month = fields.Integer(size=2)
    birthday_day = fields.Integer(size=2)
    birthday_year = fields.Integer(size=4)
    child_name = fields.Char()
    fcp_ids = fields.Many2many(
        "compassion.project",
        "childpool_project_search_rel",
        string="Projects",
        oldname="icp_ids",
        readonly=False,
    )
    fcp_name = fields.Char()
    hiv_affected_area = fields.Boolean()
    is_orphan = fields.Boolean()
    has_special_needs = fields.Boolean()
    min_days_waiting = fields.Integer(size=4)
    source_code = fields.Char()

    # Advanced Search parameters
    # List of available search parameters :
    # https://github.com/compassion-intl/R4-JSON/blob/master/EIM_Reviewed/
    # CI_NS_BeneficiarySearchRequestList_schema.json#L24
    advanced_criteria_used = fields.Boolean(compute="_compute_advanced_critieria_used")
    search_filter_ids = fields.Many2many(
        "compassion.query.filter",
        "compassion_child_search_filters",
        "search_id",
        "query_id",
        "Filters",
        readonly=False,
    )
    local_id = fields.Char("Child code")
    state_chooser = fields.Selection(
        lambda s: s.env["compassion.generic.child"]._get_availability_state()
    )
    state_selected = fields.Char(default="Available", readonly=True)
    chronic_illness = fields.Selection(
        lambda s: s.env["compassion.household"]._get_yes_no(), "Has chronic illnesses"
    )
    holding_gp_ids = fields.Many2many(
        "compassion.global.partner",
        "child_search_holding_gp",
        "search_id",
        "global_partner_id",
        "Holding Global Partner",
        readonly=False,
    )
    father_alive = fields.Selection(
        lambda s: s.env["compassion.household"]._get_yes_no()
    )
    mother_alive = fields.Selection(
        lambda s: s.env["compassion.household"]._get_yes_no()
    )
    physical_disability = fields.Selection(
        lambda s: s.env["compassion.household"]._get_yes_no(),
        "Has physical disabilities",
    )
    completion_date_after = fields.Date()
    completion_date_before = fields.Date()

    # Pagination
    # By default : skip 50000 children to take less priority
    # Leave high priority children for bigger countries
    skip = fields.Integer(size=4, default=50000)
    take = fields.Integer(default=80, size=4)

    # Returned children
    nb_found = fields.Integer("Number of matching children", readonly=True)
    nb_selected = fields.Integer("Selected children", compute="_compute_nb_children")
    all_children_available = fields.Boolean(compute="_compute_available")
    global_child_ids = fields.Many2many(
        "compassion.global.child",
        "childpool_children_rel",
        string="Available Children",
        readonly=True,
    )
    nb_restricted_children = fields.Integer(
        "Number of restricted children",
        readonly=True,
        help="These children were removed from the search results because "
             "of a Field Office restriction configuration.",
    )
    missing_dates = fields.Text(help="All birthdates not found when using 365 search")

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.depends(
        "state_selected",
        "chronic_illness",
        "holding_gp_ids",
        "father_alive",
        "mother_alive",
        "physical_disability",
        "completion_date_after",
        "completion_date_before",
        "local_id",
    )
    def _compute_advanced_critieria_used(self):
        self.advanced_criteria_used = (
            self.chronic_illness
            or self.holding_gp_ids
            or self.father_alive
            or self.mother_alive
            or self.physical_disability
            or self.completion_date_after
            or self.completion_date_before
            or self.local_id
            or (self.state_selected and self.state_selected != "Available")
        )

    def _compute_nb_children(self):
        for search in self:
            search.nb_selected = len(search.global_child_ids)

    def _compute_available(self):
        for search in self:
            search.all_children_available = len(
                search.global_child_ids.filtered(
                    lambda c: c.beneficiary_state == "Available"
                )
            ) == len(search.global_child_ids)

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def add_status(self):
        self.ensure_one()
        if self.state_selected:
            self.state_selected += ";" + self.state_chooser
        else:
            self.state_selected = self.state_chooser
        self.state_chooser = False
        return True

    @api.multi
    def reset_status(self):
        self.ensure_one()
        self.state_selected = False
        return True

    @api.multi
    def do_search(self):
        self.ensure_one()
        # Remove previous search results
        self.global_child_ids.unlink()
        # Skip value must be set before the search (with_context)
        self.skip = self.env.context.get("skip_value", 0)
        if not self.advanced_criteria_used:
            self._call_search_service(
                "profile_search",
                "beneficiaries/availabilitysearch",
                "BeneficiarySearchResponseList",
            )
        else:
            self.compute_advanced_search()
            self._call_search_service(
                "advanced_search",
                "beneficiaries/availabilityquery",
                "BeneficiarySearchResponseList",
                "POST",
            )

        return True

    @api.multi
    def add_search(self):
        self.ensure_one()
        self.skip += self.nb_selected
        if not self.advanced_criteria_used:
            self._call_search_service(
                "profile_search",
                "beneficiaries/availabilitysearch",
                "BeneficiarySearchResponseList",
            )
        else:
            self.compute_advanced_search()
            self._call_search_service(
                "advanced_search",
                "beneficiaries/availabilityquery",
                "BeneficiarySearchResponseList",
                "POST",
            )
        if self.nb_found == 0:
            raise UserError(_("No children found."))
        return True

    @api.multi
    def rich_mix(self):
        self.ensure_one()
        # Remove previous search results
        self.global_child_ids.unlink()
        # Skip 50000 children by default (for leaving high priority to big
        # countries)
        if self.skip == 0:
            self.skip = 50000
        self._call_search_service(
            "rich_mix", "beneficiaries/richmix", "BeneficiaryRichMixResponseList"
        )
        return True

    @api.multi
    def make_a_hold(self):
        """ Create hold and send to Connect """
        self.ensure_one()
        return {
            "name": _("Specify Attributes"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "child.hold.wizard",
            "context": self.with_context(
                active_id=self.id,
                active_model=self._name,
                default_yield_rate=80,
                default_no_money_yield_rate=20,
            ).env.context,
            "target": "new",
        }

    @api.multi
    def create_reservation(self):
        self.ensure_one()
        return {
            "name": _("Specify Attributes"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "child.reservation.wizard",
            "context": self.env.context,
            "target": "new",
        }

    @api.multi
    def country_mix(self):
        """
        Tries to find an even number of children for each country.
        :return:
        """
        country_codes = (
            self.env["compassion.field.office"].search([]).mapped("field_office_id")
        )
        children_by_country = {
            code: self.env["compassion.global.child"] for code in country_codes
        }
        max_per_country = ceil(float(self.take) / len(country_codes))
        found_children = self.env["compassion.global.child"]
        children_already_seen = self.env["compassion.global.child"]
        nb_found = 0
        tries = 0
        while nb_found < self.take:
            children_already_seen += self.global_child_ids
            self.take_more()
            for child in self.global_child_ids - children_already_seen:
                child_country = child.local_id[0:2]
                country_pool = children_by_country.get(child_country)
                if country_pool is not None and len(country_pool) < max_per_country:
                    children_by_country[child_country] = country_pool + child
                    found_children += child
                    nb_found += 1
                if nb_found == self.take:
                    break
            self.skip += self.take
            tries += 1
            if tries > 5:
                raise UserError(
                    _(
                        "Cannot find enough available children in all "
                        "countries. Try with less"
                    )
                )

        # Delete leftover children
        (self.global_child_ids - found_children).unlink()
        return True

    @api.multi
    def do_365_mix(self):
        """ Try to find one child per day of the year having his birthdate
        on that date."""
        today = date.today()
        first_day = today.replace(day=1, month=1)
        last_day = today.replace(day=31, month=12)
        current_date = first_day
        # First step as regular search
        self.write(
            {
                "birthday_day": 1,
                "birthday_month": 1,
                "take": 1,
                "missing_dates": "",
                "skip": 0,
            }
        )
        self.do_search()
        while current_date < last_day:
            # Next steps: add child to the search result
            current_date += relativedelta(days=1)
            self.write(
                {
                    "birthday_day": current_date.day,
                    "birthday_month": current_date.month,
                    "skip": 0,
                }
            )
            try:
                self.add_search()
            except UserError:
                # No children found on that date: displays it.
                self.missing_dates += current_date.strftime("%d.%m\n")

    @api.multi
    def filter(self):
        self.ensure_one()
        matching = self.global_child_ids.filtered(lambda child: self._does_match(child))
        (self.global_child_ids - matching).unlink()
        # Specify filter is applied
        self.nb_found = len(self.global_child_ids)
        return True

    @api.multi
    def take_more(self):
        self.ensure_one()
        # Use rich mix
        self._call_search_service(
            "rich_mix", "beneficiaries/richmix", "BeneficiaryRichMixResponseList"
        )
        return True

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def hold_children_job(self):
        """Job for holding requested children on the web."""
        self.ensure_one()
        child_hold = (
            self.env["child.hold.wizard"].with_context(active_id=self.id).sudo()
        )
        expiration_date = datetime.now() + timedelta(minutes=15)

        user_id = (
            self.env["res.users"].search([("name", "=", "Reber Rose-Marie")]).id
            or self.env.uid
        )

        holds = child_hold.create(
            {
                "type": "E-Commerce Hold",
                "hold_expiration_date": expiration_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "primary_owner": user_id,
                "secondary_owner": "Carole Rochat",
                "no_money_yield_rate": "20",
                "yield_rate": "80",
                "channel": "Website",
            }
        )
        holds.send()

    def compute_advanced_search(self):
        self.ensure_one()
        # Remove all search filters
        self.write({"search_filter_ids": [(5, False, False)]})

        # Utility to get write values for a selected filter
        def _get_filter(field_name, operator_id, value):
            field_id = (
                self.env["ir.model.fields"]
                    .search([("model", "=", self._name), ("name", "=", field_name)])
                    .id
            )
            return (
                0,
                0,
                {"field_id": field_id, "operator_id": operator_id, "value": value},
            )

        # Construct filter values
        anyof_id = self.env.ref("message_center_compassion.anyof").id
        is_id = self.env.ref("message_center_compassion.is").id
        between_id = self.env.ref("message_center_compassion.between").id
        equalto_id = self.env.ref("message_center_compassion.equalto").id
        within_id = self.env.ref("message_center_compassion.within").id
        new_filters = list()
        if self.min_age or self.max_age:
            min_age = self.min_age or 0
            max_age = self.max_age or 120
            age_range = str(min_age) + ";" + str(max_age)
            new_filters.append(_get_filter("min_age", between_id, age_range))
        if self.local_id:
            new_filters.append(_get_filter("local_id", is_id, self.local_id))
        if self.child_name:
            new_filters.append(_get_filter("child_name", is_id, self.child_name))
        if self.state_selected:
            new_filters.append(
                _get_filter("state_selected", anyof_id, self.state_selected)
            )
        if self.birthday_day:
            new_filters.append(
                _get_filter("birthday_day", equalto_id, self.birthday_day)
            )
        if self.birthday_month:
            new_filters.append(
                _get_filter("birthday_month", equalto_id, self.birthday_month)
            )
        if self.birthday_year:
            new_filters.append(
                _get_filter("birthday_year", equalto_id, self.birthday_year)
            )
        if self.chronic_illness and self.chronic_illness != "Unknown":
            new_filters.append(
                _get_filter(
                    "chronic_illness",
                    is_id,
                    "T" if self.chronic_illness == "Yes" else "F",
                )
            )
        if self.field_office_ids:
            values = ";".join(self.field_office_ids.mapped("country_code"))
            new_filters.append(_get_filter("field_office_ids", anyof_id, values))
        if self.gender:
            new_filters.append(_get_filter("gender", anyof_id, self.gender[0]))
        if self.holding_gp_ids:
            values = ";".join(self.holding_gp_ids.mapped("country_id.code"))
            new_filters.append(_get_filter("holding_gp_ids", anyof_id, values))
        if self.fcp_ids:
            values = ";".join(self.fcp_ids.mapped("fcp_id"))
            new_filters.append(_get_filter("fcp_ids", anyof_id, values))
        if self.fcp_name:
            new_filters.append(_get_filter("fcp_name", is_id, self.fcp_name))
        if self.hiv_affected_area:
            new_filters.append(_get_filter("hiv_affected_area", is_id, "T"))
        if self.is_orphan:
            new_filters.append(_get_filter("is_orphan", is_id, "T"))
        if self.has_special_needs:
            new_filters.append(_get_filter("has_special_needs", is_id, "T"))
        if self.father_alive:
            new_filters.append(_get_filter("father_alive", anyof_id, self.father_alive))
        if self.mother_alive:
            new_filters.append(_get_filter("mother_alive", anyof_id, self.mother_alive))
        if self.physical_disability and self.physical_disability != "Unknown":
            new_filters.append(
                _get_filter(
                    "physical_disability",
                    is_id,
                    "T" if self.physical_disability == "Yes" else "F",
                )
            )
        if self.completion_date_after or self.completion_date_before:
            start_date = self.completion_date_after or "1970-01-01"
            stop_date = self.completion_date_before or date.max
            date_range = start_date + ";" + stop_date
            new_filters.append(
                _get_filter("completion_date_after", within_id, date_range)
            )
        if self.min_days_waiting:
            days_range = str(self.min_days_waiting) + ";" + str(sys.maxint)
            new_filters.append(_get_filter("min_days_waiting", between_id, days_range))

        return self.write({"search_filter_ids": new_filters})

    @api.multi
    def data_to_json(self, mapping_name=None):
        json_result = super().data_to_json(mapping_name)
        if mapping_name == "profile_search":
            # Remove 0 values
            for key, val in json_result.copy().items():
                if not val:
                    del json_result[key]
        # We need to do this "workaround" because there are multiple JSON values
        # for the same odoo_field in the communications with GMC.
        # (one for the advanced_search and one for the profile_search)
        if mapping_name == "advanced_search":
            for _dict in json_result["BeneficiarySearchRequestList"]["Filter"]:
                if _dict["Field"] == "hasSpecialNeeds":
                    _dict["Field"] = "IsSpecialNeeds"

                if _dict["Field"] == "hivAffectedArea":
                    _dict["Field"] = "IsHIVAffectedArea"

                if _dict["Field"] == "isOrphan":
                    _dict["Field"] = "IsOrphan"

                if _dict["Field"] == "minDaysWaiting":
                    _dict["Field"] = "WaitTime"

                if _dict["Field"] == "churchPartnerName":
                    _dict["Field"] = "ICPName"

                if _dict["Field"] == "birthMonth":
                    _dict["Field"] = "BirthMonth"

                if _dict["Field"] == "birthDay":
                    _dict["Field"] = "BirthDay"

                if _dict["Field"] == "birthYear":
                    _dict["Field"] = "BirthYear"

                if _dict["Field"] == "minAge":
                    _dict["Field"] = "Age"
        return json_result

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _call_search_service(
            self, mapping_name, service_name, result_name, method="GET"
    ):
        """
        Calls the given search service for the global childpool
        :param mapping_name: Name of the action mapping to use the correct
                             mapping.
        :param service_name: URL endpoint of the search service to call
        :param result_name: Name of the wrapping tag for the answer
        :param method: Method URL (GET or POST)
        :return:
        """
        params = self.data_to_json(mapping_name)
        onramp = OnrampConnector()
        if method == "POST":
            result = onramp.send_message(service_name, method, params)
        else:
            result = onramp.send_message(service_name, method, None, params)
        if result["code"] == 200:
            self.nb_found = result["content"].get("NumberOfBeneficiaries", 0)

            # When the skip param default value is higher than the available beneficiaries
            # make a second request with a computed skip param to still get an available beneficiary when possible
            if self.nb_found is not 0 and self.nb_found <= params['skip']:
                # Set the 'skip' parameter to retrieve only middle urgent beneficiaries
                params['skip'] = self.nb_found // 2
                result = onramp.send_message(service_name, method, None, params)

            if not result["content"][result_name]:
                raise UserError(_("No children found meeting criterias"))
            new_children = self.env["compassion.global.child"]
            for child_data in result["content"][result_name]:
                child_vals = new_children.json_to_data(
                    child_data, "Childpool Search Response"
                )
                child_vals["search_view_id"] = self.id
                new_children += self.env["compassion.global.child"].create(child_vals)
            restricted_children = new_children - new_children.filtered(
                "field_office_id.available_on_childpool"
            )
            new_children -= restricted_children
            self.nb_restricted_children = len(restricted_children)
            restricted_children.unlink()
            self.global_child_ids += new_children
        else:
            error = result.get("content", result)["Error"]
            if isinstance(error, dict):
                error = error.get("ErrorMessage")
            raise UserError(error)

    def _does_match(self, child):
        """ Returns if the selected criterias correspond to the given child.
        """
        if (
                self.field_office_ids
                and child.project_id.field_office_id not in self.field_office_ids
        ):
            return False
        if self.fcp_ids and child.project_id not in self.fcp_ids:
            return False
        if self.fcp_name and self.fcp_name not in child.project_id.name:
            return False
        if self.child_name and self.child_name not in child.name:
            return False
        if self.gender and child.gender != self.gender[0]:
            return False
        if self.hiv_affected_area and not child.is_area_hiv_affected:
            return False
        if self.is_orphan and not child.is_orphan:
            return False
        if self.has_special_needs and not child.is_special_needs:
            return False
        if self.min_age and child.age < self.min_age:
            return False
        if self.max_age and child.age > self.max_age:
            return False
        if self.min_days_waiting and child.waiting_days < self.min_days_waiting:
            return False
        birthdate = child.birthdate
        if self.birthday_month and self.birthday_month != birthdate.month:
            return False
        if self.birthday_day and self.birthday_day != birthdate.day:
            return False
        if self.birthday_year and self.birthday_year != birthdate.year:
            return False

        return True
