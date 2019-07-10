##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Flückiger Nathan, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class CompassionMapping(models.Model):
    _name = "compassion.mapping"
    _description = "Mapping for GMC Connect"

    name = fields.Char(required=True)
    model_id = fields.Many2one(
        'ir.model', 'Model', required=True, index=True, ondelete='cascade')
    json_spec_ids = fields.One2many(
        'compassion.field.to.json', 'mapping_id', string='JSON Specifications')

    @api.model
    def create_from_json(self, json):
        """
        Find or creates a mapping using the JSON data provided.
        :param json: JSON data
        :return: The compassion.mapping record created/updated
        """
        self._validate_data(json)
        model = self.env['ir.model'].search([('model', '=', json['model'])])
        if not model:
            raise UserError(_(f"Model does not exist : {json['model']}"))
        mapping = self.search([
            ('name', '=', json['name']),
            ('model_id', '=', model.id)
        ])
        if not mapping:
            mapping = self.create({
                'name': json['name'],
                'model_id': model.id
            })
        mapping.load_from_json(json['mapping'])
        return mapping

    @api.multi
    def load_from_json(self, json):
        """
        Function used to import JSON file to create/update a mapping
        :param json: JSON loaded with json field name and odoo field name
        :return: True
        """
        self.ensure_one()
        self.json_spec_ids.unlink()
        for json_name, odoo_spec in json.items():
            if not isinstance(odoo_spec, dict):
                raise UserError(
                    _(f"Invalid data for JSON field {json_name}. "
                      f"Expected a dictionary."))
            field_spec_vals = {
                'mapping_id': self.id,
                'json_name': json_name,
                'to_json_conversion': odoo_spec.get('to_json_conversion'),
                'from_json_conversion': odoo_spec.get('from_json_conversion')
            }
            field_name = odoo_spec.get('field')
            if field_name:
                if isinstance(field_name, dict):
                    # In this case we create a sub_mapping
                    field_spec_vals['sub_mapping_id'] =\
                        self.create_from_json(field_name).id
                    continue

                # Normal case, field_name is an odoo field name
                relational_count = field_name.count('.')
                if relational_count > 1:
                    raise UserError(_(
                        f"Mapping supports only direct relations. You cannot "
                        f"link a value to further relational fields like you "
                        f"did for field {json}: {field_name}"))
                if relational_count:
                    # Relational field
                    relational_field = self.env['ir.model.fields'].search([
                        ('model_id', '=', self.model_id.id),
                        ('name', '=', field_name.split('.')[0])
                    ])
                    field = self.env['ir.model.fields'].search([
                        ('model_id', '=', relational_field.relation),
                        ('name', '=', field_name.split('.')[-1])
                    ])
                    field_spec_vals.update({
                        'relational_field_id': relational_field.id,
                        'search_relational_record': odoo_spec.get(
                            'search_relational_record')
                    })
                else:
                    # Regular field
                    field = self.env['ir.model.fields'].search([
                        ('model_id', '=', self.model_id.id),
                        ('name', '=', field_name)
                    ])
                # We should have found a valid field
                field.ensure_one()
                field_spec_vals['field_id'] = field.id
            self.env['compassion.field.to.json'].create(field_spec_vals)
        return True

    def _validate_data(self, data):
        if not isinstance(data, dict):
            raise UserError(_("JSON data must be a dictionary."))
        model = data.get('model')
        name = data.get('name')
        mapping = data.get('mapping')
        if not model or not name or not mapping:
            raise UserError(_("JSON data must contain the following keys: "
                              "name, model and mapping"))
        if not isinstance(mapping, dict):
            raise UserError(_("Mapping must be a dictionary"))

    @api.constrains('model_id')
    def validate_model_id(self):
        for mapping in self:
            model = self.env[mapping.model_id.model]
            if not hasattr(model, 'data_to_json') or not \
                    hasattr(model, 'json_to_data'):
                raise ValidationError(_(
                    "You can only add mapping to models that inherit "
                    "compassion.mapped.model"
                ))
