##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Flückiger Nathan, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, _
from odoo.tools import safe_eval


class FieldToJson(models.Model):
    """ This model is used to make a link between odoo
        field and GMC Connect Json field name for the compassion mapping
    """
    _name = "compassion.field.to.json"
    _description = "Field to GMC Json"

    mapping_id = fields.Many2one(
        'compassion.mapping', index=True, required=True,
        ondelete='cascade'
    )
    model = fields.Char(related='mapping_id.model_id.model', readonly=True)
    field_id = fields.Many2one(
        'ir.model.fields', 'Odoo field', index=True,
        help="Set in which field the Odoo value will be retrieved/stored. "
             "If not set, the JSON value won't be converted into Odoo data."
             "In case of sub mapping, this should only be a relational field "
             "that will be used to compute the sub values. If empty, the sub "
             "values will be determined from the same record as the parent.",
        ondelete='cascade'
    )
    relational_field_id = fields.Many2one(
        'ir.model.fields', 'Relational field',
        help="In case the JSON value points to relational value, specify "
             "here where is the relation stored.",
        ondelete='cascade'
    )
    search_relational_record = fields.Boolean(
        help="When converting JSON to data, set to true if you should lookup "
             "for a matching record given the JSON value. If not activated, "
             "the field won't be used in the conversion."
    )
    field_name = fields.Char(related='field_id.name', readonly=True)
    json_name = fields.Char("Json Field Name", required=True, index=True)
    sub_mapping_id = fields.Many2one(
        'compassion.mapping', string='Sub mapping',
        help='This will nest a dictionary in the JSON and use given mapping'
             'to compute the value.'
    )
    to_json_conversion = fields.Text(
        help='Pyhton function that will convert the value for its JSON '
             'representation. Use `odoo_value` as the raw value of the Odoo'
             'field. You should return the final JSON value.')
    from_json_conversion = fields.Text(
        help='Pyhton function that will convert the JSON value to its  '
             'correct value in Odoo. Use `json_value` as the value to be '
             'processed. You should return the final Odoo value.')

    _sql_constraints = [
        ('unique', 'unique(mapping_id,json_name)',
         _('This field is already mapped'))
    ]

    def to_json(self, odoo_value):
        """
        Converts the value to its JSON representation.
        :return: JSON representation (dict) of the field value in JSON
        """
        self.ensure_one()
        res = {self.json_name: odoo_value}
        if self.to_json_conversion:
            res[self.json_name] = safe_eval(self.to_json_conversion)
        return res

    def from_json(self, json_value):
        """
        Converts the JSON value to Odoo field value.
        :param json_value: JSON representation of the field
        :return: odoo data (dict)
        """
        res = {self.field_name: json_value}
        if self.from_json_conversion:
            res[self.field_name] = safe_eval(self.from_json_conversion)
        return res
