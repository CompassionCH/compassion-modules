##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Flückiger Nathan, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from collections import defaultdict

from odoo import models, api, _
from odoo.exceptions import UserError


class CompassionMappedModel(models.AbstractModel):
    """
    This is the abstract model which models will inherit in order to
    define mappings and be converted to JSON for GMC Connect.
    """
    _name = "compassion.mapped.model"

    @api.multi
    def data_to_json(self, mapping_name=None):
        """
         Function to convert an odoo record into JSON representation for
         GMC Connect.

        :param mapping_name: Name of the mapping to be used.
                             Will select the first mapping found for the model
                             if not specified.
        :return: A dictionary with the json field name and the data.
        """
        search_criterias = [('model_id.name', '=', self._name)]
        if mapping_name:
            search_criterias.append(('name', '=', mapping_name))
        mapping = self.env['compassion.mapping'].search(
            search_criterias, limit=1)
        result = list()
        for record in self:
            json = {}
            for json_spec in mapping.json_spec_ids:
                if json_spec.sub_mapping_id:
                    sub_record = record
                    if json_spec.field_name:
                        # Take the relational field as base for mapping
                        # conversion
                        sub_record = record.mapped(json_spec.field_name)
                        if not hasattr(sub_record, 'data_to_json'):
                            raise UserError(_(
                                "Sub mapping field should be a relational "
                                "field onto a model which supports GMC "
                                "mappings."))
                    json[json_spec.json_name] = sub_record.data_to_json(
                        json_spec.sub_mapping_id.name)
                else:
                    # Calls the conversion function defined in field_to_json
                    odoo_field = json_spec.field_name
                    if json_spec.relational_field_id:
                        odoo_field = json_spec.relational_field_id.name + \
                            '.' + odoo_field
                    value = None
                    if odoo_field:
                        value = record.mapped(odoo_field)
                    json.update(json_spec.to_json(value))
            result.append(json)
        return result[:1] if len(result) == 1 else result

    @api.model
    def json_to_data(self, json, mapping_name=None):
        """
        Function to convert JSON into odoo record values.

        :param json: A dictionary with the JSON value
        :param mapping_name: Name of the mapping to be use.
                             Will select the first mapping found for the model
                             if not specified.
        :return: A dictionary with the odoo field name and the data.
        """
        search_criterias = [('model_id.name', '=', self._name)]
        if mapping_name:
            search_criterias.append(('name', '=', mapping_name))
        mapping = self.env['compassion.mapping'].search(
            search_criterias, limit=1)
        data = {}
        all_fields = mapping.json_spec_ids.filtered('field_id')
        relational_fields = all_fields.filtered('search_relational_record')
        regular_fields = all_fields - relational_fields
        for json_spec in regular_fields:
            json_value = json.get(json_spec.json_name)
            if json_spec.sub_mapping_id:
                sub_model = self.env[json_spec.sub_mapping_id.model_id.model]
                data.update(sub_model.json_to_data(
                    json_value, json_spec.sub_mapping_id.name))
            else:
                data.update(json_spec.from_json(json_value))
        data.update(self._json_to_relation_fields(json, relational_fields))
        return data

    def _json_to_relation_fields(self, json, field_specs):
        """
        Internal method that takes care of JSON values that must be converted
        into relational record values. It will values that can be used by
        ORM for writing into relational fields, i.e.:
        {
            "partner_id": 12,
            "follower_ids": [(6, 0, [12, 34, 53])]
        }
        :param json: the received JSON data
        :param field_specs: compassion.field.to.json records
        :return: Odoo data dictionary
        """
        res = {}
        # Group values that concern the same relational field
        field_groups = defaultdict(lambda: {})
        for spec in field_specs:
            json_value = json.get(spec.json_name)
            field_groups[spec.relational_field_id][
                spec.field_name] = json_value
        # For each relational field, search corresponding records
        for field, field_values in field_groups.items():
            relational_model = self.env[field.model_id.model]
            operator = 'in' if isinstance(json_value, list) else '=ilike'
            search_values = [(rname, operator, rval)
                             for rname, rval in field_values.items()]
            records = relational_model.search(search_values)
            if records and field.type == 'many2one':
                res[field.name] = records[:1].id
            elif records:
                res[field.name] = [(6, 0, records.ids)]
        return res
