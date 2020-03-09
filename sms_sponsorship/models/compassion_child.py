##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models


class CompassionHold(models.Model):
    _inherit = "compassion.child"

    @api.multi
    def get_sms_sponsor_child_data(self):
        """
        Returns JSON data of the child for the mobile sponsor page
        :return: JSON data
        """
        self.ensure_one()
        result = self.read(
            [
                "name",
                "birthdate",
                "preferred_name",
                "desc_en",
                "gender",
                "image_url",
                "age",
            ]
        )[0]
        result.update(
            {
                "has_a_child": True,
                "invalid_sms_child_request": False,
                "country": self.field_office_id.country_id.name,
                "countries": self.field_office_id.search(
                    [("available_on_childpool", "=", True)]
                )
                .mapped("country_id")
                .mapped(
                    lambda country: {"value": country.code, "text": country.name}),
                "description": result["desc_en"],
            }
        )
        return result
