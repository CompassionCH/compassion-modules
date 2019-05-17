# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nathan Fluckiger <nathan.fluckiger@hotmail.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, api, exceptions


class SmartTags(models.Model):
    _name = "smart.tags"

    tagger = fields.Many2one('smart.tagger')

    related_data = fields.Many2many()
    related_field = fields.Field(related=tagger.condition_field)

    name = fields.Char(related=tagger.name)

    @api.onchange(related_field)
    def check_condition(self):
        if self.related_data:
            if self.tagger.related_tag_field in self.related_data:
                data_id = self.related_data.id
                if data_id not in self.env[self.tagger.model].\
                        search(self.tagger.condition.domain):
                    value = self.related_data[self.tagger.related_tag_field]
                    value = [x for x in value if not x == self.id]
                    self.related_data.write({
                        self.tagger.related_tag_field: value
                    })
            else:
                raise exceptions.ValidationError(
                    "Model %s has no field %s", self.tagger.model,
                    self.tagger.related_tag_field)

