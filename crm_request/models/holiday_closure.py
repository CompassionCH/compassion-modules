# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields


class Class(models.Model):
    _name = "holiday.closure"

    start_date = fields.Date(string="Start of holiday")
    end_date = fields.Date(string="End of holiday")
    holiday_name = fields.Char(string="Name of holiday")
    partner_id = fields.Many2one('res.partner', 'Partner', required=True)
