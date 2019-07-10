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
from odoo import models, api


class CompassionMappedModel(models.AbstractModel):

    _name = "compassion.mapped.model"

    @api.multi
    def data_to_json(self, mapping_name=None):
        '''
         Function to get a dic with the Json value of a mapping
        :param mapping_name: name of the mapping to be use. Select the first mapping
                             find for the model if not set
        :return: A dictionary with the json field name and the data.
        '''

        if mapping_name:
            mapping = self.env['compassion.mapping'].search(
                [('name', '=', mapping_name)])
        else:
            mapping = self.env['compassion.mapping'].search(
                [('model_id.name', '=', self._name)])
        json = {}
        for fieldtojson in mapping.fields_json_ids:
            if fieldtojson.sub_mapping_id:
                json[fieldtojson.json_name] = self.data_to_json(
                    fieldtojson.sub_mapping_id.name)
            else:
                json[fieldtojson.json_name] = getattr(self, fieldtojson.field_id.name)
        return json

    @api.model
    def json_to_data(self, json, mapping_name=None):
        '''
         Function to get a dic with the odoo value of a mapping
        :param json: A dictionary with the JSON value
        :param mapping_name: name of the mapping to be use. Select the first mapping
                             find for the model if not set
        :return: A dictionary with the odoo field name and the data to be use in write.
        '''
        if mapping_name:
            mapping = self.env['compassion.mapping'].search(
                [('name', '=', mapping_name)])
        else:
            mapping = self.env['compassion.mapping'].search(
                [('model_id.name', '=', self._name)])
        data = {}
        for fieldtojson in mapping.fields_json_ids:
            if fieldtojson.sub_mapping_id:
                data.update(self.json_to_data(json, fieldtojson.sub_mapping_id.name))
            else:
                data[fieldtojson.field_id.name] = json[fieldtojson.json_name]
        return data
