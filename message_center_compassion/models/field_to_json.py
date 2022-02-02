##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Flückiger Nathan, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import models, fields, _
from odoo.exceptions import UserError
from odoo.tools import safe_eval

_logger = logging.getLogger(__name__)


class RelationNotFound(UserError):
    def __init__(self, msg, **kwargs):
        super().__init__(msg)
        self.field_relation = kwargs['field_relation']
        self.value = kwargs['value']
        self.json_name = kwargs['json_name']
        self.field_name = kwargs['field_name']


class FieldToJson(models.Model):
    """ This model is used to make a link between odoo
        field and GMC Connect Json field name for the compassion mapping
    """

    _name = "compassion.field.to.json"
    _description = "Field to GMC Json"

    mapping_id = fields.Many2one(
        "compassion.mapping",
        index=True,
        required=True,
        ondelete="cascade",
        readonly=False,
    )
    model = fields.Char(related="mapping_id.model_id.model", readonly=True)
    field_id = fields.Many2one(
        "ir.model.fields",
        "Odoo field",
        index=True,
        help="Set in which field the Odoo value will be retrieved/stored. "
             "If not set, the JSON value won't be converted into Odoo data."
             "In case of sub mapping, this should only be a relational field "
             "that will be used to compute the sub values. If empty, the sub "
             "values will be determined from the same record as the parent.",
        ondelete="cascade",
        readonly=False,
    )
    relational_field_id = fields.Many2one(
        "ir.model.fields",
        "Relational field",
        help="In case the JSON value points to relational value, specify "
             "here where is the relation stored.",
        ondelete="cascade",
        readonly=False,
    )
    search_relational_record = fields.Boolean(
        help="When converting JSON to data, set to true if you should lookup "
             "for a matching record given the JSON value. If not activated, "
             "the field won't be used in the conversion."
    )
    search_key = fields.Char(
        help="Odoo field name that will be used to search for an existing relational "
             "record. If not specified, it will assume a single value is given and "
             "will search according the the relational_field_id set."
    )
    allow_relational_creation = fields.Boolean(
        help="If set to true, new records will be created if no matching "
             "records are found with the given JSON values"
    )
    relational_raise_if_not_found = fields.Boolean(
        default=True,
        help="Set to false if you don't care finding the relational field."
    )
    relational_write_mode = fields.Selection(
        [("overwrite", "Overwrite"), ("append", "Append")],
        default="overwrite",
        help="Either overwrite relations or add the new values to the relation"
    )
    field_name = fields.Char(related="field_id.name", readonly=True)
    json_name = fields.Char("Json Field Name", required=True, index=True)
    sub_mapping_id = fields.Many2one(
        "compassion.mapping",
        string="Sub mapping",
        help="This will nest a dictionary in the JSON and use given mapping"
             "to compute the value.",
        readonly=False,
    )
    to_json_conversion = fields.Text(
        help="Python function that will convert the value for its JSON "
             "representation. Use `odoo_value` as the raw value of the Odoo"
             "field. You should return the final JSON value."
    )
    from_json_conversion = fields.Text(
        help="Python function that will convert the JSON value to its  "
             "correct value in Odoo. Use `json_value` as the value to be "
             "processed. You should return the final Odoo value."
    )
    exclude_from_json = fields.Boolean(
        help="Value won't be converted to JSON if checked (data_to_json)."
             "The JSON value can still be converted into Odoo value "
             "(json_to_data)."
    )

    _sql_constraints = [
        ("unique", "unique(mapping_id,json_name)", _("This field is already mapped"))
    ]

    def to_json(self, odoo_value):
        """
        Converts the value to its JSON representation.
        :return: JSON representation (dict) of the field value in JSON
        """
        self.ensure_one()
        res = {self.json_name: odoo_value}
        if self.to_json_conversion:
            res[self.json_name] = safe_eval(
                self.to_json_conversion,
                {"odoo_value": odoo_value, "self": self, "fields": fields},
            )
        elif (
                self.field_id.ttype not in ("boolean", "float", "integer", "monetary")
                and not odoo_value
        ):
            # Don't include null fields
            return {}
        elif self.field_id.ttype == "datetime":
            res[self.json_name] = fields.Datetime.to_string(odoo_value)
        elif self.field_id.ttype == "date":
            res[self.json_name] = fields.Date.to_string(odoo_value)

        return res

    def from_json(self, json_value):
        """
        Converts the JSON value to Odoo field value.
        :param json_value: JSON representation of the field
        :return: odoo data (dict)
        """
        self.ensure_one()
        # Skip empty values
        if not json_value and not isinstance(json_value, (bool, int, float)):
            return {}
        # Skip invalid data
        if isinstance(json_value, str) and json_value.lower() in (
                "null",
                "false",
                "none",
                "other",
                "unknown",
        ):
            return {}
        converted_value = json_value
        field_name = self.field_name
        if self.from_json_conversion:
            # Calls a conversion method defined in mapping
            converted_value = safe_eval(
                self.from_json_conversion,
                {"json_value": json_value, "self": self},
            )
        if self.relational_field_id:
            converted_value = self._json_to_relational_value(converted_value)
            field_name = self.relational_field_id.name
        return {field_name: converted_value}

    def _json_to_relational_value(self, value):
        """
        Converts a received JSON value into valid data for a relational record
        https://www.odoo.com/documentation/12.0/developer/reference/orm.html#odoo.models.Model.write
        Example of output:
        {
            "partner_id": 12,
            "follower_ids": [(6, 0, [12, 34, 53])],
            "my_teacher_ids": [(0, 0, {'name'; 'Emanuel Cino'})]
        }
        :param value: JSON value (could be dict, list of dict, or string)
        :return: odoo value for a relational field
        """
        self.ensure_one()
        field = self.relational_field_id
        relational_model = self.env[field.relation]
        orm_vals = [(5, 0, 0)] if self.relational_write_mode == "overwrite" else []
        to_create = []
        if self.search_relational_record:
            # Lookup for records that match the values received
            values = value if isinstance(value, list) else [value]
            for val in values:
                # Skip invalid data
                if isinstance(val, str) and val.lower() in (
                        "null",
                        "false",
                        "none",
                        "other",
                        "unknown",
                ):
                    continue
                search_field = self.field_name
                search_val = val
                to_update = self.search_key and isinstance(val, dict)
                if to_update:
                    # In that case we receive several values for the relation record
                    # and use one value in particular to find a matching record.
                    search_field = self.search_key
                    search_val = val.get(self.search_key)
                records = relational_model.search([
                    "|", (search_field, "=", search_val),
                    (search_field, "=ilike", str(search_val))
                ]) if search_val else relational_model
                if field.ttype == "many2one":
                    record = records[:1]  # Only take one relation
                    if not record and self.allow_relational_creation:
                        to_create.append(val)
                    elif to_update:
                        record.write(val)
                    orm_vals = record.id
                else:
                    if not records and self.allow_relational_creation:
                        to_create.append(val)
                        continue
                    if to_update:
                        orm_vals.extend([(1, rid, val) for rid in records.ids])
                    else:
                        orm_vals.extend([(4, rid) for rid in records.ids])
        else:
            to_create = value

        if self.allow_relational_creation and to_create:
            # Replace relations with new associated records
            if field.ttype == "many2one":
                # We must create the record and return its id
                if isinstance(value, dict):
                    return relational_model.create(value).id
                else:
                    return relational_model.create({self.field_name: value}).id

            # In that case we are in many2many or one2many and will replace
            # relations.
            record_vals = value if isinstance(value, list) else [value]
            # Use dictionary values to create related record
            orm_vals.extend(
                [(0, 0, vals) for vals in record_vals if isinstance(vals, dict)]
            )
            # Use simple field to create related record
            orm_vals.extend(
                [(0, 0, {self.field_name: vals}) for vals in record_vals
                 if not isinstance(vals, dict)]
            )

        if orm_vals:
            return orm_vals

        if not self.search_relational_record and not self.allow_relational_creation:
            # In that case we don't want to search or create, we simply
            # return the raw value
            return value

        # No records found given the values
        _logger.warning(
            "Associated object not found using mapping %s, "
            "JSON Key %s, JSON value %s",
            self.mapping_id.name,
            self.json_name,
            value,
        )
        if self.relational_raise_if_not_found:
            raise RelationNotFound(
                _(
                    "Trying to find a %s "
                    "that has the following values, but nothing was found: %s"
                ) % (relational_model._description, value),
                field_relation=field.relation,
                value=value,
                json_name=self.json_name,
                field_name=self.field_name
            )
        return False

    def _get_relational_creation_values(self, field_values):
        """
        Given a dictionary with JSON field values, will create an ORM
        list of values that can be used by Odoo to create new relational
        records.
        See https://www.odoo.com/documentation/11.0/reference/
        orm.html#odoo.models.Model.write

        :param field: ir.model.fields record of the relational field
        :param field_values: dict with JSON values
        :return: list of tuples for ORM creation i.e.
        [(0, 0, record_values)]
        """
        record_values = []
        if isinstance(field_values, dict):
            nb_records = 1
            for field_name, field_val in field_values.items():
                if isinstance(field_val, list):
                    nb_records = max(nb_records, len(field_val))
                for i in range(0, nb_records):
                    record_values.append(
                        {
                            field_name: field_val[i]
                            if isinstance(field_val, list) and len(field_val) >= i
                            else field_val
                            for field_name, field_val in field_values.items()
                        }
                    )
        return [(0, 0, values) for values in record_values]
