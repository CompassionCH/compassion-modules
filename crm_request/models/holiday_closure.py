# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HolidayClosure(models.Model):
    _name = "holiday.closure"

    start_date = fields.Date(string="Start of holiday", required=True)
    end_date = fields.Date(string="End of holiday", required=True)
    holiday_name = fields.Char(string="Name of holiday", required=True)

    @api.constrains('end_date', 'start_date')
    def _validate_dates(self):
        for h in self:
            if h.start_date and h.end_date and (h.start_date >= h.end_date):
                raise ValidationError("Please choose an end_date greater than"
                                      " the start_date")
