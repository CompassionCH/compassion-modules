##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Flückiger Nathan, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, api, _
from odoo.exceptions import UserError

from odoo.addons.message_center_compassion.tools.onramp_connector import OnrampConnector
from odoo.addons.message_center_compassion.models.field_to_json import RelationNotFound


class MappingKeyNotFound(UserError):
    def __init__(self, msg, **kwargs):
        super().__init__(msg)


class CompassionMappedModel(models.AbstractModel):
    """
    This is the abstract model which models will inherit in order to
    define mappings and be converted to JSON for GMC Connect.
    """

    _name = "compassion.mapped.model"
    _description = "Compassion Mapping"

    @api.multi
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
                        sub_record = record.mapped(json_spec.field_name)
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
                    odoo_field = json_spec.field_name
                    if json_spec.relational_field_id:
                        odoo_field = (
                            json_spec.relational_field_id.name + "." + odoo_field
                        )
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
                    try:
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
                    except RelationNotFound as e:
                        self.fetch_missing_relational_records(
                            e.field_relation, e.field_name, e.value, e.json_name
                        )
            res.append(data)
        return res[0] if len(res) == 1 and not isinstance(res[0], tuple) else res

    def fetch_missing_relational_records(self, field_relation, field_name, values,
                                         json_name):
        """ Fetch missing relational records in various languages.

        Method used to catch and create missing values and translations of fields
        received by GMC.

        :param field_relation: relation
        :param field_name: name of field in the relation
        :param values: missing relational values
        :param json_name: key name in content
        :type field_relation: str
        :type values: str or list of str
        :type json_name: str

        """
        onramp = OnrampConnector()
        # mapping of languages for translations
        languages_map = {
            "English": "en_US",
            "French": "fr_CH",
            "German": "de_DE",
            "Italian": "it_IT",
        }
        # mapping for endpoints
        endpoint_map = {
            "compassion.child": "beneficiaries/{0}/details?FinalLanguage={1}",
            "compassion.project": "churchpartners/{0}/kits/icpkit?FinalLanguage={1}",
            "compassion.intervention": "interventions/{0}/kits/InterventionKit?"
                                       "FinalLanguage={1}"
        }
        # mapping for key to fetch content in GMC result
        content_key_map = {
            "compassion.child": "BeneficiaryResponseList",
            "compassion.project": "ICPResponseList",
            "compassion.intervention": "InterventionDetailsRequest"
        }
        # mapping for id of object passed
        id_map = {
            "compassion.child": "global_id",
            "compassion.project": "fcp_id",
            "compassion.intervention": "intervention_id"
        }
        # declare variables from mappings
        try:
            endpoint = endpoint_map[self._name]
            content_key = content_key_map[self._name]
            id_ = id_map[self._name]
        except KeyError:
            raise MappingKeyNotFound(
                _(
                    "Model %s has not yet been defined in mappings when fetching "
                    "missing relational records"
                ) % (self._name)
            )
        # transform values to list first
        if not isinstance(values, list):
            values = [values]
        # go over all missing values, keep count of index to know which translation
        # to take from onramp result
        for i, value in enumerate(values):
            # check if hobby/household duty, etc... exists in our database
            search_vals = [(field_name, "=", value)]
            relation_obj = self.env[field_relation].sudo()
            if hasattr(relation_obj, "value"):
                # Useful for connect.multipicklist objects
                search_vals.insert(0, "|")
                search_vals.append(("value", "=", value))
            search_count = relation_obj.search_count(search_vals)
            # if not exist, then create it
            if not search_count:
                value_record = (
                    relation_obj.create({field_name: value, "value": value})
                )
                if not hasattr(relation_obj, "value"):
                    return
                # fetch translations for connect.multipicklist values
                must_manually_translate = False
                for lang_literal, lang_context in languages_map.items():
                    result = onramp.send_message(
                        endpoint.format(getattr(self, id_), lang_literal), "GET"
                    )
                    if content_key in result.get("content", {}):
                        content = result["content"][content_key][0]
                        if json_name in content:
                            content_values = content[json_name]
                            if not isinstance(content_values, list):
                                content_values = [content_values]
                            translation = content_values[i]
                            if translation == value_record.value:
                                must_manually_translate = True
                            value_record.with_context(
                                lang=lang_context
                            ).value = translation
                if must_manually_translate:
                    value_record.assign_translation()
