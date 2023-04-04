##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields


class DemandPlanningSettings(models.TransientModel):
    """Settings configuration for Demand Planning."""

    _inherit = "res.config.settings"

    number_children_website = fields.Integer()
    number_children_ambassador = fields.Integer()
    days_allocate_before_event = fields.Integer()
    days_hold_after_event = fields.Integer()

    @api.multi
    def set_values(self):
        super().set_values()
        config = self.env["ir.config_parameter"]
        config.set_param(
            "crm_compassion.number_children_web", str(self.number_children_website)
        )
        config.set_param(
            "crm_compassion.number_children_ambassador",
            str(self.number_children_ambassador),
        )
        config.set_param(
            "crm_compassion.days_allocate_before_event",
            str(self.days_allocate_before_event),
        )
        config.set_param(
            "crm_compassion.days_hold_after_event", str(self.days_hold_after_event)
        )

    @api.model
    def get_values(self):
        res = super().get_values()
        config = self.env["ir.config_parameter"].sudo()

        res["number_children_website"] = int(
            config.get_param("crm_compassion.number_children_web", "500")
        )
        res["number_children_ambassador"] = int(
            config.get_param(
                "crm_compassion.number_children_ambassador",
                "10",
            )
        )
        res["days_allocate_before_event"] = int(
            config.get_param(
                "crm_compassion.days_allocate_before_event",
                "10",
            )
        )
        res["days_hold_after_event"] = int(
            config.get_param("crm_compassion.days_hold_after_event", "10")
        )
        return res
