##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import re
import sys

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class InterventionSearch(models.TransientModel):
    """
    Class used for searching interventions in the Mi3 Portal.
    """

    _inherit = "compassion.mapped.model"
    _name = "compassion.intervention.search"
    _description = "Intervention search"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    search_filter_ids = fields.Many2many(
        "compassion.query.filter",
        "compassion_intervention_search_filters",
        "search_id",
        "query_id",
        "Filters",
        readonly=False,
    )
    intervention_ids = fields.Many2many(
        "compassion.global.intervention",
        "compassion_intervention_search_to_results",
        "search_id",
        "global_intervention_id",
        "Interventions",
        readonly=False,
    )
    use_advanced_search = fields.Boolean()

    # Search helpers
    ################
    type_chooser = fields.Selection("get_types")
    type_selected = fields.Char(readonly=True)
    category_id = fields.Many2one(
        "compassion.intervention.category", "Category", readonly=False
    )
    status_chooser = fields.Selection("get_statuses")
    status_selected = fields.Char(readonly=True)
    intervention_id = fields.Char()
    fcp_ids = fields.Many2many(
        "compassion.project",
        "compassion_intervention_search_fcp",
        "search_id",
        "fcp_id",
        "FCPs",
        readonly=False,
    )
    field_office_ids = fields.Many2many(
        "compassion.field.office",
        "compassion_intervention_search_fo",
        "search_id",
        "fo_id",
        "Field offices",
        readonly=False,
    )
    remaining_amount_equal = fields.Float()
    remaining_amount_greater = fields.Float("Remaining amount greater than")
    remaining_amount_lower = fields.Float("Remaining amount lower than")
    disburse_without_commitment = fields.Boolean()

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    def get_types(self):
        return self.env["compassion.intervention.category"].get_types()

    def get_statuses(self):
        return self.env["compassion.generic.intervention"].get_funding_statuses()

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    def add_type(self):
        self.ensure_one()
        if self.type_selected:
            self.type_selected += ";" + self.type_chooser
        else:
            self.type_selected = self.type_chooser
        self.type_chooser = False
        return True

    def reset_type(self):
        self.ensure_one()
        self.type_selected = False
        return True

    def add_status(self):
        self.ensure_one()
        if self.status_selected:
            self.status_selected += ";" + self.status_chooser
        else:
            self.status_selected = self.status_chooser
        self.status_chooser = False
        return True

    def reset_status(self):
        self.ensure_one()
        self.status_selected = False
        return True

    def compute_search(self):
        self.ensure_one()
        # Remove all search filters
        self.write({"search_filter_ids": [(5, False, False)]})

        # Utility to get write values for a selected filter
        def _get_filter(field_name, operator_id, value):
            field_id = (
                self.env["ir.model.fields"]
                .search(
                    [
                        ("model", "=", "compassion.global.intervention"),
                        ("name", "=", field_name),
                    ]
                )
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
        new_filters = list()
        if self.type_selected:
            new_filters.append(_get_filter("type", anyof_id, self.type_selected))
        if self.category_id:
            new_filters.append(
                _get_filter("category_id", anyof_id, self.category_id.name)
            )
        if self.status_selected:
            new_filters.append(
                _get_filter("funding_status", anyof_id, self.status_selected)
            )
        if self.intervention_id:
            new_filters.append(
                _get_filter("intervention_id", is_id, self.intervention_id)
            )
        if self.fcp_ids:
            fcp_codes = ";".join(self.fcp_ids.mapped("fcp_id"))
            new_filters.append(_get_filter("fcp_ids", anyof_id, fcp_codes))
        if self.field_office_ids:
            fo_codes = ";".join(self.field_office_ids.mapped("field_office_id"))
            new_filters.append(_get_filter("field_office_id", anyof_id, fo_codes))
        if self.disburse_without_commitment:
            new_filters.append(_get_filter("disburse_without_commitment", is_id, "T"))
        if self.remaining_amount_equal:
            equalto_id = self.env.ref("message_center_compassion.equalto").id
            new_filters.append(
                _get_filter(
                    "remaining_amount_to_raise", equalto_id, self.remaining_amount_equal
                )
            )
        elif self.remaining_amount_greater or self.remaining_amount_lower:
            between_id = self.env.ref("message_center_compassion.between").id
            min_cost = self.remaining_amount_greater or 0
            max_cost = self.remaining_amount_lower or sys.maxsize
            new_filters.append(
                _get_filter(
                    "remaining_amount_to_raise",
                    between_id,
                    str(min_cost) + ";" + str(max_cost),
                )
            )

        return self.write({"search_filter_ids": new_filters})

    def do_search(self):
        self.ensure_one()
        if not self.use_advanced_search:
            self.compute_search()
        self.intervention_ids = False
        action = self.env.ref("intervention_compassion.intervention_search_action")
        message = (
            self.env["gmc.message"]
            .with_context(async_mode=False)
            .create({"action_id": action.id, "object_id": self.id})
        )
        if not self.intervention_ids:
            raise UserError(message.failure_reason or _("No intervention found"))
        return {
            "name": _("Interventions"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "compassion.global.intervention",
            "context": self.env.context,
            "domain": [("id", "in", self.intervention_ids.ids)],
            "target": "current",
        }

    def data_to_json(self, mapping_name=None):
        data = super().data_to_json(mapping_name)
        del data["InterventionQueryResponseList"]
        return {"InterventionQuery": data}

    @api.model
    def json_to_data(self, json, mapping_name=None):
        for json_data in json["InterventionQueryResponseList"]:
            if "," in json_data["InterventionSubCategory_Name"]:
                # Split only if a comma is outside of parenthesis
                # (to handle the case of Sanitation subcategory)
                if (
                    re.search(
                        r",\s*(?![^()]*\))", json_data["InterventionSubCategory_Name"]
                    )
                    is not None
                ):
                    json_data["InterventionSubCategory_Name"] = json_data[
                        "InterventionSubCategory_Name"
                    ].split(",")
                else:
                    json_data["InterventionSubCategory_Name"] = json_data[
                        "InterventionSubCategory_Name"
                    ].replace(",", "")

        odoo_data = super().json_to_data(json, mapping_name)
        return odoo_data
