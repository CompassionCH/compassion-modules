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

from odoo import models, fields, api
from odoo.tools import safe_eval


class SmartTagger(models.Model):
    _inherit = "res.partner.category"

    condition_id = fields.Many2one('ir.filters', string="Condition")
    smart = fields.Boolean()
    partner_ids = fields.Many2many("res.partner",
                                   relation='res_partner_res_partner_'
                                            'category_rel',
                                   column1='category_id',
                                   column2='partner_id')

    number_tags = fields.Integer(compute='_compute_number_tags', stored=True)

    @api.constrains('condition_id')
    def check_condition(self):
        for me in self:
            if me.condition_id.model_id != 'res.partner':
                model_link = self.env[me.condition_id.model_id]
                if 'partner_id' not in model_link:
                    raise ValueError("Le model que vous voulez utiliser "
                                     "n'as pas de lien avec Partner")

    @api.multi
    def update_partner_tags(self):
        for tagger in self.filtered('smart'):
            parents = self.search([('id', 'parent_of', tagger.id)])
            domain = safe_eval(tagger.condition_id.domain)
            model = tagger.condition_id.model_id
            data_to_update = self.env[model].search(domain)
            if data_to_update:
                partners = []
                for data in data_to_update:
                    if not model == 'res.partner':
                        data = data.partner_id
                    if not data.category_id & parents:
                        partners.append(data.id)
                tagger.write({'partner_ids': [(6, 0, partners)]})
        return True

    @api.model
    def update_all_smart_tags(self):
        return self.search([('smart', '=', True)]).update_partner_tags()

    @api.depends('partner_ids')
    def _compute_number_tags(self):
        for category in self:
            category.number_tags = len(category.partner_ids)

    @api.multi
    def open_tags(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "res.partner",
            "view_type": "form",
            "view_mode": "list,form",
            "name": "Partners",
            "domain": [["id", "in", self.partner_ids.ids]]
        }
