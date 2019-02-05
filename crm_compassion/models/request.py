# -*- coding: utf-8 -*-

#    Copyright (C) 2019 Compassion CH
#    @author: Stephane Eicher <seicher@compassion.ch>

from odoo import models, fields


class CrmRequest(models.Model):
    _inherit = ['crm.claim']

    name = fields.Char(string='Subject')
    date = fields.Datetime(string='Date')
    code = fields.Char(string='Number')
    claim_type = fields.Many2one(string='Type')
