##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


from werkzeug.exceptions import BadRequest

from odoo import api, models


class FieldOffice(models.Model):
    _inherit = "compassion.field.office"

    @api.model
    def mobile_get_learning(self, **other_params):
        if "country" not in other_params:
            raise BadRequest()

        country = other_params["country"]
        country_id = self.env["res.country"].search([("name", "=", country)])
        field_offices = self.search([("country_id", "=", country_id.id)])
        res = []
        for field in field_offices:
            res.append(
                {
                    "ID": field.id,
                    "PROJECT_ID": country,
                    "SUMMARY": field.learning_summary,
                    "IMAGE": field.learning_image_url,
                    "SCHEDULE": field._get_schedules_json(),
                }
            )
        return res

    def _get_schedules_json(self):
        res = []
        for schedule in self.learning_ids:
            res.append(schedule.get_learning_json())
        return res
