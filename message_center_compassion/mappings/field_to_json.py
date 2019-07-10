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
from odoo import models, fields


class FieldToJson(models.Model):

    _name = "compassion.field.to.json"
    _description = "This model is used to make a link between odoo " \
                   "field and Json field name for the compassion mapping"

    field_id = fields.Many2one('ir.model.fields', 'Odoo field')
    json_name = fields.Char(string="Json Field Name", required=True)
    sub_mapping_id = fields.Many2one('compassion.mapping', string='Sub mapping')
