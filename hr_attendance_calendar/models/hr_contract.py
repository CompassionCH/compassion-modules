# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    @author: Stephane Eicher <seicher@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import fields, models, api


class HrContract(models.Model):
    _inherit = 'hr.contract'

    limit_extra_hours = fields.Integer(string='Limit extra hours')
