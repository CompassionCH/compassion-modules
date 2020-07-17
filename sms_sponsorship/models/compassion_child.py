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
        # Get crm.event from child
        hold_event = self.hold_event
        # Get set of countries of all field offices
        countries = self.field_office_id.search(
            [
                ("available_on_childpool", "=", True)
            ]
        ).mapped("country_id")
        event_countries = False
        # Get set of countries of field offices in the event
        if hold_event and hold_event.disable_childpool_search:
            event_countries = hold_event.allocate_child_ids.\
                mapped("field_office_id.country_id")
        # Intersect countries
        if event_countries:
            countries &= event_countries
        # Create dictionary of countries with value and text keys
        countries = countries.mapped(lambda country: {"value": country.code,
                                                      "text": country.name})
        # Update result
        result.update(
            {
                "has_a_child": True,
                "invalid_sms_child_request": False,
                "country": self.field_office_id.country_id.name,
                "countries": countries,
                "description": result["desc_en"],
            }
        )
        return result
