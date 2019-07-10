# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Flückiger Nathan <nathan.fluckiger@hotmail.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, api


class CompassionMapping(models.Model):

    _name = "compassion.mapping"

    name = fields.Char(required=True)
    model_id = fields.Many2one('ir.model', 'Model', required=True)
    # Models and fieldToJson link
    fields_json_ids = fields.Many2many('compassion.field.to.json')

    @api.multi
    def create_from_json(self, json):
        '''
         Function used to import JSON file to create a new mapping
        :param json: JSON loaded with json field name and odoo field name
        :return:return the mapping id
        '''
        self.ensure_one()
        fields = []
        for field in json.keys():
            field_to_json = self.env['field_to_json'].search([
                '&', ('json_name', 'ilike', field),
                ('field_name', 'ilike', json[field])]).id
            if not field_to_json:
                cond = type(json[field]) is dict
                if cond:
                    tmp_mapping = self.create({
                        'name': field,
                        'model_id': self.model_id
                    })
                    tmp_mapping.create_from_json(json[field])
                    if type(json[field]) is tuple:
                        for multi_name in json[field]:
                            fields.append(self.env['field_to_json'].create({
                                'json_name': field,
                                'field_name': multi_name,
                            }).id)
                    else:
                        fields.append(self.env['field_to_json'].create({
                            'field_name': json[field] if not cond else False,
                            'json_name': field,
                            'sub_mapping_id': tmp_mapping if cond else False
                        }).id)
                else:
                    fields.append(field_to_json)
            else:
                fields.append(field_to_json)

        duplicate_mapping = self.env['compassion_mapping'].search([
            ('fields_json_ids', '=', fields)
        ])
        if duplicate_mapping:
            return duplicate_mapping

        self.write({
            'fields_json_ids': [(6, 0, fields)]
        })
        return self
