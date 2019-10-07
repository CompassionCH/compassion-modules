# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


from odoo import api, models
from werkzeug.exceptions import BadRequest


class FieldOffice(models.Model):
    _inherit = 'compassion.field.office'

    @api.model
    def mobile_get_learning(self, **other_params):
        if 'country' not in other_params:
            raise BadRequest()

        country = other_params['country']
        country_id = self.env['res.country'].search([
            ('name', '=', country)
        ])
        field_office = self.search([
            ('country_id', '=', country_id.id)
        ])
        res = []
        for field_id in field_office.ids:
            res.append({
                'ID': field_id,
                'PROJECT_ID': country,
                'SUMMARY': field_office.learning_summary,
                'IMAGE': field_office.learning_image_url,
                'SCHEDULE': field_office._get_schedules_json()
            })
        return res

    def _get_schedules_json(self):
        res = []
        for schedule in self.learning_ids:
            res.append(schedule.get_learning_json())
        return res
