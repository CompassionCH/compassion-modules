##############################################################################
#
#    Copyright (C) 2019-2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Flückiger Nathan, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, api, _
from odoo.exceptions import UserError


class CompassionMappedModel(models.AbstractModel):
    """
    This is the abstract model which models will inherit in order to
    define mappings and be converted to JSON for GMC Connect.
    """

    _name = "compassion.mapped.model"
    _description = "Compassion Mapping"

    def data_to_json(self, mapping_name=None):
        """
         Function to convert an odoo record into JSON representation for
         GMC Connect.

        :param mapping_name: Name of the mapping to be used.
                             Will select the first mapping found for the model
                             if not specified.
        :return: A dictionary or list with the json field name and the data.
        """
        search_criterias = [("model_id.model", "=", self._name)]
        if mapping_name:
            search_criterias.append(("name", "=", mapping_name))
        mapping = (
            self.env["compassion.mapping"].sudo().search(search_criterias, limit=1)
        )
        result = list()
        for record in self:
            json = {}
            for json_spec in mapping.json_spec_ids.filtered(
                    lambda jspec: not jspec.exclude_from_json
            ):
                if json_spec.sub_mapping_id:
                    sub_record = record
                    if json_spec.field_name:
                        # Take the relational field as base for mapping
                        # conversion
                        sub_record = record.mapped(json_spec.relational_field)
                        if not hasattr(sub_record, "data_to_json"):
                            raise UserError(
                                _(
                                    "Sub mapping field should be a relational "
                                    "field onto a model which supports GMC "
                                    "mappings."
                                )
                            )
                    json[json_spec.json_name] = sub_record.data_to_json(
                        json_spec.sub_mapping_id.name
                    )
                else:
                    # Calls the conversion function defined in field_to_json
                    odoo_field = json_spec.odoo_field
                    value = None
                    if odoo_field:
                        value = record.mapped(odoo_field)
                        # Unwrap single values
                        if isinstance(value, list) and len(value) == 1:
                            value = value[0]
                    json.update(json_spec.to_json(value))
            result.append(json)
        return result[0] if len(result) == 1 else result

    @api.model
    def json_to_data(self, json, mapping_name=None):
        """
        Function to convert JSON into odoo record values.

        :param json: A list or a single dictionary with the JSON value
        :param mapping_name: Name of the mapping to be use.
                             Will select the first mapping found for the model
                             if not specified.
        :return: A list or a dictionary with the odoo field name and the data.
        """
        search_criterias = [("model_id.model", "=", self._name)]
        if mapping_name:
            search_criterias.append(("name", "=", mapping_name))
        mapping = self.env["compassion.mapping"].search(search_criterias, limit=1)
        all_fields = mapping.json_spec_ids.filtered("field_id")
        res = []
        if not isinstance(json, list):
            json = [json]
        for single_json in json:
            data = {}
            for json_spec in all_fields:
                for attempt in range(10):  # try x attempts, avoid while loop
                    json_value = single_json.get(json_spec.json_name)
                    if json_spec.sub_mapping_id and json_value:
                        # Convert data using sub_mapping
                        sub_model = self.env[
                            json_spec.sub_mapping_id.model_id.model
                        ]
                        sub_data = sub_model.json_to_data(
                            json_value, json_spec.sub_mapping_id.name
                        )
                        data.update(json_spec.from_json(sub_data))
                    else:
                        data.update(json_spec.from_json(json_value))
                    break  # break from attempts if successful
            res.append(data)
        return res[0] if len(res) == 1 and not isinstance(res[0], tuple) else res
