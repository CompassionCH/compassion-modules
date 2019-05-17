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


class SmartTagger(models.Model):
    _name = "smart.tagger"

    model = fields.Many2one('ir.model')
    condition = fields.Many2one('ir.filters')
    condition_field = fields.Many2one('ir.model.fields')
    related_tag_field = fields.Many2one('ir.model.fields')

    tags = fields.One2many('smart.tags')
    name = fields.Char()
    number_tags = fields.Integer(compute='_tags_size', stored=True)

    # tag who can't be put at the same time this one
    under_tagger = fields.Many2many('smart.tagger')
    upper_tagger = fields.Many2many('smart.tagger')

    @api.multi
    def update_all(self):
        for tagger in self:
            data_to_update = self.env[tagger.model].search(
                tagger.condition.domain)
            if data_to_update:
                tags = []
                for data in data_to_update:
                    if tagger.related_tag_field in data:
                        data_tags = data[tagger.related_tag_field]
                        taggers = get_all_tagger(data_tags)
                        if tagger.id not in taggers and not \
                                set(tagger.upper_tagger).intersection(taggers):
                            tag = self.env['smart.tags'].create({
                                'related_data': data,
                                'related_field': data[tagger.condition_field]
                            })
                            tags.append(tag)
                            value = [data[tagger.related_tag_field], tag.id]
                            value = [x for x in value if x not in tagger.under_tagger]
                            data.write({
                                tagger.related_tag_field: value
                                        })
                    else:
                        raise exceptions.ValidationError(
                            "Model %s has no field %s", tagger.model,
                            tagger.related_tag_field)
            tagger.write({'tags': tags})

    @api.onchange(tags)
    def _tags_size(self):
        self.number_tags = len(self.tags)

    @api.multi
    def open_tags(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "smart.tags",
            "view_type": "form",
            "view_mode": "form",
            "target": "new",
            "domain": "['id', in, tags]"
        }


def get_all_tagger(data):
    result = []
    for tag in data:
        if tag.tagger not in result:
            result.append(tag.tagger.id)

    return result
